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

        for child in self._table.getChildren():
            child.removeNode()

        headers = [("NAME", 0.0), ("ROLE", 8.0), ("SURVIVED", 14.0), ("ELIMS", 20.0), ("OBJ", 25.0), ("XP", 30.0)]
        y = 0
        for title, x in headers:
            _label(self._table, title, pos=(x, 0, y), scale=0.9, fg=_c(210, 215, 220), align=TextNode.ALeft)
        
        y -= 1.2
        for p in result.get("players", []):
            _label(self._table, p['name'][:14], pos=(headers[0][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            _label(self._table, p['role'], pos=(headers[1][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            _label(self._table, 'yes' if p['survived'] else 'no', pos=(headers[2][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            _label(self._table, str(p['eliminations']), pos=(headers[3][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            _label(self._table, str(p['objectives_completed']), pos=(headers[4][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            _label(self._table, str(p['xp']), pos=(headers[5][1], 0, y), scale=0.8, fg=_c(210, 215, 220), align=TextNode.ALeft)
            y -= 1.0
            
        self.show()

    def show(self):  self.root.show()
    def hide(self):  self.root.hide()
