# AI Heritage Explorer – Ancient Tamil & Keeladi Digital Archaeological Platform

A comprehensive, source-grounded data collection, dataset engineering, and web research system dedicated to preserving, documenting, and exploring **ancient Tamil heritage**, Sangam-era archaeology, and South Indian epigraphy.

---

## 🌟 Highlights & Features

- **🏛️ Interactive Web UI (`web/`)**: Dark-luxe Sangam obsidian and terracotta design system featuring:
  - **Bilingual Interface**: Seamless toggle between English and Tamil (தமிழ்).
  - **Artifact Card Grid**: 53 verified records with excavation citations, script/material tags, and full detail modals.
  - **Audio Narration (🔊)**: Web Speech API audio synthesis in English & Tamil.
  - **தமிழி (Tamil-Brahmi) Epigraphy Lab**: Paleographical breakdown of Keeladi potsherds (*குவிரன் ஆதன்*, *ஆதன்*, *திசன்*).
  - **Sangam Timeline**: Visual chronology from 580 BCE to modern digital preservation.
  - **Archaeometry Science Lab**: Scientific reports from Beta Analytic (Miami), Deccan College (Pune), VIT University (Vellore), and University of Pisa (Italy).
- **🏺 Keeladi Museum Ingestion**: Reverse-engineered React bundle AST extractor capturing 12 curated exhibits, AMS C-14 dating (Beta-499770: 580 BCE), and 509 discovered artifact media references.
- **📜 ASI BharatSHRI Pipeline**: Digitized epigraphical corpus covering South Indian Inscriptions (SII), Tamil-Brahmi, Grantha, Vatteluttu, and copper-plate charters.
- **🔍 Full-Text Search (FTS5)**: Embedded SQLite database (`db/heritage.db`) indexed for real-time sub-millisecond search across English and Tamil terms.
- **📊 Standard Multi-Format Exports**: JSON, CSV (UTF-8 BOM), Excel (XLSX), SQLite, Image Manifest, and Field Evidence JSONL.

---

## 🚀 Quick Start

### 1. Launch the Web Application

```bash
# Clone the repository
git clone https://github.com/gow1n-d/madhumitha-.git
cd madhumitha-

# Start the local server daemon
python serve.py
```

Then open **[http://localhost:8000/web/](http://localhost:8000/web/)** in any modern web browser!

---

### 2. Python Environment Setup

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Run the Data Collection Pipeline

To re-run the complete pipeline and regenerate all datasets, SQLite FTS5 database, and markdown reports:

```bash
python direct_collect.py
```

Or run unit tests:

```bash
python -m pytest tests/ -v
```

---

## 📊 Dataset Structure & Schema

All records strictly comply with the 74-field `HeritageRecord` standard schema:

| File | Format | Records | Description |
| :--- | :--- | :--- | :--- |
| `data/heritage_records.json` | JSON | 53 | Hierarchical complete dataset with citations and extra metadata |
| `data/heritage_records.csv` | CSV | 53 | Flat tabular format with UTF-8 BOM encoding for Excel/Pandas |
| `data/heritage_records.xlsx` | Excel | 53 | Styled multi-column spreadsheet |
| `db/heritage.db` | SQLite3 | 53 | Relational database with `heritage_records_fts` virtual table |
| `data/image_manifest.json` | JSON | 51 | Media asset tracking and discovered artifact links |
| `data/source_registry.json` | JSON | 3 | Source feasibility, robots.txt status, and access audits |
| `data/field_evidence.jsonl` | JSONL | 176 | Direct quotes and excavation citations extracted from source text |

---

## 🔬 Scientific Validation & Sources

1. **Keeladi Site Museum (`keeladimuseum.tn.gov.in`)**:
   - AMS Radiocarbon Dating: **580 BCE** (*Beta Analytic Miami*, Beta-499770).
   - Faunal Remains: **Deccan College Pune** osteology confirming 53% cattle/bulls and pastoral economy.
   - Construction Science: **VIT University** analysis showing 97% lime mortar and >80% silica brickwork.
   - Ceramic Petrography: **University of Pisa** thin-section confirmation of local Vaigai riverbed clay.
2. **Archaeological Survey of India – BharatSHRI (`bharatshri.asi.gov.in`)**:
   - 45 volumes of *South Indian Inscriptions (SII)*.
   - 43 volumes of *Epigraphia Indica*.
   - 20,861 archival ink estampages and transcripts.
3. **Tamil Nadu Department of Archaeology (`tnarch.gov.in`)**:
   - Monitored for network availability.

---

## 📜 Reports

- [Inspection Report](reports/inspection_report.md) – Discovery, robots.txt, TLS audits, and architecture.
- [Data Quality Report](reports/data_quality_report.md) – Validation scorecard, deduplication, and provenance verification.

---

## ⚖️ License & Provenance

Public Digital Cultural Heritage. Curated strictly for academic, research, and educational preservation. Citations and original government portal attributions are preserved with every record.
