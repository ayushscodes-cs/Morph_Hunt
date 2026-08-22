from __future__ import annotations

import math
import threading
import time

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
# pyrefly: ignore [missing-import]
from panda3d.core import (
    AmbientLight, DirectionalLight, Spotlight, PerspectiveLens,
    GeomNode, CardMaker, LineSegs,
    CollisionNode, CollisionBox, CollisionSphere, CollisionCapsule,
    CollisionRay, CollisionSegment, CollisionPlane, Plane,
    CollisionHandlerPusher, CollisionHandlerFluidPusher, CollisionHandlerQueue, CollisionTraverser,
    LVecBase4f, LPoint3f, LVecBase3f, Vec3, LVector3f,
    WindowProperties,
    Shader,
    NodePath,
    loadPrcFileData,
    BitMask32,
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

loadPrcFileData("", "window-title Morph Hunt")
loadPrcFileData("", "undecorated 0")
loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "sync-video 1")
loadPrcFileData("", "show-frame-rate-meter 0")

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
    vec3 light1 = normalize(vec3(0.5, 0.7, 0.9));
    vec3 light2 = normalize(vec3(-0.4, -0.6, 0.3));
    float diff1 = max(dot(v_normal, light1), 0.0) * 0.55;
    float diff2 = max(dot(v_normal, light2), 0.0) * 0.25;
    float ambient = 0.75;
    float brightness = clamp(ambient + diff1 + diff2, 0.3, 1.3);
    fragColor = vec4(v_color.rgb * brightness, v_color.a);
}
"""


def _make_shader():
    return Shader.make(Shader.SL_GLSL, _VERT_GLSL, _FRAG_GLSL)


def _c4(r, g, b, a=1.0) -> LVecBase4f:
    return LVecBase4f(r / 255.0, g / 255.0, b / 255.0, a)


# pyrefly: ignore [missing-import]
from panda3d.core import get_model_path, Filename
from direct.actor.Actor import Actor
import os

# Add our assets dir
_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, 'assets/models/furniture/Models')).getFullpath())
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, 'assets/models/characters/Model')).getFullpath())
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, 'assets/models/characters/Animations')).getFullpath())

PROP_MODEL_MAP = {
    "sofa": "loungeSofaLong.obj", "sofa_side": "loungeChair.obj",
    "coffee_table": "tableCoffee.obj", "tv_stand": "cabinetTelevision.obj",
    "tv": "televisionModern.obj", "bookshelf": "bookcaseOpen.obj",
    "counter_l": "kitchenCabinet.obj", "counter_r": "kitchenCabinet.obj",
    "island": "kitchenBar.obj", "fridge": "kitchenFridge.obj",
    "stove": "kitchenStove.obj", "sink": "kitchenSink.obj",
    "dining_table": "table.obj", "dining_chair_1": "chair.obj",
    "dining_chair_2": "chair.obj", "dining_chair_3": "chair.obj",
    "dining_chair_4": "chair.obj", "family_sofa": "loungeSofa.obj",
    "family_table": "tableCoffeeSquare.obj", "armchair": "loungeChairRelax.obj",
    "bed_master": "bedDouble.obj", "wardrobe_master": "bookcaseClosedDoors.obj",
    "nightstand_1": "sideTableDrawers.obj", "nightstand_2": "sideTableDrawers.obj",
    "bed_2": "bedSingle.obj", "bed_3": "bedSingle.obj", "desk_2": "desk.obj",
    "desk_3": "desk.obj", "wardrobe_2": "bookcaseClosedDoors.obj",
    "shelf_3": "bookcaseOpen.obj", "bath_sink_1": "bathroomSink.obj",
    "bath_sink_2": "bathroomSink.obj", "bath_tub": "bathtub.obj",
    "bath_toilet": "toilet.obj", "garage_car": "cardboardBoxClosed.obj",
    "garage_shelf": "bookcaseOpen.obj", "garage_toolbox": "cardboardBoxClosed.obj",
    "bmt_pillar_1": "cardboardBoxClosed.obj", "bmt_pillar_2": "cardboardBoxClosed.obj",
    "bmt_pillar_3": "cardboardBoxClosed.obj", "bmt_pillar_4": "cardboardBoxClosed.obj",
    "bmt_shelf_1": "bookcaseOpen.obj", "bmt_shelf_2": "bookcaseOpen.obj",
    "bmt_workbench": "desk.obj", "bmt_boiler": "washer.obj",
    "bmt_storage_rack": "bookcaseOpen.obj", "terrace_table": "table.obj",
    "terrace_chair_1": "chair.obj", "terrace_chair_2": "chair.obj",
    "terrace_planter_1": "pottedPlant.obj", "terrace_planter_2": "pottedPlant.obj",
    "terrace_bench": "bench.obj", "yard_tree_1": "plantSmall1.obj",
    "yard_tree_2": "plantSmall2.obj", "yard_tree_3": "plantSmall1.obj",
    "yard_tree_4": "plantSmall2.obj", "garden_bench": "bench.obj",
    "garden_table": "tableRound.obj", "garden_chair_1": "chair.obj",
    "garden_chair_2": "chair.obj", "garden_shed": "cardboardBoxClosed.obj",
    "garden_swing": "bench.obj", "garden_fountain": "bathroomSink.obj",
    "mailbox": "trashcan.obj", "garden_gnome": "pottedPlant.obj",
    "chair": "chair.obj", "plant": "pottedPlant.obj", "lamp": "lampRoundFloor.obj",
    "box": "cardboardBoxClosed.obj", "bin": "trashcan.obj", "monitor": "computerScreen.obj",
    "barrel": "trashcan.obj", "crate": "cardboardBoxClosed.obj", "cart": "bench.obj",
    "table": "tableCoffee.obj",
}

def _make_box(render_root, pos, scale, color_rgb, shader):
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
    faces = [
        ((1, 0, 0),  [(hw, -hd, -hh), (hw, hd, -hh), (hw, hd, hh), (hw, -hd, hh)]),
        ((-1, 0, 0), [(-hw, hd, -hh), (-hw, -hd, -hh), (-hw, -hd, hh), (-hw, hd, hh)]),
        ((0, 1, 0),  [(hw, hd, -hh), (-hw, hd, -hh), (-hw, hd, hh), (hw, hd, hh)]),
        ((0, -1, 0), [(-hw, -hd, -hh), (hw, -hd, -hh), (hw, -hd, hh), (-hw, -hd, hh)]),
        ((0, 0, 1),  [(-hw, -hd, hh), (hw, -hd, hh), (hw, hd, hh), (-hw, hd, hh)]),
        ((0, 0, -1), [(hw, -hd, -hh), (-hw, -hd, -hh), (-hw, hd, -hh), (hw, hd, -hh)]),
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


def _make_prop(parent, model_name, pos, target_scale):
    try:
        import os
        from panda3d.core import Filename
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        assets_dir = os.path.join(workspace_dir, "assets", "models", "furniture", "Models")
        model_path = Filename.fromOsSpecific(os.path.join(assets_dir, model_name)).getFullpath()
        model = base.loader.loadModel(model_path)
    except:
        return None
    model.reparentTo(parent)
    model.setPos(pos)
    
    # Calculate scale factor to match target_scale (w, h, d in game coords)
    min_pt, max_pt = model.getTightBounds()
    dims = max_pt - min_pt
    if dims.x > 0 and dims.y > 0 and dims.z > 0:
        model.setScale(target_scale[0] / dims.x, target_scale[2] / dims.y, target_scale[1] / dims.z)
    
    # Kenney models often need a bit of adjustment, center them if necessary
    model.setPos(pos[0], pos[1] + target_scale[1]*0.5, pos[2] - target_scale[2]*0.5)
    return model

def _build_character(parent, is_hunter=False):
    try:
        import os
        from panda3d.core import Filename
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        char_dir = os.path.join(workspace_dir, "assets", "models", "characters")
        
        # Paths for Actor must be Panda3D-friendly strings if they are absolute.
        # But wait, Filename.fromOsSpecific(path).getFullpath() gives a Panda3D absolute path
        model_path = Filename.fromOsSpecific(os.path.join(char_dir, "Model", "characterMedium.fbx")).getFullpath()
        idle_path = Filename.fromOsSpecific(os.path.join(char_dir, "Animations", "idle.fbx")).getFullpath()
        run_path = Filename.fromOsSpecific(os.path.join(char_dir, "Animations", "run.fbx")).getFullpath()
        jump_path = Filename.fromOsSpecific(os.path.join(char_dir, "Animations", "jump.fbx")).getFullpath()

        actor = Actor(model_path, {
            "idle": idle_path,
            "run": run_path,
            "jump": jump_path
        })
        actor.reparentTo(parent)
        actor.setScale(1.2) # Default character scale
        actor.setPos(0, 0, -0.9) # Align feet with capsule bottom
        # Adjust rotation because Kenney models might face Z or Y
        actor.setH(180) 
        
        if is_hunter:
            hand = actor.exposeJoint(None, "modelRoot", "RightHand")
            if hand:
                weapon = _make_box(hand, pos=(0.0, 0.2, 0.0), scale=(0.08, 0.4, 0.15), color_rgb=(40, 40, 40))
                # Adjust orientation to point forward
                weapon.setHpr(0, 90, 0)

        actor.loop("idle")
        return actor
    except Exception as e:
        print("Failed to load character:", e)
        return None




STATE_MENU    = "menu"
STATE_CONNECT = "connect"
STATE_LOBBY   = "lobby"
STATE_INGAME  = "ingame"

WALL_MASK = BitMask32.bit(1)
FLOOR_MASK = BitMask32.bit(2)
PLAYER_FROM_MASK = BitMask32.bit(3)


class ClientApp(ShowBase):

    def __init__(self):
        super().__init__()

        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Morph Hunt")
        props.setUndecorated(False)
        if hasattr(self.win, "requestProperties"):
            self.win.requestProperties(props)
        self.win.setClearColor(_c4(18, 20, 28))

        self.camLens.setNearFar(0.2, 500.0)

        self._shader = _make_shader()

        self._cam_yaw   = 0.0
        self._cam_pitch = 0.0
        self._mouse_locked = False
        self._third_person = False
        self._rotation_locked = False
        self._locked_player_yaw = 0.0
        self._vel_z = 0.0
        self._is_grounded = True
        self._ground_z = 1.0

        self._laser_np = None
        self._laser_timer = 0.0
        self._flashlight_on = True
        self._flashlight = None

        self.cTrav = CollisionTraverser()
        self.cTrav.setRespectPrevTransform(True)
        self._pusher = CollisionHandlerFluidPusher()
        self._pusher.setHorizontal(True)

        self.cam_trav = CollisionTraverser("cam_trav")
        self._cam_handler = CollisionHandlerQueue()
        self._cam_seg = CollisionSegment(0,0,0, 0,1,0)
        cam_node = CollisionNode("cam_ray")
        cam_node.addSolid(self._cam_seg)
        cam_node.setFromCollideMask(WALL_MASK | FLOOR_MASK)
        cam_node.setIntoCollideMask(BitMask32.allOff())
        self._cam_ray_np = self.render.attachNewNode(cam_node)
        self.cam_trav.addCollider(self._cam_ray_np, self._cam_handler)

        self.shoot_trav = CollisionTraverser("shoot_trav")
        self._shoot_handler = CollisionHandlerQueue()
        self._shoot_ray = CollisionRay(0,0,0, 0,1,0)
        shoot_node = CollisionNode("shoot_ray")
        shoot_node.addSolid(self._shoot_ray)
        shoot_node.setFromCollideMask(PLAYER_FROM_MASK | WALL_MASK | FLOOR_MASK)
        shoot_node.setIntoCollideMask(BitMask32.allOff())
        self._shoot_ray_np = self.camera.attachNewNode(shoot_node)
        self.shoot_trav.addCollider(self._shoot_ray_np, self._shoot_handler)

        self._floor_handler = CollisionHandlerQueue()
        self._floor_ray_np = None

        self.net = NetworkClient()
        self.server_thread = None
        self.local_server  = None

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

        self.level_nodes:  list[NodePath] = []
        self.remote_nodes: dict[str, NodePath] = {}
        self.objective_nodes: list[NodePath] = []
        self._player_np:   NodePath | None = None
        self._player_visual: NodePath | None = None
        self._player_col:  NodePath | None = None

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

        self._keys: dict[str, bool] = {}
        for k in ("w", "a", "s", "d", "space", "shift", "escape",
                  "1","2","3","4","5","6","7","8","9",
                  "e", "q", "f", "c", "t", "l", "mouse1", "mouse3"):
            self.accept(k,        self._key_down, [k])
            self.accept(k + "-up",self._key_up,   [k])

        self.taskMgr.add(self._main_loop, "main_loop")

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

        if self.my_role == ROLE_HIDER:
            if key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(self._object_hotbar):
                    obj_key = self._object_hotbar[idx]
                    self.my_transformed = obj_key
                    SoundManager.morph()
                    self._update_local_player_model()
                    self.net.send({"type": MSG_TRANSFORM, "object_type": obj_key})

            elif key in ("f", "mouse3"):
                self._rotation_locked = not self._rotation_locked
                if self._rotation_locked:
                    self._locked_player_yaw = self._cam_yaw
                    self.hud.push_clue("[Locked Rotation] Camera moves freely!")
                else:
                    self.hud.push_clue("[Unlocked Rotation]")

            elif key == "c":
                self._third_person = not self._third_person

            elif key == "t":
                now = time.time()
                if (now - self.last_taunt_press) >= settings.TAUNT_COOLDOWN:
                    self.last_taunt_press = now
                    SoundManager.taunt()
                    self.net.send({"type": MSG_TAUNT})
                    self.hud.push_clue("You taunted the Hunter! (+20 XP)")

            elif key == "e":
                self.net.send({"type": MSG_INTERACT})

        elif self.my_role == ROLE_HUNTER:
            if key == "mouse1":
                self._fire_blaster()

            elif key == "q":
                self.last_scanner_press = time.time()
                SoundManager.scanner()
                self.net.send({"type": MSG_SCANNER})

            elif key == "l":
                self._toggle_flashlight()

    def _fire_blaster(self):
        SoundManager.laser()
        
        target_id = None
        hit_pos = None
        
        self.shoot_trav.traverse(self.render)
        if self._shoot_handler.getNumEntries() > 0:
            self._shoot_handler.sortEntries()
            for i in range(self._shoot_handler.getNumEntries()):
                entry = self._shoot_handler.getEntry(i)
                hit_np = entry.getIntoNodePath()
                
                # Check if we hit ourselves (just in case)
                if hit_np.hasPythonTag("player_id") and hit_np.getPythonTag("player_id") == self.net.player_id:
                    continue
                    
                dist = (entry.getSurfacePoint(self.render) - self.camera.getPos(self.render)).length()
                if dist <= settings.ATTACK_RANGE:
                    hit_pos = entry.getSurfacePoint(self.render)
                    if hit_np.hasPythonTag("player_id"):
                        target_id = hit_np.getPythonTag("player_id")
                break
                
        self._spawn_laser_tracer(hit_pos)
        self.net.send({"type": MSG_ATTACK, "target_id": target_id})

    def _spawn_laser_tracer(self, hit_pos=None):
        if self._laser_np:
            self._laser_np.removeNode()

        segs = LineSegs("laser")
        segs.setColor(0.3, 0.9, 1.0, 1.0)
        segs.setThickness(4.0)

        p = self.camera.getPos(self.render)
        fwd = self.camera.getQuat(self.render).getForward()
        
        end_p = hit_pos if hit_pos else (p + fwd * settings.ATTACK_RANGE)

        segs.moveTo(p + fwd * 0.4 + Vec3(0.15, -0.1, -0.1))
        segs.drawTo(end_p)

        self._laser_np = self.render.attachNewNode(segs.create())
        self._laser_timer = 0.08

    def _toggle_flashlight(self):
        self._flashlight_on = not self._flashlight_on
        if self._flashlight:
            self._flashlight.node().setActive(self._flashlight_on)

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

    def _clear_level(self):
        self.cTrav.clearColliders()

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
        self._player_col = None
        self._floor_ray_np = None

        self.win.setClearColor(_c4(10, 12, 20))

    def _build_level(self, level_key):
        self._clear_level()
        self.current_map = level_key
        level_def = load_level(level_key)

        level_root = self.render.attachNewNode("level_root")
        self.level_nodes.append(level_root)

        for g in level_def.get("geometry", []):
            p = g["position"]
            s = g["scale"]
            rot = g.get("rotation", (0, 0, 0))
            is_visible = g.get("visible", True)
            
            is_floor = g.get("type") == "floor"
            is_prop = g.get("type") == "prop"
            is_solid = g.get("solid", True)
            
            np = None
            if is_prop and g.get("kind") in PROP_MODEL_MAP:
                # Try loading the real 3D model
                np = _make_prop(level_root, PROP_MODEL_MAP[g["kind"]], (p[0], p[2], p[1]), s)
            
            if not np:
                # Fallback to simple colored box, or if it's a wall/floor
                np = _make_box(
                    level_root,
                    pos=(p[0], p[2], p[1]),
                    scale=(s[0], s[2], s[1]),
                    color_rgb=g["color"],
                    shader=self._shader,
                )

            np.setHpr(rot)
            if not is_visible:
                np.hide()

            if is_solid and not is_floor:
                col_node = CollisionNode("wall_col")
                half_x = max(abs(s[0]) * 0.5, 0.05)
                half_y = max(abs(s[2]) * 0.5, 0.05)
                half_z = max(abs(s[1]) * 0.5, 0.05)
                col_node.addSolid(
                    CollisionBox(LPoint3f(0, 0, 0), half_x, half_y, half_z)
                )
                col_node.setIntoCollideMask(WALL_MASK)
                col_node.setFromCollideMask(BitMask32.allOff())
                col_np = np.attachNewNode(col_node)

            if is_floor and is_solid:
                col_node = CollisionNode("floor_col")
                half_x = max(abs(s[0]) * 0.5, 0.05)
                half_y = max(abs(s[2]) * 0.5, 0.05)
                half_z = max(abs(s[1]) * 0.5, 0.05)
                col_node.addSolid(
                    CollisionBox(LPoint3f(0, 0, 0), half_x, half_y, half_z)
                )
                col_node.setIntoCollideMask(FLOOR_MASK)
                col_node.setFromCollideMask(BitMask32.allOff())
                col_np = np.attachNewNode(col_node)

        wf = _make_box(
            level_root,
            pos=(0, 0, -0.65),
            scale=(200, 200, 1),
            color_rgb=(35, 38, 45),
            shader=self._shader,
        )
        ground_col = CollisionNode("ground_floor_col")
        ground_col.addSolid(CollisionBox(LPoint3f(0, 0, 0), 100, 100, 0.5))
        ground_col.setIntoCollideMask(FLOOR_MASK)
        ground_col.setFromCollideMask(BitMask32.allOff())
        wf.attachNewNode(ground_col)
        self.level_nodes.append(wf)

        for spot in level_def.get("hider_spawn_objects", []):
            obj = REGISTRY.get(spot["key"])
            if not obj:
                continue
            p = spot["position"]
            s = obj.scale
            np = _make_box(
                level_root,
                pos=(p[0], p[2], p[1]),
                scale=(s[0], s[2], s[1]),
                color_rgb=obj.color,
                shader=self._shader,
            )
            self.level_nodes.append(np)

        for obj in level_def.get("objectives", []):
            p = obj["position"]
            np = _make_box(
                level_root,
                pos=(p[0], p[2], p[1]),
                scale=(0.8, 0.8, 1.2),
                color_rgb=(255, 180, 40),
                shader=self._shader,
            )
            self.objective_nodes.append(np)
            self.level_nodes.append(np)

        self.win.setClearColor(_c4(18, 22, 30))

        self._setup_lighting()

        spawn = level_def.get("hunter_spawns", [[0, 1.0, 0]])[0]
        self._player_np = self.render.attachNewNode("player_root")
        self._player_np.setPos(spawn[0], spawn[2], 1.0)
        self._vel_z = 0.0
        self._is_grounded = True
        self._ground_z = 1.0

        self._player_visual = self._player_np.attachNewNode("player_visual")
        self._update_local_player_model()

        self.camera.reparentTo(self._player_np)
        self.camera.setPos(0, 0, 0.6)
        self.camera.setHpr(0, 0, 0)
        self._cam_yaw   = 0.0
        self._cam_pitch = 0.0

        c_node = CollisionNode("player_col")
        capsule = CollisionSphere(0, 0, 0, 0.35)
        c_node.addSolid(capsule)
        c_node.setFromCollideMask(WALL_MASK)
        c_node.setIntoCollideMask(BitMask32.allOff())

        self._player_col = self._player_np.attachNewNode(c_node)

        self._pusher.addCollider(self._player_col, self._player_np)
        self.cTrav.addCollider(self._player_col, self._pusher)

        ray_node = CollisionNode("player_floor_ray")
        ray = CollisionRay(0, 0, 0.5, 0, 0, -1)
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(FLOOR_MASK)
        ray_node.setIntoCollideMask(BitMask32.allOff())
        self._floor_ray_np = self._player_np.attachNewNode(ray_node)
        self.cTrav.addCollider(self._floor_ray_np, self._floor_handler)

    def _setup_lighting(self):
        alight = AmbientLight("ambient")
        alight.setColor(LVecBase4f(0.35, 0.35, 0.40, 1.0))
        alight_np = self.render.attachNewNode(alight)
        self.render.setLight(alight_np)
        self.level_nodes.append(alight_np)

        dlight = DirectionalLight("sun")
        dlight.setColor(LVecBase4f(0.6, 0.55, 0.5, 1.0))
        dlight_np = self.render.attachNewNode(dlight)
        dlight_np.setHpr(45, -60, 0)
        self.render.setLight(dlight_np)
        self.level_nodes.append(dlight_np)

        dlight2 = DirectionalLight("fill")
        dlight2.setColor(LVecBase4f(0.2, 0.22, 0.3, 1.0))
        dlight2_np = self.render.attachNewNode(dlight2)
        dlight2_np.setHpr(-135, -30, 0)
        self.render.setLight(dlight2_np)
        self.level_nodes.append(dlight2_np)

    def _update_local_player_model(self):
        if not self._player_visual:
            return
            
        current_state = (self.my_role, self.my_transformed if self.my_role == ROLE_HIDER else None)
        if not hasattr(self, "_last_visual_state") or self._last_visual_state != current_state:
            self._last_visual_state = current_state
            for child in self._player_visual.getChildren():
                child.removeNode()
                
            self.local_actor = None

            if self.my_role == ROLE_HIDER and self.my_transformed:
                obj = REGISTRY.get(self.my_transformed)
                if obj:
                    np = None
                    if self.my_transformed in PROP_MODEL_MAP:
                        np = _make_prop(self._player_visual, PROP_MODEL_MAP[self.my_transformed], (0,0,0), obj.scale)
                    if not np:
                        _make_box(
                            self._player_visual,
                            pos=(0, 0, 0),
                            scale=obj.scale,
                            color_rgb=obj.color,
                            shader=self._shader,
                        )
            elif self.my_role == ROLE_HUNTER or self.my_role == ROLE_HIDER:
                self.local_actor = _build_character(self._player_visual, self.my_role == ROLE_HUNTER)
                if not self.local_actor:
                    _make_box(
                        self._player_visual,
                        pos=(0, 0, 0),
                        scale=(0.6, 0.6, 1.8),
                        color_rgb=(210, 70, 70) if self.my_role == ROLE_HUNTER else (70, 200, 90),
                        shader=self._shader,
                    )
        
        # Animate local actor if present
        if hasattr(self, "local_actor") and self.local_actor:
            current_anim = self.local_actor.getCurrentAnim()
            if current_anim != "idle":
                self.local_actor.loop("idle")


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
                self.hud.push_clue("Hiding phase \u2014 Hunters preparing...")
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
        vel   = p.get("velocity", [0, 0, 0])

        if not alive or p.get("eliminated"):
            if pid in self.remote_nodes:
                self.remote_nodes[pid].hide()
            return

        if not hasattr(self, "remote_state_tracking"):
            self.remote_state_tracking = {}
            self.remote_actors = {}

        current_state = (role, p.get("transformed_into") if role == ROLE_HIDER else None)
        last_state = self.remote_state_tracking.get(pid)
        
        if pid not in self.remote_nodes or last_state != current_state:
            self.remote_state_tracking[pid] = current_state
            
            if pid in self.remote_nodes:
                self.remote_nodes[pid].removeNode()
                
            self.remote_actors[pid] = None
            np = self.render.attachNewNode(f"remote_player_{pid}")
            
            if role == ROLE_HIDER and current_state[1]:
                obj = REGISTRY.get(current_state[1])
                if obj:
                    prop_np = None
                    if current_state[1] in PROP_MODEL_MAP:
                        prop_np = _make_prop(np, PROP_MODEL_MAP[current_state[1]], (0,0,0), obj.scale)
                    if not prop_np:
                        _make_box(np, pos=(0, 0, 0), scale=obj.scale, color_rgb=obj.color, shader=self._shader)
                    
                    # Add hitbox for prop
                    col = CollisionNode(f"hitbox_{pid}")
                    hx, hy, hz = max(0.1, obj.scale[0]*0.5), max(0.1, obj.scale[1]*0.5), max(0.1, obj.scale[2]*0.5)
                    col.addSolid(CollisionBox(LPoint3f(0, 0, hz), hx, hy, hz))
                    col.setIntoCollideMask(PLAYER_FROM_MASK)
                    col.setFromCollideMask(BitMask32.allOff())
                    np.attachNewNode(col)
                    np.setPythonTag("player_id", pid)
            else:
                actor = _build_character(np, role == ROLE_HUNTER)
                if actor:
                    self.remote_actors[pid] = actor
                else:
                    _make_box(np, pos=(0, 0, 0), scale=(0.6, 0.6, 1.8), color_rgb=(210, 70, 70) if role == ROLE_HUNTER else (70, 200, 90), shader=self._shader)
                
                # Add hitbox for human
                if role == ROLE_HIDER:
                    col = CollisionNode(f"hitbox_{pid}")
                    col.addSolid(CollisionCapsule(0, 0, 0.5, 0, 0, 1.8, 0.4))
                    col.setIntoCollideMask(PLAYER_FROM_MASK)
                    col.setFromCollideMask(BitMask32.allOff())
                    np.attachNewNode(col)
                    np.setPythonTag("player_id", pid)
            
            self.remote_nodes[pid] = np

        np = self.remote_nodes[pid]
        np.show()
        
        # Animate remote actor if present
        actor = self.remote_actors.get(pid)
        if actor:
            speed = LVector3f(vel[0], vel[1], 0).length()
            current_anim = actor.getCurrentAnim()
            target_anim = "run" if speed > 0.5 else "idle"
            if current_anim != target_anim:
                actor.loop(target_anim)

        np.setPos(pos[0], pos[2], pos[1])
        np.setH(p.get("rotation_y", 0))

    def _main_loop(self, task):
        dt = globalClock.getDt()

        self._process_network()

        if self._laser_np:
            self._laser_timer -= dt
            if self._laser_timer <= 0:
                self._laser_np.removeNode()
                self._laser_np = None

        if self.state == STATE_INGAME and not self.paused and self._player_np:
            self._update_player(dt)

        return Task.cont

    def _update_player(self, dt: float):
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

            if self._third_person:
                if self._player_visual:
                    self._player_visual.show()
                rad_yaw = math.radians(self._cam_yaw)
                max_cam_dist = 4.0
                cam_z_offset = 1.2

                if self.my_transformed:
                    obj = REGISTRY.get(self.my_transformed)
                    if obj:
                        cam_z_offset = max(0.5, obj.scale[1] * 1.5)
                        max_cam_dist = max(3.0, obj.scale[1] * 3.0)

                head_pos = self._player_np.getPos(self.render) + LVector3f(0, 0, cam_z_offset)
                target_x = math.sin(rad_yaw) * max_cam_dist
                target_y = -math.cos(rad_yaw) * max_cam_dist
                target_pos = head_pos + LVector3f(target_x, target_y, 0)
                
                self._cam_seg.setPointA(head_pos)
                self._cam_seg.setPointB(target_pos)
                self.cam_trav.traverse(self.render)
                
                cam_dist = max_cam_dist
                if self._cam_handler.getNumEntries() > 0:
                    self._cam_handler.sortEntries()
                    entry = self._cam_handler.getEntry(0)
                    hit_pos = entry.getSurfacePoint(self.render)
                    cam_dist = (hit_pos - head_pos).length() - 0.2
                    if cam_dist < 0.2:
                        cam_dist = 0.2
                        
                cam_x = math.sin(rad_yaw) * cam_dist
                cam_y = -math.cos(rad_yaw) * cam_dist
                
                self.camera.reparentTo(self.render)
                self.camera.setPos(head_pos.x + cam_x, head_pos.y + cam_y, head_pos.z)
                self.camera.setHpr(self._cam_yaw, self._cam_pitch, 0)
            else:
                if self._player_visual:
                    self._player_visual.hide()
                self.camera.reparentTo(self._player_np)
                self.camera.setPos(0, 0, 0.6)
                self.camera.setHpr(0 if not self._rotation_locked else self._cam_yaw - self._locked_player_yaw, self._cam_pitch, 0)

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

        vx = 0.0
        vy = 0.0
        if forward or right:
            if self._rotation_locked:
                self._rotation_locked = False

            yaw_rad = math.radians(self._cam_yaw)
            fx = -math.sin(yaw_rad)
            fy =  math.cos(yaw_rad)
            rx =  math.cos(yaw_rad)
            ry =  math.sin(yaw_rad)

            vx = (fx * forward + rx * right) * speed
            vy = (fy * forward + ry * right) * speed

            pos = self._player_np.getPos()
            self._player_np.setPos(pos.x + vx * dt, pos.y + vy * dt, pos.z)

        # Update local animation
        if hasattr(self, "local_actor") and self.local_actor:
            vel_mag = math.sqrt(vx*vx + vy*vy)
            target_anim = "run" if vel_mag > 0.5 else "idle"
            if self.local_actor.getCurrentAnim() != target_anim:
                self.local_actor.loop(target_anim)

        if self._k("space") and self._is_grounded:
            self._vel_z = 6.5
            self._is_grounded = False

        if not self._is_grounded:
            self._vel_z -= 22.0 * dt
            pos = self._player_np.getPos()
            new_z = pos.z + self._vel_z * dt
            if new_z <= self._ground_z:
                new_z = self._ground_z
                self._vel_z = 0.0
                self._is_grounded = True
            self._player_np.setZ(new_z)
        else:
            self._player_np.setZ(self._ground_z)

        self.cTrav.traverse(self.render)

        if self._is_grounded:
            self._player_np.setZ(self._ground_z)

        self._update_ground_z()

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

    def _update_ground_z(self):
        if not self._floor_ray_np:
            return

        best_z = -0.15
        num = self._floor_handler.getNumEntries()
        if num > 0:
            self._floor_handler.sortEntries()
            for i in range(num):
                entry = self._floor_handler.getEntry(i)
                pt = entry.getSurfacePoint(self.render)
                if pt.z > best_z:
                    best_z = pt.z

        target_ground = best_z + 1.0
        self._ground_z = target_ground
