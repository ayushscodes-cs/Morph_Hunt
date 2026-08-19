"""
Headless smoke test: exercises the server-authoritative game logic
(round manager, morph system, hunter scanner/attack, objectives, level
loading) without sockets or Ursina, to catch real runtime bugs.
Run: python smoke_test.py
"""
import sys
import time

from config import settings
from game.player import PlayerState
from game.round_manager import RoundManager
from game.objective import ObjectiveManager
from game.level_manager import load_level, all_level_keys
from game import morph_system
from game.hunter import try_scanner, try_attack, scanner_regen_tick
from game.hider import eliminate_hider
from game.object_prop import REGISTRY
from game.game_state import ROLE_HIDER, ROLE_HUNTER, PHASE_HIDING, PHASE_HUNTING


def check(cond, msg):
    if not cond:
        raise AssertionError(f"FAILED: {msg}")
    print(f"  ok: {msg}")


def main():
    print("== Loading all 5 levels ==")
    for key in all_level_keys():
        lvl = load_level(key)
        check(len(lvl["geometry"]) > 0, f"{key} has geometry")
        check(len(lvl["hider_spawn_objects"]) > 0, f"{key} has hider spawn objects")
        check(len(lvl["hunter_spawns"]) > 0, f"{key} has hunter spawns")
        check(len(lvl["objectives"]) > 0, f"{key} has objectives")
    check(len(all_level_keys()) == 5, "exactly 5 levels registered")

    print("== Object registry ==")
    check(len(REGISTRY.keys()) >= 9, "at least 9 object personalities defined")
    for key in REGISTRY.keys():
        obj = REGISTRY.get(key)
        check(0 <= obj.camouflage <= 1, f"{key} camouflage in range")
        check(obj.speed_mult > 0, f"{key} speed_mult positive")

    print("== Round manager / role assignment ==")
    players = [PlayerState(i, f"P{i}") for i in range(1, 7)]
    rm = RoundManager()
    rm.mode = "classic"
    rm.assign_roles(players)
    hunters = [p for p in players if p.role == ROLE_HUNTER]
    hiders = [p for p in players if p.role == ROLE_HIDER]
    check(len(hunters) >= 1, "at least one hunter assigned")
    check(len(hunters) + len(hiders) == len(players), "all players assigned a role")

    print("== Morph system ==")
    hider = hiders[0]
    hider.morph_energy = 100
    ok, reason = morph_system.try_transform(hider, "chair")
    check(ok, f"initial transform succeeds ({reason})")
    check(hider.transformed_into == "chair", "transformed_into set")
    check(hider.morph_energy == 100 - settings.MORPH_ENERGY_TRANSFORM_COST, "energy deducted on transform")

    ok, reason = morph_system.try_transform(hider, "box")
    check(not ok, "switch blocked by cooldown immediately after transform")
    hider.last_switch_time -= settings.MORPH_SWITCH_COOLDOWN + 1
    ok, reason = morph_system.try_transform(hider, "box")
    check(ok, f"switch succeeds after cooldown ({reason})")
    check(hider.transformed_into == "box", "switched to box")

    for _ in range(50):
        morph_system.tick_energy(hider, dt=1.0, is_moving=True)
    check(hider.morph_energy == 0 or hider.transformed_into is None or hider.morph_energy >= 0,
          "energy never goes negative while draining")
    check(hider.morph_energy >= 0, "energy floor at zero")

    hider.morph_energy = 10
    hider.still_since = time.time() - 10
    morph_system.tick_energy(hider, dt=1.0, is_moving=False)
    check(hider.morph_energy > 10, "energy regenerates while still")

    print("== Hunter scanner ==")
    hunter = hunters[0]
    hunter.position = [0, 1, 0]
    hider.position = [1, 1, 0]
    hider.role = ROLE_HIDER
    ok, clues = try_scanner(hunter, players)
    check(ok, "scanner usable")
    check(isinstance(clues, list) and len(clues) >= 1, "scanner returns clue list")
    ok2, clues2 = try_scanner(hunter, players)
    check(not ok2, "scanner respects cooldown")

    hunter.last_scanner_time = -999
    hunter.scanner_charges = 0
    ok3, clues3 = try_scanner(hunter, players)
    check(not ok3, "scanner blocked with zero charges")
    hunter.last_scanner_charge_time = time.time() - settings.SCANNER_CHARGE_REGEN_SECONDS - 1
    scanner_regen_tick(hunter)
    check(hunter.scanner_charges == 1, "scanner charge regenerates")

    print("== Hunter attack ==")
    hider.health = settings.PLAYER_START_HEALTH
    hider.alive = True
    hunter.rotation_y = 90.0  # facing +x, hider is at +x relative position
    hunter.last_attack_time = -999
    ok4, msg4, eliminated = try_attack(hunter, players)
    check(ok4, f"attack resolves ({msg4})")

    hider.health = 1
    hunter.last_attack_time = -999
    ok5, msg5, eliminated5 = try_attack(hunter, players)
    check(eliminated5 is hider or hider.eliminated, "low-health hider eliminated by attack")

    print("== Objectives ==")
    level_def = load_level("house")
    om = ObjectiveManager()
    om.load_for_level(level_def)
    check(len(om.objectives) == len(level_def["objectives"]), "objective count matches level def")
    first_obj = om.objectives[0]
    interacting = {99: first_obj.obj_id}
    for _ in range(int(settings.OBJECTIVE_HOLD_SECONDS) + 2):
        om.tick(1.0, interacting)
    check(first_obj.completed, "objective completes after sustained interaction")
    check(om.completed_count() == 1, "completed_count reflects one finished objective")

    print("== Win condition ==")
    rm2 = RoundManager()
    rm2.mode = "classic"
    p2 = [PlayerState(1, "H1"), PlayerState(2, "S1")]
    p2[0].role = ROLE_HUNTER
    p2[1].role = ROLE_HIDER
    p2[1].alive = False
    result = rm2.check_win_condition(p2, ObjectiveManager())
    check(result is not None and result["winner"] == "hunters", "hunters win when all hiders eliminated")

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
