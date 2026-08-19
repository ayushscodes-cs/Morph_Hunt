"""
Hider-specific server-side helpers.

Most Hider behavior (movement, transform) is generic and lives in
morph_system.py / game_server.py. This module holds Hider-only rules
that don't belong to the generic PlayerState.
"""
from config import settings


def eliminate_hider(player):
    player.alive = False
    player.eliminated = True
    player.spectator = True
    player.transformed_into = None


def award_survival_xp(player):
    if player.alive and player.role == "hider":
        player.survived = True
        player.xp += settings.XP_SURVIVE_ROUND
