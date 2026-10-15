"""
config.py – Central configuration for the AI Heritage Explorer scraper.

Values can be overridden via environment variables or a .env file.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project layout ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
DB_DIR = BASE_DIR / "db"
CACHE_DIR = BASE_DIR / ".cache"
CHECKPOINT_DIR = BASE_DIR / ".checkpoints"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

for _d in (DATA_DIR, LOGS_DIR, REPORTS_DIR, DB_DIR, CACHE_DIR, CHECKPOINT_DIR,
           DATA_DIR / "images" / "inscriptions",
           DATA_DIR / "images" / "archaeological_sites",
           DATA_DIR / "images" / "artifacts",
           DATA_DIR / "images" / "museums",
           DATA_DIR / "images" / "needs_permission"):
    _d.mkdir(parents=True, exist_ok=True)

# ── Scraper behaviour ─────────────────────────────────────────────────────────
SCRAPER_VERSION = "1.0.0"

USER_AGENT = os.getenv(
    "USER_AGENT",
    "AIHeritageExplorer-Researcher/1.0 (Tamil Heritage Dataset; academic use; "
    "contact: researcher@example.com)"
)

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))          # seconds
REQUEST_DELAY  = float(os.getenv("REQUEST_DELAY", "2.0"))          # seconds between requests
MAX_RETRIES    = int(os.getenv("MAX_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "2.0"))
VERIFY_TLS     = True                                               # NEVER set to False

# ── Pagination defaults ───────────────────────────────────────────────────────
DEFAULT_PAGE_LIMIT  = int(os.getenv("DEFAULT_PAGE_LIMIT", "999"))  # 999 = unlimited
SAMPLE_RECORD_LIMIT = int(os.getenv("SAMPLE_RECORD_LIMIT", "10"))

# ── Output files ──────────────────────────────────────────────────────────────
HERITAGE_CSV      = DATA_DIR / "heritage_records.csv"
HERITAGE_JSON     = DATA_DIR / "heritage_records.json"
HERITAGE_XLSX     = DATA_DIR / "heritage_records.xlsx"
SOURCE_REG_CSV    = DATA_DIR / "source_registry.csv"
SOURCE_REG_JSON   = DATA_DIR / "source_registry.json"
FIELD_EVIDENCE    = DATA_DIR / "field_evidence.jsonl"
IMAGE_MANIFEST_CSV  = DATA_DIR / "image_manifest.csv"
IMAGE_MANIFEST_JSON = DATA_DIR / "image_manifest.json"
SCRAPER_LOG       = LOGS_DIR / "scraper.log"
FAILED_URLS_LOG   = LOGS_DIR / "failed_urls.jsonl"
INSPECTION_REPORT = REPORTS_DIR / "inspection_report.md"
QUALITY_REPORT    = REPORTS_DIR / "data_quality_report.md"
DATASET_SUMMARY   = REPORTS_DIR / "dataset_summary.json"
SQLITE_DB         = DB_DIR / "heritage.db"

# ── Source URLs ───────────────────────────────────────────────────────────────
SOURCES = {
    "tnarch_inscription_books": "https://tnarch.gov.in/inscription/book?page=1",
    "tnarch_tamil_brahmi":      "https://www.tnarch.gov.in/tamil-brahmi-script",
    "tnarch_brahmi_inscription":"https://www.tnarch.gov.in/brahmi-inscription-0",
    "tnarch_node_1257":         "https://www.tnarch.gov.in/node/1257",
    "keeladi_museum":           "https://www.keeladimuseum.tn.gov.in/",
    "asi_bharatshri":           "https://bharatshri.asi.gov.in/index",
}
