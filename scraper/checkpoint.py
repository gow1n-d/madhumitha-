"""
checkpoint.py – Resumable scraping checkpoint management.

Checkpoints store the list of already-collected record IDs and the last
processed page/URL per adapter. If the scraper is interrupted, the next
run can skip already-processed pages.
"""

from __future__ import annotations
import json
from pathlib import Path

from scraper import config
from scraper.utils import log, utc_now


def _ckpt_path(adapter_name: str) -> Path:
    config.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return config.CHECKPOINT_DIR / f"{adapter_name}.json"


def load_checkpoint(adapter_name: str) -> dict:
    path = _ckpt_path(adapter_name)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            log.info("[Checkpoint] Loaded for %s: page=%s, records=%d",
                     adapter_name, data.get("last_page"), len(data.get("record_ids", [])))
            return data
        except Exception as exc:
            log.warning("[Checkpoint] Failed to load for %s: %s", adapter_name, exc)
    return {"adapter": adapter_name, "last_page": 0, "record_ids": [], "updated_at": None}


def save_checkpoint(adapter_name: str, last_page: int, record_ids: list[str]) -> None:
    data = {
        "adapter": adapter_name,
        "last_page": last_page,
        "record_ids": record_ids,
        "updated_at": utc_now(),
    }
    path = _ckpt_path(adapter_name)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.debug("[Checkpoint] Saved for %s (page=%d, records=%d).",
              adapter_name, last_page, len(record_ids))


def clear_checkpoint(adapter_name: str) -> None:
    path = _ckpt_path(adapter_name)
    if path.exists():
        path.unlink()
        log.info("[Checkpoint] Cleared for %s.", adapter_name)
