"""
In-game HUD — Panda3D DirectGui, fixed render-bin ordering.
Uses DirectLabel for all text (shares bin with DirectGui), CardMaker for bars.
"""
import builtins

from direct.gui.DirectGui import DirectFrame, DirectLabel
from panda3d.core import TextNode, LVecBase4f, CardMaker, NodePath


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


def _bar(parent, x, z, w, h, bg_col, fg_col):
    """Two flat quads: background and foreground progress bar."""
    cm = CardMaker("bar")
    cm.setFrame(0, w, -h / 2, h / 2)

    bg = parent.attachNewNode(cm.generate())
    bg.setPos(x, 0, z)
    bg.setColor(bg_col)
    bg.setBin("gui-popup", 0)
    bg.setDepthTest(False)
    bg.setDepthWrite(False)

    fg = parent.attachNewNode(cm.generate())
    fg.setPos(x, 0, z)
    fg.setColor(fg_col)
    fg.setBin("gui-popup", 1)
    fg.setDepthTest(False)
    fg.setDepthWrite(False)

    return bg, fg


class HUD:
    def __init__(self, aspect2d=None):
        a2d = aspect2d or builtins.base.aspect2d
        self.root = a2d.attachNewNode("hud_root")
        self.root.hide()

        # ---- Role -------------------------------------------------------
        self._role = _label(self.root, "",
                            pos=(-1.55, 0, 0.88), scale=0.074,
                            fg=_c(240, 210, 60))

        # ---- Timer ------------------------------------------------------
        self._timer = _label(self.root, "--:--",
                             pos=(0, 0, 0.88), scale=0.095,
                             fg=_c(255, 255, 255), align=TextNode.ACenter)
        self._phase = _label(self.root, "",
                             pos=(0, 0, 0.78), scale=0.052,
                             fg=_c(180, 180, 180), align=TextNode.ACenter)

        # ---- Player count -----------------------------------------------
        self._players = _label(self.root, "",
                               pos=(1.55, 0, 0.88), scale=0.052,
                               fg=_c(220, 220, 220), align=TextNode.ARight)

        # ---- Health bar -------------------------------------------------
        self._health_bg, self._health_fg = _bar(
            self.root, -1.55, -0.62, 0.55, 0.040,
            _c(40, 40, 40), _c(220, 60, 60))
        self._health_lbl = _label(self.root, "HEALTH",
                                  pos=(-1.55, 0, -0.54), scale=0.046,
                                  fg=_c(210, 210, 210))

        # ---- Energy bar (hider only) ------------------------------------
        self._energy_bg, self._energy_fg = _bar(
            self.root, -1.55, -0.74, 0.55, 0.040,
            _c(40, 40, 40), _c(90, 200, 230))
        self._energy_lbl = _label(self.root, "MORPH ENERGY",
                                  pos=(-1.55, 0, -0.66), scale=0.046,
                                  fg=_c(210, 210, 210))
        self._energy_bg.hide()
        self._energy_fg.hide()
        self._energy_lbl.hide()

        # ---- Scanner status (hunter only) --------------------------------
        self._scanner = _label(self.root, "",
                               pos=(1.55, 0, -0.62), scale=0.050,
                               fg=_c(80, 220, 215), align=TextNode.ARight)
        self._scanner.hide()

        # ---- Objectives -------------------------------------------------
        self._objectives = _label(self.root, "",
                                  pos=(-1.55, 0, 0.04), scale=0.056,
                                  fg=_c(235, 160, 60))

        # ---- Clue / chat log --------------------------------------------
        self._clue_log = _label(self.root, "",
                                pos=(1.55, 0, 0.04), scale=0.048,
                                fg=_c(150, 220, 255), align=TextNode.ARight)
        self._clue_lines = []

        # ---- Transform hint (bottom) -------------------------------------
        self._hint = _label(self.root, "",
                            pos=(0, 0, -0.92), scale=0.046,
                            fg=_c(200, 200, 200), align=TextNode.ACenter)

        # ---- Crosshair --------------------------------------------------
        self._crosshair = _label(self.root, "+",
                                 pos=(0, 0, 0), scale=0.06,
                                 fg=_c(255, 255, 255, 0.7),
                                 align=TextNode.ACenter)

    # ------------------------------------------------------------------
    def set_role(self, role):
        self._role["text"] = f"ROLE: {role.upper()}"
        is_hider  = (role == "hider")
        is_hunter = (role == "hunter")
        for n in (self._energy_bg, self._energy_fg, self._energy_lbl):
            n.show() if is_hider else n.hide()
        self._scanner.show() if is_hunter else self._scanner.hide()

    def set_timer(self, phase, time_left):
        self._phase["text"] = phase.replace("_", " ").upper()
        if time_left and time_left > 0:
            m, s = divmod(int(time_left), 60)
            self._timer["text"] = f"{m:02d}:{s:02d}"
        else:
            self._timer["text"] = "--:--"

    def set_players(self, alive_hiders, total_hunters):
        self._players["text"] = (
            f"Hiders left: {alive_hiders}  |  Hunters: {total_hunters}"
        )

    def set_energy(self, value, max_value=100):
        pct = max(0.0, min(1.0, value / max_value))
        self._energy_fg.setScale(pct, 1, 1)

    def set_health(self, value, max_value=100):
        pct = max(0.0, min(1.0, value / max_value))
        self._health_fg.setScale(pct, 1, 1)

    def set_scanner_status(self, charges, max_charges, cooldown_left):
        if cooldown_left > 0:
            self._scanner["text"] = (
                f"SCANNER: recharging ({cooldown_left:.1f}s) [{charges}/{max_charges}]"
            )
        else:
            self._scanner["text"] = f"SCANNER: ready [{charges}/{max_charges}]"

    def set_objectives(self, completed, required):
        self._objectives["text"] = (
            f"Objectives: {completed}/{required}" if required > 0 else ""
        )

    def push_clue(self, clue):
        self._clue_lines.append(clue)
        self._clue_lines = self._clue_lines[-5:]
        self._clue_log["text"] = "\n".join(self._clue_lines)

    def set_transform_hint(self, text):
        self._hint["text"] = text

    def show(self):  self.root.show()
    def hide(self):  self.root.hide()
