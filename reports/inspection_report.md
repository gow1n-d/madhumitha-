# AI Heritage Explorer – Archaeological Source Inspection Report

**Generated:** 2026-10-15T07:02:11Z  
**System:** AI Heritage Explorer Web Scraping & Archaeological Data Ingest Engine  
**Scraper Version:** 1.0.0  

---

## 1. Executive Summary

This report documents the discovery, connectivity, protocol feasibility, and structural architecture of official archaeological websites surveyed for the **AI Heritage Explorer** project. The project focuses on collecting, structuring, and preserving authentic ancient Tamil and South Indian heritage data (inscriptions, estampages, copper plates, excavation records, and museum documentation).

### Target Sources Surveyed
| Source ID | Organization | Base URL | Live Status | Ingest Feasibility |
|:----------|:-------------|:---------|:------------|:-------------------|
| `asi_bharatshri` | Archaeological Survey of India (ASI) | `https://bharatshri.asi.gov.in` | **200 OK (Accessible)** | **High** – Rich static HTML scholarship & discoveries |
| `tnarch_inscriptions` | TN Department of Archaeology | `https://tnarch.gov.in` | **Connection Timeout** | **Blocked** – TLS timeout / geo-restriction |
| `keeladi_museum` | Keeladi Site Museum | `https://www.keeladimuseum.tn.gov.in` | **200 OK (React Bundle)** | **High** – Ingested via application bundle AST (12 bilingual records) |

---

## 2. Detailed Source Assessments

### 2.1 Archaeological Survey of India – BharatSHRI (`asi_bharatshri`)
- **Portal Identity:** Bharat Shared Repository of Inscriptions (BharatSHRI), Ministry of Culture, Govt. of India.
- **Repository Scope:** 
  - **24,816** metadata records
  - **24,225** published transcripts
  - **20,861** archival ink estampages
- **Epigraphy Branch Coverage:** Mysore Epigraphy Branch handles Dravidian and South Indian Inscriptions.
  - *South Indian Inscriptions (SII):* 45 published volumes (majority in ancient Tamil).
  - *Epigraphia Indica:* 43 critically edited volumes.
  - *Annual Report on Indian Epigraphy (ARIE):* Century-long systematic survey copies.
  - Documented scripts: **Tamil-Brahmi**, **Grantha**, **Vatteluttu**, **Nandinagari**, **Tamil**, **Kannada**, **Telugu**, **Brahmi**, and **Kufic/Persian**.
- **Robots.txt Analysis:**
  - URL: `https://bharatshri.asi.gov.in/robots.txt`
  - Status: HTTP 200 OK (`User-agent: * Allow: /`). Automated academic crawling permitted with respectful rate limits.
- **Technical Architecture:**
  - Content pages (`/index`, `/AboutEpigraphy.aspx`, `/inscription.aspx`, `/AboutEstampages.aspx`, `/discoveries.aspx`) render full static HTML.
  - Search interface (`/FrontEndSearch.aspx`) uses ASP.NET postback with `__VIEWSTATE` tokens and session cookies.
- **Media & Estampage Assets:**
  - High-resolution photographic plates and ink estampage images hosted under `assets/img/`, `discovery/`, and `discovery2/`.
- **Copyright & License:**
  - Official Government of India repository. Open for scholarly consultation. Terms not explicitly commercial; attribution required.

---

### 2.2 Tamil Nadu Department of Archaeology (`tnarch_inscriptions`)
- **Portal Identity:** Department of Archaeology, Government of Tamil Nadu (`tnarch.gov.in`).
- **Anticipated Holdings:**
  - 1,200+ digitized Inscription Books (*Kalvettu Noolgal*).
  - Tamil-Brahmi rock-cut cavern inscriptions across Madurai, Pudukkottai, and Tirunelveli.
  - Excavation site reports (Keeladi, Korkai, Alagankulam, Kodumanal).
- **Inspection Findings:**
  - Direct HTTP/HTTPS requests to `tnarch.gov.in` and `www.tnarch.gov.in` fail during TLS handshake (connection timeout after 30+ seconds).
  - Root Cause: Host server is either down, subject to regional IP geo-blocking, or rejecting automated requests at the firewall layer.
- **Ingest Strategy:**
  - Documented as an inaccessible live source. Offline ingestion recommended via locally mirrored PDF publications and archival CD-ROM datasets.

---

### 2.3 Keeladi Museum (`keeladimuseum.tn.gov.in`)
- **Portal Identity:** Keeladi Site Museum, Sivagangai District, Tamil Nadu.
- **Anticipated Holdings:**
  - Vaigai River Valley civilization artifacts dated to 6th century BCE (Sangam era).
  - Tamil-Brahmi inscribed potsherds, weaving tools, carnelian beads, brick structures.
- **Inspection & Reverse-Engineering Findings:**
  - Site is a React SPA (built with create-react-app).
  - The static HTML payload is a shell (`<div id="root"></div>`), but the full bilingual scholarly corpus and 509 media references are statically bundled in `/static/js/main.edb7d69e.js`.
  - Scraper reverse-engineered the AST bundle, decoded unicode sequences (`஀` to `௿`), and extracted 12 structured bilingual exhibits covering urban planning, brick architecture, pastoral osteology (Deccan College), material science (VIT), weaving, maritime trade, and Tamil-Brahmi epigraphy (Beta-499770: 580 BCE).
- **Ingest Status:**
  - **Successfully Ingested:** 12 verified heritage records and 509 discovered media image assets.

---

## 3. Crawler Politeness & Safety Protocols
1. **Configurable Delays:** Default delay of **2.0 seconds** per request between successive hits to official servers.
2. **Deterministic Caching:** SHA-256 hashed request caching (`.cache/`) ensures identical pages are never downloaded twice.
3. **Resilient Failure Logging:** Unreachable URLs logged to `logs/failed_urls.jsonl` with timestamps and error codes.
4. **Attribution & Provenance:** Every record retains its source URL, organization title, access date, and SHA-256 content checksum.

---

## 4. Next Steps & Recommended Actions
- [x] Extract all accessible ASI BharatSHRI epigraphy scholarship and copper plate discoveries.
- [x] Structure records under the standardized `HeritageRecord` schema.
- [x] Deduplicate records based on content hash and composite title/url keys.
- [x] Export datasets to JSON, CSV, XLSX, and SQLite with FTS5.
- [ ] Implement headless browser adapter (Playwright) for Keeladi Museum React SPA when browser automation environment is configured.
- [ ] Configure local proxy / VPN if external access to `tnarch.gov.in` becomes available.
