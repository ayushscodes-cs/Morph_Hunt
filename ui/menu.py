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
    hfg = hover_fg or fg
    return DirectButton(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text0_fg=fg,
        text1_fg=_c(255, 255, 255),
        text2_fg=_c(255, 255, 255), # Bright hover
        text3_fg=_c(80, 80, 80),
        text_shadow=(0, 0, 0, 1.0),
        frameColor=( (0,0,0,0), (0,0,0,0), (0,0,0,0), (0,0,0,0) ),
        frameSize=(-width, width, -0.55, 0.9),
        relief=1,
        pos=pos,
        command=command,
    )


class MainMenu:
    def __init__(self, on_host, on_join, on_quit):
        self.on_host = on_host
        self.on_join = on_join
        self.on_quit = on_quit

        self._aspect2d = builtins.base.aspect2d
        self.root = self._aspect2d.attachNewNode("main_menu")



        self._bg_img = None
        bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "menu_bg.jpg")
        if os.path.exists(bg_path):
            try:
                tex = builtins.base.loader.loadTexture(Filename.fromOsSpecific(bg_path))
                if tex:
                    cm = CardMaker("menu_bg_card")
                    cm.setFrame(-2.5, 2.5, -1.5, 1.5)
                    self._bg_img = self.root.attachNewNode(cm.generate())
                    self._bg_img.setTexture(tex)
                    self._bg_img.setColor(1, 1, 1, 1.0)
                    self._bg_img.setBin("background", 1)
                    self._bg_img.setDepthWrite(False)
                    self._bg_img.setDepthTest(False)
            except Exception:
                pass



        _label(self.root, "MORPH HUNT",
               pos=(0, 0, 0.72), scale=0.18,
               fg=_c(240, 245, 248),
               shadow=(0, 0, 0, 0.7))

        _label(self.root, "MAIN MENU",
               pos=(0, 0, 0.56), scale=0.065,
               fg=_c(220, 245, 255),
               shadow=(0, 0, 0, 0.8))

        _label(self.root, "\u2022  HIDE  \u2022  MORPH  \u2022  SURVIVE  \u2022",
               pos=(0, 0, 0.44), scale=0.048,
               fg=_c(240, 180, 70, 0.9),
               shadow=(0, 0, 0, 0.5))

        _menu_btn(self.root, "HOST GAME", (0, 0, 0.20), self._do_host,
                  _c(220, 235, 238), _c(80, 240, 230))

        _menu_btn(self.root, "JOIN GAME", (0, 0, 0.04), self._do_join,
                  _c(220, 235, 238), _c(80, 240, 230))

        self._howto_btn = _menu_btn(
            self.root, "HOW TO PLAY", (0, 0, -0.12), self._do_howto,
            _c(220, 235, 238), _c(80, 240, 230))

        self._settings_btn = _menu_btn(
            self.root, "SETTINGS", (0, 0, -0.28), self._do_settings,
            _c(220, 235, 238), _c(80, 240, 230))

        _menu_btn(self.root, "QUIT", (0, 0, -0.44), on_quit,
                  _c(225, 140, 140), _c(255, 110, 100))

        sep = DirectFrame(
            parent=self.root,
            frameColor=_c(80, 225, 220, 0.3),
            frameSize=(-0.3, 0.3, -0.001, 0.001),
            pos=(0, 0, -0.58),
            sortOrder=5,
        )

        _label(self.root, "LAN MULTIPLAYER",
               pos=(0, 0, -0.66), scale=0.038,
               fg=_c(100, 200, 205, 0.8))

        _label(self.root, "v1.0",
               pos=(0, 0, -0.72), scale=0.032,
               fg=_c(80, 160, 165, 0.6))

        _label(self.root, "\u00A9 2025 Morph Hunt",
               pos=(0, 0, -0.92), scale=0.030,
               fg=_c(60, 120, 125, 0.5))

        self._howto_panel = self._build_howto()
        self._howto_panel.hide()

        self._settings_panel = self._build_settings()
        self._settings_panel.hide()

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
            "Fire your Energy Blaster to eliminate\n"
            "Use your Flashlight in dark areas\n"
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

    def _do_host(self):  self.on_host()
    def _do_join(self):  self.on_join()
    def _do_howto(self): self._howto_panel.show()
    def _close_howto(self): self._howto_panel.hide()
    def _do_settings(self): self._settings_panel.show()
    def _close_settings(self): self._settings_panel.hide()

    def show(self):   self.root.show()
    def hide(self):   self.root.hide()
    def update(self): pass
    def input(self, key): pass


class ConnectDialog:
    def __init__(self, on_submit, on_cancel, mode="join"):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.mode = mode

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
               pos=(-0.55, 0, 0.48), scale=0.050, fg=_c(110, 220, 215),
               align=TextNode.ALeft)
        self._name_entry = DirectEntry(
            parent=self.root,
            initialText="Player",
            scale=0.058,
            pos=(-0.70, 0, 0.32),
            width=11,
            frameColor=_c(20, 24, 38),
            text_fg=_c(230, 230, 230),
            relief=1,
        )

        addr_label   = "SERVER ADDRESS" if mode == "join" else "SERVER PORT"
        addr_default = "127.0.0.1:5555" if mode == "join" else "5555"

        _label(self.root, addr_label,
               pos=(-0.55, 0, 0.12), scale=0.050, fg=_c(110, 220, 215),
               align=TextNode.ALeft)
        self._addr_entry = DirectEntry(
            parent=self.root,
            initialText=addr_default,
            scale=0.058,
            pos=(-0.70, 0, -0.04),
            width=11,
            frameColor=_c(20, 24, 38),
            text_fg=_c(230, 230, 230),
            relief=1,
        )

        submit_text = "JOIN SERVER" if mode == "join" else "START HOSTING"
        _menu_btn(self.root, submit_text, (0, 0, -0.34), self._submit,
                  _c(80, 240, 230))
        _menu_btn(self.root, "CANCEL", (0, 0, -0.54), self._cancel,
                  _c(215, 120, 120))

        self._status = _label(self.root, "",
                              pos=(0, 0, -0.76), scale=0.046,
                              fg=_c(170, 190, 195))

    def _submit(self):
        name = self._name_entry.get().strip() or "Player"
        addr = self._addr_entry.get().strip()
        self._status["text"] = ("STARTING SERVER..." if self.mode == "host"
                                else "CONNECTING...")
        self.on_submit(name, addr)

    def _cancel(self): self.on_cancel()

    def show(self):    self.root.show()
    def hide(self):    self.root.hide()
    def update(self):  pass
    def input(self, key): pass

    def destroy(self):
        self.root.removeNode()