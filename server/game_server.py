"""
Authoritative multiplayer server for Morph Hunt.

Architecture:
- One TCP listener thread accepts new connections.
- One thread per connected client blocks on recv_json() and pushes
  parsed messages onto a thread-safe queue.
- A single game-loop thread (fixed tick rate) drains the queue, mutates
  authoritative state, runs round/morph/objective logic, and periodically
  broadcasts snapshots to every client.

All game *rules* live in game/*.py — this file is glue: sockets in,
state mutation, snapshots out.
"""
import queue
import socket
import threading
import time

from config import settings
from game.game_state import (
    send_json, recv_json,
    MSG_JOIN, MSG_SET_READY, MSG_SET_MAP, MSG_SET_MODE, MSG_START_GAME,
    MSG_INPUT, MSG_TRANSFORM, MSG_UNTRANSFORM, MSG_SCANNER, MSG_ATTACK,
    MSG_INTERACT, MSG_CHAT, MSG_LEAVE,
    MSG_WELCOME, MSG_LOBBY_STATE, MSG_PHASE_CHANGE, MSG_ROLE_ASSIGNED,
    MSG_SNAPSHOT, MSG_SCANNER_RESULT, MSG_OBJECTIVE_UPDATE, MSG_ELIMINATED,
    MSG_ROUND_RESULT, MSG_CHAT_BROADCAST, MSG_ERROR, MSG_PLAYER_LEFT,
    PHASE_LOBBY, PHASE_ROLE_ASSIGN, PHASE_COUNTDOWN, PHASE_HIDING, PHASE_HUNTING, PHASE_RESULTS,
    ROLE_HIDER, ROLE_HUNTER,
)
from game.player import PlayerState
from game.round_manager import RoundManager
from game.objective import ObjectiveManager
from game import morph_system
from game.hunter import try_scanner, try_attack, scanner_regen_tick
from game.hider import eliminate_hider
from game.level_manager import load_level
from game.stats_db import StatsDB


class ClientConnection:
    def __init__(self, sock, addr, player_id):
        self.sock = sock
        self.addr = addr
        self.player_id = player_id
        self.send_lock = threading.Lock()
        self.alive = True

    def send(self, payload):
        if not self.alive:
            return
        try:
            with self.send_lock:
                send_json(self.sock, payload)
        except OSError:
            self.alive = False


class GameServer:
    def __init__(self, host=settings.DEFAULT_HOST, port=settings.DEFAULT_PORT):
        self.host = host
        self.port = port
        self.listener = None
        self._next_id = 1
        self._lock = threading.RLock()

        self.connections: dict[int, ClientConnection] = {}
        self.players: dict[int, PlayerState] = {}
        self.host_player_id = None

        self.round_mgr = RoundManager()
        self.objective_mgr = ObjectiveManager()
        self.level_def = None

        self.msg_queue: "queue.Queue[tuple[int, dict]]" = queue.Queue()
        self._running = False
        self._interact_state: dict[int, str] = {}
        self.stats_db = StatsDB()

    # ------------------------------------------------------------------
    def start(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.host, self.port))
        self.listener.listen(settings.MAX_PLAYERS)
        self._running = True
        print(f"[server] listening on {self.host}:{self.port}")

        threading.Thread(target=self._accept_loop, daemon=True).start()
        self._game_loop()

    def stop(self):
        self._running = False
        try:
            self.listener.close()
        except OSError:
            pass

    # ------------------------------------------------------------------
    def _accept_loop(self):
        while self._running:
            try:
                sock, addr = self.listener.accept()
            except OSError:
                break
            threading.Thread(target=self._client_thread, args=(sock, addr), daemon=True).start()

    def _client_thread(self, sock, addr):
        with self._lock:
            if len(self.players) >= settings.MAX_PLAYERS:
                try:
                    send_json(sock, {"type": MSG_ERROR, "message": "Server full."})
                except OSError:
                    pass
                sock.close()
                return
            player_id = self._next_id
            self._next_id += 1
            is_host = self.host_player_id is None

        conn = ClientConnection(sock, addr, player_id)
        with self._lock:
            self.connections[player_id] = conn
            if is_host:
                self.host_player_id = player_id

        try:
            conn.send({"type": MSG_WELCOME, "player_id": player_id, "is_host": is_host})
            while self._running and conn.alive:
                msg = recv_json(sock)
                self.msg_queue.put((player_id, msg))
        except (ConnectionError, OSError, ValueError):
            pass
        finally:
            self._handle_disconnect(player_id)

    def _handle_disconnect(self, player_id):
        with self._lock:
            conn = self.connections.pop(player_id, None)
            if conn:
                conn.alive = False
                try:
                    conn.sock.close()
                except OSError:
                    pass
            self.players.pop(player_id, None)
            self._interact_state.pop(player_id, None)
            if self.host_player_id == player_id:
                remaining = list(self.connections.keys())
                self.host_player_id = remaining[0] if remaining else None
                if self.host_player_id and self.host_player_id in self.players:
                    self.players[self.host_player_id].is_host = True
        self._broadcast({"type": MSG_PLAYER_LEFT, "player_id": player_id})
        self._broadcast_lobby_state()

    # ------------------------------------------------------------------
    def _broadcast(self, payload, exclude=None):
        with self._lock:
            conns = list(self.connections.values())
        for c in conns:
            if exclude is not None and c.player_id == exclude:
                continue
            c.send(payload)

    def _broadcast_lobby_state(self):
        with self._lock:
            players_payload = [p.to_public_dict(None) for p in self.players.values()]
        self._broadcast({
            "type": MSG_LOBBY_STATE,
            "players": players_payload,
            "map": self.round_mgr.map_key,
            "mode": self.round_mgr.mode,
            "host_id": self.host_player_id,
        })

    # ------------------------------------------------------------------
    # GAME LOOP
    # ------------------------------------------------------------------
    def _game_loop(self):
        tick_dt = 1.0 / settings.TICK_RATE
        last_snapshot = 0.0
        snapshot_interval = 1.0 / settings.SNAPSHOT_RATE

        while self._running:
            start = time.time()
            self._drain_messages()
            self._simulate(tick_dt)

            if start - last_snapshot >= snapshot_interval:
                self._broadcast_snapshot()
                last_snapshot = start

            elapsed = time.time() - start
            time.sleep(max(0.0, tick_dt - elapsed))

    def _drain_messages(self):
        while True:
            try:
                player_id, msg = self.msg_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_message(player_id, msg)

    def _handle_message(self, player_id, msg):
        mtype = msg.get("type")
        with self._lock:
            if mtype == MSG_JOIN:
                name = str(msg.get("name", f"Player{player_id}"))[:20]
                is_host = player_id == self.host_player_id
                self.players[player_id] = PlayerState(player_id, name, is_host)
                self._broadcast_lobby_state()
                return

            player = self.players.get(player_id)
            if player is None:
                return

            if mtype == MSG_SET_READY:
                player.ready = bool(msg.get("ready", False))
                self._broadcast_lobby_state()
            elif mtype == MSG_SET_MAP and player_id == self.host_player_id:
                if msg.get("map") in settings.LEVELS:
                    self.round_mgr.map_key = msg["map"]
                    self._broadcast_lobby_state()
            elif mtype == MSG_SET_MODE and player_id == self.host_player_id:
                if msg.get("mode") in settings.GAME_MODES:
                    self.round_mgr.mode = msg["mode"]
                    self._broadcast_lobby_state()
            elif mtype == MSG_START_GAME and player_id == self.host_player_id:
                self._try_start_round()
            elif mtype == MSG_INPUT:
                self._apply_input(player, msg)
            elif mtype == MSG_TRANSFORM:
                ok, reason = morph_system.try_transform(player, msg.get("object_type", ""))
                if not ok:
                    self.connections[player_id].send({"type": MSG_ERROR, "message": reason})
            elif mtype == MSG_UNTRANSFORM:
                morph_system.untransform(player)
            elif mtype == MSG_SCANNER:
                ok, clues = try_scanner(player, list(self.players.values()))
                self.connections[player_id].send({"type": MSG_SCANNER_RESULT, "clues": clues})
            elif mtype == MSG_ATTACK:
                self._handle_attack(player)
            elif mtype == MSG_INTERACT:
                self._handle_interact(player)
            elif mtype == MSG_CHAT:
                text = str(msg.get("text", ""))[:200]
                self._broadcast({"type": MSG_CHAT_BROADCAST, "name": player.name, "text": text})
            elif mtype == MSG_LEAVE:
                pass  # disconnect handled by socket closing

    def _apply_input(self, player, msg):
        move = msg.get("move", [0.0, 0.0])
        if isinstance(move, list) and len(move) == 2:
            player.move_input = [float(move[0]), float(move[1])]
        player.rotation_y = float(msg.get("look_y", player.rotation_y))
        player.sprint = bool(msg.get("sprint", False))
        if msg.get("jump"):
            player.jump_requested = True
        if "position" in msg and isinstance(msg["position"], list) and len(msg["position"]) == 3:
            # Client-authoritative position with light server sanity clamp (MVP trust model).
            player.position = [float(v) for v in msg["position"]]

    def _handle_attack(self, hunter):
        ok, message, eliminated = try_attack(hunter, list(self.players.values()))
        if eliminated:
            self._broadcast({"type": MSG_ELIMINATED, "player_id": eliminated.player_id})
            self.round_mgr.infection_reassign(eliminated)

    def _handle_interact(self, player):
        if player.role != ROLE_HIDER or not player.alive:
            return
        nearby = self.objective_mgr.find_nearby(player.position)
        self._interact_state[player.player_id] = nearby.obj_id if nearby else None

    # ------------------------------------------------------------------
    def _try_start_round(self):
        if len(self.players) < settings.MIN_PLAYERS_TO_START:
            self._broadcast({"type": MSG_ERROR, "message": "Need at least 2 players to start."})
            return
        self.level_def = load_level(self.round_mgr.map_key)
        self.objective_mgr.load_for_level(self.level_def)
        self.objective_mgr.reset()
        self.round_mgr.assign_roles(list(self.players.values()))
        self._place_spawns()

        self.round_mgr.set_phase(PHASE_ROLE_ASSIGN, 0.0)
        for p in self.players.values():
            self.connections[p.player_id].send({"type": MSG_ROLE_ASSIGNED, "role": p.role})
        self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_ROLE_ASSIGN, "time_left": 0})

        self.round_mgr.set_phase(PHASE_COUNTDOWN, settings.COUNTDOWN_SECONDS)
        self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_COUNTDOWN, "time_left": settings.COUNTDOWN_SECONDS})

    def _place_spawns(self):
        hider_spots = self.level_def["hider_spawn_objects"]
        hunter_spots = self.level_def["hunter_spawns"]
        hi = 0
        hu = 0
        for p in self.players.values():
            if p.role == ROLE_HIDER:
                spot = hider_spots[hi % len(hider_spots)]["position"]
                hi += 1
                p.position = [spot[0], spot[1] + 0.5, spot[2]]
            elif p.role == ROLE_HUNTER:
                spot = hunter_spots[hu % len(hunter_spots)]
                hu += 1
                p.position = list(spot)

    # ------------------------------------------------------------------
    def _simulate(self, dt):
        phase = self.round_mgr.phase

        for p in self.players.values():
            is_moving = abs(p.move_input[0]) > 0.01 or abs(p.move_input[1]) > 0.01
            morph_system.tick_energy(p, dt, is_moving)
            if p.role == ROLE_HUNTER:
                scanner_regen_tick(p)

        if phase == PHASE_COUNTDOWN and self.round_mgr.is_phase_over():
            self.round_mgr.set_phase(PHASE_HIDING, settings.HIDING_PHASE_SECONDS)
            self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_HIDING, "time_left": settings.HIDING_PHASE_SECONDS})

        elif phase == PHASE_HIDING and self.round_mgr.is_phase_over():
            self.round_mgr.set_phase(PHASE_HUNTING, settings.HUNTING_PHASE_SECONDS)
            self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_HUNTING, "time_left": settings.HUNTING_PHASE_SECONDS})

        elif phase == PHASE_HUNTING:
            completed = self.objective_mgr.tick(dt, dict(self._interact_state))
            for obj in completed:
                pid = obj.active_player_id
                if pid in self.players:
                    self.players[pid].objectives_completed += 1
                    self.players[pid].xp += settings.XP_PER_OBJECTIVE
            if completed:
                self._broadcast({
                    "type": MSG_OBJECTIVE_UPDATE,
                    "objectives": [o.to_dict() for o in self.objective_mgr.objectives],
                })

            result = self.round_mgr.check_win_condition(list(self.players.values()), self.objective_mgr)
            if result:
                self.round_mgr.set_phase(PHASE_RESULTS, settings.RESULTS_SCREEN_SECONDS)
                self._broadcast({"type": MSG_ROUND_RESULT, **result})
                self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_RESULTS, "time_left": settings.RESULTS_SCREEN_SECONDS})
                self._persist_stats(result)

        elif phase == PHASE_RESULTS and self.round_mgr.is_phase_over():
            self.round_mgr.set_phase(PHASE_LOBBY, 0.0)
            for p in self.players.values():
                p.ready = False
            self._broadcast({"type": MSG_PHASE_CHANGE, "phase": PHASE_LOBBY, "time_left": 0})
            self._broadcast_lobby_state()

    def _persist_stats(self, result):
        winner = result.get("winner")
        for p in result.get("players", []):
            won = (winner == "hiders" and p["role"] == ROLE_HIDER) or (winner == "hunters" and p["role"] == ROLE_HUNTER)
            self.stats_db.record_round(
                p["name"], p["xp"], won, p["eliminations"], p["objectives_completed"],
            )

    def _broadcast_snapshot(self):
        with self._lock:
            players_payload = [p.to_public_dict(None) for p in self.players.values()]
            objectives_payload = [o.to_dict() for o in self.objective_mgr.objectives] if self.objective_mgr.objectives else []
        self._broadcast({
            "type": MSG_SNAPSHOT,
            "phase": self.round_mgr.phase,
            "time_left": round(self.round_mgr.time_left(), 1),
            "mode": self.round_mgr.mode,
            "map": self.round_mgr.map_key,
            "players": players_payload,
            "objectives": objectives_payload,
        })
