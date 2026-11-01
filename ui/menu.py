from __future__ import annotations
import os
import builtins

from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectEntry, DirectLabel, DirectSlider,
)
from panda3d.core import (
    TextNode, LVecBase4f, TransparencyAttrib, Filename,
    CardMaker,
)


def _c(r, g, b, a=1.0):
    return LVecBase4f(r / 255, g / 255, b / 255, a)


def _label(parent, text, pos, scale, fg, align=TextNode.ACenter, shadow=None):
    kwargs = {}
    if shadow:
        kwargs["text_shadow"] = shadow
    return DirectLabel(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text_align=align,
        frameColor=(0, 0, 0, 0),
        relief=None,
        pos=pos,
        **kwargs,
    )


def _menu_btn(parent, text, pos, command, fg, hover_fg=None, scale=0.065, width=4.0):
    from direct.gui.DirectGuiGlobals import ENTER, EXIT
    hfg = hover_fg or fg
    btn = DirectButton(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text_shadow=(0, 0, 0, 1.0),
        frameColor=(0,0,0,0),
        relief=None,
        pos=pos,
        command=command,
    )
    def on_enter(event):
        btn["text_fg"] = hfg
        btn.setScale(scale * 1.15)
    def on_exit(event):
        btn["text_fg"] = fg
        btn.setScale(scale)
    btn.bind(ENTER, on_enter)
    btn.bind(EXIT, on_exit)
    return btn


class MainMenu:
    def __init__(self, on_host, on_join, on_quit, on_char_change):
        self.on_host = on_host
        self.on_join = on_join
        self.on_quit = on_quit
        self.on_char_change = on_char_change

        self._aspect2d = builtins.base.aspect2d
        self.root = self._aspect2d.attachNewNode("main_menu")



        self._bg_img = None
        bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "new_assets", "background", "menu_bg.jpg")
        if os.path.exists(bg_path):
            try:
                import math
                from panda3d.core import Filename
                from direct.gui.OnscreenImage import OnscreenImage
                
                unix_path = Filename.fromOsSpecific(bg_path).getFullpath()
                tex = builtins.base.loader.loadTexture(unix_path)
                
                self._bg_img = OnscreenImage(image=tex, parent=builtins.base.camera)
                dist = 200
                self._bg_img.setPos(0, dist, 0)
                
                # Scale to perfectly fit the camera FOV
                fov = builtins.base.camLens.getFov()
                half_w = math.tan(math.radians(fov[0] / 2.0)) * dist
                half_h = math.tan(math.radians(fov[1] / 2.0)) * dist
                self._bg_img.setScale(half_w, 1, half_h)
                
                self._bg_img.setBin("background", 10)
                self._bg_img.setDepthWrite(False)
                self._bg_img.setDepthTest(False)
                self._bg_img.setLightOff(1)
                self._bg_img.clearShader()
            except Exception as e:
                print(f"Failed to load menu bg: {e}")



        _label(self.root, "MORPH HUNT",
               pos=(0, 0, 0.80), scale=0.15,
               fg=_c(240, 245, 248),
               shadow=(0, 0, 0, 0.7))

        # Anchor nodes for edges
        self.top_left = builtins.base.a2dTopLeft
        self.top_right = builtins.base.a2dTopRight
        self.bottom_left = builtins.base.a2dBottomLeft
        self.bottom_right = builtins.base.a2dBottomRight

        # TOP LEFT: PROFILE
        self._profile_btn = _menu_btn(
            self.root, "PROFILE", (0.3, 0, -0.15), self._do_profile,
            _c(220, 235, 238), _c(80, 240, 230), scale=0.06
        )
        self._profile_btn.reparentTo(self.top_left)

        # TOP RIGHT: NEWS / TIPS
        self.tips = [
            "Tip: Listen carefully for nearby footsteps.",
            "Tip: Hiders can morph into objects.",
            "Tip: Hunters can use their scanner to find suspicious objects.",
            "Tip: Stay moving while hiding.",
            "Tip: Sound can reveal your position."
        ]
        self.tip_idx = 0
        
        # Wrap long tips
        self.tip_label = _label(self.root, self.tips[0], (-0.1, 0, -0.15), 0.045, _c(240, 180, 70), align=TextNode.ARight, shadow=(0,0,0,1))
        self.tip_label["text_wordwrap"] = 20
        self.tip_label.reparentTo(self.top_right)
        
        # CENTER: CHARACTER SHOWCASE
        self.char_idx = 1
        self._left_btn = _menu_btn(self.root, "<", (-0.6, 0, 0.0), self._prev_char, _c(255, 255, 255), scale=0.1)
        self._right_btn = _menu_btn(self.root, ">", (0.6, 0, 0.0), self._next_char, _c(255, 255, 255), scale=0.1)
        self.char_name_label = _label(self.root, f"Character {self.char_idx}", (0, 0, -0.7), 0.06, _c(220, 245, 255), align=TextNode.ACenter, shadow=(0,0,0,0.8))

        # BOTTOM LEFT: HOW TO PLAY, SETTINGS
        self._howto_btn = _menu_btn(
            self.root, "HOW TO PLAY", (0.4, 0, 0.25), self._do_howto,
            _c(220, 235, 238), _c(80, 240, 230), scale=0.06)
        self._howto_btn.reparentTo(self.bottom_left)

        self._settings_btn = _menu_btn(
            self.root, "SETTINGS", (0.32, 0, 0.15), self._do_settings,
            _c(220, 235, 238), _c(80, 240, 230), scale=0.06)
        self._settings_btn.reparentTo(self.bottom_left)

        # BOTTOM RIGHT: START
        self._start_btn = _menu_btn(
            self.root, "START GAME", (-0.4, 0, 0.25), self._do_start,
            _c(80, 240, 230), _c(120, 255, 240), scale=0.08)
        self._start_btn.reparentTo(self.bottom_right)

        self._quit_btn = _menu_btn(
            self.root, "QUIT", (-0.2, 0, 0.12), on_quit,
            _c(225, 140, 140), _c(255, 110, 100), scale=0.05)
        self._quit_btn.reparentTo(self.bottom_right)

        self._edge_nodes = [
            self._profile_btn, self.tip_label, self._howto_btn,
            self._settings_btn, self._start_btn, self._quit_btn
        ]

        self._howto_panel = self._build_howto()
        self._howto_panel.hide()

        self._settings_panel = self._build_settings()
        self._settings_panel.hide()
        
        self._play_panel = self._build_play()
        self._play_panel.hide()
        
        self._profile_panel = self._build_profile()
        self._profile_panel.hide()

    def _build_howto(self):
        panel = DirectFrame(
            parent=self.root,
            frameColor=_c(8, 10, 20, 0.97),
            frameSize=(-1.8, 1.8, -1.05, 1.05),
            pos=(0, 0, 0),
            sortOrder=20,
        )

        _label(panel, "HOW TO PLAY",
               pos=(0, 0, 0.88), scale=0.10,
               fg=_c(80, 240, 230))

        sep = DirectFrame(
            parent=panel,
            frameColor=_c(80, 240, 230, 0.3),
            frameSize=(-0.5, 0.5, -0.001, 0.001),
            pos=(0, 0, 0.78),
        )

        col_left_x = -1.55
        col_right_x = 0.15

        _label(panel, "HIDERS",
               pos=(col_left_x, 0, 0.68), scale=0.058,
               fg=_c(100, 220, 130), align=TextNode.ALeft)
        _label(panel, (
            "Morph into everyday objects to hide\n"
            "Complete objectives while staying hidden\n"
            "Avoid the Hunter's scanner and blaster\n"
            "Stay still to regenerate morph energy\n"
            "Taunt hunters for bonus XP (risky!)"
        ), pos=(col_left_x, 0, 0.58), scale=0.042,
               fg=_c(200, 215, 218), align=TextNode.ALeft)

        _label(panel, "HUNTERS",
               pos=(col_right_x, 0, 0.68), scale=0.058,
               fg=_c(220, 100, 100), align=TextNode.ALeft)
        _label(panel, (
            "Find disguised Hiders among objects\n"
            "Use your Scanner to detect nearby Hiders\n"
            "Shoot your weapon to eliminate Hiders\n"
            "Watch for movement - objects don't move!"
        ), pos=(col_right_x, 0, 0.58), scale=0.042,
               fg=_c(200, 215, 218), align=TextNode.ALeft)

        _label(panel, "CONTROLS",
               pos=(col_left_x, 0, 0.18), scale=0.058,
               fg=_c(240, 190, 70), align=TextNode.ALeft)

        controls = (
            "WASD ............... Move\n"
            "Mouse .............. Look Around\n"
            "Shift .............. Sprint\n"
            "Space .............. Jump\n"
            "ESC ................ Pause\n"
        )
        _label(panel, controls,
               pos=(col_left_x, 0, 0.08), scale=0.040,
               fg=_c(190, 200, 205), align=TextNode.ALeft)

        _label(panel, "ROLE ACTIONS",
               pos=(col_right_x, 0, 0.18), scale=0.058,
               fg=_c(240, 190, 70), align=TextNode.ALeft)

        actions = (
            "1-9 ............... Morph (Hider)\n"
            "F / RMB ........... Lock Rotation (Hider)\n"
            "C ................. Toggle Camera (Hider)\n"
            "T ................. Taunt (Hider)\n"
            "E ................. Interact (Hider)\n"
            "LMB ............... Fire Blaster (Hunter)\n"
            "Q ................. Scanner (Hunter)\n"
            "L ................. Flashlight (Hunter)"
        )
        _label(panel, actions,
               pos=(col_right_x, 0, 0.08), scale=0.040,
               fg=_c(190, 200, 205), align=TextNode.ALeft)

        _label(panel, "GAME PHASES",
               pos=(col_left_x, 0, -0.38), scale=0.055,
               fg=_c(180, 140, 220), align=TextNode.ALeft)
        _label(panel, (
            "Lobby -> Role Assign -> Countdown -> Hiding Phase -> Hunting Phase -> Results"
        ), pos=(col_left_x, 0, -0.48), scale=0.040,
               fg=_c(180, 190, 195), align=TextNode.ALeft)

        _label(panel, "OBJECTIVES",
               pos=(col_left_x, 0, -0.60), scale=0.055,
               fg=_c(240, 160, 60), align=TextNode.ALeft)
        _label(panel, (
            "Classic: Hiders survive the timer to win\n"
            "Object Rush: Complete objectives to win\n"
            "Infection: Eliminated hiders become hunters"
        ), pos=(col_left_x, 0, -0.70), scale=0.040,
               fg=_c(180, 190, 195), align=TextNode.ALeft)

        _menu_btn(panel, "BACK", (0, 0, -0.92), self._close_howto,
                  _c(80, 240, 230), scale=0.060, width=3.0)

        return panel

    def _build_play(self):
        panel = DirectFrame(
            parent=self.root,
            frameColor=_c(15, 20, 30, 0.95),
            frameSize=(-0.6, 0.6, -0.5, 0.5),
            pos=(0, 0, 0),
            sortOrder=30,
        )
        _label(panel, "PLAY", pos=(0, 0, 0.35), scale=0.08, fg=_c(80, 240, 230))
        _menu_btn(panel, "HOST GAME", (0, 0, 0.1), self._do_host, _c(220, 235, 238), _c(80, 240, 230))
        _menu_btn(panel, "JOIN GAME", (0, 0, -0.1), self._do_join, _c(220, 235, 238), _c(80, 240, 230))
        _menu_btn(panel, "CANCEL", (0, 0, -0.35), self._close_start, _c(225, 140, 140), _c(255, 110, 100))
        return panel
        
    def _build_profile(self):
        panel = DirectFrame(
            parent=self.root,
            frameColor=_c(8, 10, 20, 0.97),
            frameSize=(-0.8, 0.8, -0.8, 0.8),
            pos=(0, 0, 0),
            sortOrder=30,
        )
        _label(panel, "PROFILE", pos=(0, 0, 0.65), scale=0.1, fg=_c(80, 240, 230))
        
        _label(panel, "PLAYER NAME", pos=(-0.4, 0, 0.4), scale=0.05, fg=_c(200, 200, 200), align=TextNode.ALeft)
        self.profile_name = DirectEntry(parent=panel, initialText="Player", scale=0.05, pos=(-0.4, 0, 0.3), width=10, frameColor=_c(30, 30, 40), text_fg=_c(255,255,255))
        from client.profile import get_profile_name
        saved_name = get_profile_name()
        if saved_name:
            self.profile_name.enterText(saved_name)
        
        stats = [
            ("LEVEL", "1"),
            ("GAMES PLAYED", "0"),
            ("WINS", "0"),
            ("LOSSES", "0"),
            ("WIN RATE", "0.0%")
        ]
        
        self._stat_labels = {}
        y = 0.1
        for title, val in stats:
            _label(panel, title, pos=(-0.4, 0, y), scale=0.045, fg=_c(150, 150, 150), align=TextNode.ALeft)
            lbl = _label(panel, val, pos=(0.4, 0, y), scale=0.045, fg=_c(200, 220, 220), align=TextNode.ARight)
            self._stat_labels[title] = lbl
            y -= 0.15
            
        _menu_btn(panel, "SAVE", (-0.3, 0, -0.65), self._close_profile, _c(80, 240, 230), scale=0.06)
        _menu_btn(panel, "CLOSE", (0.3, 0, -0.65), self._close_profile, _c(225, 140, 140), scale=0.06)
        
        return panel

    def _build_settings(self):
        panel = DirectFrame(
            parent=self.root,
            frameColor=_c(8, 10, 20, 0.97),
            frameSize=(-1.2, 1.2, -1.05, 1.05),
            pos=(0, 0, 0),
            sortOrder=20,
        )

        _label(panel, "SETTINGS", pos=(0, 0, 0.82), scale=0.10, fg=_c(80, 240, 230))

        sep = DirectFrame(
            parent=panel,
            frameColor=_c(80, 240, 230, 0.3),
            frameSize=(-0.5, 0.5, -0.001, 0.001),
            pos=(0, 0, 0.72),
        )

        _label(panel, "BRIGHTNESS", pos=(0, 0, 0.45), scale=0.055, fg=_c(220, 225, 228))
        self._slider_brightness = DirectSlider(
            parent=panel, pos=(0, 0, 0.35), scale=0.5,
            value=1.0, range=(0.1, 2.0),
            thumb_frameColor=_c(80, 240, 230),
            frameColor=_c(20, 24, 38)
        )

        _label(panel, "MASTER VOLUME", pos=(0, 0, 0.15), scale=0.055, fg=_c(220, 225, 228))
        self._slider_audio = DirectSlider(
            parent=panel, pos=(0, 0, 0.05), scale=0.5,
            value=1.0, range=(0.0, 1.0),
            thumb_frameColor=_c(80, 240, 230),
            frameColor=_c(20, 24, 38)
        )

        _label(panel, "MOUSE SENSITIVITY", pos=(0, 0, -0.15), scale=0.055, fg=_c(220, 225, 228))
        self._slider_mouse = DirectSlider(
            parent=panel, pos=(0, 0, -0.25), scale=0.5,
            value=40.0, range=(10.0, 100.0),
            thumb_frameColor=_c(80, 240, 230),
            frameColor=_c(20, 24, 38)
        )

        _menu_btn(panel, "BACK", (0, 0, -0.92), self._close_settings,
                  _c(80, 240, 230), scale=0.060, width=3.0)

        return panel

    def _prev_char(self):
        self.char_idx -= 1
        if self.char_idx < 1: self.char_idx = 10
        self.char_name_label["text"] = f"Character {self.char_idx}"
        self.on_char_change(self.char_idx)
        
    def _next_char(self):
        self.char_idx += 1
        if self.char_idx > 10: self.char_idx = 1
        self.char_name_label["text"] = f"Character {self.char_idx}"
        self.on_char_change(self.char_idx)

    def _do_start(self): self._play_panel.show()
    def _close_start(self): self._play_panel.hide()
    
    def _do_profile(self): 
        from game.stats_db import StatsDB
        from game.progression import get_level
        from client.profile import get_profile_id
        
        profile_id = get_profile_id()
        db = StatsDB()
        stats = db.get_stats(profile_id)
        
        if stats:
            xp = stats.get("total_xp", 0)
            level = get_level(xp)
            played = stats.get("rounds_played", 0)
            wins = stats.get("rounds_won", 0)
            losses = played - wins
            win_rate = (wins / played * 100) if played > 0 else 0.0
            
            self._stat_labels["LEVEL"]["text"] = f"{level}  (XP: {xp})"
            self._stat_labels["GAMES PLAYED"]["text"] = str(played)
            self._stat_labels["WINS"]["text"] = str(wins)
            self._stat_labels["LOSSES"]["text"] = str(losses)
            self._stat_labels["WIN RATE"]["text"] = f"{win_rate:.1f}%"
        else:
            self._stat_labels["LEVEL"]["text"] = "1  (XP: 0)"
            self._stat_labels["GAMES PLAYED"]["text"] = "0"
            self._stat_labels["WINS"]["text"] = "0"
            self._stat_labels["LOSSES"]["text"] = "0"
            self._stat_labels["WIN RATE"]["text"] = "0.0%"
            
        self._profile_panel.show()
    def _close_profile(self):
        from client.profile import set_profile_name
        set_profile_name(self.profile_name.get())
        self._profile_panel.hide()

    def _do_host(self): 
        self._play_panel.hide()
        self.on_host(self.profile_name.get())
    def _do_join(self): 
        self._play_panel.hide()
        self.on_join(self.profile_name.get())
    def _do_howto(self): self._howto_panel.show()
    def _close_howto(self): self._howto_panel.hide()
    def _do_settings(self): self._settings_panel.show()
    def _close_settings(self): self._settings_panel.hide()

    def show(self):   
        self.root.show()
        for node in self._edge_nodes: node.show()
        if hasattr(self, '_bg_img') and self._bg_img:
            self._bg_img.show()
        # Initialize character on show
        self.on_char_change(self.char_idx)
        
    def hide(self):
        self.root.hide()
        for node in self._edge_nodes: node.hide()
        if hasattr(self, '_bg_img') and self._bg_img:
            self._bg_img.hide()
    
    def update(self):
        if hasattr(self, '_bg_img') and self._bg_img:
            import math
            fov = builtins.base.camLens.getFov()
            dist = 200
            half_w = math.tan(math.radians(fov[0] / 2.0)) * dist
            half_h = math.tan(math.radians(fov[1] / 2.0)) * dist
            self._bg_img.setScale(half_w, 1, half_h)

        self.tip_idx += 1
        if self.tip_idx % 300 == 0:  # ~every 5 seconds at 60fps
            tip = self.tips[(self.tip_idx // 300) % len(self.tips)]
            self.tip_label["text"] = tip
            
        if hasattr(self, '_showcase_actor') and self._showcase_actor and builtins.base.mouseWatcherNode.hasMouse():
            m_x = builtins.base.mouseWatcherNode.getMouseX()
            from panda3d.core import MouseButton
            if builtins.base.mouseWatcherNode.isButtonDown(MouseButton.one()):
                if not hasattr(self, '_last_mx'):
                    self._last_mx = m_x
                dx = m_x - self._last_mx
                # Inverted: positive dx rotates right instead of left
                self._showcase_actor.setH(self._showcase_actor.getH() + dx * 200)
                self._last_mx = m_x
            else:
                if hasattr(self, '_last_mx'):
                    del self._last_mx

    def input(self, key): pass


class ConnectDialog:
    def __init__(self, on_submit, on_cancel, mode="join", player_name="Player"):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.mode = mode
        self._udp_sock = None
        self._servers = set()
        self._task = None

        self.root = builtins.base.aspect2d.attachNewNode("connect_dialog")

        DirectFrame(
            parent=self.root,
            frameColor=_c(8, 10, 20, 0.97),
            frameSize=(-1.5, 1.5, -1.05, 1.05),
            pos=(0, 0, 0),
            sortOrder=0,
        )

        title = "HOST GAME" if mode == "host" else "JOIN GAME"
        _label(self.root, title,
               pos=(0, 0, 0.82), scale=0.12, fg=_c(80, 240, 230))

        subtitle = ("CREATE A LOCAL MULTIPLAYER LOBBY"
                    if mode == "host"
                    else "CONNECT TO A MORPH HUNT SERVER")
        _label(self.root, subtitle,
               pos=(0, 0, 0.65), scale=0.046, fg=_c(140, 185, 190))

        _label(self.root, "PLAYER NAME",
               pos=(-0.55, 0, 0.45), scale=0.050, fg=_c(110, 220, 215),
               align=TextNode.ALeft)
        
        self._name_label = _label(self.root, player_name, 
               pos=(-0.55, 0, 0.35), scale=0.055, fg=_c(180, 200, 200),
               align=TextNode.ALeft)

        if mode == "join":
            _label(self.root, "DISCOVERED SERVERS:",
                   pos=(-0.55, 0, 0.12), scale=0.050, fg=_c(110, 220, 215),
                   align=TextNode.ALeft)
                   
            from direct.gui.DirectScrolledList import DirectScrolledList
            self.server_list = DirectScrolledList(
                parent=self.root,
                decButton_pos=(0.35, 0, 0.5),
                decButton_text="^",
                decButton_text_scale=0.04,
                decButton_borderWidth=(0.005, 0.005),
                incButton_pos=(0.35, 0, -0.02),
                incButton_text="v",
                incButton_text_scale=0.04,
                incButton_borderWidth=(0.005, 0.005),
                frameSize=(-0.4, 0.4, -0.05, 0.55),
                frameColor=_c(20, 24, 38),
                pos=(-0.15, 0, -0.3),
                numItemsVisible=5,
                forceHeight=0.1,
                itemFrame_frameColor=(0,0,0,0),
                itemFrame_pos=(0, 0, 0.4),
            )
            
            _menu_btn(self.root, "CONNECT TO SELECTED", (0, 0, -0.45), self._submit,
                      _c(80, 240, 230))
                      
            import socket
            self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_sock.setblocking(False)
            try:
                self._udp_sock.bind(('', 5556))
            except Exception:
                pass
            self._task = builtins.base.taskMgr.add(self._poll_servers, "poll_servers")
            
        else:
            _menu_btn(self.root, "START HOSTING", (0, 0, -0.34), self._submit,
                      _c(80, 240, 230))
                      
        _menu_btn(self.root, "CANCEL", (0, 0, -0.54 if mode == "join" else -0.54), self._cancel,
                  _c(215, 120, 120))

        self._status = _label(self.root, "",
                              pos=(0, 0, -0.76), scale=0.046,
                              fg=_c(170, 190, 195))

    def _poll_servers(self, task):
        if not self._udp_sock: return task.done
        try:
            while True:
                data, addr = self._udp_sock.recvfrom(1024)
                if data == b"MORPH_HUNT_SERVER" and addr[0] not in self._servers:
                    self._servers.add(addr[0])
                    btn = _menu_btn(None, f"Server ({addr[0]})", (0,0,0), 
                                  lambda a=addr[0]: self.server_list.selectListItem(btn), 
                                  _c(230, 230, 230), hover_fg=_c(80, 240, 230))
                    # Store address on the button for retrieval
                    btn.server_addr = addr[0]
                    self.server_list.addItem(btn)
        except BlockingIOError:
            pass
        except Exception:
            pass
        return task.cont

    def _submit(self):
        if self.mode == "join":
            # Get selected server
            selected = self.server_list.getSelectedIndex()
            if selected < 0 or selected >= len(self.server_list['items']):
                self._status["text"] = "PLEASE SELECT A SERVER"
                return
            btn = self.server_list['items'][selected]
            addr = getattr(btn, 'server_addr', '127.0.0.1')
            addr = f"{addr}:5555"
            self._status["text"] = "CONNECTING..."
        else:
            addr = "5555"
            self._status["text"] = "STARTING SERVER..."
            
        self.on_submit(addr)

    def _cancel(self): self.on_cancel()

    def show(self):    self.root.show()
    def hide(self):    self.root.hide()
    def update(self):  pass
    def input(self, key): pass

    def destroy(self):
        if self._task:
            builtins.base.taskMgr.remove(self._task)
        if self._udp_sock:
            self._udp_sock.close()
        self.root.removeNode()