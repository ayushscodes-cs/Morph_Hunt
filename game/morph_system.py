"""
Server-authoritative Morph System.

Handles all rules around transforming into objects, switching disguises,
and Morph Energy regen/drain. Pure functions operating on a PlayerState so
they're easy to reason about and to unit test.
"""
import time

from config import settings
from game.object_prop import REGISTRY


def try_transform(player, object_key: str) -> (bool, str):
    """Attempt an initial transform or a disguise switch. Returns (ok, reason)."""
    if player.role != "hider":
        return False, "Only Hiders can transform."
    if not REGISTRY.is_valid(object_key):
        return False, "Unknown object type."

    now = time.time()
    is_switch = player.transformed_into is not None and player.transformed_into != object_key
    cost = settings.MORPH_ENERGY_SWITCH_COST if is_switch else settings.MORPH_ENERGY_TRANSFORM_COST

    if is_switch and (now - player.last_switch_time) < settings.MORPH_SWITCH_COOLDOWN:
        remaining = settings.MORPH_SWITCH_COOLDOWN - (now - player.last_switch_time)
        return False, f"Switch on cooldown ({remaining:.1f}s left)."

    if player.morph_energy < cost:
        return False, "Not enough Morph Energy."

    player.morph_energy = max(0, player.morph_energy - cost)
    player.transformed_into = object_key
    player.last_switch_time = now
    return True, "ok"


def untransform(player) -> (bool, str):
    if player.role != "hider":
        return False, "Only Hiders can untransform."
    if not player.transformed_into:
        return False, "Not currently transformed."
    player.transformed_into = None
    return True, "ok"


def use_ability(player) -> (bool, str):
    """Generic special-ability energy gate hook (reserved for future abilities)."""
    if player.morph_energy < settings.MORPH_ENERGY_ABILITY_COST:
        return False, "Not enough Morph Energy."
    player.morph_energy -= settings.MORPH_ENERGY_ABILITY_COST
    return True, "ok"


def tick_energy(player, dt: float, is_moving: bool):
    """Call once per server tick for every hider to update Morph Energy."""
    if player.role != "hider":
        return

    now = time.time()
    if is_moving:
        player.still_since = now
        drain = settings.MORPH_ENERGY_MOVE_DRAIN_PER_SEC
        if player.transformed_into:
            obj = REGISTRY.get(player.transformed_into)
            if obj:
                drain *= obj.energy_mult
        player.morph_energy = max(0.0, player.morph_energy - drain * dt)
        # forced un-morph if energy hits zero while moving
        if player.morph_energy <= 0 and player.transformed_into:
            player.transformed_into = None
    else:
        if (now - player.still_since) >= settings.MORPH_ENERGY_REGEN_DELAY:
            player.morph_energy = min(
                settings.MORPH_ENERGY_MAX,
                player.morph_energy + settings.MORPH_ENERGY_REGEN_PER_SEC * dt,
            )
