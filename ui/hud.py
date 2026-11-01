"""
In-game HUD — Panda3D DirectGui, fixed render-bin ordering.
Uses DirectLabel for all text (shares bin with DirectGui), CardMaker for bars.
"""
import builtins

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton
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
            self.root, -1.55, -0.75, 0.55, 0.040,
            _c(40, 40, 40), _c(220, 60, 60))
        self._health_lbl = _label(self.root, "HEALTH",
                                  pos=(-1.55, 0, -0.69), scale=0.046,
                                  fg=_c(210, 210, 210))

        # ---- Energy bar (hider only) ------------------------------------
        self._energy_bg, self._energy_fg = _bar(
            self.root, -1.55, -0.90, 0.55, 0.040,
            _c(40, 40, 40), _c(90, 200, 230))
        self._energy_lbl = _label(self.root, "MORPH ENERGY",
                                  pos=(-1.55, 0, -0.84), scale=0.046,
                                  fg=_c(210, 210, 210))
        self._energy_bg.hide()
        self._energy_fg.hide()
        self._energy_lbl.hide()

        # ---- Scanner status (hunter only) --------------------------------
        self._scanner = _label(self.root, "",
                               pos=(1.55, 0, -0.62), scale=0.050,
                               fg=_c(80, 220, 215), align=TextNode.ARight)
        self._scanner.hide()

        # ---- Personal Tasks (Object Rush) -------------------------------
        self._task_title = _label(self.root, "Do the objectives:",
                                  pos=(-1.70, 0, 0.10), scale=0.05,
                                  fg=_c(255, 255, 255), align=TextNode.ALeft)
        self._task_labels = []
        for i in range(3):
            lbl = _label(self.root, "",
                         pos=(-1.70, 0, 0.04 - i * 0.06), scale=0.048,
                         fg=_c(235, 160, 60), align=TextNode.ALeft)
            self._task_labels.append(lbl)

        # ---- Clue / chat log --------------------------------------------
        self._clue_log = _label(self.root, "",
                                pos=(1.55, 0, 0.04), scale=0.048,
                                fg=_c(150, 220, 255), align=TextNode.ARight)
        self._clue_lines = []

        # ---- Transform hint (bottom) -------------------------------------
        self._hint = _label(self.root, "",
                            pos=(0, 0, -0.92), scale=0.046,
                            fg=_c(200, 200, 200), align=TextNode.ACenter)

        # ---- Hotbar -----------------------------------------------------
        self._hotbar_open = False
        
        # Toggle button
        self._hotbar_btn = DirectButton(
            parent=self.root,
            text="Props [M]",
            scale=0.045,
            text_fg=_c(220, 220, 220),
            frameColor=(0.1, 0.1, 0.15, 0.8),
            pos=(-1.5, 0, -0.55),
            command=self._toggle_hotbar,
            pad=(0.1, 0.1)
        )
        self._hotbar_btn.hide()
        
        self._hotbar_frame = DirectFrame(
            parent=self.root,
            frameColor=(0, 0, 0, 0.6),
            frameSize=(-0.25, 0.25, -0.45, 0.45),
            pos=(-1.5, 0, -0.05)
        )
        self._hotbar_frame.hide()
        self._hotbar_labels = []
        for i in range(9):
            lbl = _label(self._hotbar_frame, "",
                         pos=(-0.2, 0, 0.35 - i * 0.08), scale=0.04,
                         fg=_c(240, 240, 240), align=TextNode.ALeft)
            self._hotbar_labels.append(lbl)

        # Hunter weapons list
        self._hunter_weapons = []
        for i, wname in enumerate(["[0] Unarmed", "[1] Assault", "[2] Pistol", "[3] Shotgun", "[4] SMG"]):
            lbl = _label(self.root, wname,
                         pos=(1.55, 0, 0.7 - i * 0.06), scale=0.045,
                         fg=_c(150, 150, 150), align=TextNode.ARight)
            self._hunter_weapons.append(lbl)
            lbl.hide()

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
        for n in (self._health_bg, self._health_fg, self._health_lbl):
            n.hide() if is_hunter else n.show()
        self._scanner.show() if is_hunter else self._scanner.hide()
        
        
        for lbl in getattr(self, "_hunter_weapons", []):
            lbl.show() if is_hunter else lbl.hide()
        
    def set_weapon(self, name):
        # Highlight active weapon
        idx = int(name[1]) if name.startswith("[") else 0
        for i, lbl in enumerate(getattr(self, "_hunter_weapons", [])):
            if i == idx:
                lbl["text_fg"] = _c(255, 255, 100)
            else:
                lbl["text_fg"] = _c(150, 150, 150)

    def set_timer(self, phase, time_left):
        self._phase["text"] = phase.replace("_", " ").upper()
        if phase == "hiding":
            self._phase["text"] += "\nHunters cant move for a while"
            
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
        pct = max(0, min(1, value / max_value))
        self._health_fg.setScale(pct, 1, 1)

    def set_scanner_status(self, charges, max_charges, cooldown_left):
        if cooldown_left > 0:
            self._scanner["text"] = (
                f"SCANNER: recharging ({cooldown_left:.1f}s) [{charges}/{max_charges}]"
            )
        else:
            self._scanner["text"] = f"SCANNER: ready [{charges}/{max_charges}]"

    def set_tasks(self, tasks):
        if not tasks:
            self._task_title.hide()
            for lbl in self._task_labels:
                lbl.hide()
            return
            
        self._task_title.show()
        for i, lbl in enumerate(self._task_labels):
            if i < len(tasks):
                lbl.show()
                t = tasks[i]
                if t.get("done"):
                    lbl["text"] = f"DONE {t.get('desc')}"
                    lbl["text_fg"] = _c(80, 235, 80)
                else:
                    if t.get('type') == 'morph' or t.get('type') == 'unmorphed':
                        lbl["text"] = f"{t.get('desc')} ({int(t.get('cur', 0))}s/{int(t.get('tgt', 0))}s)"
                    elif t.get('type') == 'move':
                        lbl["text"] = f"{t.get('desc')} ({int(t.get('cur', 0))}m/{int(t.get('tgt', 0))}m)"
                    else:
                        lbl["text"] = f"{t.get('desc')} ({int(t.get('cur', 0))}/{int(t.get('tgt', 0))})"
                    lbl["text_fg"] = _c(235, 160, 60)
            else:
                lbl.hide()

    def push_clue(self, clue):
        self._clue_lines.append(clue)
        self._clue_lines = self._clue_lines[-5:]
        self._clue_log["text"] = "\n".join(self._clue_lines)

    def set_transform_hint(self, text):
        self._hint["text"] = text

    def set_hotbar(self, objects):
        if not objects:
            self._hotbar_btn.hide()
            self._hotbar_frame.hide()
            return
        self._hotbar_btn.show()
        if self._hotbar_open:
            self._hotbar_frame.show()
        else:
            self._hotbar_frame.hide()
        for i, lbl in enumerate(self._hotbar_labels):
            if i < len(objects):
                name = objects[i].replace('_', ' ').title()
                # Limit length so it fits
                if len(name) > 10: name = name[:8] + ".."
                lbl["text"] = f"[{i+1}] {name}"
            else:
                lbl["text"] = ""

    def _toggle_hotbar(self):
        self.toggle_prop_menu()

    def toggle_prop_menu(self):
        self._hotbar_open = not self._hotbar_open
        if self._hotbar_open:
            self._hotbar_frame.show()
        else:
            self._hotbar_frame.hide()

    def show(self):  self.root.show()
    def hide(self):  self.root.hide()
