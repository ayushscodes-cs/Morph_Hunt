"""
Main Menu and Connect Dialog — Panda3D DirectGui implementation.

Fix: use DirectLabel for all text (shares DirectGui render bin with DirectButton)
and use a plain aspect2d NodePath as the root container instead of DirectFrame.
"""
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectEntry, DirectLabel,
)
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, LVecBase4f


def _c(r, g, b, a=1.0):
    return LVecBase4f(r / 255, g / 255, b / 255, a)


def _label(parent, text, pos, scale, fg, align=TextNode.ACenter):
    """Plain text label (DirectLabel, no frame)."""
    return DirectLabel(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text_align=align,
        frameColor=(0, 0, 0, 0),   # transparent frame
        relief=None,
        pos=pos,
    )


def _btn(parent, text, pos, command, fg, hover_fg=None, scale=0.07):
    hfg = hover_fg or fg
    return DirectButton(
        parent=parent,
        text=text,
        scale=scale,
        text_fg=fg,
        text0_fg=fg,
        text1_fg=_c(255, 255, 255),   # pressed
        text2_fg=hfg,                  # hover
        text3_fg=_c(80, 80, 80),       # disabled
        frameColor=(
            _c(30, 32, 48),    # normal
            _c(50, 52, 75),    # click
            _c(42, 45, 65),    # hover
            _c(20, 22, 35),    # disabled
        ),
        frameSize=(-3.6, 3.6, -0.5, 0.85),
        relief=1,
        pos=pos,
        command=command,
    )


# ---------------------------------------------------------------------------
class MainMenu:
    def __init__(self, on_host, on_join, on_quit):
        self.on_host  = on_host
        self.on_join  = on_join
        self.on_quit  = on_quit

        # Plain NodePath container parented to aspect2d
        from direct.showbase.ShowBase import ShowBase
        import builtins
        self._aspect2d = builtins.base.aspect2d
        self.root = self._aspect2d.attachNewNode("main_menu")

        # Background panel (rendered first = behind everything)
        self._bg = DirectFrame(
            parent=self.root,
            frameColor=_c(10, 12, 20),
            frameSize=(-2, 2, -1.2, 1.2),
            pos=(0, 0, 0),
            sortOrder=0,
        )

        # ---- Title -------------------------------------------------------
        _label(self.root, "MORPH HUNT",
               pos=(0, 0, 0.72), scale=0.17, fg=_c(235, 242, 245))
        _label(self.root, "MAIN MENU",
               pos=(0, 0, 0.55), scale=0.068, fg=_c(80, 220, 215))
        _label(self.root, "HIDE  \u2022  MORPH  \u2022  SURVIVE",
               pos=(0, 0, 0.42), scale=0.052, fg=_c(235, 170, 70))

        # ---- Buttons -----------------------------------------------------
        _btn(self.root, "HOST GAME",    (0, 0, 0.18),  self._do_host,
             _c(220, 232, 235), _c(75, 235, 225))
        _btn(self.root, "JOIN GAME",    (0, 0, 0.02),  self._do_join,
             _c(220, 232, 235), _c(75, 235, 225))
        self._howto_btn = _btn(
            self.root, "HOW TO PLAY", (0, 0, -0.14), self._do_howto,
            _c(220, 232, 235), _c(75, 235, 225))
        _btn(self.root, "QUIT",         (0, 0, -0.30), on_quit,
             _c(220, 130, 130), _c(255, 100, 90))

        _label(self.root, "LAN MULTIPLAYER  \u2022  v1.0",
               pos=(0, 0, -0.96), scale=0.042, fg=_c(75, 190, 195))

        # ---- How-to panel (hidden by default) ----------------------------
        self._howto_panel = self._build_howto()
        self._howto_panel.hide()

    # ------------------------------------------------------------------
    def _build_howto(self):
        panel = DirectFrame(
            parent=self.root,
            frameColor=_c(14, 16, 28, 0.97),
            frameSize=(-1.7, 1.7, -1.0, 1.0),
            pos=(0, 0, 0),
            sortOrder=10,
        )
        _label(panel, "HOW TO PLAY",
               pos=(0, 0, 0.78), scale=0.10, fg=_c(75, 235, 225))

        body = (
            "HIDERS\n"
            "Morph into objects and stay hidden.\n"
            "Complete objectives while avoiding the Hunter.\n\n"
            "HUNTERS\n"
            "Find suspicious objects and eliminate Hiders.\n"
            "Use your scanner to locate clues.\n\n"
            "CONTROLS\n"
            "WASD  Move         Mouse  Look\n"
            "Shift  Sprint        Space  Jump\n"
            "1-9  Morph           E  Interact\n"
            "Q  Scanner          LMB  Attack\n"
            "ESC  Pause"
        )
        _label(panel, body, pos=(0, 0, 0.38), scale=0.052,
               fg=_c(210, 225, 228))
        _btn(panel, "BACK", (0, 0, -0.82), self._close_howto,
             _c(75, 235, 225), scale=0.065)
        return panel

    def _do_host(self):  self.on_host()
    def _do_join(self):  self.on_join()
    def _do_howto(self): self._howto_panel.show()
    def _close_howto(self): self._howto_panel.hide()

    def show(self):   self.root.show()
    def hide(self):   self.root.hide()
    def update(self): pass
    def input(self, key): pass


# ---------------------------------------------------------------------------
class ConnectDialog:
    def __init__(self, on_submit, on_cancel, mode="join"):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.mode = mode

        import builtins
        self.root = builtins.base.aspect2d.attachNewNode("connect_dialog")

        DirectFrame(
            parent=self.root,
            frameColor=_c(14, 16, 28, 0.97),
            frameSize=(-1.5, 1.5, -1.05, 1.05),
            pos=(0, 0, 0),
            sortOrder=0,
        )

        title = "HOST GAME" if mode == "host" else "JOIN GAME"
        _label(self.root, title,
               pos=(0, 0, 0.82), scale=0.12, fg=_c(75, 235, 225))

        subtitle = ("CREATE A LOCAL MULTIPLAYER LOBBY"
                    if mode == "host"
                    else "CONNECT TO A MORPH HUNT SERVER")
        _label(self.root, subtitle,
               pos=(0, 0, 0.65), scale=0.050, fg=_c(150, 190, 195))

        # Name field
        _label(self.root, "PLAYER NAME",
               pos=(-0.55, 0, 0.48), scale=0.054, fg=_c(110, 220, 215),
               align=TextNode.ALeft)
        self._name_entry = DirectEntry(
            parent=self.root,
            initialText="Player",
            scale=0.06,
            pos=(-0.70, 0, 0.32),
            width=11,
            frameColor=_c(28, 32, 48),
            text_fg=_c(230, 230, 230),
            relief=1,
        )

        addr_label   = "SERVER ADDRESS" if mode == "join" else "SERVER PORT"
        addr_default = "127.0.0.1:5555" if mode == "join" else "5555"

        _label(self.root, addr_label,
               pos=(-0.55, 0, 0.12), scale=0.054, fg=_c(110, 220, 215),
               align=TextNode.ALeft)
        self._addr_entry = DirectEntry(
            parent=self.root,
            initialText=addr_default,
            scale=0.06,
            pos=(-0.70, 0, -0.04),
            width=11,
            frameColor=_c(28, 32, 48),
            text_fg=_c(230, 230, 230),
            relief=1,
        )

        submit_text = "JOIN SERVER" if mode == "join" else "START HOSTING"
        _btn(self.root, submit_text, (0, 0, -0.38), self._submit,
             _c(75, 235, 225))
        _btn(self.root, "CANCEL",    (0, 0, -0.58), self._cancel,
             _c(210, 115, 115))

        self._status = _label(self.root, "",
                              pos=(0, 0, -0.80), scale=0.050,
                              fg=_c(180, 195, 200))

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