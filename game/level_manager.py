
import importlib

from config import settings

_CACHE = {}


def load_level(level_key: str) -> dict:
    if level_key not in settings.LEVELS:
        level_key = settings.LEVELS[0]
    if level_key in _CACHE:
        return _CACHE[level_key]
    module = importlib.import_module(f"maps.{level_key}")
    level_def = module.build()
    _CACHE[level_key] = level_def
    return level_def


def all_level_keys():
    return list(settings.LEVELS)
