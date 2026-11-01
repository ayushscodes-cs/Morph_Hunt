from __future__ import annotations

import builtins
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

_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_furniture_dir = os.path.join(_base_dir, "assets", "models", "furniture", "Models")
_char_dir = os.path.join(_base_dir, "assets", "models", "characters")
get_model_path().appendDirectory(Filename.fromOsSpecific(_furniture_dir).getFullpath())
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "characters", "char9", "textures")).getFullpath())
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "characters", "char9", "source")).getFullpath())
get_model_path().appendDirectory(Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "animations")).getFullpath())

_model_cache = {}

def _cached_load(model_path_str):
    if model_path_str in _model_cache:
        return _model_cache[model_path_str]
    try:
        m = base.loader.loadModel(model_path_str)
        _model_cache[model_path_str] = m
        return m
    except Exception:
        _model_cache[model_path_str] = None
        return None

PROP_MODEL_MAP = {
    "TrashCommercial": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "TrashCommercial", "is_fbx": True},
    "Bench": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "Bench", "is_fbx": True},
    "FireHydrant": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "FireHydrant", "is_fbx": True},
    "ParkingMeter": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "ParkingMeter", "is_fbx": True},
    "PostBox": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "PostBox", "is_fbx": True},
    "pallet1": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "pallet1", "is_fbx": True},
    # Utility: front panel faces +Y in raw FBX. After Pitch=90, the panel faces upward (+Z).
    # An extra Roll=90 tilts it back so the panel faces the viewer (+Y world direction).
    "Utility": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "Utility", "is_fbx": True, "hpr": (0, 90, 90)},
    "ConcreteBench": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "ConcreteBench", "is_fbx": True},
    "TrashCanSmall": {"file": "city_props/source/unzipped/CityPropsCollection.fbx", "node": "TrashCanSmall", "is_fbx": True},
    "Couch": {"file": "trailer_park_props.glb", "node": "Couch_Couch_0", "is_fbx": False},
    "TV": {"file": "trailer_park_props.glb", "node": "TV_TV_0", "is_fbx": False},
    "Bed": {"file": "trailer_park_props.glb", "node": "Bed_Bed_0", "is_fbx": False},
    "Refrigerator": {"file": "trailer_park_props.glb", "node": "Refrigerator_Refrigerator_0", "is_fbx": False},
    "Tree": {"file": "trailer_park_props.glb", "node": "Trees_Trees_0", "is_fbx": False},
    "Toilet": {"file": "trailer_park_props.glb", "node": "Toilet_Toilet_0", "is_fbx": False},
    "Fence": {"file": "trailer_park_props.glb", "node": "Fence_Metal_Fence_0", "is_fbx": False},
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


def _make_prop(parent, prop_def, pos, target_scale, instance_hpr=None):
    import os
    import glob
    
    if not isinstance(prop_def, dict):
        return None
        
    file_rel = prop_def.get("file", "")
    node_name = prop_def.get("node", "")
    is_fbx = prop_def.get("is_fbx", False)
    
    # Clean the path depending on OS
    file_path_os = os.path.normpath(file_rel)
    prop_col_path = Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "props", file_path_os)).getFullpath()
    
    if is_fbx:
        props_tex_dir_os = os.path.dirname(os.path.join(_base_dir, "new_assets", "props", file_path_os))
        props_tex_dir = Filename.fromOsSpecific(props_tex_dir_os).getFullpath()
        if props_tex_dir not in get_model_path().getDirectories():
            get_model_path().appendDirectory(props_tex_dir)
            
    cached = _cached_load(prop_col_path)
    if cached is None:
        return None
        
    node = cached.find(f"**/{node_name}")
    if node.isEmpty():
        return None
        
    prop_root = render.attachNewNode(f"prop_{node_name}_root")

    # Apply instance-specific rotation to the root node if provided
    if instance_hpr:
        prop_root.setHpr(*instance_hpr)
        
    model = prop_root.attachNewNode("mesh")
    node.copyTo(model)
    
    # Apply orientation. Use per-model 'hpr' override if specified, otherwise auto-detect axis convention.
    hpr_override = prop_def.get("hpr", None)
    if hpr_override:
        model.setHpr(*hpr_override)
    elif is_fbx:
        # All FBX models in CityPropsCollection are Y-up, need 90-degree pitch to stand upright
        model.setHpr(0, 90, 0)
    else:
        # GLB models in trailer_park_props are also Y-up
        model.setHpr(0, -90, 0)
    
    if is_fbx:
        search = os.path.join(props_tex_dir_os, f"*{node_name}*Diffuse.png")
        tex_matches = glob.glob(search)
        if not tex_matches:
            for f in os.listdir(props_tex_dir_os):
                if node_name.lower() in f.lower() and "diffuse" in f.lower():
                    tex_matches = [os.path.join(props_tex_dir_os, f)]
                    break
        if tex_matches:
            tex = base.loader.loadTexture(Filename.fromOsSpecific(tex_matches[0]).getFullpath())
            if tex:
                model.setTexture(tex, 1)
    
    # Compute bounds while prop_root is at render origin (world 0,0,0) with scale=1
    # so min_pt/max_pt are clean local-space values not contaminated by parent transforms
    try:
        min_pt, max_pt = prop_root.getTightBounds()
    except Exception:
        prop_root.removeNode()
        return None
    dims = max_pt - min_pt
    if dims.x < 0.001 or dims.y < 0.001 or dims.z < 0.001:
        prop_root.removeNode()
        return None
        
    sx = target_scale[0] / dims.x
    sy = target_scale[1] / dims.y
    sz = target_scale[2] / dims.z
    prop_root.setScale(sx, sy, sz)
    cx = (min_pt.x + max_pt.x) * 0.5
    cy = (min_pt.y + max_pt.y) * 0.5
    # Place so XY center is at pos[0,1] and bottom (min_pt.z) lands exactly at pos[2]
    prop_root.setPos(pos[0] - cx * sx, pos[1] - cy * sy, pos[2] - min_pt.z * sz)
    # Now reparent into the actual scene parent
    prop_root.reparentTo(parent)
    return prop_root

def _build_character(parent, loader, is_hunter=False, char_idx=1):
    try:
        model_path = Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "rigged_characters", f"char{char_idx}_Animated.glb")).getFullpath()
        if not os.path.exists(Filename(model_path).toOsSpecific()):
            model_path = Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "rigged_characters", "Booyah_Girl_Animated.glb")).getFullpath()

        anim_dir = os.path.join(_base_dir, "new_assets", "animations")
        
        # All characters now have their animations baked directly into their .glb files
        actor = Actor(model_path)
        
        actor.reparentTo(parent)
        # Pre-calculated scales based on original model heights to normalize to ~1.2 units
        char_scales = {
            1: 0.077,
            2: 24.276,
            3: 25.784,
            4: 49.131,
            5: 13.702,
            6: 952.863,
            7: 115.395,
            8: 30.964,
            9: 1.356,
            10: 23.450
        }
        
        target_scale = char_scales.get(int(char_idx), 0.077)
        actor.setScale(target_scale)
        
        # Prevent Panda3D frustum culling bugs on heavily scaled rigged meshes
        from panda3d.core import OmniBoundingVolume
        actor.node().setBounds(OmniBoundingVolume())
        actor.node().setFinal(True)

        actor.setH(180)
        actor.setPythonTag("available_anims", set(actor.getAnimNames()))
        
        # Pre-calculate the natural resting hip Z position from the idle animation to prevent floating during root motion
        actor.pose("idle", 0)
        min_pt, max_pt = actor.getTightBounds()
        
        # Calculate exactly how far the lowest vertex is from the actor's origin
        # Then inverse it to push the actor up/down so its feet perfectly touch the floor (Z=0 in its parent's space)
        base_z = -min_pt.z
        actor.setPythonTag("base_z", base_z)
        actor.setPos(0, 0, base_z)
        
        actor.setPythonTag("idle_hip_pos", None)
        try:
            if "idle" in actor.getAnimNames():
                hips = actor.exposeJoint(None, 'modelRoot', 'mixamorig:Hips')
                actor.pose("idle", 0)
                actor.setPythonTag("idle_hip_pos", hips.getPos(actor))
        except:
            pass

        # Apply basic materials properties if needed, but rely on GLB embedded materials
        for geom_node in actor.findAllMatches('**/+GeomNode'):
            for i in range(geom_node.node().getNumGeoms()):
                rs = geom_node.node().getGeomState(i)
                from panda3d.core import MaterialAttrib
                if rs.hasAttrib(MaterialAttrib):
                    mat_attrib = rs.getAttrib(MaterialAttrib)
                    mat = mat_attrib.getMaterial()
                    if mat:
                        mat.setRoughness(1.0)
                        geom_node.node().setGeomState(i, rs.setAttrib(MaterialAttrib.make(mat)))

        return actor
    except Exception as e:
        print(f"[client] Failed to load character model: {e}")
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

        # We will initialize simplepbr after lighting setup

        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Morph Hunt")
        props.setUndecorated(False)
        if hasattr(self.win, "requestProperties"):
            self.win.requestProperties(props)
        self.win.setClearColor(_c4(135, 206, 235))

        self.camLens.setNearFar(0.2, 5000.0)

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
        self._pusher = CollisionHandlerPusher()
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
        builtins.base.net = self.net
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
        self._pending_jump   = False
        self.last_input_sent = 0.0
        self.paused          = False

        self._object_hotbar = list(REGISTRY.keys())[:9]

        self.level_nodes:  list[NodePath] = []
        self.remote_nodes: dict[str, NodePath] = {}
        self.objective_nodes: list[NodePath] = []
        self._player_np:   NodePath | None = None
        self._player_visual: NodePath | None = None
        self._player_col:  NodePath | None = None
        self.selected_char_idx = 1

        self._showcase_actor = None
        self.menu   = MainMenu(self._on_host_clicked, self._on_join_clicked, self.userExit, self._on_char_change)
        self.connect_dialog: ConnectDialog | None = None
        self.lobby  = LobbyScreen(
            self._on_ready_toggle,
            self._on_set_map,
            self._on_set_mode,
            self._on_start_game,
            self._on_leave_lobby,
            self._on_add_bot,
            self._on_chat_send,
        )
        self.hud     = HUD(self.aspect2d)
        self.results = ResultsScreen(self._on_results_continue)

        self._show_only(STATE_MENU)

        self._keys: dict[str, bool] = {}
        for k in ("w", "a", "s", "d", "space", "lshift", "escape",
                  "0","1","2","3","4","5","6","7","8","9",
                  "e", "q", "f", "v", "c", "t", "l", "p", "m",
                  "arrow_left", "arrow_right",
                  "mouse1", "mouse3"):
            self.accept(k,        self._key_down, [k])
            self.accept(k + "-up",self._key_up,   [k])

        self.taskMgr.add(self._main_loop, "main_loop")
        
        self._setup_lighting()
        
        import simplepbr
        simplepbr.init(
            enable_shadows=True,
            use_normal_maps=True,
        )
        
        # simplepbr overrides clear color, set it again here
        self.win.setClearColor(_c4(135, 206, 235))
        
        self._bullets = []

    def _key_down(self, key):
        self._keys[key] = True
        if key == "p" and getattr(self, "state", None) == STATE_INGAME and getattr(self, "_player_np", None):
            pos = self._player_np.getPos()
            self.hud.push_clue(f"Location: [{pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}]")
            print(f"Player Coordinates: [{pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}]")
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

        if key == "l":
            self._show_leave_dialog()
            return

        if self.my_health <= 0:
            if key in ("a", "d", "arrow_left", "arrow_right"):
                alive = [p for p in getattr(self, "_players_cache", []) if p.get("alive") and not p.get("eliminated")]
                if alive:
                    if not hasattr(self, "_spectate_idx"):
                        self._spectate_idx = 0
                    if key in ("a", "arrow_left"):
                        self._spectate_idx = (self._spectate_idx - 1) % len(alive)
                    else:
                        self._spectate_idx = (self._spectate_idx + 1) % len(alive)
                    self.hud.push_clue(f"Spectating: {alive[self._spectate_idx].get('name')}")
            return

        if key in ("f", "mouse3"):
            if self.my_role == ROLE_HIDER:
                self._rotation_locked = not self._rotation_locked
                if self._rotation_locked:
                    self._locked_player_yaw = self._cam_yaw
                    self.hud.push_clue("[Locked] Camera moves freely!")
                else:
                    self.hud.push_clue("[Unlocked]")

        elif key == "v":
            self._third_person = not self._third_person

        if self.my_role == ROLE_HIDER:
            if key == "0":
                if self.my_transformed is not None:
                    self.my_transformed = None
                    SoundManager.morph()
                    self._update_local_player_model()
                    self.net.send({"type": MSG_UNTRANSFORM})

            elif key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(self._object_hotbar):
                    obj_key = self._object_hotbar[idx]
                    self.my_transformed = obj_key
                    SoundManager.morph()
                    self._update_local_player_model()
                    self.net.send({"type": MSG_TRANSFORM, "object_type": obj_key})

            elif key == "t":
                now = time.time()
                if (now - self.last_taunt_press) >= settings.TAUNT_COOLDOWN:
                    self.last_taunt_press = now
                    SoundManager.taunt()
                    self.net.send({"type": MSG_TAUNT})
                    self.hud.push_clue("You taunted the Hunter! (+20 XP)")

            elif key == "e":
                self.net.send({"type": MSG_INTERACT})

            elif key == "m":
                self.hud.toggle_prop_menu()

        elif self.my_role == ROLE_HUNTER:
            if key == "mouse1":
                self._fire_blaster()
                
            elif key in ("0", "1", "2", "3", "4"):
                self.equip_weapon(int(key))

            elif key == "q":
                self.last_scanner_press = time.time()
                SoundManager.scanner()
                self.net.send({"type": MSG_SCANNER})

            elif key == "k":
                self._toggle_flashlight()

    def _show_leave_dialog(self):
        from direct.gui.DirectGui import DirectDialog
        if hasattr(self, "_leave_dialog") and self._leave_dialog:
            return
            
        def on_yes():
            self._leave_dialog.cleanup()
            self._leave_dialog = None
            
            from direct.gui.DirectGui import DirectFrame, DirectLabel
            self._leave_msg_frame = DirectFrame(frameColor=(0,0,0,1), frameSize=(-2,2,-2,2), sortOrder=100)
            DirectLabel(parent=self._leave_msg_frame, text="Leaving the game...", scale=0.1, text_fg=(1,1,1,1), frameColor=(0,0,0,0))
            self.hud.hide()
            
            def finish_leave(task):
                if hasattr(self, "_leave_msg_frame") and self._leave_msg_frame:
                    self._leave_msg_frame.destroy()
                    self._leave_msg_frame = None
                    
                if getattr(self, "net", None):
                    if hasattr(self.net, "client"):
                        self.net.client.disconnect()
                    self.net.disconnect()
                    import queue
                    self.net.incoming = queue.Queue()
                
                if self.local_server:
                    self.local_server.stop()
                    if hasattr(self, "server_thread") and self.server_thread:
                        self.server_thread.join(timeout=1.0)
                    self.local_server = None
                    
                self._clear_level()
                self._my_ready = False
                self._show_only(STATE_MENU)
                return task.done
                
            self.taskMgr.doMethodLater(1.5, finish_leave, "finish_leave_task")

        def on_no():
            self._leave_dialog.cleanup()
            self._leave_dialog = None
            self._set_mouse_locked(True)

        self._set_mouse_locked(False)
        
        self._leave_dialog = DirectDialog(
            dialogName="LeaveDialog",
            text="Are you sure you want to leave?",
            buttonTextList=["YES", "NO"],
            buttonValueList=[1, 0],
            command=lambda val: on_yes() if val == 1 else on_no(),
            scale=1.2,
            pos=(0, 0, 0),
            fadeScreen=0.5
        )

    def _fire_blaster(self):
        import time
        now = time.time()
        weapon_idx = getattr(self, "current_weapon", 1)
        if weapon_idx == 0:
            return
            
        if not hasattr(self, "_last_fire_time"):
            self._last_fire_time = 0
            
        # Hard cap firing rate to prevent macro spam
        cooldown = {1: 0.15, 2: 0.3, 3: 0.8, 4: 0.1}.get(weapon_idx, 0.2)
        if now - self._last_fire_time < cooldown:
            return
            
        self._last_fire_time = now
        SoundManager.gun_fire(weapon_idx)
        
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
                
        self._spawn_laser_tracer(hit_pos, target_id)
        self.net.send({"type": MSG_ATTACK, "target_id": target_id, "weapon": getattr(self, "current_weapon", 1)})

    def _spawn_laser_tracer(self, hit_pos=None, target_id=None):
        if self._laser_np:
            self._laser_np.removeNode()

        # Play shooting animation
        if hasattr(self, "local_actor") and self.local_actor:
            weapon_idx = getattr(self, "current_weapon", 1)
            if weapon_idx == 2:
                anim_name = "pistol_shoot"
                self._shoot_anim_timer = 0.3
            elif weapon_idx == 3:
                anim_name = "shotgun_shoot"
                self._shoot_anim_timer = 0.5
            elif weapon_idx in (1, 4):
                anim_name = "rifle_smg_shoot"
                self._shoot_anim_timer = 0.2
            else:
                anim_name = None

            if anim_name and self.local_actor.getCurrentAnim() != anim_name:
                self.local_actor.play(anim_name)

        # Hit sparks
        if hit_pos:
            spark = self.render.attachNewNode("spark")
            if target_id is not None:
                # Red blood spark
                _make_box(spark, (0, 0, 0), (0.15, 0.15, 0.15), (255, 0, 0), self._shader)
                spark.setScale(1.5)
            else:
                # Yellow environment spark
                _make_box(spark, (0, 0, 0), (0.1, 0.1, 0.1), (255, 204, 51), self._shader)
                spark.setScale(1.0)
                
            spark.setPos(hit_pos)
            if not hasattr(self, "_hit_sparks"):
                self._hit_sparks = []
            self._hit_sparks.append({"np": spark, "timer": 0.15})

        p = self.camera.getPos(self.render)
        fwd = self.camera.getQuat(self.render).getForward()
        
        end_p = hit_pos if hit_pos else (p + fwd * settings.ATTACK_RANGE)

        # Start tracer from weapon if equipped
        start_p = p + fwd * 0.4 + Vec3(0.15, -0.1, -0.1)
        if hasattr(self, "_weapon_np") and self._weapon_np:
            # Add a slight offset so it comes out of the barrel
            start_p = self._weapon_np.getPos(self.render) + fwd * 0.5
            
        dir_vec = (end_p - start_p).normalized()
        dist = (end_p - start_p).length()
        
        # Create bullet projectile
        segs = LineSegs("bullet")
        segs.setColor(1.0, 0.8, 0.2, 1.0) # Yellow/orange tracer
        segs.setThickness(3.0)
        segs.moveTo(0, 0, 0)
        segs.drawTo(0, min(2.5, dist), 0)
        
        b_np = self.render.attachNewNode(segs.create())
        b_np.setPos(start_p)
        b_np.lookAt(start_p + dir_vec)
        
        self._bullets.append({
            "np": b_np,
            "dir": dir_vec,
            "speed": 120.0,
            "distance_left": dist,
            "timer": 2.0
        })

    def _toggle_flashlight(self):
        self._flashlight_on = not self._flashlight_on

    def equip_weapon(self, weapon_idx):
        if getattr(self, "my_role", None) != ROLE_HUNTER:
            return
            
        self.current_weapon = weapon_idx
        names = {0: "[0] Unarmed", 1: "[1] Assault Rifle", 2: "[2] Pistol", 3: "[3] Shotgun", 4: "[4] SMG"}
        self.hud.set_weapon(names.get(weapon_idx, "Unknown"))
        self._update_weapon_visual()

    def _update_weapon_visual(self):
        if not hasattr(self, "_weapon_np"):
            self._weapon_np = None
            
        if self._weapon_np:
            self._weapon_np.removeNode()
            self._weapon_np = None
            
        weapon_idx = getattr(self, "current_weapon", 0)
        _base_dir = os.path.dirname(os.path.dirname(__file__))
        
        if hasattr(self, "local_actor") and self.local_actor:
            pass

        if weapon_idx == 0:
            return
            
        
        if weapon_idx == 1:
            full_path = os.path.join(_base_dir, "new_assets", "equipments", "assualt", "source", "AK47", "AK47.gltf")
        elif weapon_idx == 2:
            full_path = os.path.join(_base_dir, "new_assets", "equipments", "pistol", "source", "pistol.fbx")
        elif weapon_idx == 3:
            full_path = os.path.join(_base_dir, "new_assets", "equipments", "shotgun", "shotgun.glb")
        elif weapon_idx == 4:
            full_path = os.path.join(_base_dir, "new_assets", "equipments", "sub-machine", "source", "mp40.obj")
        else:
            full_path = os.path.join(_base_dir, "new_assets", "equipments", "assualt", "source", "AK47", "AK47.gltf")
        
        try:
            from panda3d.core import Filename
            model_path = Filename.fromOsSpecific(full_path).getFullpath()
            self._weapon_np = self.loader.loadModel(model_path)
            if self._weapon_np:
                # Attach to right hand if possible, otherwise camera
                if hasattr(self, "local_actor") and self.local_actor:
                    try:
                        right_hand = self.local_actor.exposeJoint(None, 'modelRoot', 'mixamorig:RightHand')
                        if right_hand:
                            self._weapon_np.reparentTo(right_hand)
                            self._weapon_np.setPos(0, 0, 0)
                            self._weapon_np.setHpr(0, 0, 0)
                        else:
                            self._weapon_np.reparentTo(self.camera)
                            self._weapon_np.setPos(0.3, 0.5, -0.2)
                    except:
                        self._weapon_np.reparentTo(self.camera)
                        self._weapon_np.setPos(0.3, 0.5, -0.2)
                else:
                    self._weapon_np.reparentTo(self.camera)
                    self._weapon_np.setPos(0.3, 0.5, -0.2)
                
                # Rescale and color based on weapon
                # Use self.render to set absolute world scale, bypassing complex bone scaling issues
                weapon_configs = {
                    1: {"scale": 0.67, "color": (1, 1, 1, 1), "pos": (0.05, 0.2, -0.05), "hpr": (180, -90, -90)},
                    2: {"scale": 0.003, "color": (1, 1, 1, 1), "pos": (0.05, 0.2, -0.05), "hpr": (-180, 0, -90)},
                    3: {"scale": 0.52, "color": (1, 1, 1, 1), "pos": (0.05, 0.2, -0.05), "hpr": (-180, 0, -90)},
                    4: {"scale": 0.7, "color": (1, 1, 1, 1), "pos": (0.05, 0.2, -0.05), "hpr": (0, 0, 90)}
                }
                
                cfg = weapon_configs.get(weapon_idx, weapon_configs[1])
                self._weapon_np.setScale(self.render, cfg["scale"])
                self._weapon_np.setColor(*cfg["color"])
                
                self._weapon_np.setPos(cfg["pos"])
                self._weapon_np.setHpr(cfg["hpr"])
                self._weapon_np.setPythonTag("base_hpr", cfg["hpr"])
                self._weapon_np.setHpr(cfg["hpr"])

                # Apply textures manually for Pistol and SMG
                if weapon_idx == 2:
                    tex = self.loader.loadTexture(Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "equipments", "pistol", "textures", "pistolcolor.png")).getFullpath())
                    self._weapon_np.setTexture(tex, 1)
                elif weapon_idx == 4:
                    tex = self.loader.loadTexture(Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "equipments", "sub-machine", "textures", "mp40.png")).getFullpath())
                    self._weapon_np.setTexture(tex, 1)

                # Arm pose is handled by the animations, no manual joint release needed

        except Exception as e:
            print(f"Could not load weapon {full_path}: {e}")
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

    def _show_only(self, state):
        self.state = state
        if self.menu: self.menu.hide()
        if self.lobby: self.lobby.hide()
        if self.hud: self.hud.hide()
        self._hide_loading_screen()
        self.results.hide()
        if self.connect_dialog:
            self.connect_dialog.hide()

        if state == STATE_MENU:
            self.menu.show()
            self._set_mouse_locked(False)
            if self._showcase_actor:
                self._showcase_actor.show()
        else:
            if self._showcase_actor:
                self._showcase_actor.hide()

        if state == STATE_LOBBY:
            self.lobby.show()
            self._set_mouse_locked(False)
        elif state == STATE_INGAME:
            self.hud.show()
            self._set_mouse_locked(True)
            self._hide_loading_screen()

    def _show_loading_screen(self):
        if not hasattr(self, "_loading_frame"):
            from direct.gui.DirectGui import DirectFrame, DirectLabel
            self._loading_frame = DirectFrame(parent=self.aspect2d, frameColor=_c4(10,12,20,1), frameSize=(-2,2,-2,2), sortOrder=100)
            DirectLabel(parent=self._loading_frame, text="LOADING MAP & SYNCING CHARACTERS...", scale=0.08, text_fg=_c4(240,240,240), frameColor=(0,0,0,0), pos=(0,0,0))
        self._loading_frame.show()
        builtins.base.graphicsEngine.renderFrame()
        builtins.base.graphicsEngine.renderFrame()

    def _hide_loading_screen(self):
        if hasattr(self, "_loading_frame"):
            self._loading_frame.hide()

    def _on_host_clicked(self, name):
        self._my_name = name
        self._show_only(STATE_CONNECT)
        self.connect_dialog = ConnectDialog(self._do_host, self._cancel_dialog, mode="host", player_name=name)

    def _on_join_clicked(self, name):
        self._my_name = name
        self._show_only(STATE_CONNECT)
        self.connect_dialog = ConnectDialog(self._do_join, self._cancel_dialog, mode="join", player_name=name)

    def _on_char_change(self, idx):
        self.selected_char_idx = idx
        if getattr(self.menu, '_showcase_actor', None):
            self.menu._showcase_actor.cleanup()
            self.menu._showcase_actor.removeNode()
            self.menu._showcase_actor = None
            
        if getattr(self.menu, '_dummy_actor', None):
            self.menu._dummy_actor.cleanup()
            self.menu._dummy_actor.removeNode()
            self.menu._dummy_actor = None
            
        self.taskMgr.remove("offset_showcase_arms")
            
        model_path = os.path.join(_base_dir, "new_assets", "rigged_characters", f"char{idx}_Animated.glb")
        
        if not os.path.exists(model_path):
            model_path = os.path.join(_base_dir, "new_assets", "rigged_characters", "char1_Animated.glb")

        if os.path.exists(model_path):
            try:
                # Convert Windows path to Panda3D Unix-style path
                from panda3d.core import Filename, Point3
                p3d_path = Filename.fromOsSpecific(model_path).getFullpath()
                
                from direct.actor.Actor import Actor
                from panda3d.core import Material
                
                # All characters now have the 'idle' animation baked directly into their .glb files
                try:
                    self.menu._showcase_actor = Actor(p3d_path)
                    self.menu._showcase_actor.hide() # Hide until bounds are calculated
                except Exception as e:
                    print(f"[client] Corrupt model file {model_path}: {e}. Falling back to char1.")
                    self.menu._showcase_actor = None
                
                if self.menu._showcase_actor and self.menu._showcase_actor.getJoints():
                    self.menu._showcase_actor.reparentTo(self.render)
                    self.menu._showcase_actor.setPos(0, 15, -2.5) # Placed in front of camera
                    self.menu._showcase_actor.setH(0) # Face the camera
                    self.menu._showcase_actor.setColorOff(1)
                    self.menu._showcase_actor.clearColorScale()
                    
                    # Play idle animation - list available anims and pick the best one
                    anim_names = self.menu._showcase_actor.getAnimNames()
                    
                    # Stop all animations first to prevent blending conflicts
                    self.menu._showcase_actor.stop()
                    
                    # Pick the best idle animation
                    idle_anim = None
                    if "idle" in anim_names:
                        idle_anim = "idle"
                    elif "Idle" in anim_names:
                        idle_anim = "Idle"
                    else:
                        # Find any animation with 'idle' in the name
                        for name in anim_names:
                            if "idle" in name.lower() and "jump" not in name.lower():
                                idle_anim = name
                                break
                    
                    if idle_anim:
                        self.menu._showcase_actor.loop(idle_anim)
                        self.menu._showcase_actor.setPlayRate(0.5, idle_anim)
                    else:
                        print(f"WARNING {model_path}: No idle animation found in {anim_names}")
                    
                    # Dynamically scale even rigged models to a standard height of 3.5
                    # We delay this by a frame so the animation updates the vertices first!
                    def apply_bounds(task):
                        if getattr(self.menu, '_showcase_actor', None):
                            bounds = self.menu._showcase_actor.getTightBounds()
                            if bounds:
                                min_b, max_b = bounds
                                height = max_b.getZ() - min_b.getZ()
                                if height > 0:
                                    self.menu._showcase_actor.setScale(3.5 / height)
                                
                                # Re-calculate bounds to center the model on the platform
                                bounds = self.menu._showcase_actor.getTightBounds()
                                min_b, max_b = bounds
                                center_x = (min_b.getX() + max_b.getX()) / 2.0
                                curr_pos = self.menu._showcase_actor.getPos()
                                self.menu._showcase_actor.setPos(curr_pos.getX() - center_x, 15, -2.5 - (min_b.getZ() - curr_pos.getZ()))
                            
                            self.menu._showcase_actor.show() # Show the actor now that it's positioned
                        return task.done
                    
                    self.taskMgr.remove("apply_showcase_bounds")
                    self.taskMgr.doMethodLater(0.05, apply_bounds, "apply_showcase_bounds")

                    self.taskMgr.remove("freeze_showcase_hips")
                    
                    try:
                        hips = self.menu._showcase_actor.controlJoint(None, "modelRoot", "mixamorig:Hips")
                        if hips:
                            hips.setX(0)
                            hips.setY(0)
                    except:
                        pass

                else:
                    # Model is either unrigged, broken FBX, or completely corrupt. Fallback to char1.
                    print(f"[client] Model {model_path} has no joints or failed to load. Falling back to char1.")
                    print(f"DEBUG: getJoints returned {self.menu._showcase_actor.getJoints() if self.menu._showcase_actor else 'None'}")
                    if self.menu._showcase_actor:
                        self.menu._showcase_actor.cleanup()
                    
                    p3d_path_fallback = Filename.fromOsSpecific("new_assets/characters/char1/source/Booyah Girl/Booyah_Girl_Animated.glb").getFullpath()
                    self.menu._showcase_actor = Actor(p3d_path_fallback)
                    self.menu._showcase_actor.reparentTo(self.render)
                    self.menu._showcase_actor.setPos(0, 15, -2.5)
                    self.menu._showcase_actor.setH(0)
                    self.menu._showcase_actor.setScale(0.18)
                    self.menu._showcase_actor.setColorOff(1)
                    self.menu._showcase_actor.clearColorScale()
                    try:
                        self.menu._showcase_actor.loop("idle")
                    except:
                        pass
                
                if self.state != STATE_MENU:
                    self.menu._showcase_actor.hide()
                    
            except Exception as e:
                print(f"[client] Failed to load showcase char{idx} from {model_path}: {e}")

    def _cancel_dialog(self):
        if self.connect_dialog:
            self.connect_dialog.destroy()
            self.connect_dialog = None
        self.paused = False
        self._show_only(STATE_MENU)

    def _do_host(self, port_str):
        try:
            port = int(port_str) if port_str else settings.DEFAULT_PORT
        except ValueError:
            port = settings.DEFAULT_PORT

        from server.game_server import GameServer
        self.local_server = GameServer(host=settings.DEFAULT_HOST, port=port)
        self.server_thread = threading.Thread(target=self.local_server.start, daemon=True)
        self.server_thread.start()
        
        ok = False
        msg = ""
        for _ in range(5):
            time.sleep(0.2)
            ok, msg = self.net.connect("127.0.0.1", port, self._my_name, self.selected_char_idx)
            if ok:
                break

        self._finish_connect(ok, msg)

    def _do_join(self, addr_str):
        host, _, port_str = addr_str.partition(":")
        host = host.strip() or "127.0.0.1"
        try:
            port = int(port_str.strip()) if port_str.strip() else settings.DEFAULT_PORT
        except ValueError:
            port = settings.DEFAULT_PORT
        ok, msg = self.net.connect(host, port, self._my_name, self.selected_char_idx)
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
        self.net.send({"type": MSG_SET_READY, "ready": self._my_ready, "char_idx": self.selected_char_idx})

    def _on_set_map(self, map_key):
        self.net.send({"type": MSG_SET_MAP, "map": map_key})

    def _on_set_mode(self, mode):
        self.net.send({"type": MSG_SET_MODE, "mode": mode})

    def _on_add_bot(self):
        self.net.send({"type": MSG_ADD_BOT})

    def _on_start_game(self):
        self.net.send({"type": MSG_START_GAME})

    def _on_chat_send(self, text):
        self.net.send({"type": "chat", "text": text})

    def _on_leave_lobby(self):
        self.net.send({"type": MSG_LEAVE})
        self.net.disconnect()
        import queue
        self.net.incoming = queue.Queue()
        if self.local_server:
            self.local_server.stop()
            if hasattr(self, "server_thread") and self.server_thread:
                self.server_thread.join(timeout=1.0)
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

        if hasattr(self, "_weapon_np") and self._weapon_np:
            self._weapon_np.removeNode()
            self._weapon_np = None

        if hasattr(self, "_bullets"):
            for b in self._bullets:
                if b["np"]: b["np"].removeNode()
            self._bullets.clear()

        if hasattr(self, "_hit_sparks"):
            for s in self._hit_sparks:
                if s["np"]: s["np"].removeNode()
            self._hit_sparks.clear()

        if self._player_np:
            self._player_np.removeNode()
            self._player_np = None
        if self._player_visual:
            self._player_visual.removeNode()
            self._player_visual = None
        self._player_col = None
        self._floor_ray_np = None

        self.camera.reparentTo(self.render)
        self.camera.setPos(0, 0, 0)
        self.camera.setHpr(0, 0, 0)

        self.win.setClearColor(_c4(135, 206, 235))

    def _build_level(self, level_key):
        self._clear_level()
        self.current_map = level_key
        level_def = load_level(level_key)

        level_root = self.render.attachNewNode("level_root")
        self.level_nodes.append(level_root)

        map_path = Filename.fromOsSpecific(os.path.join(_base_dir, "new_assets", "map", "paraguay", "source", "free_fire_maxx_new_clock_tower_map_download_free.glb")).getFullpath()
        try:
            self._map_model = self.loader.loadModel(map_path)
            self._map_model.reparentTo(level_root)
            self._map_model.setScale(100.0) # Map scale calibrated to character bounds
            self._map_model.setZ(0.0)       # Align map visual with physics bounds
            self._map_model.setTwoSided(True)
            self._map_model.flattenStrong()
            
            # Fix shiny materials and blurry textures
            from panda3d.core import Texture
            for mat in self._map_model.findAllMaterials():
                mat.setRoughness(1.0)
                mat.setMetallic(0.0)
            for tex in self._map_model.findAllTextures():
                tex.setAnisotropicDegree(16)
                tex.setMinfilter(Texture.FT_linear_mipmap_linear)
                tex.setMagfilter(Texture.FT_linear)


            # Auto-generate static collision for the map
            # Set collision on all geometry nodes
            self._map_model.setCollideMask(WALL_MASK | FLOOR_MASK)
            for np in self._map_model.findAllMatches("**/+GeomNode"):
                np.node().setIntoCollideMask(WALL_MASK | FLOOR_MASK)
        except Exception as e:
            print(f"Failed to load map: {e}")



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

        # Spawn physical props scattered in the level
        from game.object_prop import REGISTRY
        # NOTE: P-key reports player_np.getPos().z = ground_surface + 1.0 (see _update_ground_z).
        # So user-captured Z coords are 1.0 above actual ground. We subtract 1.0 to land props flush.
        PROP_Z_OFFSET = -1.0
        for prop_def in level_def.get("hider_spawn_objects", []):
            p = prop_def["position"]
            key = prop_def["key"]
            instance_hpr = prop_def.get("hpr", None)
            if key in PROP_MODEL_MAP:
                obj_def = REGISTRY.get(key)
                if obj_def:
                    # Raycast down to find the floor Z
                    z_coord = p[2] + PROP_Z_OFFSET
                    # Start raycast from slightly above the prop's intended Z to avoid hitting roofs
                    ray = CollisionRay(p[0], p[1], z_coord + 2.0, 0, 0, -1)
                    ray_node = CollisionNode("prop_ray")
                    ray_node.addSolid(ray)
                    ray_node.setFromCollideMask(FLOOR_MASK)
                    ray_np = level_root.attachNewNode(ray_node)
                    queue = CollisionHandlerQueue()
                    trav = CollisionTraverser()
                    trav.addCollider(ray_np, queue)
                    trav.traverse(self.render)
                    if queue.getNumEntries() > 0:
                        queue.sortEntries()
                        z_coord = queue.getEntry(0).getSurfacePoint(self.render).z
                    ray_np.removeNode()
                    
                    prop_np = _make_prop(level_root, PROP_MODEL_MAP[key], (p[0], p[1], z_coord), obj_def.scale, instance_hpr)
                    if prop_np:
                        self.level_nodes.append(prop_np)

        self.win.setClearColor(_c4(18, 22, 30))

        if getattr(self, "my_role", ROLE_HUNTER) == ROLE_HIDER:
            spawn = level_def.get("hider_spawns", [[0, 0.0, 5.0]])[0]
        else:
            spawn = level_def.get("hunter_spawns", [[5, 0.0, 5.0]])[0]
            
        self._player_np = self.render.attachNewNode("player_root")
        self._player_np.setPos(spawn[0], spawn[1], spawn[2])
        self._vel_z = 0.0
        self._is_grounded = False
        self._ground_z = spawn[2]

        self._player_visual = self._player_np.attachNewNode("player_visual")
        self._update_local_player_model()
        if getattr(self, "my_role", None) == ROLE_HUNTER:
            self.equip_weapon(1)

        self.camera.reparentTo(self._player_np)
        self._target_cam_z = 0.6
        self.camera.setPos(0, 0, self._target_cam_z)
        self.camera.setHpr(0, 0, 0)
        self._cam_yaw   = 0.0
        self._cam_pitch = 0.0

        c_node = CollisionNode("player_col")
        c_node.addSolid(CollisionSphere(0, 0, -0.2, 0.35))
        c_node.addSolid(CollisionSphere(0, 0, 0.4, 0.35))
        c_node.addSolid(CollisionSphere(0, 0, 1.0, 0.35))
        c_node.setFromCollideMask(WALL_MASK)
        c_node.setIntoCollideMask(BitMask32.allOff())

        self._player_col = self._player_np.attachNewNode(c_node)

        self._pusher.addCollider(self._player_col, self._player_np)
        self.cTrav.addCollider(self._player_col, self._pusher)

        ray_node = CollisionNode("player_floor_ray")
        ray = CollisionRay(0, 0, 0.8, 0, 0, -1)
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(FLOOR_MASK)
        ray_node.setIntoCollideMask(BitMask32.allOff())
        self._floor_ray_np = self._player_np.attachNewNode(ray_node)
        self.cTrav.addCollider(self._floor_ray_np, self._floor_handler)

    def _setup_lighting(self):
        alight = AmbientLight("ambient")
        alight.setColor(LVecBase4f(0.4, 0.4, 0.5, 1.0))
        alight_np = self.render.attachNewNode(alight)
        self.render.setLight(alight_np)

        dlight = DirectionalLight("sunlight")
        dlight.setColor(LVecBase4f(8.0, 7.5, 7.0, 1.0))
        dlight.setShadowCaster(True, 4096, 4096)
        lens = dlight.getLens()
        lens.setFilmSize(1500, 1500)
        lens.setNearFar(-1500, 1500)
        self.dlight_np = self.render.attachNewNode(dlight)
        self.dlight_np.setHpr(45, -50, 0)
        self.render.setLight(self.dlight_np)
        
        # Add visual sky dome
        try:
            sky = self.loader.loadModel("models/misc/sphere")
            if sky:
                sky.reparentTo(self.render)
                sky.setScale(2000)
                sky.setColor(_c4(135, 206, 235))
                sky.setLightOff()
                sky.setTwoSided(True)
                sky.setBin("background", 0)
                sky.setDepthWrite(False)
        except:
            pass
            
        # Add visual sun sphere
        try:
            sun = self.loader.loadModel("models/misc/sphere")
            if sun:
                sun.reparentTo(self.render)
                # Light points from sun (-862, -862, 1455) to origin
                sun.setPos(-862, -862, 1455)
                sun.setScale(150)
                sun.setColor(1.0, 1.0, 0.8, 1.0)
                sun.setLightOff()
        except:
            pass

        # Add a subtle point-like fill for basement/indoor visibility
        dlight2 = DirectionalLight("fill")
        dlight2.setColor(LVecBase4f(0.2, 0.2, 0.3, 1.0))
        dlight2_np = self.render.attachNewNode(dlight2)
        dlight2_np.setHpr(-135, 10, 0)
        self.render.setLight(dlight2_np)

    def _update_local_player_model(self):
        if not self._player_visual:
            return
            
        current_state = (self.my_role, self.my_transformed if self.my_role == ROLE_HIDER else None)
        if not hasattr(self, "_last_visual_state") or self._last_visual_state != current_state:
            self._last_visual_state = current_state
            
            if self._player_visual.find("human_visual").isEmpty():
                self._human_visual = self._player_visual.attachNewNode("human_visual")
                self.local_actor = _build_character(self._human_visual, self.loader, self.my_role == ROLE_HUNTER, self.selected_char_idx)
                if self.local_actor:
                    try:
                        self._hips_node = self.local_actor.exposeJoint(None, 'modelRoot', 'mixamorig:Hips')
                    except:
                        self._hips_node = None
            else:
                self._human_visual = self._player_visual.find("human_visual")

            if self._player_visual.find("morph_visual").isEmpty():
                self._morph_visual = self._player_visual.attachNewNode("morph_visual")
                self._morph_visual.setZ(-0.55) # Offset so prop origin sits on the floor
            else:
                self._morph_visual = self._player_visual.find("morph_visual")
                
            for child in self._morph_visual.getChildren():
                child.removeNode()
                
            self._human_visual.hide()
            self._morph_visual.hide()

            if self.my_role == ROLE_HIDER and self.my_transformed:
                self._morph_visual.show()
                obj = REGISTRY.get(self.my_transformed)
                if obj and self.my_transformed in PROP_MODEL_MAP:
                    _make_prop(self._morph_visual, PROP_MODEL_MAP[self.my_transformed], (0,0,0), obj.scale)
            elif self.my_role == ROLE_HUNTER or self.my_role == ROLE_HIDER:
                self._human_visual.show()
        
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
            elif mtype == MSG_CHAT_BROADCAST:
                if self.state == STATE_LOBBY:
                    self.lobby.add_chat_message(msg.get("name", ""), msg.get("text", ""))
                else:
                    self.hud.push_clue(f"{msg.get('name')}: {msg.get('text')}")
            elif mtype == MSG_TAUNT_BROADCAST:
                SoundManager.taunt()
                self.hud.push_clue(f"[!] {msg.get('name')} taunted!")
            elif mtype == MSG_ELIMINATED:
                SoundManager.eliminated()
                elim_id = msg.get("player_id")
                if elim_id == self.net.player_id:
                    self.hud.push_clue("You were eliminated. Spectating...")
                    if hasattr(self, "local_actor") and self.local_actor:
                        try:
                            self.local_actor.play("death")
                        except:
                            pass
                else:
                    if elim_id in self.remote_actors and self.remote_actors[elim_id]:
                        try:
                            self.remote_actors[elim_id].play("death")
                        except:
                            pass
            elif mtype == MSG_ROUND_RESULT:
                self._show_only(STATE_INGAME)
                self.hud.hide()
                self._set_mouse_locked(False)
                self.results.display(msg)
            elif mtype == MSG_ERROR:
                self.hud.push_clue(f"[!] {msg.get('message')}")
            elif mtype == MSG_PLAYER_LEFT:
                pid = msg.get("player_id")
                if pid in self.remote_nodes:
                    self.remote_nodes.pop(pid).removeNode()

    def _on_phase_change(self, phase, time_left):
        if phase != PHASE_LOBBY and self.current_phase == PHASE_LOBBY:
            self._show_loading_screen()
            
        self.current_phase = phase
        self.current_time_left = time_left
        self.hud.set_timer(phase, time_left)

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
                self.hud.set_transform_hint("[LMB] Shoot  |  [Q] Scanner  |  [L] Leave Game")
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
        self._players_cache = players

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

            if self.my_role == ROLE_HUNTER:
                self.scanner_charges = my_data.get("scanner_charges", self.scanner_charges)
                self.last_scanner_press = my_data.get("last_scanner_time", self.last_scanner_press)

        self.hud.set_timer(self.current_phase, self.current_time_left)
        self.hud.set_players(alive_hiders, total_hunters)
        self.hud.set_energy(self.my_energy)
        self.hud.set_health(self.my_health)
        
        if self.my_role == ROLE_HUNTER:
            import time
            cooldown_left = max(0.0, settings.SCANNER_COOLDOWN - (time.time() - self.last_scanner_press))
            self.hud.set_scanner_status(self.scanner_charges, settings.SCANNER_MAX_CHARGES, cooldown_left)
            self.hud.set_hotbar([])
        elif self.my_role == ROLE_HIDER:
            self.hud.set_hotbar(self._object_hotbar)

        if self.current_mode == "object_rush" and self.my_role == ROLE_HIDER:
            if my_data:
                tasks = my_data.get("tasks", [])
                self.hud.set_tasks(tasks)
        else:
            self.hud.set_tasks([])

    def _update_remote_node(self, p):
        pid   = p["player_id"]
        role  = p.get("role")
        alive = p.get("alive", True)
        pos   = p.get("position", [0, 1, 0])
        vel   = p.get("velocity", [0, 0, 0])

        if not alive or p.get("eliminated"):
            if pid in self.remote_nodes:
                np = self.remote_nodes[pid]
                np.setHpr(0, 90, 0)
                if not np.hasPythonTag("dead"):
                    np.setZ(np.getZ() - 0.5)
                    np.setPythonTag("dead", True)
            return

        if not hasattr(self, "remote_state_tracking"):
            self.remote_state_tracking = {}
            self.remote_actors = {}

        current_state = (role, p.get("transformed_into") if role == ROLE_HIDER else None)
        last_state = self.remote_state_tracking.get(pid)
        
        if pid not in self.remote_nodes:
            self.remote_nodes[pid] = self.render.attachNewNode(f"remote_player_{pid}")
            np = self.remote_nodes[pid]
            np.setPythonTag("player_id", pid)
            
            col = CollisionNode(f"hitbox_{pid}")
            col.addSolid(CollisionSphere(0, 0, -0.2, 0.35))
            col.addSolid(CollisionSphere(0, 0, 0.4, 0.35))
            col.addSolid(CollisionSphere(0, 0, 1.0, 0.35))
            col.setIntoCollideMask(PLAYER_FROM_MASK)
            col.setFromCollideMask(BitMask32.allOff())
            hitbox_np = np.attachNewNode(col)
            hitbox_np.setPythonTag("player_id", pid)
            
            human_visual = np.attachNewNode("human_visual")
            human_visual.setZ(-0.55) # Offset human by -0.55 to sit precisely on the floor
            morph_visual = np.attachNewNode("morph_visual")
            morph_visual.setZ(-0.55) # Offset so prop origin sits on the floor
            
            actor = _build_character(human_visual, self.loader, role == ROLE_HUNTER, p.get("char_idx", 1))
            self.remote_actors[pid] = actor

        np = self.remote_nodes[pid]
        
        # Scale for crouching
        if p.get("crouch"):
            np.setScale(1, 1, 0.6)
        else:
            np.setScale(1, 1, 1.0)
        human_visual = np.find("human_visual")
        morph_visual = np.find("morph_visual")

        if last_state != current_state:
            self.remote_state_tracking[pid] = current_state
            
            for child in morph_visual.getChildren():
                child.removeNode()

            human_visual.hide()
            morph_visual.hide()

            if role == ROLE_HIDER and current_state[1]:
                morph_visual.show()
                obj = REGISTRY.get(current_state[1])
                if obj and current_state[1] in PROP_MODEL_MAP:
                    _make_prop(morph_visual, PROP_MODEL_MAP[current_state[1]], (0,0,0), obj.scale)
            else:
                human_visual.show()

        np.show()
        
        # Animate remote actor if present
        actor = self.remote_actors.get(pid)
        if actor:
            speed = LVector3f(vel[0], vel[1], 0).length()
            if p.get("role") == ROLE_HUNTER:
                desired_run = "non_pistol_run" if "non_pistol_run" in actor.getPythonTag("available_anims") else "run"
                target_anim = desired_run if speed > 0.5 else "big_gun_Idle"
            else:
                desired_run = "run" if "run" in actor.getPythonTag("available_anims") else "non_pistol_run"
                target_anim = desired_run if speed > 0.5 else "idle"
            if len(vel) > 2 and abs(vel[2]) > 0.5:
                target_anim = "jump"
            current_anim = actor.getCurrentAnim()
            if current_anim != target_anim:
                try:
                    actor.loop(target_anim)
                except:
                    pass

        np.setPos(pos[0], pos[2], pos[1])
        np.setH(p.get("rotation_y", 0))

        if vel[0] != 0 or vel[1] != 0:
            move_angle_deg = math.degrees(math.atan2(-vel[0], vel[1]))
            human_visual.setH(move_angle_deg - np.getH())
            morph_visual.setH(move_angle_deg - np.getH())

    def _apply_root_motion(self, actor):
        """Neutralizes unwanted root motion from broken mixamo animations so the character doesn't slide away"""
        if actor and actor.hasPythonTag("idle_hip_pos"):
            idle_pos = actor.getPythonTag("idle_hip_pos")
            base_z = actor.getPythonTag("base_z")
            if idle_pos is not None and base_z is not None:
                current_anim = actor.getCurrentAnim()
                
                try:
                    hips = actor.exposeJoint(None, 'modelRoot', 'mixamorig:Hips')
                    hip_pos = hips.getPos(actor)
                    scale_val = actor.getScale()[0]
                    
                    target_x = (hip_pos.x - idle_pos.x) * scale_val
                    target_y = (hip_pos.y - idle_pos.y) * scale_val
                    if current_anim not in ("death",):
                        target_z = base_z - (hip_pos.z - idle_pos.z) * scale_val
                    else:
                        # For running/walking, preserve the original logic that the user liked
                        target_x = (hip_pos.x - idle_pos.x) * scale_val
                        target_y = (hip_pos.y - idle_pos.y) * scale_val
                        if current_anim not in ("death",):
                            target_z = base_z - (hip_pos.z - idle_pos.z) * scale_val
                        else:
                            target_z = base_z
                        
                    actor.setPos(target_x, target_y, target_z)
                except:
                    actor.setPos(0, 0, base_z)

    def _main_loop(self, task):
        dt = builtins.globalClock.getDt()

        if hasattr(self, "local_actor"):
            self._apply_root_motion(self.local_actor)

        for pid, actor in getattr(self, "remote_actors", {}).items():
            self._apply_root_motion(actor)

        if self.state == STATE_MENU:
            if self.menu: self.menu.update()
            return task.cont

        self._process_network()

        if hasattr(self, "_shoot_anim_timer"):
            self._shoot_anim_timer -= dt

        # Update bullet projectiles
        if hasattr(self, "_bullets"):
            kept_bullets = []
            for b in self._bullets:
                move_dist = b["speed"] * dt
                b["np"].setPos(b["np"].getPos() + b["dir"] * move_dist)
                b["distance_left"] -= move_dist
                b["timer"] -= dt
                if b["timer"] > 0 and b["distance_left"] > 0:
                    kept_bullets.append(b)
                else:
                    b["np"].removeNode()
            self._bullets = kept_bullets

        if hasattr(self, "_hit_sparks"):
            for s in self._hit_sparks[:]:
                s["timer"] -= dt
                # expand spark
                scale = s["np"].getScale()[0]
                s["np"].setScale(scale + dt * 2.0)
                if s["timer"] <= 0:
                    s["np"].removeNode()
                    self._hit_sparks.remove(s)

        if hasattr(self, "_weapon_recoil") and self._weapon_recoil > 0:
            self._weapon_recoil = max(0.0, self._weapon_recoil - dt * 5.0)
            if hasattr(self, "_weapon_np") and self._weapon_np:
                weapon_idx = getattr(self, "current_weapon", 1)
                base_hpr = self._weapon_np.getPythonTag("base_hpr")
                if not base_hpr:
                    base_hpr = (0, 0, 0)
                # Add pitch recoil (negative pitch kicks it up)
                recoil_pitch = self._weapon_recoil * 30.0 
                self._weapon_np.setHpr(base_hpr[0], base_hpr[1] + recoil_pitch, base_hpr[2])

        if self.state == STATE_INGAME and not self.paused and self._player_np:
            self._update_player(dt)
            
            if getattr(self, "my_role", None) == ROLE_HUNTER and getattr(self, "current_phase", None) != PHASE_HIDING:
                if self._k("mouse1"):
                    weapon_idx = getattr(self, "current_weapon", 1)
                    if weapon_idx in (1, 4): # Full-auto weapons
                        self._fire_blaster()
                            
        return Task.cont

    def _update_player(self, dt: float):
        is_spectator = (self.my_health <= 0)
        target_np = self._player_np
        if is_spectator:
            alive = [p for p in getattr(self, "_players_cache", []) if p.get("alive") and not p.get("eliminated")]
            if alive:
                if not hasattr(self, "_spectate_idx"):
                    self._spectate_idx = 0
                if self._spectate_idx >= len(alive):
                    self._spectate_idx = 0
                target_id = alive[self._spectate_idx]["player_id"]
                if target_id in self.remote_nodes:
                    target_np = self.remote_nodes[target_id]

        if self._mouse_locked and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            cx = self.win.getProperties().getXSize() // 2
            cy = self.win.getProperties().getYSize() // 2
            dx = md.getX() - cx
            dy = md.getY() - cy
            if dx or dy:
                self._cam_yaw   -= dx * 0.15
                self._cam_pitch -= dy * 0.15
                self._cam_pitch = max(-89, min(89, self._cam_pitch))
            
            if self._k("c"):
                self._target_cam_z = 0.2
            else:
                self._target_cam_z = 0.6
                
            cam_z = self.camera.getZ()
            self.camera.setZ(cam_z + (self._target_cam_z - cam_z) * 10 * dt)
            
            self.camera.setHpr(0, self._cam_pitch, 0)
            self.win.movePointer(0, cx, cy)

            if self._player_visual:
                if is_spectator:
                    self._player_visual.hide()
                else:
                    self._player_visual.show()
                
            if not is_spectator:
                if not self._rotation_locked:
                    target_np.setH(self._cam_yaw)
                else:
                    target_np.setH(self._locked_player_yaw)

            rad_yaw = math.radians(self._cam_yaw)
            
            # Choose camera parameters based on toggle
            if self._third_person:
                max_cam_dist = 4.0
                cam_z_offset = 2.1
            else:
                max_cam_dist = -0.2 # Slightly inside/front of face
                cam_z_offset = 1.2

            if self.my_transformed:
                obj = REGISTRY.get(self.my_transformed)
                if obj:
                    prop_height = obj.scale[2]
                    cam_z_offset = max(-0.2, prop_height - 0.1)
                    max_cam_dist = max(1.5, prop_height * 2.5)
                    if not self._third_person:
                        max_cam_dist *= 0.4  # Closer view for prop

            head_pos = target_np.getPos(self.render) + LVector3f(0, 0, cam_z_offset)
            target_x = math.sin(rad_yaw) * max_cam_dist
            target_y = -math.cos(rad_yaw) * max_cam_dist
            target_pos = head_pos + LVector3f(target_x, target_y, 0)
            
            cam_dist = max_cam_dist
            if max_cam_dist > 0:
                self._cam_seg.setPointA(head_pos)
                self._cam_seg.setPointB(target_pos)
                self.cam_trav.traverse(self.render)
                
                if self._cam_handler.getNumEntries() > 0:
                    self._cam_handler.sortEntries()
                    for i in range(self._cam_handler.getNumEntries()):
                        entry = self._cam_handler.getEntry(i)
                        if entry.hasSurfacePoint():
                            hit_pos = entry.getSurfacePoint(self.render)
                            cam_dist = (hit_pos - head_pos).length() - 0.2
                            if cam_dist < 0.2:
                                cam_dist = 0.2
                            break
                    
            cam_x = math.sin(rad_yaw) * cam_dist
            cam_y = -math.cos(rad_yaw) * cam_dist
            self.camera.reparentTo(self.render)
            self.camera.setPos(head_pos.x + cam_x, head_pos.y + cam_y, head_pos.z)
            self.camera.setHpr(self._cam_yaw, self._cam_pitch, 0)


        speed = 2.5
        if self.my_role == ROLE_HIDER and self.my_transformed:
            obj = REGISTRY.get(self.my_transformed)
            if obj:
                speed *= obj.speed_mult
        elif self._k("lshift"):
            speed = 5.0

        forward = 0.0
        right   = 0.0
        is_spectator = (self.my_health <= 0)
        can_move = not is_spectator
        
        if can_move:
            if self.my_role == ROLE_HUNTER and self.current_phase == PHASE_HIDING:
                can_move = False
            if self.my_role == ROLE_HIDER and getattr(self, "_rotation_locked", False):
                can_move = False

        if can_move:
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
            self._player_np.setFluidPos(pos.x + vx * dt, pos.y + vy * dt, pos.z)
            
        if hasattr(self, "dlight_np") and self.dlight_np:
            self.dlight_np.setPos(self._player_np.getPos())
            
            if self._player_visual:
                is_hunter = getattr(self, "my_role", None) == ROLE_HUNTER
                in_shoot_anim = getattr(self, "_shoot_anim_timer", 0) > 0
                
                if vx != 0 or vy != 0:
                    self._last_move_angle = math.degrees(math.atan2(-vx, vy))
                elif not hasattr(self, "_last_move_angle"):
                    self._last_move_angle = self._player_np.getH()
                    
                if is_hunter and in_shoot_anim:
                    self._last_move_angle = self._cam_yaw
                
                self._player_visual.setH(self._last_move_angle - self._player_np.getH())

        # Update local animation
        if hasattr(self, "local_actor") and self.local_actor:
            is_moving = (forward != 0 or right != 0)
            
            weapon_idx = getattr(self, "current_weapon", 0)
            is_hunter = getattr(self, "my_role", None) == ROLE_HUNTER
            
            if is_moving:
                is_sprint = self._k("lshift")
                if is_hunter and weapon_idx == 2:
                    target_anim = "Pistol Run" if is_sprint else "Pistol Walk"
                elif is_hunter and weapon_idx != 0:
                    my_anims = self.local_actor.getPythonTag("available_anims")
                    desired_run = "non_pistol_run" if "non_pistol_run" in my_anims else "run"
                    desired_walk = "non_pistol_walk" if "non_pistol_walk" in my_anims else "walk"
                    target_anim = desired_run if is_sprint else desired_walk
                else:
                    my_anims = self.local_actor.getPythonTag("available_anims")
                    desired_run = "run" if "run" in my_anims else "non_pistol_run"
                    desired_walk = "walk" if "walk" in my_anims else "non_pistol_walk"
                    target_anim = desired_run if is_sprint else desired_walk
            else:
                if is_hunter and weapon_idx != 0:
                    target_anim = "Pistol_Idle" if weapon_idx == 2 else "big_gun_Idle"
                else:
                    target_anim = "idle"
                
            if not self._is_grounded:
                target_anim = "jump"
                
            # Only loop new animations if not currently in a shooting animation override
            in_shoot_anim = getattr(self, "_shoot_anim_timer", 0) > 0
            if not in_shoot_anim and self.local_actor.getCurrentAnim() != target_anim:
                try:
                    self.local_actor.loop(target_anim)
                except:
                    pass

        if not is_spectator and self._k("space") and self._is_grounded:
            self._vel_z = 6.5
            self._is_grounded = False
            self._pending_jump = True

        # Physics collision with walls
        self.cTrav.traverse(self.render)
        
        self._update_ground_z()

        # Stable vertical physics (smooth jump & rock-solid ground lock)
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
                "sprint": bool(self._k("lshift")),
                "crouch": bool(self._k("c")),
                "jump": self._pending_jump,
                "position": [p.x, p.z, p.y],
            })
            self._pending_jump = False

        if self.my_role == ROLE_HUNTER:
            cooldown_left = max(
                0.0, settings.SCANNER_COOLDOWN - (now - self.last_scanner_press)
            )
            self.hud.set_scanner_status(
                self.scanner_charges, settings.SCANNER_MAX_CHARGES, cooldown_left
            )
            self.hud.set_transform_hint("[LMB] Blaster  |  [Q] Scanner  |  [K] Flashlight  |  [L] Leave Game")

        elif self.my_role == ROLE_HIDER:
            rot_status = "LOCKED (F to unlock)" if self._rotation_locked else "F: Lock Angle"
            view_status = "3rd Person 1 (V)" if self._third_person else "3rd Person 2 (V)"
            if self.my_transformed:
                obj = REGISTRY.get(self.my_transformed)
                hint = f"Disguise: {obj.display if obj else '?'}  |  {rot_status}  |  {view_status}  |  [T] Taunt  |  [L] Leave"
            else:
                hint = f"[1-9] Choose Morph  |  {rot_status}  |  {view_status}  |  [T] Taunt  |  [L] Leave"
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

        # The lowest collision sphere is at z=-0.2 with radius 0.35 -> bottom is at -0.55.
        # Thus, when resting on the ground, the player origin should be at best_z + 0.55
        target_ground = best_z + 0.55
        self._ground_z = target_ground
