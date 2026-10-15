"""
base_adapter.py – Abstract base class for all source adapters.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator

from scraper.schema import HeritageRecord, SourceRegistryEntry
from scraper.utils import get_session, log


class BaseAdapter(ABC):
    """Every source adapter must implement this interface."""

    source_name: str = "unknown"
    organization: str = "Unknown"
    base_url: str = ""

    def __init__(self, sample_limit: int = 0):
        """
        Args:
            sample_limit: If > 0, stop after this many records (sample mode).
                          0 or negative means collect everything permitted.
        """
        self.sample_limit = sample_limit
        self.session = get_session()
        self._count = 0

    @abstractmethod
    def fetch_records(self) -> Iterator[HeritageRecord]:
        """Yield HeritageRecord objects from the source."""
        ...

    @abstractmethod
    def source_registry_entry(self) -> SourceRegistryEntry:
        """Return a SourceRegistryEntry describing this source."""
        ...

    def _should_stop(self) -> bool:
        if self.sample_limit > 0 and self._count >= self.sample_limit:
            log.info("[%s] Sample limit %d reached – stopping.", self.source_name, self.sample_limit)
            return True
        return False
