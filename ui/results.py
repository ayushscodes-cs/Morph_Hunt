"""
Results Screen — Panda3D DirectGui, fixed render-bin ordering.
"""
import builtins

from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode, LVecBase4f


def _c(r, g, b, a=1.0):
    return LVecBase4f(r / 255, g / 255, b / 255, a)


def _label(parent, text, pos, scale, fg, align=TextNode.ACenter):
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


class ResultsScreen:
    def __init__(self, on_continue):
        self.on_continue = on_continue

        a2d = builtins.base.aspect2d
        self.root = a2d.attachNewNode("results_root")
        self.root.hide()

        # Dark overlay
        DirectFrame(
            parent=self.root,
            frameColor=_c(10, 10, 16, 0.94),
            frameSize=(-2, 2, -1.2, 1.2),
            sortOrder=0,
        )

        self._winner = _label(self.root, "",
                              pos=(0, 0, 0.80), scale=0.13,
                              fg=_c(240, 210, 90))
        self._reason = _label(self.root, "",
                              pos=(0, 0, 0.62), scale=0.065,
                              fg=_c(220, 220, 220))
        self._table  = _label(self.root, "",
                              pos=(-1.35, 0, 0.44), scale=0.050,
                              fg=_c(210, 215, 220), align=TextNode.ALeft)

        DirectButton(
            parent=self.root,
            text="RETURN TO LOBBY",
            scale=0.07,
            text_fg=_c(200, 230, 205),
            text0_fg=_c(200, 230, 205),
            text1_fg=_c(255, 255, 255),
            text2_fg=_c(130, 255, 170),
            frameColor=(
                _c(40, 80, 50),
                _c(60, 110, 70),
                _c(50, 95, 60),
                _c(30, 60, 40),
            ),
            frameSize=(-4.2, 4.2, -0.55, 0.90),
            relief=1,
            pos=(0, 0, -0.88),
            command=self._continue,
        )

    def _continue(self):
        self.on_continue()

    def display(self, result: dict):
        winner = result.get("winner", "?").upper()
        self._winner["text"] = f"{winner} WIN!"
        self._reason["text"] = result.get("reason", "")

        rows = ["NAME            ROLE      SURVIVED  ELIMS  OBJ   XP"]
        for p in result.get("players", []):
            rows.append(
                f"{p['name'][:14]:<15} {p['role']:<9} "
                f"{'yes' if p['survived'] else 'no':<9}"
                f"{p['eliminations']:<7}{p['objectives_completed']:<6}{p['xp']}"
            )
        self._table["text"] = "\n".join(rows)
        self.show()

    def show(self):  self.root.show()
    def hide(self):  self.root.hide()
