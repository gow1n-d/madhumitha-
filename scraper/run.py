"""
run.py – Main CLI entry point for the AI Heritage Explorer scraper.

Usage:
    python -m scraper.run --sample 10     # sample mode: up to 10 records
    python -m scraper.run --all           # full permitted crawl
    python -m scraper.run --inspect       # inspection only (Phase 1)
    python -m scraper.run --validate      # validate output files only
    python -m scraper.run --export        # re-export existing records

Flags:
    --adapters tnarch_inscriptions keeladi    # run specific adapters only
    --no-cache                                 # force fresh fetches
    --clear-checkpoints                        # start from page 0 again
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from scraper.adapters import ALL_ADAPTERS
from scraper.checkpoint import load_checkpoint, save_checkpoint, clear_checkpoint
from scraper.config import FAILED_URLS_LOG, SCRAPER_VERSION
from scraper.deduplication import deduplicate, quality_summary
from scraper.export import (
    export_records, export_source_registry,
    export_field_evidence, export_image_manifest, write_quality_report,
)
from scraper.schema import HeritageRecord, SourceRegistryEntry, ImageManifestEntry
from scraper.utils import log, utc_now


def parse_args():
    p = argparse.ArgumentParser(
        description="AI Heritage Explorer – Data Collection System v" + SCRAPER_VERSION
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument("--sample", type=int, metavar="N",
                       help="Run in sample mode: collect up to N records per adapter.")
    group.add_argument("--all", action="store_true",
                       help="Run full permitted crawl.")
    group.add_argument("--inspect", action="store_true",
                       help="Run Phase 1 inspection only.")
    group.add_argument("--validate", action="store_true",
                       help="Validate existing output files only.")
    group.add_argument("--export", action="store_true",
                       help="Re-export records already in heritage_records.json.")

    p.add_argument("--adapters", nargs="+", metavar="NAME",
                   help="Run only these adapters (by source_name).")
    p.add_argument("--no-cache", action="store_true",
                   help="Force fresh HTTP fetches, ignoring disk cache.")
    p.add_argument("--clear-checkpoints", action="store_true",
                   help="Clear saved checkpoints before running.")
    return p.parse_args()


def count_failed_urls() -> int:
    if not FAILED_URLS_LOG.exists():
        return 0
    return sum(1 for line in FAILED_URLS_LOG.read_text(encoding="utf-8").splitlines() if line.strip())


def run_collection(
    sample_limit: int = 0,
    adapter_filter: list[str] | None = None,
    clear_ckpts: bool = False,
) -> tuple[list[HeritageRecord], list[SourceRegistryEntry]]:
    all_records: list[HeritageRecord] = []
    source_registry: list[SourceRegistryEntry] = []

    adapters_to_run = [
        A for A in ALL_ADAPTERS
        if (adapter_filter is None or A.source_name in adapter_filter)
    ]

    if not adapters_to_run:
        log.error("No adapters selected. Check --adapters filter.")
        return [], []

    for AdapterClass in adapters_to_run:
        adapter = AdapterClass(sample_limit=sample_limit)
        source_name = adapter.source_name

        if clear_ckpts:
            clear_checkpoint(source_name)

        ckpt = load_checkpoint(source_name)
        collected_ids: set[str] = set(ckpt.get("record_ids", []))

        log.info("=== Starting adapter: %s (sample_limit=%d, checkpoint_records=%d) ===",
                 source_name, sample_limit, len(collected_ids))

        batch: list[HeritageRecord] = []
        try:
            for rec in adapter.fetch_records():
                if rec.record_id in collected_ids:
                    log.debug("[%s] Skipping already-collected: %s", source_name, rec.record_id)
                    continue
                collected_ids.add(rec.record_id)
                batch.append(rec)

                # Save checkpoint every 50 records
                if len(batch) % 50 == 0:
                    save_checkpoint(source_name, 0, list(collected_ids))

        except KeyboardInterrupt:
            log.warning("[%s] Interrupted by user.", source_name)
            save_checkpoint(source_name, 0, list(collected_ids))
            break
        except Exception as exc:
            log.error("[%s] Unexpected error: %s", source_name, exc, exc_info=True)

        save_checkpoint(source_name, 0, list(collected_ids))

        # Register source
        entry = adapter.source_registry_entry()
        entry.records_collected = len(batch)
        source_registry.append(entry)

        log.info("[%s] Collected %d records.", source_name, len(batch))
        all_records.extend(batch)

    return all_records, source_registry


def main():
    args = parse_args()
    log.info("AI Heritage Explorer Scraper v%s – started at %s", SCRAPER_VERSION, utc_now())

    # ── Inspect only ──
    if args.inspect:
        from scraper.inspect_sources import inspect_all
        registry = inspect_all()
        export_source_registry(registry)
        log.info("Inspection complete. Report → reports/inspection_report.md")
        return

    # ── Validate only ──
    if args.validate:
        from scraper.validate import validate_all
        ok = validate_all()
        sys.exit(0 if ok else 1)

    # ── Re-export only ──
    if args.export:
        from scraper.config import HERITAGE_JSON
        if not HERITAGE_JSON.exists():
            log.error("heritage_records.json not found. Run collection first.")
            sys.exit(1)
        data = json.loads(HERITAGE_JSON.read_text(encoding="utf-8"))
        records = [HeritageRecord(**{k: v for k, v in r.items() if k in HeritageRecord.__dataclass_fields__})
                   for r in data]
        counts = export_records(records)
        log.info("Re-export complete: %s", counts)
        return

    # ── Collection ──
    sample_limit = args.sample if args.sample else (0 if args.all else 10)
    adapter_filter = args.adapters

    if not args.all and not args.sample:
        log.info("No mode specified. Defaulting to --sample 10 for safety.")
        sample_limit = 10

    log.info("Mode: %s | sample_limit=%d | adapters=%s",
             "sample" if sample_limit else "full",
             sample_limit,
             adapter_filter or "all")

    # ── Phase 1: Inspect (lightweight – runs regardless) ──
    try:
        from scraper.inspect_sources import inspect_all
        inspect_registry = inspect_all(sources_filter=adapter_filter)
        export_source_registry(inspect_registry)
    except Exception as exc:
        log.warning("Inspection phase failed (non-fatal): %s", exc)
        inspect_registry = []

    # ── Phase 2: Collect ──
    records, source_registry = run_collection(
        sample_limit=sample_limit,
        adapter_filter=adapter_filter,
        clear_ckpts=args.clear_checkpoints,
    )

    if not records:
        log.warning("No records collected from any source.")
    else:
        log.info("Total records collected (before dedup): %d", len(records))

    # ── Phase 7: Deduplication ──
    records = deduplicate(records)

    # ── Phase 8: Export ──
    counts = export_records(records)
    export_source_registry(source_registry or inspect_registry)
    export_field_evidence(records)
    export_image_manifest([], records)

    # ── Quality report ──
    quality = quality_summary(records)
    failed_count = count_failed_urls()
    write_quality_report(quality, source_registry or inspect_registry, failed_count)

    # ── Validate ──
    from scraper.validate import validate_all
    validate_all()

    log.info("=== Run complete. Records: %d | Dupes: %d | Exports: %s ===",
             quality["total_records"], quality["duplicate_records"], counts)
    log.info("Output files in: data/")
    log.info("Reports: reports/inspection_report.md, reports/data_quality_report.md")


if __name__ == "__main__":
    main()
