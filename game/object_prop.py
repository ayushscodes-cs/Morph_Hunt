"""
Object "personalities" — the props a Hider can transform into.

This module wraps config.settings.OBJECT_PERSONALITIES into a small,
convenient registry object used by both server (for authoritative
speed/energy calculations) and client (for visuals).
"""
from config import settings


class ObjectDefinition:
    __slots__ = ("key", "display", "camouflage", "speed_mult", "scale", "energy_mult", "model", "color")

    def __init__(self, key, data):
        self.key = key
        self.display = data["display"]
        self.camouflage = data["camouflage"]
        self.speed_mult = data["speed_mult"]
        self.scale = tuple(data["scale"])
        self.energy_mult = data["energy_mult"]
        self.model = data.get("model", "cube")
        self.color = tuple(data.get("color", (200, 200, 200)))

    def to_dict(self):
        return {
            "key": self.key,
            "display": self.display,
            "camouflage": self.camouflage,
            "speed_mult": self.speed_mult,
            "scale": self.scale,
            "energy_mult": self.energy_mult,
            "model": self.model,
            "color": self.color,
        }


class ObjectRegistry:
    """Loads every object personality once and exposes lookup helpers."""

    def __init__(self):
        self._objects = {
            key: ObjectDefinition(key, data)
            for key, data in settings.OBJECT_PERSONALITIES.items()
        }

    def get(self, key: str) -> ObjectDefinition:
        return self._objects.get(key)

    def all(self):
        return list(self._objects.values())

    def keys(self):
        return list(self._objects.keys())

    def is_valid(self, key: str) -> bool:
        return key in self._objects


# Singleton used across the codebase.
REGISTRY = ObjectRegistry()
