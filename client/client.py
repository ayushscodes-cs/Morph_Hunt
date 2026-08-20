"""
ClientApp — full Panda3D implementation with rich gameplay mechanics:
- 3D directional & ambient lighting + shaders
- First & 3rd-person camera modes (C key)
- Prop rotation freeze/lock (F key / RMB)
- Hunter laser blaster visual effects + crosshair hitmarker
- Hunter flashlight (L key)
- Hider taunts (T key)
- Procedural audio feedback (laser, morph, hit, scanner, taunt)
- Interactive glowing objective beacons
"""

from __future__ import annotations

import math
import threading
import time

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    AmbientLight, DirectionalLight, Spotlight, PerspectiveLens,
    GeomNode, CardMaker, LineSegs,
    CollisionNode, CollisionBox, CollisionCapsule,
    CollisionHandlerPusher, CollisionTraverser,
    LVecBase4f, LPoint3f, LVecBase3f, Vec3,
    WindowProperties,
    Shader,
    NodePath,
    loadPrcFileData,
)

from config import settings
from game.game_state import (
    MSG_SET_READY, MSG_SET_MAP, MSG_SET_MODE, MSG_START_GAME, MSG_INPUT,
    MSG_TRANSFORM, MSG_UNTRANSFORM, MSG_SCANNER, MSG_ATTACK, MSG_INTERACT, MSG_LEAVE,
    MSG_ADD_BOT, MSG_TAUNT,
    MSG_WELCOME, MSG_LOBBY_STATE, MSG_PHASE_CHANGE, MSG_ROLE_ASSIGNED, MSG_SNAPSHOT,
    MSG_SCANNER_RESULT, MSG_OBJECTIVE_UPDATE, MSG_ELIMINATED, MSG_ROUND_RESULT,
    MSG_CHAT_BROADCAST, MSG_TAUNT_BROADCAST, MSG_ERROR, MSG_PLAYER_LEFT,
    PHASE_LOBBY, PHASE_ROLE_ASSIGN, PHASE_COUNTDOWN, PHASE_HIDING, PHASE_HUNTING, PHASE_RESULTS,
    ROLE_HIDER, ROLE_HUNTER,
)
from game.object_prop import REGISTRY
from game.level_manager import load_level
from client.network_client import NetworkClient
from client.audio import SoundManager
from ui.menu import MainMenu, ConnectDialog
from ui.lobby import LobbyScreen
from ui.hud import HUD
from ui.results import ResultsScreen

# ---------------------------------------------------------------------------
# Panda3D window settings
# ---------------------------------------------------------------------------
loadPrcFileData("", "window-title Morph Hunt: The Object Among Us")
loadPrcFileData("", "undecorated 0")
loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "sync-video 1")
loadPrcFileData("", "show-frame-rate-meter 0")

# ---------------------------------------------------------------------------
# Lit shader with vertex colors and normals for rich 3D shading
# ---------------------------------------------------------------------------
_VERT_GLSL = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec4 p3d_Color;
in vec3 p3d_Normal;
out vec4 v_color;
out vec3 v_normal;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_color = p3d_Color;
    v_normal = normalize(p3d_NormalMatrix * p3d_Normal);
}
"""
_FRAG_GLSL = """
#version 130
in vec4 v_color;
in vec3 v_normal;
out vec4 fragColor;
void main() {
    // 2-point directional lighting for rich 3D depth
    vec3 light1 = normalize(vec3(0.5, 0.7, 0.9));
    vec3 light2 = normalize(vec3(-0.4, -0.6, 0.3));
    float diff1 = max(dot(v_normal, light1), 0.0) * 0.55;
    float diff2 = max(dot(v_normal, light2), 0.0) * 0.25;
    float ambient = 0.45;
    float brightness = clamp(ambient + diff1 + diff2, 0.2, 1.1);
    fragColor = vec4(v_color.rgb * brightness, v_color.a);
}
"""


def _make_shader():
    return Shader.make(Shader.SL_GLSL, _VERT_GLSL, _FRAG_GLSL)


def _c4(r, g, b, a=1.0) -> LVecBase4f:
    return LVecBase4f(r / 255.0, g / 255.0, b / 255.0, a)


# ---------------------------------------------------------------------------
# Box geometry builder with proper normals and vertex colours
# ---------------------------------------------------------------------------
def _make_box(render_root: NodePath, pos, scale, color_rgb, shader) -> NodePath:
    from panda3d.core import (
        GeomVertexFormat, GeomVertexData, GeomVertexWriter,
        Geom, GeomTriangles, GeomNode,
    )

    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("box", fmt, Geom.UHStatic)
    vdata.setNumRows(24)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")

    r, g, b = color_rgb[0] / 255.0, color_rgb[1] / 255.0, color_rgb[2] / 255.0
    col = (r, g, b, 1.0)

    hw, hh, hd = 0.5, 0.5, 0.5
    # 6 faces: (normal, 4 corners)
    faces = [
        ((1, 0, 0),  [(hw, -hd, -hh), (hw, hd, -hh), (hw, hd, hh), (hw, -hd, hh)]),     # +X
        ((-1, 0, 0), [(-hw, hd, -hh), (-hw, -hd, -hh), (-hw, -hd, hh), (-hw, hd, hh)]),  # -X
        ((0, 1, 0),  [(hw, hd, -hh), (-hw, hd, -hh), (-hw, hd, hh), (hw, hd, hh)]),      # +Y
        ((0, -1, 0), [(-hw, -hd, -hh), (hw, -hd, -hh), (hw, -hd, hh), (-hw, -hd, hh)]),  # -Y
        ((0, 0, 1),  [(-hw, -hd, hh), (hw, -hd, hh), (hw, hd, hh), (-hw, hd, hh)]),      # +Z (Up)
        ((0, 0, -1), [(hw, -hd, -hh), (-hw, -hd, -hh), (-hw, hd, -hh), (hw, hd, -hh)]),  # -Z (Down)
    ]

    tris = GeomTriangles(Geom.UHStatic)
    for fi, (norm, corners) in enumerate(faces):
        base_idx = fi * 4
        for vx, vy, vz in corners:
            vertex.addData3(vx, vy, vz)
            normal.addData3(*norm)
            color_w.addData4(*col)
        tris.addVertices(base_idx, base_idx + 1, base_idx + 2)
        tris.addVertices(base_idx, base_idx + 2, base_idx + 3)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    gn = GeomNode("box_geom")
    gn.addGeom(geom)

    np = render_root.attachNewNode(gn)
    np.setPos(*pos)
    np.setScale(*scale)
    np.setShader(shader)
    return np


# ---------------------------------------------------------------------------
# State constants
# ---------------------------------------------------------------------------
STATE_MENU    = "menu"
STATE_CONNECT = "connect"
STATE_LOBBY   = "lobby"
STATE_INGAME  = "ingame"


# ---------------------------------------------------------------------------
# ClientApp
# ---------------------------------------------------------------------------
class ClientApp(ShowBase):

    def __init__(self):
        super().__init__()

        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Morph Hunt: The Object Among Us")
        props.setUndecorated(False)
        if hasattr(self.win, "requestProperties"):
            self.win.requestProperties(props)
        self.win.setClearColor(_c4(18, 20, 28))

        # Shader
        self._shader = _make_shader()

        # Camera & View modes
        self._cam_yaw   = 0.0
        self._cam_pitch = 0.0
        self._mouse_locked = False
        self._third_person = False
        self._rotation_locked = False
        self._locked_player_yaw = 0.0
        self._vel_z = 0.0
        self._is_grounded = True

        # Laser beam & VFX nodes
        self._laser_np = None
        self._laser_timer = 0.0
        self._flashlight_on = True
        self._flashlight = None

        # Player collision & physics
        self.cTrav = CollisionTraverser()
        self._pusher = CollisionHandlerPusher()

        # Networking
        self.net = NetworkClient()
        self.server_thread = None
        self.local_server  = None

        # Game State
        self.state           = STATE_MENU
        self.current_phase   = PHASE_LOBBY
        self.current_time_left = 0
        self.current_mode    = settings.GAME_MODES[0]
        self.current_map     = settings.LEVELS[0]
        self.my_role         = None
        self.my_transformed  = None
        self.my_health       = settings.PLAYER_START_HEALTH
        self.my_energy       = settings.MORPH_ENERGY_MAX
        self.scanner_charges = settings.SCANNER_MAX_CHARGES
        self.last_scanner_press = -999.0
        self.last_taunt_press   = -999.0
        self.objectives      = []
        self.last_input_sent = 0.0
        self.paused          = False

        self._object_hotbar = list(REGISTRY.keys())[:9]

        # Geometry references
        self.level_nodes:  list[NodePath] = []
        self.remote_nodes: dict[str, NodePath] = {}
        self.objective_nodes: list[NodePath] = []
        self._player_np:   NodePath | None = None
        self._player_visual: NodePath | None = None
        self._player_col:  NodePath | None = None

        # UI
        self.menu   = MainMenu(self._on_host_clicked, self._on_join_clicked, self.userExit)
        self.connect_dialog: ConnectDialog | None = None
        self.lobby  = LobbyScreen(
            self._on_ready_toggle,
            self._on_set_map,
            self._on_set_mode,
            self._on_start_game,
            self._on_leave_lobby,
            self._on_add_bot,
        )
        self.hud     = HUD(self.aspect2d)
        self.results = ResultsScreen(self._on_results_continue)

        self._show_only(STATE_MENU)

        # Keybinds
        self._keys: dict[str, bool] = {}
        for k in ("w", "a", "s", "d", "space", "shift", "escape",
                  "1","2","3","4","5","6","7","8","9",
                  "e", "q", "f", "c", "t", "l", "mouse1", "mouse3"):
            self.accept(k,        self._key_down, [k])
            self.accept(k + "-up",self._key_up,   [k])

        # Main Loop Task
        self.taskMgr.add(self._main_loop, "main_loop")

    # ==================================================================
    # INPUT HANDLING
    # ==================================================================
    def _key_down(self, key):
        self._keys[key] = True
        self._handle_press(key)

    def _key_up(self, key):
        self._keys[key] = False

    def _k(self, key) -> bool:
        return self._keys.get(key, False)

    def _handle_press(self, key):
        if key == "escape":
            if self.state == STATE_INGAME:
                self.paused = not self.paused
                self._set_mouse_locked(not self.paused)
            return

        if self.state != STATE_INGAME or self.paused:
            return

        # ---- HIDER ACTIONS ----
        if self.my_role == ROLE_HIDER:
            # 1-9 Transform
            if key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(self._object_hotbar):
                    obj_key = self._object_hotbar[idx]
                    self.my_transformed = obj_key
                    SoundManager.morph()
                    self._update_local_player_model()
                    self.net.send({"type": MSG_TRANSFORM, "object_type": obj_key})

            # F or Mouse3 (RMB): Freeze / Lock Prop Rotation
            elif key in ("f", "mouse3"):
                self._rotation_locked = not self._rotation_locked
                if self._rotation_locked:
                    self._locked_player_yaw = self._cam_yaw
                    self.hud.push_clue("[Locked Rotation] Camera moves freely!")
                else:
                    self.hud.push_clue("[Unlocked Rotation]")

            # C: Toggle 3rd Person View
            elif key == "c":
                self._third_person = not self._third_person

            # T: Taunt Whistle
            elif key == "t":
                now = time.time()
                if (now - self.last_taunt_press) >= settings.TAUNT_COOLDOWN:
                    self.last_taunt_press = now
                    SoundManager.taunt()
                    self.net.send({"type": MSG_TAUNT})
                    self.hud.push_clue("You taunted the Hunter! (+20 XP)")

            # E: Interact with Objective
            elif key == "e":
                self.net.send({"type": MSG_INTERACT})

        # ---- HUNTER ACTIONS ----
        elif self.my_role == ROLE_HUNTER:
            # LMB: Fire Energy Blaster
            if key == "mouse1":
                self._fire_blaster()

            # Q: Scanner Sonar
            elif key == "q":
                self.last_scanner_press = time.time()
                SoundManager.scanner()
                self.net.send({"type": MSG_SCANNER})

            # L: Toggle Flashlight
            elif key == "l":
                self._toggle_flashlight()

    def _fire_blaster(self):
        SoundManager.laser()
        self._spawn_laser_tracer()
        self.net.send({"type": MSG_ATTACK})

    def _spawn_laser_tracer(self):
        """Draw an instant glowing cyan laser beam from player camera forward."""
        if self._laser_np:
            self._laser_np.removeNode()

        segs = LineSegs("laser")
        segs.setColor(0.3, 0.9, 1.0, 1.0)
        segs.setThickness(4.0)

        p = self.camera.getPos(self.render)
        fwd = self.camera.getQuat(self.render).getForward()
        end_p = p + fwd * settings.ATTACK_RANGE

        segs.moveTo(p + fwd * 0.4 + Vec3(0.15, -0.1, -0.1))
        segs.drawTo(end_p)

        self._laser_np = self.render.attachNewNode(segs.create())
        self._laser_timer = 0.08

    def _toggle_flashlight(self):
        self._flashlight_on = not self._flashlight_on
        if self._flashlight:
            self._flashlight.node().setActive(self._flashlight_on)

    # ==================================================================
    # MOUSE LOCK
    # ==================================================================
    def _set_mouse_locked(self, locked: bool):
        self._mouse_locked = locked
        if hasattr(self.win, "requestProperties"):
            props = WindowProperties()
            props.setCursorHidden(locked)
            props.setMouseMode(
                WindowProperties.M_confined if locked else WindowProperties.M_absolute
            )
            self.win.requestProperties(props)
        if locked and hasattr(self.win, "getProperties"):
            cx = self.win.getProperties().getXSize() // 2
            cy = self.win.getProperties().getYSize() // 2
            self.win.movePointer(0, cx, cy)

    # ==================================================================
    # SCREEN TRANSITIONS
    # ==================================================================
    def _show_only(self, state: str):
        self.state = state
        self.menu.hide()
        self.lobby.hide()
        self.hud.hide()
        self.results.hide()
        if self.connect_dialog:
            self.connect_dialog.hide()

        if state == STATE_MENU:
            self.menu.show()
            self._set_mouse_locked(False)
        elif state == STATE_LOBBY:
            self.lobby.show()
            self._set_mouse_locked(False)
        elif state == STATE_INGAME:
            self.hud.show()
            self._set_mouse_locked(True)

    # ==================================================================
    # MENU & LOBBY CALLBACKS
    # ==================================================================
    def _on_host_clicked(self):
        self.state = STATE_CONNECT
        self.connect_dialog = ConnectDialog(self._do_host, self._cancel_dialog, mode="host")
        self.menu.hide()
        self._set_mouse_locked(False)

    def _on_join_clicked(self):
        self.state = STATE_CONNECT
        self.connect_dialog = ConnectDialog(self._do_join, self._cancel_dialog, mode="join")
        self.menu.hide()
        self._set_mouse_locked(False)

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
        time.sleep(0.3)

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

    def _on_ready_toggle(self):
        self._my_ready = not getattr(self, "_my_ready", False)
        self.net.send({"type": MSG_SET_READY, "ready": self._my_ready})

    def _on_set_map(self, map_key):
        self.net.send({"type": MSG_SET_MAP, "map": map_key})

    def _on_set_mode(self, mode):
        self.net.send({"type": MSG_SET_MODE, "mode": mode})

    def _on_add_bot(self):
        self.net.send({"type": MSG_ADD_BOT})

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

    # ==================================================================
    # LEVEL BUILDING
    # ==================================================================
    def _clear_level(self):
        for np in self.level_nodes:
            np.removeNode()
        self.level_nodes.clear()

        for np in self.remote_nodes.values():
            np.removeNode()
        self.remote_nodes.clear()

        for np in self.objective_nodes:
            np.removeNode()
        self.objective_nodes.clear()

        if self._player_np:
            self._player_np.removeNode()
            self._player_np = None
        if self._player_visual:
            self._player_visual.removeNode()
            self._player_visual = None

        self.win.setClearColor(_c4(10, 12, 20))

    def _build_level(self, level_key):
        self._clear_level()
        self.current_map = level_key
        level_def = load_level(level_key)

        # 1. Map geometry (Panda3D coordinate mapping: X=x, Y=z, Z=y)
        for g in level_def.get("geometry", []):
            p = g["position"]
            s = g["scale"]
            np = _make_box(
                self.render,
                pos=(p[0], p[2], p[1]),
                scale=(s[0], s[2], s[1]),
                color_rgb=g["color"],
                shader=self._shader,
            )
            # Only add collision to solid walls and props (not floors, to avoid vertical collision fighting)
            if g.get("solid", True) and g.get("type") != "floor":
                col_node = CollisionNode("wall_col")
                col_node.addSolid(CollisionBox(LPoint3f(0, 0, 0), 0.5, 0.5, 0.5))
                col_np = np.attachNewNode(col_node)
                self.level_nodes.append(col_np)
            self.level_nodes.append(np)

        # 2. Continuous world floor visual
        wf = _make_box(
            self.render,
            pos=(0, 0, -0.65),
            scale=(80, 80, 1),
            color_rgb=(35, 38, 45),
            shader=self._shader,
        )
        self.level_nodes.append(wf)

        # 3. Static hider spawn objects
        for spot in level_def.get("hider_spawn_objects", []):
            obj = REGISTRY.get(spot["key"])
            if not obj:
                continue
            p = spot["position"]
            s = obj.scale
            np = _make_box(
                self.render,
                pos=(p[0], p[2], p[1]),
                scale=(s[0], s[2], s[1]),
                color_rgb=obj.color,
                shader=self._shader,
            )
            self.level_nodes.append(np)

        # 4. Interactive objective markers (glowing yellow/orange beacons)
        for obj in level_def.get("objectives", []):
            p = obj["position"]
            np = _make_box(
                self.render,
                pos=(p[0], p[2], p[1]),
                scale=(0.8, 0.8, 1.2),
                color_rgb=(255, 180, 40),
                shader=self._shader,
            )
            self.objective_nodes.append(np)
            self.level_nodes.append(np)

        # 5. Clear color
        self.win.setClearColor(_c4(20, 24, 32))

        # 6. Player Root Node
        spawn = level_def.get("hunter_spawns", [[0, 1.0, 0]])[0]
        self._player_np = self.render.attachNewNode("player_root")
        self._player_np.setPos(spawn[0], spawn[2], 1.0)
        self._vel_z = 0.0
        self._is_grounded = True

        # Player visual model (visible in 3rd person)
        self._player_visual = self._player_np.attachNewNode("player_visual")
        self._update_local_player_model()

        # Camera
        self.camera.reparentTo(self._player_np)
        self.camera.setPos(0, 0, 0.6)
        self.camera.setHpr(0, 0, 0)
        self._cam_yaw   = 0.0
        self._cam_pitch = 0.0

        # Collision Capsule for horizontal wall sliding
        c_node = CollisionNode("player_col")
        capsule = CollisionCapsule(0, 0, -0.3, 0, 0, 0.3, 0.35)
        c_node.addSolid(capsule)
        self._player_col = self._player_np.attachNewNode(c_node)
        self._pusher.addCollider(self._player_col, self._player_np)
        self.cTrav.addCollider(self._player_col, self._pusher)


    def _update_local_player_model(self):
        if not self._player_visual:
            return
        for child in self._player_visual.getChildren():
            child.removeNode()

        if self.my_role == ROLE_HIDER and self.my_transformed:
            obj = REGISTRY.get(self.my_transformed)
            if obj:
                _make_box(
                    self._player_visual,
                    pos=(0, 0, 0),
                    scale=obj.scale,
                    color_rgb=obj.color,
                    shader=self._shader,
                )
        elif self.my_role == ROLE_HUNTER:
            _make_box(
                self._player_visual,
                pos=(0, 0, 0),
                scale=(0.6, 0.6, 1.8),
                color_rgb=(210, 70, 70),
                shader=self._shader,
            )

    # ==================================================================
    # NETWORK MESSAGE PROCESSING
    # ==================================================================
    def _process_network(self):
        for msg in self.net.poll():
            mtype = msg.get("type")
            if mtype == "_disconnected":
                self._on_leave_lobby()
                return
            elif mtype == MSG_LOBBY_STATE:
                self._players_cache = msg.get("players", [])
                self.current_map  = msg.get("map", self.current_map)
                self.current_mode = msg.get("mode", self.current_mode)
                self._host_id = msg.get("host_id")
                self.lobby.update_state(
                    self._players_cache, self.current_map,
                    self.current_mode, self._host_id, self.net.player_id,
                )
            elif mtype == MSG_PHASE_CHANGE:
                self._on_phase_change(msg.get("phase"), msg.get("time_left", 0))
            elif mtype == MSG_ROLE_ASSIGNED:
                self.my_role = msg.get("role")
                self.my_transformed = None
                self._update_local_player_model()
                self.hud.set_role(self.my_role)
            elif mtype == MSG_SNAPSHOT:
                self._apply_snapshot(msg)
            elif mtype == MSG_SCANNER_RESULT:
                for clue in msg.get("clues", []):
                    self.hud.push_clue(clue)
            elif mtype == MSG_OBJECTIVE_UPDATE:
                self.objectives = msg.get("objectives", [])
            elif mtype == MSG_TAUNT_BROADCAST:
                SoundManager.taunt()
                self.hud.push_clue(f"[!] {msg.get('name')} taunted!")
            elif mtype == MSG_ELIMINATED:
                SoundManager.eliminated()
                if msg.get("player_id") == self.net.player_id:
                    self.hud.push_clue("You were eliminated. Spectating...")
            elif mtype == MSG_ROUND_RESULT:
                self.results.display(msg)
                self._show_only(STATE_INGAME)
                self.results.show()
            elif mtype == MSG_CHAT_BROADCAST:
                self.hud.push_clue(f"{msg.get('name')}: {msg.get('text')}")
            elif mtype == MSG_ERROR:
                self.hud.push_clue(f"[!] {msg.get('message')}")
            elif mtype == MSG_PLAYER_LEFT:
                pid = msg.get("player_id")
                if pid in self.remote_nodes:
                    self.remote_nodes.pop(pid).removeNode()

    def _on_phase_change(self, phase, time_left):
        self.current_phase     = phase
        self.current_time_left = time_left

        if phase == PHASE_ROLE_ASSIGN:
            self._build_level(self.current_map)
            self.taskMgr.doMethodLater(0.05, self._enter_game_task, "enter_game")
        elif phase == PHASE_COUNTDOWN:
            SoundManager.countdown()
            self.hud.push_clue("Get ready...")
        elif phase == PHASE_HIDING:
            if self.my_role == ROLE_HIDER:
                self.hud.push_clue("Find a spot and disguise! [1-9] Morph  [F] Lock Angle")
            else:
                self.hud.push_clue("Hiding phase — Hunters preparing...")
        elif phase == PHASE_HUNTING:
            self.hud.push_clue("HUNTING BEGUN! Find the disguised objects!")
        elif phase == PHASE_LOBBY:
            self._clear_level()
            self._show_only(STATE_LOBBY)

    def _enter_game_task(self, task):
        if self.current_phase in (
            PHASE_ROLE_ASSIGN, PHASE_COUNTDOWN, PHASE_HIDING, PHASE_HUNTING
        ):
            self._show_only(STATE_INGAME)
            self._set_mouse_locked(True)
        return Task.done

    def _apply_snapshot(self, msg):
        self.current_phase     = msg.get("phase", self.current_phase)
        self.current_time_left = msg.get("time_left", self.current_time_left)
        self.objectives        = msg.get("objectives", self.objectives)
        players = msg.get("players", [])

        alive_hiders  = 0
        total_hunters = 0
        my_data       = None
        seen_ids      = set()

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
            self._update_remote_node(p)

        for pid in list(self.remote_nodes.keys()):
            if pid not in seen_ids:
                self.remote_nodes.pop(pid).removeNode()

        if my_data:
            new_trans = my_data.get("transformed_into")
            if new_trans != self.my_transformed:
                self.my_transformed = new_trans
                self._update_local_player_model()

            if "morph_energy" in my_data:
                self.my_energy = my_data["morph_energy"]
            self.my_health = my_data.get("health", self.my_health)

        self.hud.set_timer(self.current_phase, self.current_time_left)
        self.hud.set_players(alive_hiders, total_hunters)
        self.hud.set_energy(self.my_energy)
        self.hud.set_health(self.my_health)

        needed = settings.OBJECTIVES_TO_WIN.get(self.current_mode, 0)
        required = min(needed, len(self.objectives)) if needed and self.objectives else 0
        completed = sum(1 for o in self.objectives if o.get("completed"))
        self.hud.set_objectives(completed, required)

    def _update_remote_node(self, p):
        pid   = p["player_id"]
        role  = p.get("role")
        alive = p.get("alive", True)
        pos   = p.get("position", [0, 1, 0])

        if not alive or p.get("eliminated"):
            if pid in self.remote_nodes:
                self.remote_nodes[pid].hide()
            return

        if pid not in self.remote_nodes:
            self.remote_nodes[pid] = _make_box(
                self.render,
                pos=(0, 0, 0),
                scale=(0.6, 0.6, 1.8),
                color_rgb=(150, 150, 150),
                shader=self._shader,
            )

        np = self.remote_nodes[pid]
        np.show()

        if role == ROLE_HUNTER:
            np.setScale(0.6, 0.6, 1.8)
            np.setColor(_c4(210, 70, 70))
        elif role == ROLE_HIDER:
            transformed = p.get("transformed_into")
            if transformed:
                obj = REGISTRY.get(transformed)
                if obj:
                    np.setScale(obj.scale[0], obj.scale[2], obj.scale[1])
                    np.setColor(_c4(*obj.color))
            else:
                np.setScale(0.6, 0.6, 1.8)
                np.setColor(_c4(70, 200, 90))

        # Position mapping: [x, z, y]
        np.setPos(pos[0], pos[2], pos[1])
        np.setH(p.get("rotation_y", 0))

    # ==================================================================
    # MAIN LOOP
    # ==================================================================
    def _main_loop(self, task):
        dt = globalClock.getDt()

        self._process_network()

        # Laser beam decay
        if self._laser_np:
            self._laser_timer -= dt
            if self._laser_timer <= 0:
                self._laser_np.removeNode()
                self._laser_np = None

        if self.state == STATE_INGAME and not self.paused and self._player_np:
            self._update_player(dt)

        return Task.cont

    # ==================================================================
    # PLAYER MOVEMENT & CAMERA
    # ==================================================================
    def _update_player(self, dt: float):
        # ---- Mouse look ------------------------------------------------
        if self._mouse_locked and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            cx = self.win.getProperties().getXSize() // 2
            cy = self.win.getProperties().getYSize() // 2
            dx = md.getX() - cx
            dy = md.getY() - cy
            if dx or dy:
                self._cam_yaw   -= dx * 0.15
                self._cam_pitch -= dy * 0.15
                self._cam_pitch  = max(-80.0, min(80.0, self._cam_pitch))
                self.win.movePointer(0, cx, cy)

            if not self._rotation_locked:
                self._player_np.setH(self._cam_yaw)
            else:
                self._player_np.setH(self._locked_player_yaw)

            # Camera 1st vs 3rd Person
            if self._third_person and self.my_role == ROLE_HIDER:
                rad_yaw = math.radians(self._cam_yaw)
                cam_dist = 2.4
                cam_x = math.sin(rad_yaw) * cam_dist
                cam_y = -math.cos(rad_yaw) * cam_dist
                self.camera.setPos(cam_x, cam_y, 1.2)
                self.camera.setHpr(self._cam_yaw - self._player_np.getH(), self._cam_pitch, 0)
            else:
                self.camera.setPos(0, 0, 0.6)
                self.camera.setHpr(0 if not self._rotation_locked else self._cam_yaw - self._locked_player_yaw, self._cam_pitch, 0)

        # ---- Movement --------------------------------------------------
        speed = settings.PLAYER_WALK_SPEED
        if self.my_role == ROLE_HIDER and self.my_transformed:
            obj = REGISTRY.get(self.my_transformed)
            if obj:
                speed *= obj.speed_mult
        elif self._k("shift"):
            speed *= settings.PLAYER_SPRINT_MULTIPLIER

        forward = 0.0
        right   = 0.0
        if self._k("w"): forward += 1
        if self._k("s"): forward -= 1
        if self._k("d"): right   += 1
        if self._k("a"): right   -= 1

        if forward or right:
            # If player moves while rotation was locked, unlock rotation
            if self._rotation_locked:
                self._rotation_locked = False

            yaw_rad = math.radians(self._cam_yaw)
            fx = -math.sin(yaw_rad)
            fy =  math.cos(yaw_rad)
            rx =  math.cos(yaw_rad)
            ry =  math.sin(yaw_rad)

            vx = (fx * forward + rx * right) * speed * dt
            vy = (fy * forward + ry * right) * speed * dt

            pos = self._player_np.getPos()
            self._player_np.setPos(pos.x + vx, pos.y + vy, pos.z)

        # Jump input
        if self._k("space") and self._is_grounded:
            self._vel_z = 6.5
            self._is_grounded = False

        # Stable vertical physics (smooth jump & rock-solid ground lock at Z=1.0)
        if not self._is_grounded:
            self._vel_z -= 22.0 * dt
            pos = self._player_np.getPos()
            new_z = pos.z + self._vel_z * dt
            if new_z <= 1.0:
                new_z = 1.0
                self._vel_z = 0.0
                self._is_grounded = True
            self._player_np.setZ(new_z)
        else:
            self._player_np.setZ(1.0)

        # Physics collision with walls
        self.cTrav.traverse(self.render)
        self._player_np.setZ(1.0 if self._is_grounded else self._player_np.getZ())

        # ---- Send Snapshot Input ---------------------------------------
        now = time.time()
        if now - self.last_input_sent >= (1.0 / settings.SNAPSHOT_RATE):
            self.last_input_sent = now
            p = self._player_np.getPos()
            self.net.send({
                "type": MSG_INPUT,
                "move": [
                    (1 if self._k("d") else 0) - (1 if self._k("a") else 0),
                    (1 if self._k("w") else 0) - (1 if self._k("s") else 0),
                ],
                "look_y": self._player_np.getH(),
                "sprint": bool(self._k("shift")),
                "jump": False,
                "position": [p.x, p.z, p.y],
            })

        # ---- HUD Prompts -----------------------------------------------
        if self.my_role == ROLE_HUNTER:
            cooldown_left = max(
                0.0, settings.SCANNER_COOLDOWN - (now - self.last_scanner_press)
            )
            self.hud.set_scanner_status(
                self.scanner_charges, settings.SCANNER_MAX_CHARGES, cooldown_left
            )
            self.hud.set_transform_hint("[LMB] Blaster  |  [Q] Scanner  |  [L] Flashlight")

        elif self.my_role == ROLE_HIDER:
            rot_status = "LOCKED (F to unlock)" if self._rotation_locked else "F: Lock Angle"
            view_status = "3rd Person (C)" if self._third_person else "1st Person (C)"
            if self.my_transformed:
                obj = REGISTRY.get(self.my_transformed)
                hint = f"Disguise: {obj.display if obj else '?'}  |  {rot_status}  |  {view_status}  |  [T] Taunt"
            else:
                hint = f"[1-9] Choose Morph  |  {rot_status}  |  {view_status}  |  [T] Taunt"
            self.hud.set_transform_hint(hint)
