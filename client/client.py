
import threading
import time

from ursina import (
    Ursina, Entity, Text, color, camera, application, held_keys,
    Vec3, destroy, mouse, invoke, window, scene,
)
from ursina.shaders.unlit_shader import unlit_shader
from ursina.prefabs.first_person_controller import FirstPersonController

from config import settings
from game.game_state import (
    MSG_SET_READY, MSG_SET_MAP, MSG_SET_MODE, MSG_START_GAME, MSG_INPUT,
    MSG_TRANSFORM, MSG_UNTRANSFORM, MSG_SCANNER, MSG_ATTACK, MSG_INTERACT, MSG_LEAVE,
    MSG_WELCOME, MSG_LOBBY_STATE, MSG_PHASE_CHANGE, MSG_ROLE_ASSIGNED, MSG_SNAPSHOT,
    MSG_SCANNER_RESULT, MSG_OBJECTIVE_UPDATE, MSG_ELIMINATED, MSG_ROUND_RESULT,
    MSG_CHAT_BROADCAST, MSG_ERROR, MSG_PLAYER_LEFT,
    PHASE_LOBBY, PHASE_ROLE_ASSIGN, PHASE_COUNTDOWN, PHASE_HIDING, PHASE_HUNTING, PHASE_RESULTS,
    ROLE_HIDER, ROLE_HUNTER,
)
from game.object_prop import REGISTRY
from game.level_manager import load_level
from client.network_client import NetworkClient
from ui.menu import MainMenu, ConnectDialog
from ui.lobby import LobbyScreen
from ui.hud import HUD
from ui.results import ResultsScreen

STATE_MENU = "menu"
STATE_CONNECT = "connect"
STATE_LOBBY = "lobby"
STATE_INGAME = "ingame"


class ClientApp:
    def __init__(self):
        window.title = "Morph Hunt: The Object Among Us"
        window.borderless = False
        window.fps_counter.enabled = False
        window.render_mode = "default"
        camera.fov = 90

        self.net = NetworkClient()
        self.state = STATE_MENU
        self.server_thread = None
        self.local_server = None

        self.menu = MainMenu(self._on_host_clicked, self._on_join_clicked, application.quit)
        self.connect_dialog = None
        self.lobby = LobbyScreen(
            self._on_ready_toggle,
            self._on_set_map,
            self._on_set_mode,
            self._on_start_game,
            self._on_leave_lobby
        )
        self.hud = HUD()
        self.results = ResultsScreen(self._on_results_continue)

        self.level_key = None
        self.level_entities = []
        self.remote_entities = {}
        self.controller = None
        self.my_role = None
        self.my_transformed = None
        self.my_health = settings.PLAYER_START_HEALTH
        self.my_energy = settings.MORPH_ENERGY_MAX
        self.scanner_charges = settings.SCANNER_MAX_CHARGES
        self.last_scanner_press = -999.0
        self.current_phase = PHASE_LOBBY
        self.current_time_left = 0
        self.current_mode = settings.GAME_MODES[0]
        self.current_map = settings.LEVELS[0]
        self.objectives = []
        self.required_objectives = 0
        self.last_input_sent = 0.0
        self.paused = False

        self._object_hotbar = list(REGISTRY.keys())[:9]

    # ------------------------------------------------------------------
    # SCREEN TRANSITIONS
    # ------------------------------------------------------------------
    def _show_only(self, state):
        self.state = state
        self.menu.hide()
        self.lobby.hide()
        self.hud.hide()
        self.results.hide()
        window.render_mode = "default"
        if state == STATE_MENU:
            self.menu.show()
            mouse.locked = False
        elif state == STATE_LOBBY:
            self.lobby.show()
            mouse.locked = False
        elif state == STATE_INGAME:
            self.hud.show()
            mouse.locked = True

    # ------------------------------------------------------------------
    # MENU CALLBACKS
    # ------------------------------------------------------------------
    def _on_host_clicked(self):
        self.state = STATE_CONNECT
        self.connect_dialog = ConnectDialog(
            self._do_host,
            self._cancel_dialog,
            mode="host"
        )
        self.menu.hide()
        mouse.locked = False

    def _on_join_clicked(self):
        self.state = STATE_CONNECT
        self.connect_dialog = ConnectDialog(
            self._do_join,
            self._cancel_dialog,
            mode="join"
        )
        self.menu.hide()
        mouse.locked = False

    def _cancel_dialog(self):
        if self.connect_dialog:
            self.connect_dialog.destroy()
            self.connect_dialog = None

        self.paused = False
        self._show_only(STATE_MENU)

    def _do_host(self, name, port_str):
        try:
            port = int(port_str) if port_str else settings.DEFAULT_PORT
        except ValueError:
            port = settings.DEFAULT_PORT

        from server.game_server import GameServer
        self.local_server = GameServer(host=settings.DEFAULT_HOST, port=port)
        self.server_thread = threading.Thread(target=self.local_server.start, daemon=True)
        self.server_thread.start()
        time.sleep(0.3)  # give the listener a moment to bind

        ok, msg = self.net.connect("127.0.0.1", port, name)
        self._finish_connect(ok, msg)

    def _do_join(self, name, addr_str):
        host, _, port_str = addr_str.partition(":")
        host = host.strip() or "127.0.0.1"
        try:
            port = int(port_str.strip()) if port_str.strip() else settings.DEFAULT_PORT
        except ValueError:
            port = settings.DEFAULT_PORT
        ok, msg = self.net.connect(host, port, name)
        self._finish_connect(ok, msg)

    def _finish_connect(self, ok, msg):
        
        if self.connect_dialog:
            self.connect_dialog.destroy()
            self.connect_dialog = None
        if not ok:
            print(f"[client] connection failed: {msg}")
            self._show_only(STATE_MENU)
            return
        self._show_only(STATE_LOBBY)

    # ------------------------------------------------------------------
    # LOBBY CALLBACKS
    # ------------------------------------------------------------------
    def _on_ready_toggle(self):
        self._my_ready = not getattr(self, "_my_ready", False)
        self.net.send({"type": MSG_SET_READY, "ready": self._my_ready})

    def _on_set_map(self, map_key):
        self.net.send({"type": MSG_SET_MAP, "map": map_key})

    def _on_set_mode(self, mode):
        self.net.send({"type": MSG_SET_MODE, "mode": mode})

    def _on_start_game(self):
        self.net.send({"type": MSG_START_GAME})

    def _on_leave_lobby(self):
        self.net.send({"type": MSG_LEAVE})
        self.net.disconnect()
        if self.local_server:
            self.local_server.stop()
            self.local_server = None
        self._clear_level()
        self._show_only(STATE_MENU)

    def _on_results_continue(self):
        self._show_only(STATE_LOBBY)

    # ------------------------------------------------------------------
    # LEVEL BUILDING
    # ------------------------------------------------------------------
    def _clear_level(self):
        for e in self.level_entities:
            destroy(e)
        self.level_entities = []
        for e in self.remote_entities.values():
            destroy(e)
        self.remote_entities = {}
        if self.controller:
            destroy(self.controller)
            self.controller = None

    def _build_level(self, level_key):
        self._clear_level()
        self.level_key = level_key

        level_def = load_level(level_key)

        # --------------------------------------------------------------
        # MAP GEOMETRY
        # --------------------------------------------------------------
        for g in level_def.get("geometry", []):
            e = Entity(
            model="cube",
            position=Vec3(*g["position"]),
            scale=Vec3(*g["scale"]),
            color=color.rgb(*g["color"]),
            shader=unlit_shader,
            collider="box" if g.get("solid", True) else None,
        )

            self.level_entities.append(e)

        # --------------------------------------------------------------
        # CONTINUOUS FLOOR
        #
        # Prevents the player from falling through gaps between rooms.
        # This is intentionally a large invisible-ish solid floor under
        # the whole playable house.
        # --------------------------------------------------------------
        world_floor = Entity(
            model="cube",
            position=Vec3(0, -0.15, 0),
            scale=Vec3(40, 1, 40),
            color=color.rgb(45, 45, 45),
            shader=unlit_shader,
            collider="box",
        )

        self.level_entities.append(world_floor)

        # --------------------------------------------------------------
        # STATIC HIDER OBJECTS
        # --------------------------------------------------------------
        for spot in level_def.get("hider_spawn_objects", []):
            obj = REGISTRY.get(spot["key"])

            if not obj:
                continue

            e = Entity(
                model="cube",
                position=Vec3(*spot["position"]),
                scale=Vec3(*obj.scale),
                color=color.rgb(*obj.color),
                shader=unlit_shader,
            )
            self.level_entities.append(e)

        # --------------------------------------------------------------
        # PLAYER
        # --------------------------------------------------------------
        self.controller = FirstPersonController(
            position=Vec3(0, 2, 0),
            speed=settings.PLAYER_WALK_SPEED,
            jump_height=settings.PLAYER_JUMP_HEIGHT,
            gravity=1,
            jump_up_duration=0.5,
            fall_after=0.35,
        )

        self.controller.cursor.visible = False
        self.controller.cursor.model = None
        self.controller.camera_pivot.y = 1.6

    # ------------------------------------------------------------------
    # NETWORK MESSAGE HANDLING
    # ------------------------------------------------------------------
    def _process_network(self):
        for msg in self.net.poll():
            mtype = msg.get("type")
            if mtype == "_disconnected":
                self._on_leave_lobby()
                return
            elif mtype == MSG_LOBBY_STATE:
                self._players_cache = msg.get("players", [])
                self.current_map = msg.get("map", self.current_map)
                self.current_mode = msg.get("mode", self.current_mode)
                self._host_id = msg.get("host_id")
                self.lobby.update_state(self._players_cache, self.current_map, self.current_mode,
                                         self._host_id, self.net.player_id)
            elif mtype == MSG_PHASE_CHANGE:
                self._on_phase_change(msg.get("phase"), msg.get("time_left", 0))
            elif mtype == MSG_ROLE_ASSIGNED:
                self.my_role = msg.get("role")
                self.my_transformed = None
                self.hud.set_role(self.my_role)
            elif mtype == MSG_SNAPSHOT:
                self._apply_snapshot(msg)
            elif mtype == MSG_SCANNER_RESULT:
                for clue in msg.get("clues", []):
                    self.hud.push_clue(clue)
            elif mtype == MSG_OBJECTIVE_UPDATE:
                self.objectives = msg.get("objectives", [])
            elif mtype == MSG_ELIMINATED:
                if msg.get("player_id") == self.net.player_id:
                    self.hud.push_clue("You were eliminated. Spectating...")
            elif mtype == MSG_ROUND_RESULT:
                self.results.display(msg)
            elif mtype == MSG_CHAT_BROADCAST:
                self.hud.push_clue(f"{msg.get('name')}: {msg.get('text')}")
            elif mtype == MSG_ERROR:
                self.hud.push_clue(f"[!] {msg.get('message')}")
            elif mtype == MSG_PLAYER_LEFT:
                pid = msg.get("player_id")
                if pid in self.remote_entities:
                    destroy(self.remote_entities.pop(pid))

    def _on_phase_change(self, phase, time_left):
        self.current_phase = phase
        self.current_time_left = time_left

        if phase == PHASE_ROLE_ASSIGN:
            self._build_level(self.current_map)
            invoke(self._enter_game_after_build, delay=0.05)
        elif phase == PHASE_COUNTDOWN:
            self.hud.push_clue("Get ready...")
        elif phase == PHASE_HIDING:
            if self.my_role == ROLE_HIDER:
                self.hud.push_clue("Find a hiding spot and transform! (Press 1-9)")
            else:
                self.hud.push_clue("Hiding phase - Hunters are locked out.")
        elif phase == PHASE_HUNTING:
            self.hud.push_clue("Hunting phase has begun!")
        elif phase == PHASE_RESULTS:
            self._show_only(STATE_INGAME)  # results overlays on top briefly via ResultsScreen.show()
            self.results.show()
        elif phase == PHASE_LOBBY:
            self._clear_level()
            self._show_only(STATE_LOBBY)

    def _enter_game_after_build(self):
        if self.current_phase in (
            PHASE_ROLE_ASSIGN,
            PHASE_COUNTDOWN,
            PHASE_HIDING,
            PHASE_HUNTING,
        ):
            self._show_only(STATE_INGAME)

            # Force the camera/player state to update immediately.
            if self.controller:
                self.controller.enabled = True

            mouse.locked = True

    def _apply_snapshot(self, msg):
        self.current_phase = msg.get("phase", self.current_phase)
        self.current_time_left = msg.get("time_left", self.current_time_left)
        self.objectives = msg.get("objectives", self.objectives)
        players = msg.get("players", [])

        alive_hiders = 0
        total_hunters = 0
        my_data = None

        seen_ids = set()
        for p in players:
            pid = p["player_id"]
            seen_ids.add(pid)
            if p.get("role") == ROLE_HIDER and p.get("alive"):
                alive_hiders += 1
            if p.get("role") == ROLE_HUNTER:
                total_hunters += 1

            if pid == self.net.player_id:
                my_data = p
                continue
            self._update_remote_entity(p)

        for pid in list(self.remote_entities.keys()):
            if pid not in seen_ids:
                destroy(self.remote_entities.pop(pid))

        if my_data:
            self.my_transformed = my_data.get("transformed_into")
            if "morph_energy" in my_data:
                self.my_energy = my_data["morph_energy"]
            self.my_health = my_data.get("health", self.my_health)

        self.hud.set_timer(self.current_phase, self.current_time_left)
        self.hud.set_players(alive_hiders, total_hunters)
        self.hud.set_energy(self.my_energy)
        self.hud.set_health(self.my_health)
        required = 0
        if self.objectives:
            needed = settings.OBJECTIVES_TO_WIN.get(self.current_mode, 0)
            required = min(needed, len(self.objectives)) if needed else 0
        completed = sum(1 for o in self.objectives if o.get("completed"))
        self.hud.set_objectives(completed, required)

    def _update_remote_entity(self, p):
        pid = p["player_id"]
        role = p.get("role")
        alive = p.get("alive", True)
        pos = p.get("position", [0, 1, 0])

        if not alive or p.get("eliminated"):
            if pid in self.remote_entities:
                self.remote_entities[pid].enabled = False
            return

        if pid not in self.remote_entities:
            self.remote_entities[pid] = Entity(
            model="cube",
            shader=unlit_shader
        )
            self.level_entities  # (kept separate; cleaned up via remote_entities dict directly)

        e = self.remote_entities[pid]
        e.enabled = True

        if role == ROLE_HUNTER:
            e.scale = Vec3(0.6, 1.8, 0.6)
            e.color = color.rgb(210, 70, 70)
        elif role == ROLE_HIDER:
            transformed = p.get("transformed_into")
            if transformed:
                obj = REGISTRY.get(transformed)
                if obj:
                    e.scale = Vec3(*obj.scale)
                    e.color = color.rgb(*obj.color)
            else:
                e.scale = Vec3(0.6, 1.8, 0.6)
                e.color = color.rgb(70, 200, 90)
        else:
            e.scale = Vec3(0.6, 1.8, 0.6)
            e.color = color.gray

        e.position = Vec3(pos[0], pos[1], pos[2])
        e.rotation_y = p.get("rotation_y", 0)

    # ------------------------------------------------------------------
    # PER-FRAME UPDATE / INPUT
    # ------------------------------------------------------------------
    def update(self):
        self._process_network()
        if self.state == STATE_MENU:
            self.menu.update()
        elif self.state == STATE_CONNECT and self.connect_dialog:
            self.connect_dialog.update()
        elif self.state == STATE_LOBBY:
            self.lobby.update()
        if self.state != STATE_INGAME or not self.controller:
            return
        if self.current_phase == PHASE_RESULTS:
            return

        # apply role-based movement speed
        speed = settings.PLAYER_WALK_SPEED
        if self.my_role == ROLE_HIDER and self.my_transformed:
            obj = REGISTRY.get(self.my_transformed)
            if obj:
                speed *= obj.speed_mult
        elif held_keys["shift"]:
            speed *= settings.PLAYER_SPRINT_MULTIPLIER
        self.controller.speed = speed

        # throttle outgoing input messages
        now = time.time()
        if now - self.last_input_sent >= (1.0 / settings.SNAPSHOT_RATE):
            self.last_input_sent = now
            pos = self.controller.world_position
            self.net.send({
                "type": MSG_INPUT,
                "move": [held_keys["d"] - held_keys["a"], held_keys["w"] - held_keys["s"]],
                "look_y": self.controller.rotation_y,
                "sprint": bool(held_keys["shift"]),
                "jump": False,
                "position": [pos.x, pos.y, pos.z],
            })

        if self.my_role == ROLE_HUNTER:
            cooldown_left = max(0.0, settings.SCANNER_COOLDOWN - (now - self.last_scanner_press))
            self.hud.set_scanner_status(self.scanner_charges, settings.SCANNER_MAX_CHARGES, cooldown_left)

        if self.my_role == ROLE_HIDER:
            hint = "Press 1-9 to transform" if not self.my_transformed else f"Disguised as: {REGISTRY.get(self.my_transformed).display if REGISTRY.get(self.my_transformed) else '?'}"
            hint += "  |  E: interact with objective"
            self.hud.set_transform_hint(hint)
        else:
            self.hud.set_transform_hint("Left Click: attack  |  Q: scanner")

    def input(self, key):
        if self.state == STATE_MENU:
            self.menu.input(key)
            return

        if self.state == STATE_CONNECT and self.connect_dialog:
            self.connect_dialog.input(key)
            return

        if self.state == STATE_LOBBY:
            self.lobby.input(key)
            return

        if key == "escape":
            self.paused = not self.paused
            mouse.locked = not self.paused and self.state == STATE_INGAME
            return

        if self.state != STATE_INGAME or self.paused:
            return

        if self.my_role == ROLE_HIDER and key.isdigit() and key != "0":
            idx = int(key) - 1
            if 0 <= idx < len(self._object_hotbar):
                obj_key = self._object_hotbar[idx]
                self.my_transformed = obj_key
                self.net.send({"type": MSG_TRANSFORM, "object_type": obj_key})

        elif key == "e" and self.my_role == ROLE_HIDER:
            self.net.send({"type": MSG_INTERACT})

        elif key == "q" and self.my_role == ROLE_HUNTER:
            self.last_scanner_press = time.time()
            self.net.send({"type": MSG_SCANNER})

        elif key == "left mouse down" and self.my_role == ROLE_HUNTER:
            self.net.send({"type": MSG_ATTACK})


# ----------------------------------------------------------------------
# MODULE-LEVEL URSINA HOOKS
# ----------------------------------------------------------------------
_app_instance: "ClientApp | None" = None


def update():
    if _app_instance:
        _app_instance.update()


def input(key):  # noqa: A001 - Ursina calls a global `input(key)` by convention
    if _app_instance:
        _app_instance.input(key)


def run():
    global _app_instance
    ursina_app = Ursina(title="Morph Hunt: The Object Among Us")
    _app_instance = ClientApp()
    ursina_app.run()
