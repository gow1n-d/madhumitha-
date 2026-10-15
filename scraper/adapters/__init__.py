"""
adapters/__init__.py – Source adapter registry.
"""
from scraper.adapters.tnarch_inscriptions import TNArchInscriptionAdapter
from scraper.adapters.tnarch_brahmi import TNArchBrahmiAdapter
from scraper.adapters.keeladi import KeeladiAdapter
from scraper.adapters.asi_bharatshri import ASIAdapter

ALL_ADAPTERS = [
    TNArchInscriptionAdapter,
    TNArchBrahmiAdapter,
    KeeladiAdapter,
    ASIAdapter,
]
