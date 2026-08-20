"""
Lobby Screen — Panda3D DirectGui, fixed render-bin ordering.
Uses DirectLabel for all static text, plain NodePath root container.
"""
import builtins

from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode, LVecBase4f

from config import settings


def _c(r, g, b, a=1.0):
    return LVecBase4f(r / 255, g / 255, b / 255, a)


def _label(parent, text, pos, scale, fg, align=TextNode.ALeft):
    return DirectLabel(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text_align=align,
        frameColor=(0, 0, 0, 0),
        relief=None,
        pos=pos,
    )


def _btn(parent, text, pos, command, fg, hover_fg=None, scale=0.065):
    hfg = hover_fg or fg
    return DirectButton(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text0_fg=fg,
        text1_fg=_c(255, 255, 255),
        text2_fg=hfg,
        text3_fg=_c(70, 70, 70),
        frameColor=(
            _c(28, 30, 42),
            _c(55, 58, 80),
            _c(42, 45, 62),
            _c(20, 20, 30),
        ),
        frameSize=(-3.4, 3.4, -0.5, 0.85),
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

        self._map_idx  = 0
        self._mode_idx = 0
        self.is_host   = False

        self.root = builtins.base.aspect2d.attachNewNode("lobby_root")

        # Background
        DirectFrame(
            parent=self.root,
            frameColor=_c(10, 12, 20),
            frameSize=(-2, 2, -1.2, 1.2),
            sortOrder=0,
        )

        # Title
        _label(self.root, "LOBBY",
               pos=(0, 0, 0.88), scale=0.13,
               fg=_c(240, 210, 90), align=TextNode.ACenter)

        # Player list section
        _label(self.root, "PLAYERS",
               pos=(-1.55, 0, 0.68), scale=0.068, fg=_c(80, 220, 240))
        self._player_label = _label(
            self.root, "(waiting for players...)",
            pos=(-1.55, 0, 0.56), scale=0.053, fg=_c(220, 220, 220))

        # Map / Mode labels
        self._map_label = _label(
            self.root, "Map: house",
            pos=(0.10, 0, 0.68), scale=0.065, fg=_c(80, 220, 240))
        self._mode_label = _label(
            self.root, "Mode: classic",
            pos=(0.10, 0, 0.54), scale=0.065, fg=_c(80, 220, 240))

        # Cycle & Bot buttons
        _btn(self.root, "CYCLE MAP",  (1.05, 0, 0.44), self._cycle_map,
             _c(220, 232, 235), _c(75, 235, 225))
        _btn(self.root, "CYCLE MODE", (1.05, 0, 0.24), self._cycle_mode,
             _c(220, 232, 235), _c(75, 235, 225))
        self._add_bot_btn = _btn(self.root, "+ ADD BOT",   (1.05, 0, 0.04), self._add_bot,
             _c(235, 170, 70), _c(255, 210, 90))

        # Action buttons
        _btn(self.root, "READY",      (-0.65, 0, -0.62), self._toggle_ready,
             _c(100, 220, 150), _c(130, 255, 175))
        self._start_btn = _btn(
            self.root, "START GAME",  (0.0, 0, -0.84), self._start,
            _c(220, 190, 110), _c(255, 225, 150))
        _btn(self.root, "LEAVE",      (0.80, 0, -0.62), self.on_leave,
             _c(220, 150, 150), _c(255, 180, 180))

    def _add_bot(self):
        if self.is_host and self.on_add_bot:
            self.on_add_bot()

    # ------------------------------------------------------------------
    def _cycle_map(self):
        self._map_idx = (self._map_idx + 1) % len(settings.LEVELS)
        self.on_set_map(settings.LEVELS[self._map_idx])

    def _cycle_mode(self):
        self._mode_idx = (self._mode_idx + 1) % len(settings.GAME_MODES)
        self.on_set_mode(settings.GAME_MODES[self._mode_idx])

    def _toggle_ready(self):
        self.on_ready_toggle()

    def _start(self):
        if self.is_host:
            self.on_start()

    # ------------------------------------------------------------------
    def update_state(self, players, map_key, mode, host_id, my_id):
        lines = []
        for p in players:
            tag   = " (HOST)" if p.get("player_id") == host_id else ""
            ready = "READY"   if p.get("ready")                else "not ready"
            you   = " <-- you" if p.get("player_id") == my_id  else ""
            lines.append(f"{p.get('name')}{tag} - {ready}{you}")

        self._player_label["text"] = (
            "\n".join(lines) if lines else "(waiting for players...)"
        )
        self._map_label["text"]  = f"Map: {map_key}"
        self._mode_label["text"] = f"Mode: {mode}"
        self.is_host = (host_id == my_id)

        if self.is_host:
            self._start_btn["text_fg"]   = _c(220, 190, 110)
            self._start_btn["text0_fg"]  = _c(220, 190, 110)
        else:
            self._start_btn["text_fg"]   = _c(80, 80, 80)
            self._start_btn["text0_fg"]  = _c(80, 80, 80)

    # ------------------------------------------------------------------
    def show(self):    self.root.show()
    def hide(self):    self.root.hide()
    def update(self):  pass
    def input(self, key): pass