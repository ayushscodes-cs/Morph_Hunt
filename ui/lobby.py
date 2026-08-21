from __future__ import annotations
import os
import builtins

from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode, LVecBase4f, Filename, CardMaker

from config import settings


def _c(r, g, b, a=1.0):
    return LVecBase4f(r / 255, g / 255, b / 255, a)


def _label(parent, text, pos, scale, fg, align=TextNode.ALeft, shadow=None):
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


def _btn(parent, text, pos, command, fg, hover_fg=None, scale=0.060, width=3.8):
    hfg = hover_fg or fg
    return DirectButton(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text0_fg=fg,
        text1_fg=_c(255, 255, 255),
        text2_fg=_c(255, 255, 255),
        text3_fg=_c(65, 65, 65),
        text_shadow=(0, 0, 0, 1.0),
        frameColor=( (0,0,0,0), (0,0,0,0), (0,0,0,0), (0,0,0,0) ),
        frameSize=(-width, width, -0.5, 0.85),
        relief=1,
        pos=pos,
        command=command,
    )


class LobbyScreen:
    def __init__(self, on_ready_toggle, on_set_map, on_set_mode, on_start, on_leave, on_add_bot=None):
        self.on_ready_toggle = on_ready_toggle
        self.on_set_map      = on_set_map
        self.on_set_mode     = on_set_mode
        self.on_start        = on_start
        self.on_leave        = on_leave
        self.on_add_bot      = on_add_bot

        self._mode_idx = 0
        self.is_host   = False
        self._my_ready = False
        self._player_count = 0
        self._host_ready = False

        self.root = builtins.base.aspect2d.attachNewNode("lobby_root")

        self._bg_img = None
        bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "lobby_bg.jpg")
        if os.path.exists(bg_path):
            try:
                tex = builtins.base.loader.loadTexture(Filename.fromOsSpecific(bg_path))
                if tex:
                    cm = CardMaker("lobby_bg_card")
                    cm.setFrame(-2.5, 2.5, -1.5, 1.5)
                    self._bg_img = self.root.attachNewNode(cm.generate())
                    self._bg_img.setTexture(tex)
                    self._bg_img.setColor(1, 1, 1, 1.0)
                    self._bg_img.setBin("background", 1)
                    self._bg_img.setDepthWrite(False)
                    self._bg_img.setDepthTest(False)
            except Exception:
                pass



        _label(self.root, "GAME LOBBY",
               pos=(0, 0, 0.88), scale=0.11,
               fg=_c(240, 215, 90), align=TextNode.ACenter,
               shadow=(0, 0, 0, 0.8))

        sep_top = DirectFrame(
            parent=self.root,
            relief=None,
            frameSize=(-0.4, 0.4, -0.001, 0.001),
            pos=(0, 0, 0.80),
        )

        player_panel = DirectFrame(
            parent=self.root,
            relief=None,
            frameSize=(-1.65, -0.05, -0.40, 0.72),
            pos=(0, 0, 0),
            sortOrder=1,
        )

        _label(self.root, "PLAYERS",
               pos=(-1.60, 0, 0.68), scale=0.058,
               fg=_c(80, 225, 240))

        self._player_count_label = _label(
            self.root, "0 / 8",
            pos=(-0.10, 0, 0.68), scale=0.048,
            fg=_c(160, 170, 175), align=TextNode.ARight, shadow=(0,0,0,0.8))

        self._player_label = _label(
            self.root, "Waiting for players...",
            pos=(-1.58, 0, 0.58), scale=0.048,
            fg=_c(210, 215, 218), shadow=(0,0,0,0.8))

        info_panel = DirectFrame(
            parent=self.root,
            frameColor=(0, 0, 0, 0),
            frameSize=(0.10, 1.65, -0.25, 0.72),
            pos=(0, 0, 0),
            sortOrder=1,
        )

        _label(self.root, "MAP",
               pos=(0.15, 0, 0.68), scale=0.050,
               fg=_c(80, 225, 240))
        self._map_label = _label(
            self.root, "House",
            pos=(0.15, 0, 0.56), scale=0.055,
            fg=_c(220, 225, 228))

        _label(self.root, "Large residential property with basement and terrace",
               pos=(0.15, 0, 0.46), scale=0.036,
               fg=_c(180, 190, 195), shadow=(0,0,0,0.8))

        _label(self.root, "MODE",
               pos=(0.15, 0, 0.32), scale=0.050,
               fg=_c(80, 225, 240))
        self._mode_label = _label(
            self.root, "Classic",
            pos=(0.15, 0, 0.20), scale=0.055,
            fg=_c(220, 225, 228))

        self._mode_desc = _label(
            self.root, "Hiders survive the timer to win",
            pos=(0.15, 0, 0.10), scale=0.036,
            fg=_c(180, 190, 195), shadow=(0,0,0,0.8))

        _btn(self.root, "CYCLE MODE", (1.05, 0, -0.02), self._cycle_mode,
             _c(200, 215, 220), _c(80, 240, 230), scale=0.050, width=3.0)

        if on_add_bot:
            self._add_bot_btn = _btn(
                self.root, "+ ADD BOT", (1.05, 0, -0.20), self._add_bot,
                _c(240, 180, 75), _c(255, 215, 95), scale=0.050, width=3.0)

        self._status_label = _label(
            self.root, "",
            pos=(0, 0, -0.52), scale=0.052,
            fg=_c(255, 180, 80), align=TextNode.ACenter, shadow=(0,0,0,0.8))

        self._ready_btn = _btn(
            self.root, "READY", (-0.80, 0, -0.76), self._toggle_ready,
            _c(110, 225, 155), _c(140, 255, 180), width=3.2)

        self._start_btn = _btn(
            self.root, "START GAME", (0.0, 0, -0.76), self._start,
            _c(240, 210, 120), _c(255, 235, 160), scale=0.070, width=4.5)

        _btn(self.root, "LEAVE", (0.85, 0, -0.76), self.on_leave,
             _c(225, 155, 155), _c(255, 185, 185), width=3.2)

    def _add_bot(self):
        if self.is_host and self.on_add_bot:
            self.on_add_bot()

    def _cycle_mode(self):
        self._mode_idx = (self._mode_idx + 1) % len(settings.GAME_MODES)
        self.on_set_mode(settings.GAME_MODES[self._mode_idx])

    def _toggle_ready(self):
        self._my_ready = not self._my_ready
        self.on_ready_toggle()

    def _start(self):
        if self.is_host:
            self.on_start()

    def update_state(self, players, map_key, mode, host_id, my_id):
        lines = []
        self._player_count = len(players)
        self._host_ready = False

        for p in players:
            pid = p.get("player_id")
            name = p.get("name", "???")

            tags = []
            if pid == host_id:
                tags.append("HOST")
            if pid == my_id:
                tags.append("YOU")

            tag_str = f" [{', '.join(tags)}]" if tags else ""

            ready = p.get("ready", False)
            ready_str = "[OK] READY" if ready else "[X] NOT READY"

            if pid == host_id and ready:
                self._host_ready = True

            lines.append(f"  {name}{tag_str}  -  {ready_str}")

        self._player_label["text"] = (
            "\n".join(lines) if lines else "Waiting for players..."
        )

        self._player_count_label["text"] = f"{self._player_count} / {settings.MAX_PLAYERS}"

        self._map_label["text"] = map_key.replace("_", " ").title()
        self._mode_label["text"] = mode.replace("_", " ").title()

        mode_descs = {
            "classic": "Hiders survive the timer to win",
            "object_rush": "Complete objectives before time runs out",
            "infection": "Eliminated hiders become hunters",
        }
        self._mode_desc["text"] = mode_descs.get(mode, "")

        self.is_host = (host_id == my_id)

        status = ""
        can_start = True

        if self._player_count < settings.MIN_PLAYERS_TO_START:
            status = f"Need at least {settings.MIN_PLAYERS_TO_START} players"
            can_start = False
        elif self.is_host and not self._host_ready:
            status = "Host must be ready"
            can_start = False
        elif self.is_host:
            status = "Ready to start!"
        elif not self.is_host:
            status = "Waiting for host to start..."

        self._status_label["text"] = status

        if self.is_host and can_start:
            self._start_btn["text_fg"] = _c(240, 210, 120)
            self._start_btn["text0_fg"] = _c(240, 210, 120)
            self._start_btn["state"] = 1
        elif self.is_host:
            self._start_btn["text_fg"] = _c(100, 100, 100)
            self._start_btn["text0_fg"] = _c(100, 100, 100)
            self._start_btn["state"] = 0
        else:
            self._start_btn["text_fg"] = _c(70, 70, 70)
            self._start_btn["text0_fg"] = _c(70, 70, 70)
            self._start_btn["state"] = 0

        if self._my_ready:
            self._ready_btn["text"] = "UNREADY"
            self._ready_btn["text_fg"] = _c(255, 180, 80)
            self._ready_btn["text0_fg"] = _c(255, 180, 80)
        else:
            self._ready_btn["text"] = "READY"
            self._ready_btn["text_fg"] = _c(110, 225, 155)
            self._ready_btn["text0_fg"] = _c(110, 225, 155)

    def show(self):
        self._my_ready = False
        self.root.show()

    def hide(self):    self.root.hide()
    def update(self):  pass
    def input(self, key): pass