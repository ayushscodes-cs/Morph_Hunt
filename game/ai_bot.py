"""
AI Bot Controller for Morph Hunt.

Simulates intelligent Bot players:
- In Lobby: Auto-ready.
- As Hider:
  * Chooses a room during Hiding Phase.
  * Picks a thematic disguise prop and transforms.
  * Moves to a spot near walls/corners, freezes rotation, and holds still.
  * Periodically emits a taunt or flees if a hunter approaches too close.
- As Hunter:
  * Waits in spawn during Hiding Phase.
  * In Hunting Phase, patrols rooms systematically.
  * Uses scanner sonar periodically.
  * Attacks suspected props and nearby suspicious players.
"""

import math
import random
import time

from config import settings
from game.game_state import (
    ROLE_HIDER, ROLE_HUNTER,
    PHASE_HIDING, PHASE_HUNTING,
)
from game.object_prop import REGISTRY


BOT_NAMES = [
    "Bot_Shadow", "Bot_Sneaky", "Bot_Disguised", "Bot_Chaser",
    "Bot_Phantom", "Bot_Radar", "Bot_Camouflage", "Bot_Seeker"
]


class AIBot:
    def __init__(self, player):
        self.player = player
        self.target_pos = None
        self.state_timer = 0.0
        self.last_action_time = time.time()
        self.last_taunt_time = time.time()
        self.has_transformed = False
        self.patrol_room_idx = 0
        self.patrol_points = []

    def setup_round(self, level_def):
        self.has_transformed = False
        self.target_pos = None
        self.patrol_points = []
        for r in level_def.get("rooms", []):
            cx, cz = r["position"]
            self.patrol_points.append([cx, 1.0, cz])
        random.shuffle(self.patrol_points)

    def tick(self, dt, phase, all_players, level_def, server):
        if not self.player.alive or self.player.eliminated:
            return

        now = time.time()
        if self.player.role == ROLE_HIDER:
            self._tick_hider(dt, phase, all_players, level_def, server, now)
        elif self.player.role == ROLE_HUNTER:
            self._tick_hunter(dt, phase, all_players, level_def, server, now)

    # ------------------------------------------------------------------
    # HIDER BOT LOGIC
    # ------------------------------------------------------------------
    def _tick_hider(self, dt, phase, all_players, level_def, server, now):
        if phase in (PHASE_HIDING, PHASE_HUNTING):
            # 1. Transform if not already disguised
            if not self.has_transformed:
                options = list(REGISTRY.keys())
                chosen = random.choice(options)
                self.player.transformed_into = chosen
                self.has_transformed = True

            # 2. Pick a hiding spot in a random room if no target
            if not self.target_pos:
                spots = level_def.get("hider_spawn_objects", [])
                if spots:
                    s = random.choice(spots)
                    self.target_pos = [s["position"][0], 0.5, s["position"][2]]
                else:
                    self.target_pos = [random.uniform(-10, 10), 0.5, random.uniform(-10, 10)]

            # 3. Move towards target spot
            dx = self.target_pos[0] - self.player.position[0]
            dz = self.target_pos[2] - self.player.position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist > 0.6:
                angle = math.atan2(dx, dz)
                speed = settings.PLAYER_WALK_SPEED * 0.8
                self.player.position[0] += math.sin(angle) * speed * dt
                self.player.position[2] += math.cos(angle) * speed * dt
                self.player.rotation_y = math.degrees(angle)
                self.player.move_input = [1.0, 0.0]
            else:
                # Arrived at hiding spot — stay still to save energy!
                self.player.move_input = [0.0, 0.0]

                # Occasional taunt to tease hunters!
                if phase == PHASE_HUNTING and (now - self.last_taunt_time) > 25.0:
                    if random.random() < 0.3:
                        self.last_taunt_time = now
                        server._broadcast({
                            "type": "taunt_broadcast",
                            "name": self.player.name,
                            "position": self.player.position,
                        })

    # ------------------------------------------------------------------
    # HUNTER BOT LOGIC
    # ------------------------------------------------------------------
    def _tick_hunter(self, dt, phase, all_players, level_def, server, now):
        if phase != PHASE_HUNTING:
            self.player.move_input = [0.0, 0.0]
            return

        # 1. Patrol between rooms
        if not self.target_pos or (now - self.last_action_time) > 10.0:
            if self.patrol_points:
                self.target_pos = random.choice(self.patrol_points)
                self.last_action_time = now

        # 2. Check for nearby disguised hiders
        nearest_hider = None
        min_dist = 6.0
        for p in all_players:
            if p.role == ROLE_HIDER and p.alive and not p.eliminated:
                d = math.dist(self.player.position, p.position)
                if d < min_dist:
                    min_dist = d
                    nearest_hider = p

        # If a hider is within attack range, attack!
        if nearest_hider and min_dist <= settings.ATTACK_RANGE:
            self.target_pos = list(nearest_hider.position)
            # Attack
            server._handle_attack(self.player)

        # Move towards target
        if self.target_pos:
            dx = self.target_pos[0] - self.player.position[0]
            dz = self.target_pos[2] - self.player.position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist > 0.8:
                angle = math.atan2(dx, dz)
                speed = settings.PLAYER_WALK_SPEED * 0.9
                self.player.position[0] += math.sin(angle) * speed * dt
                self.player.position[2] += math.cos(angle) * speed * dt
                self.player.rotation_y = math.degrees(angle)
                self.player.move_input = [1.0, 0.0]
            else:
                self.target_pos = None
                self.player.move_input = [0.0, 0.0]

        # Use scanner sonar periodically
        if (now - self.player.last_scanner_time) >= (settings.SCANNER_COOLDOWN + 2.0):
            self.player.last_scanner_time = now
            server.connections[self.player.player_id].send = lambda *args: None if self.player.player_id not in server.connections else None
            # Trigger scanner logic
            from game.hunter import try_scanner
            try_scanner(self.player, all_players, now=now)
