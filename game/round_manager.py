"""
Round system state machine.

LOBBY -> ROLE_ASSIGN -> COUNTDOWN -> HIDING -> HUNTING -> RESULTS -> LOBBY

The RoundManager is deliberately server-only and holds no networking
code; game_server.py drives it and broadcasts phase changes/snapshots.
"""
import random
import time

from config import settings
from game.game_state import (
    PHASE_LOBBY, PHASE_ROLE_ASSIGN, PHASE_COUNTDOWN, PHASE_HIDING,
    PHASE_HUNTING, PHASE_RESULTS, ROLE_HIDER, ROLE_HUNTER,
)
from game.hider import award_survival_xp
from config import settings as cfg


class RoundManager:
    def __init__(self):
        self.phase = PHASE_LOBBY
        self.phase_started_at = time.time()
        self.map_key = settings.LEVELS[0]
        self.mode = settings.GAME_MODES[0]
        self.phase_duration = 0.0

    # ------------------------------------------------------------------
    def set_phase(self, phase: str, duration: float = 0.0):
        self.phase = phase
        self.phase_started_at = time.time()
        self.phase_duration = duration

    def time_left(self) -> float:
        if self.phase_duration <= 0:
            return 0.0
        elapsed = time.time() - self.phase_started_at
        return max(0.0, self.phase_duration - elapsed)

    def is_phase_over(self) -> bool:
        if self.phase_duration <= 0:
            return False
        return self.time_left() <= 0

    # ------------------------------------------------------------------
    def assign_roles(self, players: list):
        """Randomly assign one-third (min 1) of players as Hunters."""
        eligible = [p for p in players if not p.spectator]
        random.shuffle(eligible)
        n_hunters = max(1, len(eligible) // 3)
        for i, p in enumerate(eligible):
            p.reset_for_new_round()
            p.role = ROLE_HUNTER if i < n_hunters else ROLE_HIDER

    def infection_reassign(self, eliminated_player):
        """INFECTION mode: eliminated hiders become hunters instead of spectators."""
        if self.mode != "infection":
            return
        eliminated_player.role = ROLE_HUNTER
        eliminated_player.alive = True
        eliminated_player.eliminated = False
        eliminated_player.spectator = False
        eliminated_player.health = cfg.PLAYER_START_HEALTH
        eliminated_player.transformed_into = None

    # ------------------------------------------------------------------
    def check_win_condition(self, players, objective_mgr):
        """Returns None if round continues, else a result dict."""
        hiders = [p for p in players if p.role == ROLE_HIDER]
        hunters = [p for p in players if p.role == ROLE_HUNTER]
        alive_hiders = [p for p in hiders if p.alive]

        if self.mode == "object_rush":
            required = objective_mgr.required_count(self.mode)
            if required and objective_mgr.completed_count() >= required:
                return self._build_result(players, winner="hiders", reason="Objectives completed!")

        if not alive_hiders and hiders:
            return self._build_result(players, winner="hunters", reason="All Hiders eliminated!")

        if self.is_phase_over() and self.phase == PHASE_HUNTING:
            if alive_hiders:
                for p in alive_hiders:
                    award_survival_xp(p)
                return self._build_result(players, winner="hiders", reason="Hiders survived the round!")
            return self._build_result(players, winner="hunters", reason="Time expired.")

        return None

    def _build_result(self, players, winner, reason):
        for p in players:
            if winner == "hiders" and p.role == ROLE_HIDER:
                p.xp += settings.XP_WIN_BONUS
            if winner == "hunters" and p.role == ROLE_HUNTER:
                p.xp += settings.XP_WIN_BONUS
        return {
            "winner": winner,
            "reason": reason,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "role": p.role,
                    "survived": p.survived or (p.alive and p.role == ROLE_HIDER),
                    "eliminations": p.eliminations,
                    "objectives_completed": p.objectives_completed,
                    "xp": p.xp,
                }
                for p in players
            ],
        }
