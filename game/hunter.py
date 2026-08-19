"""
Hunter-specific server-side logic: the scanner ability and the attack.

Both are deliberately imprecise / risk-based rather than omniscient, per
design: Hunters must observe and deduce, not be handed exact positions.
"""
import math
import random
import time

from config import settings
from game.hider import eliminate_hider

CLUE_PHRASES_NEAR = [
    "Unusual movement detected close by.",
    "Object anomaly detected — very close.",
    "Something nearby doesn't look right.",
]
CLUE_PHRASES_MID = [
    "Activity detected nearby.",
    "A faint anomaly registers on the scanner.",
    "Something in this area seems off.",
]
CLUE_PHRASES_FAR = [
    "Distant activity detected.",
    "Minor anomaly detected somewhere in range.",
    "The scanner flickers faintly.",
]
CLUE_NONE = ["No anomalies detected.", "Scanner reads clean."]


def _distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def try_scanner(hunter, all_players, now=None) -> (bool, list):
    """Attempt to use the scanner. Returns (ok, clues[]) — never exact coords."""
    now = now or time.time()
    if hunter.role != "hunter":
        return False, ["Only Hunters can scan."]
    if hunter.scanner_charges <= 0:
        return False, ["Scanner out of charges. Wait for recharge."]
    if (now - hunter.last_scanner_time) < settings.SCANNER_COOLDOWN:
        remaining = settings.SCANNER_COOLDOWN - (now - hunter.last_scanner_time)
        return False, [f"Scanner recharging ({remaining:.1f}s)."]

    hunter.last_scanner_time = now
    hunter.scanner_charges -= 1

    clues = []
    near_b, mid_b, far_b = settings.SCANNER_CLUE_RADIUS_BUCKETS
    for p in all_players:
        if p.role != "hider" or not p.alive or p.player_id == hunter.player_id:
            continue
        dist = _distance(hunter.position, p.position)
        if dist > settings.SCANNER_RANGE:
            continue
        # camouflage reduces detection chance / clarity
        from game.object_prop import REGISTRY
        obj = REGISTRY.get(p.transformed_into) if p.transformed_into else None
        camo = obj.camouflage if obj else 0.0
        detect_chance = max(0.15, 1.0 - camo)
        if random.random() > detect_chance:
            continue
        if dist <= near_b:
            clues.append(random.choice(CLUE_PHRASES_NEAR))
        elif dist <= mid_b:
            clues.append(random.choice(CLUE_PHRASES_MID))
        else:
            clues.append(random.choice(CLUE_PHRASES_FAR))

    if not clues:
        clues = [random.choice(CLUE_NONE)]
    return True, clues


def scanner_regen_tick(hunter, now=None):
    now = now or time.time()
    if hunter.scanner_charges >= settings.SCANNER_MAX_CHARGES:
        hunter.last_scanner_charge_time = now
        return
    if (now - hunter.last_scanner_charge_time) >= settings.SCANNER_CHARGE_REGEN_SECONDS:
        hunter.scanner_charges = min(settings.SCANNER_MAX_CHARGES, hunter.scanner_charges + 1)
        hunter.last_scanner_charge_time = now


def try_attack(hunter, all_players, now=None):
    """
    Resolve a Hunter's attack: hits the nearest alive Hider within range/
    cone in front of the hunter. Returns (ok, message, eliminated_player_or_None).
    """
    now = now or time.time()
    if hunter.role != "hunter":
        return False, "Only Hunters can attack.", None
    if (now - hunter.last_attack_time) < settings.ATTACK_COOLDOWN:
        return False, "Attack on cooldown.", None

    hunter.last_attack_time = now

    best_target = None
    best_dist = settings.ATTACK_RANGE
    for p in all_players:
        if p.role != "hider" or not p.alive:
            continue
        dist = _distance(hunter.position, p.position)
        if dist <= best_dist:
            # simple forward-facing check using rotation_y and vector to target
            dx = p.position[0] - hunter.position[0]
            dz = p.position[2] - hunter.position[2]
            angle_to_target = math.degrees(math.atan2(dx, dz))
            facing = hunter.rotation_y % 360
            diff = abs((angle_to_target - facing + 180) % 360 - 180)
            if diff <= 60:  # ~120 degree attack cone
                best_target = p
                best_dist = dist

    if not best_target:
        return True, "Attack missed.", None

    best_target.health -= settings.ATTACK_DAMAGE
    if best_target.health <= 0:
        eliminate_hider(best_target)
        hunter.eliminations += 1
        hunter.xp += settings.XP_PER_ELIMINATION
        return True, f"{best_target.name} was eliminated!", best_target

    return True, f"Hit {best_target.name}.", None
