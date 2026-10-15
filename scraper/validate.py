"""
validate.py – Post-collection validation of generated dataset files.

Run as:
    python -m scraper.validate
"""

from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

from scraper.config import (
    HERITAGE_CSV, HERITAGE_JSON, HERITAGE_XLSX,
    SOURCE_REG_JSON, IMAGE_MANIFEST_JSON, FAILED_URLS_LOG,
)
from scraper.utils import log, contains_tamil


def validate_all() -> bool:
    """
    Validate all output files.
    Returns True if all checks pass, False otherwise.
    """
    ok = True
    ok &= _validate_json(HERITAGE_JSON, "heritage_records.json")
    ok &= _validate_csv(HERITAGE_CSV, "heritage_records.csv")
    ok &= _validate_xlsx(HERITAGE_XLSX, "heritage_records.xlsx")
    ok &= _validate_json(SOURCE_REG_JSON, "source_registry.json")
    ok &= _validate_json_or_absent(IMAGE_MANIFEST_JSON, "image_manifest.json")
    ok &= _validate_failed_urls(FAILED_URLS_LOG)
    return ok


def _validate_json(path: Path, label: str) -> bool:
    if not path.exists():
        log.error("[Validate] MISSING: %s", path)
        return False
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, list):
            log.error("[Validate] %s – expected JSON array, got %s", label, type(data))
            return False
        # Check every item has record_id or source_id
        id_field = "record_id" if "record_id" in (data[0] if data else {}) else "source_id"
        missing_ids = sum(1 for r in data if not r.get(id_field))
        no_source_url = sum(1 for r in data if "source_url" in r and not r.get("source_url"))

        # Tamil round-trip check
        tamil_ok = 0
        for r in data:
            for v in r.values():
                if isinstance(v, str) and contains_tamil(v):
                    tamil_ok += 1
                    break

        log.info("[Validate] %-35s records=%d, missing_%s=%d, no_source_url=%d, tamil_records=%d",
                 label, len(data), id_field, missing_ids, no_source_url, tamil_ok)
        return True
    except json.JSONDecodeError as exc:
        log.error("[Validate] %s – JSON parse error: %s", label, exc)
        return False


def _validate_csv(path: Path, label: str) -> bool:
    if not path.exists():
        log.error("[Validate] MISSING: %s", path)
        return False
    try:
        with path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            log.warning("[Validate] %s – 0 data rows.", label)
            return True
        missing_title = sum(1 for r in rows if not r.get("title"))
        log.info("[Validate] %-35s rows=%d, missing_title=%d, columns=%d",
                 label, len(rows), missing_title, len(reader.fieldnames or []))
        return True
    except Exception as exc:
        log.error("[Validate] %s – error: %s", label, exc)
        return False


def _validate_xlsx(path: Path, label: str) -> bool:
    if not path.exists():
        log.warning("[Validate] MISSING (xlsx may have been skipped): %s", path)
        return True   # non-fatal
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        row_count = ws.max_row - 1  # subtract header
        col_count = ws.max_column
        log.info("[Validate] %-35s rows=%d, cols=%d", label, row_count, col_count)
        wb.close()
        return True
    except Exception as exc:
        log.error("[Validate] %s – error: %s", label, exc)
        return False


def _validate_json_or_absent(path: Path, label: str) -> bool:
    if not path.exists():
        log.info("[Validate] %s – not present (may be empty run).", label)
        return True
    return _validate_json(path, label)


def _validate_failed_urls(path: Path) -> bool:
    if not path.exists():
        log.info("[Validate] failed_urls.jsonl – not present (no failures recorded).")
        return True
    count = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                count += 1
            except json.JSONDecodeError:
                log.warning("[Validate] Malformed line in failed_urls.jsonl")
    log.info("[Validate] failed_urls.jsonl – %d failure entries.", count)
    return True


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
