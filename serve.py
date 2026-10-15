"""
serve.py – Local web server & API daemon for AI Heritage Explorer.

Run with:
    python serve.py
    
Then open:
    http://localhost:8000/
"""

from __future__ import annotations
import http.server
import json
import os
from pathlib import Path
import socketserver
import sqlite3
import sys
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "db" / "heritage.db"
DEFAULT_PORT = 8000


class HeritageRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the frontend application, static assets, and archaeological JSON/FTS APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Root redirect to web/
        if path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/web/")
            self.end_headers()
            return

        # FTS5 Search API
        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0].strip()
            self._handle_search(q)
            return

        # Stats API
        if path == "/api/stats":
            self._handle_stats()
            return

        # Fallback to serving static files from workspace
        return super().do_GET()

    def _handle_search(self, q: str):
        if not DB_PATH.exists():
            self._send_json({"error": "Database not found. Run direct_collect.py first."}, 404)
            return

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            if q:
                # Sanitize FTS5 query
                safe_q = "".join(ch for ch in q if ch.isalnum() or ch in (" ", "_", "-"))
                if not safe_q.strip():
                    safe_q = q
                sql = """
                    SELECT r.*
                    FROM heritage_records r
                    JOIN heritage_records_fts fts ON r.record_id = fts.record_id
                    WHERE heritage_records_fts MATCH ?
                    ORDER BY rank
                    LIMIT 100
                """
                cur.execute(sql, (f"{safe_q}*",))
            else:
                sql = "SELECT * FROM heritage_records ORDER BY scraped_at DESC LIMIT 100"
                cur.execute(sql)

            rows = [dict(row) for row in cur.fetchall()]
            for r in rows:
                if r.get("extra") and isinstance(r["extra"], str):
                    try:
                        r["extra"] = json.loads(r["extra"])
                    except Exception:
                        pass
            self._send_json({"query": q, "count": len(rows), "records": rows})
        except Exception as e:
            # Fallback to simple LIKE search if MATCH syntax fails
            try:
                like_sql = """
                    SELECT * FROM heritage_records
                    WHERE title LIKE ? OR description LIKE ? OR local_name_ta LIKE ?
                    LIMIT 100
                """
                cur.execute(like_sql, (f"%{q}%", f"%{q}%", f"%{q}%"))
                rows = [dict(row) for row in cur.fetchall()]
                self._send_json({"query": q, "count": len(rows), "records": rows})
            except Exception as e2:
                self._send_json({"error": str(e2)}, 500)
        finally:
            conn.close()

    def _handle_stats(self):
        records_json = DATA_DIR / "heritage_records.json"
        count = 0
        if records_json.exists():
            try:
                data = json.loads(records_json.read_text(encoding="utf-8"))
                count = len(data)
            except Exception:
                pass
        self._send_json({
            "status": "online",
            "total_records": count,
            "provenance": "Archaeological Survey of India & Keeladi Site Museum",
            "antiquity": "580 BCE (AMS Radiocarbon Validated)",
        })

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def find_free_port(start_port: int = DEFAULT_PORT) -> int:
    import socket
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def main():
    port = find_free_port()
    print("=" * 70)
    print("  AI Heritage Explorer – Ancient Tamil & Keeladi Web Platform")
    print("=" * 70)
    print(f"  Web UI URL:   http://localhost:{port}/web/")
    print(f"  FTS API:      http://localhost:{port}/api/search?q=Keeladi")
    print(f"  Stats API:    http://localhost:{port}/api/stats")
    print(f"  Local dir:    {BASE_DIR}")
    print("=" * 70)
    print("  Serving... Press Ctrl+C to stop.")

    handler = HeritageRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
