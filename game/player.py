
import time

from config import settings
from game.game_state import ROLE_UNASSIGNED
from game.object_prop import REGISTRY
from game.progression import get_level


class PlayerState:
    def __init__(self, player_id: int, name: str, is_host: bool = False, profile_id: str = ""):
        self.player_id = player_id
        self.name = name
        self.profile_id = profile_id or f"Player{player_id}"
        self.is_host = is_host
        self.ready = False
        self.char_idx = 1

        self.role = ROLE_UNASSIGNED
        self.alive = True
        self.eliminated = False
        self.health = settings.PLAYER_START_HEALTH
        self.spectator = False

        # transform / position
        self.position = [0.0, 1.0, 0.0]
        self.rotation_y = 0.0
        self.move_input = [0.0, 0.0]
        self.sprint = False
        self.crouch = False
        self.jump_requested = False
        self.velocity_y = 0.0
        self.grounded = True

        # hider-only state
        self.morph_energy = settings.MORPH_ENERGY_MAX
        self.transformed_into = None     # object key or None
        self.last_switch_time = 0.0
        self.last_move_time = 0.0
        self.still_since = time.time()
        self.objectives_completed = 0
        self.personal_tasks = []

        # hunter-only state
        self.scanner_charges = settings.SCANNER_MAX_CHARGES
        self.last_scanner_time = -999.0
        self.last_scanner_charge_time = time.time()
        self.last_attack_time = -999.0

        # scoring
        self.xp = 0
        self.eliminations = 0
        self.survived = False
        self.connected_at = time.time()

    @property
    def level(self):
        return get_level(self.xp)

    # ------------------------------------------------------------------
    def current_speed(self) -> float:
        """Compute this player's effective movement speed given role/disguise."""
        base = settings.PLAYER_WALK_SPEED
        if self.crouch:
            base *= 0.5
        elif self.sprint and self.role != "hider":
            base *= settings.PLAYER_SPRINT_MULTIPLIER
        if self.role == "hider" and self.transformed_into:
            obj = REGISTRY.get(self.transformed_into)
            if obj:
                base *= obj.speed_mult
        elif self.role == "hunter" and self.sprint:
            base *= settings.PLAYER_SPRINT_MULTIPLIER
        return base

    def reset_for_new_round(self):
        self.role = ROLE_UNASSIGNED
        self.alive = True
        self.eliminated = False
        self.health = settings.PLAYER_START_HEALTH
        self.spectator = False
        self.morph_energy = settings.MORPH_ENERGY_MAX
        self.transformed_into = None
        self.last_switch_time = 0.0
        self.objectives_completed = 0
        self.scanner_charges = settings.SCANNER_MAX_CHARGES
        self.last_scanner_time = -999.0
        self.last_attack_time = -999.0
        self.survived = False

    def to_public_dict(self, viewer_role: str):
        """
        Serialize this player for network transmission.

        `viewer_role` controls information hiding: Hunters must NOT learn
        which specific player a disguised object represents, nor see raw
        hider positions -- they only see the object entity itself (handled
        at a higher level in game_server.py). This dict is used for the
        generic player list / spectator / same-team views.
        """
        data = {
            "player_id": self.player_id,
            "name": self.name,
            "is_host": self.is_host,
            "ready": self.ready,
            "role": self.role,
            "alive": self.alive,
            "eliminated": self.eliminated,
            "profile_id": self.profile_id,
            "health": self.health,
            "position": self.position,
            "rotation_y": self.rotation_y,
            "velocity": self.move_input,
            "char_idx": self.char_idx,
            "crouch": self.crouch,
            "xp": self.xp,
            "level": self.level,
        }
        if self.role == "hider":
            data["transformed_into"] = self.transformed_into
            if viewer_role in ("hider", "spectator") or viewer_role is None:
                data["morph_energy"] = self.morph_energy
            if getattr(self, "personal_tasks", None):
                data["tasks"] = [t.to_dict() for t in self.personal_tasks]
        if self.role == "hunter":
            data["scanner_charges"] = self.scanner_charges
            data["last_scanner_time"] = self.last_scanner_time
        return data
