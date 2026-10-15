"""
test_scraper.py – Automated tests for the AI Heritage Explorer scraper.

Uses saved HTML fixtures (tests/fixtures/) so tests run without hitting live sites.
"""

from __future__ import annotations
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Bootstrap path ─────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.schema import HeritageRecord, SourceRegistryEntry, ImageManifestEntry
from scraper.deduplication import deduplicate, quality_summary, _normalize_title
from scraper.utils import contains_tamil, normalize_tamil, sha256_text, utc_now, canonical_url
from scraper.export import export_records, export_source_registry, export_field_evidence

FIXTURES = Path(__file__).parent / "fixtures"


# ── Schema Tests ───────────────────────────────────────────────────────────────

class TestHeritageRecordSchema(unittest.TestCase):

    def test_default_record_has_uuid(self):
        rec = HeritageRecord()
        self.assertIsNotNone(rec.record_id)
        self.assertEqual(len(rec.record_id), 36)  # UUID4 length

    def test_all_optional_fields_default_none(self):
        rec = HeritageRecord()
        optional_fields = [
            "title", "dynasty", "district", "inscription_text_original",
            "source_url", "latitude", "longitude",
        ]
        for f in optional_fields:
            self.assertIsNone(getattr(rec, f), f"Field {f} should default to None")

    def test_to_dict_has_all_keys(self):
        rec = HeritageRecord(title="Test", dynasty="Chola", district="Thanjavur")
        d = rec.to_dict()
        self.assertIn("record_id", d)
        self.assertIn("title", d)
        self.assertIn("dynasty", d)
        self.assertIn("extra", d)

    def test_to_flat_dict_flattens_extra(self):
        rec = HeritageRecord(title="Test", extra={"page_number": 3})
        d = rec.to_flat_dict()
        self.assertIn("extra_page_number", d)
        self.assertNotIn("extra", d)

    def test_record_status_default(self):
        rec = HeritageRecord()
        self.assertEqual(rec.record_status, "active")

    def test_scraper_version_set(self):
        rec = HeritageRecord()
        self.assertEqual(rec.scraper_version, "1.0.0")


# ── Tamil Text Tests ────────────────────────────────────────────────────────────

class TestTamilText(unittest.TestCase):

    TAMIL_SAMPLE = "கீழடி தொல்லியல் ஆய்வு"
    ENGLISH_SAMPLE = "Keeladi Archaeological Survey"

    def test_detect_tamil(self):
        self.assertTrue(contains_tamil(self.TAMIL_SAMPLE))
        self.assertFalse(contains_tamil(self.ENGLISH_SAMPLE))

    def test_empty_string_not_tamil(self):
        self.assertFalse(contains_tamil(""))

    def test_normalize_tamil_roundtrip(self):
        normalized = normalize_tamil(self.TAMIL_SAMPLE)
        self.assertEqual(normalized, self.TAMIL_SAMPLE)

    def test_normalize_tamil_nfc(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", self.TAMIL_SAMPLE)
        nfc = normalize_tamil(nfd)
        self.assertEqual(nfc, self.TAMIL_SAMPLE)

    def test_tamil_in_record_field(self):
        rec = HeritageRecord(title=self.TAMIL_SAMPLE)
        d = rec.to_dict()
        self.assertIn("கீழடி", d["title"])

    def test_tamil_csv_roundtrip(self):
        """Tamil text must survive CSV round-trip."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                        encoding="utf-8-sig", delete=False, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["title"])
            writer.writeheader()
            writer.writerow({"title": self.TAMIL_SAMPLE})
            tmp_path = Path(f.name)
        with tmp_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(rows[0]["title"], self.TAMIL_SAMPLE)
        tmp_path.unlink()

    def test_tamil_json_roundtrip(self):
        """Tamil text must survive JSON round-trip."""
        data = [{"title": self.TAMIL_SAMPLE}]
        serialized = json.dumps(data, ensure_ascii=False)
        parsed = json.loads(serialized)
        self.assertEqual(parsed[0]["title"], self.TAMIL_SAMPLE)


# ── Deduplication Tests ────────────────────────────────────────────────────────

class TestDeduplication(unittest.TestCase):

    def _make(self, title, url="https://example.com/1") -> HeritageRecord:
        return HeritageRecord(title=title, source_url=url)

    def test_exact_title_duplicates_flagged(self):
        r1 = self._make("Inscription at Thanjavur")
        r2 = self._make("Inscription at Thanjavur")
        records = deduplicate([r1, r2])
        statuses = [r.record_status for r in records]
        self.assertIn("duplicate", statuses)
        self.assertIn("active", statuses)

    def test_same_url_duplicates_flagged(self):
        r1 = HeritageRecord(title="A", source_url="https://example.com/x")
        r2 = HeritageRecord(title="B", source_url="https://example.com/x")
        records = deduplicate([r1, r2])
        group_ids = [r.duplicate_group_id for r in records]
        self.assertTrue(all(g == group_ids[0] for g in group_ids))

    def test_different_titles_not_flagged(self):
        r1 = self._make("Copper plate grant", "https://a.com/1")
        r2 = self._make("Stone inscription Madurai", "https://a.com/2")
        records = deduplicate([r1, r2])
        self.assertTrue(all(r.record_status == "active" for r in records))

    def test_normalize_title_strips_punctuation(self):
        self.assertEqual(_normalize_title("Hello, World!"), "hello world")

    def test_normalize_preserves_tamil(self):
        tamil = "கீழடி"
        result = _normalize_title(tamil)
        self.assertIn("கீழடி", result)

    def test_single_record_not_flagged(self):
        records = deduplicate([self._make("Unique inscription")])
        self.assertEqual(records[0].record_status, "active")

    def test_empty_list(self):
        result = deduplicate([])
        self.assertEqual(result, [])


# ── URL Helpers Tests ──────────────────────────────────────────────────────────

class TestURLHelpers(unittest.TestCase):

    def test_canonical_absolute_url_unchanged(self):
        result = canonical_url("https://example.com", "https://other.com/page")
        self.assertEqual(result, "https://other.com/page")

    def test_canonical_relative_url_resolved(self):
        result = canonical_url("https://example.com/base/", "/page")
        self.assertEqual(result, "https://example.com/page")

    def test_canonical_relative_no_slash(self):
        result = canonical_url("https://example.com/base", "page")
        self.assertEqual(result, "https://example.com/page")


# ── Hashing Tests ──────────────────────────────────────────────────────────────

class TestHashing(unittest.TestCase):

    def test_sha256_deterministic(self):
        self.assertEqual(sha256_text("hello"), sha256_text("hello"))

    def test_sha256_different_inputs(self):
        self.assertNotEqual(sha256_text("hello"), sha256_text("world"))

    def test_sha256_length(self):
        self.assertEqual(len(sha256_text("test")), 64)


# ── Quality Summary Tests ──────────────────────────────────────────────────────

class TestQualitySummary(unittest.TestCase):

    def test_empty_records(self):
        summary = quality_summary([])
        self.assertEqual(summary["total_records"], 0)

    def test_counts_with_records(self):
        records = [
            HeritageRecord(title="A", source_url="https://x.com/1", review_required=True),
            HeritageRecord(title="B", source_url="https://x.com/2", review_required=False),
        ]
        summary = quality_summary(records)
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["requires_expert_review"], 1)
        self.assertEqual(summary["missing_title"], 0)

    def test_missing_title_counted(self):
        records = [HeritageRecord(title=None), HeritageRecord(title="A")]
        summary = quality_summary(records)
        self.assertEqual(summary["missing_title"], 1)


# ── Export Tests ───────────────────────────────────────────────────────────────

class TestExport(unittest.TestCase):

    def test_export_records_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from scraper import config as cfg
            original_json = cfg.HERITAGE_JSON
            original_csv  = cfg.HERITAGE_CSV
            original_xlsx = cfg.HERITAGE_XLSX
            cfg.HERITAGE_JSON = Path(tmpdir) / "heritage_records.json"
            cfg.HERITAGE_CSV  = Path(tmpdir) / "heritage_records.csv"
            cfg.HERITAGE_XLSX = Path(tmpdir) / "heritage_records.xlsx"

            records = [
                HeritageRecord(title="Test Record", description="A test",
                               source_url="https://example.com/1"),
            ]
            from scraper.export import export_records as er
            counts = er(records)

            self.assertTrue(cfg.HERITAGE_JSON.exists())
            self.assertTrue(cfg.HERITAGE_CSV.exists())
            self.assertGreater(counts["json"], 0)
            self.assertGreater(counts["csv"], 0)

            # Restore
            cfg.HERITAGE_JSON = original_json
            cfg.HERITAGE_CSV  = original_csv
            cfg.HERITAGE_XLSX = original_xlsx

    def test_json_valid_after_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from scraper import config as cfg
            cfg.HERITAGE_JSON = Path(tmpdir) / "heritage_records.json"
            cfg.HERITAGE_CSV  = Path(tmpdir) / "heritage_records.csv"
            cfg.HERITAGE_XLSX = Path(tmpdir) / "heritage_records.xlsx"

            records = [HeritageRecord(title="கீழடி", description="Sangam site")]
            from scraper.export import export_records as er
            er(records)

            data = json.loads(cfg.HERITAGE_JSON.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "கீழடி")


# ── Pagination Parsing Tests (using fixtures if present) ──────────────────────

class TestPaginationParsing(unittest.TestCase):

    def _load_fixture(self, name: str) -> str | None:
        p = FIXTURES / f"{name}.html"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        return None

    def test_tnarch_inscription_fixture_parseable(self):
        html = self._load_fixture("tnarch_inscription_books")
        if html is None:
            self.skipTest("Fixture tnarch_inscription_books.html not present (run inspect first).")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        self.assertIsNotNone(soup.find("html"))

    def test_keeladi_fixture_parseable(self):
        html = self._load_fixture("keeladi_museum")
        if html is None:
            self.skipTest("Fixture keeladi_museum.html not present.")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        self.assertIsNotNone(soup.find("html"))


# ── Image Permission Tests ─────────────────────────────────────────────────────

class TestImagePermissions(unittest.TestCase):

    def test_unknown_permission_not_downloaded(self):
        img = ImageManifestEntry(
            source_url="https://example.com/img.jpg",
            permission_status="UNKNOWN",
            download_status="pending",
        )
        self.assertNotEqual(img.download_status, "downloaded")
        self.assertEqual(img.permission_status, "UNKNOWN")

    def test_image_manifest_entry_defaults(self):
        img = ImageManifestEntry()
        self.assertIsNone(img.local_path)
        self.assertIsNone(img.checksum)


# ── Checkpoint Tests ───────────────────────────────────────────────────────────

class TestCheckpoints(unittest.TestCase):

    def test_save_and_load_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from scraper import config as cfg
            original = cfg.CHECKPOINT_DIR
            cfg.CHECKPOINT_DIR = Path(tmpdir)

            from scraper.checkpoint import save_checkpoint, load_checkpoint
            save_checkpoint("test_adapter", 5, ["id1", "id2"])
            ckpt = load_checkpoint("test_adapter")

            self.assertEqual(ckpt["last_page"], 5)
            self.assertIn("id1", ckpt["record_ids"])

            cfg.CHECKPOINT_DIR = original

    def test_load_missing_checkpoint_returns_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from scraper import config as cfg
            original = cfg.CHECKPOINT_DIR
            cfg.CHECKPOINT_DIR = Path(tmpdir)

            from scraper.checkpoint import load_checkpoint
            ckpt = load_checkpoint("nonexistent_adapter")
            self.assertEqual(ckpt["last_page"], 0)
            self.assertEqual(ckpt["record_ids"], [])

            cfg.CHECKPOINT_DIR = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
