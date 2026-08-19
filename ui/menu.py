from ursina import Entity, Text, color, camera, mouse, destroy, time
from ursina.prefabs.input_field import InputField


class MainMenu:
    def __init__(self, on_host, on_join, on_quit):
        self.on_host = on_host
        self.on_join = on_join
        self.on_quit = on_quit
        self.root = Entity(parent=camera.ui, enabled=True)

        self.title = Text(
            parent=self.root,
            text="MORPH HUNT",
            origin=(0, 0),
            y=0.30,
            scale=2.2,
            color=color.rgb(235, 242, 245)
        )

        self.subtitle = Text(
            parent=self.root,
            text="MAIN MENU",
            origin=(0, 0),
            y=0.215,
            scale=0.92,
            color=color.rgb(80, 220, 215)
        )

        self.tagline = Text(
            parent=self.root,
            text="HIDE  •  MORPH  •  SURVIVE",
            origin=(0, 0),
            y=0.135,
            scale=0.72,
            color=color.rgb(235, 170, 70)
        )

        self.host_button = self._make_button("HOST GAME", 0.025)
        self.join_button = self._make_button("JOIN GAME", -0.115)
        self.howto_button = self._make_button("HOW TO PLAY", -0.255)
        self.quit_button = self._make_button("QUIT", -0.395)

        self.footer = Text(
            parent=self.root,
            text="LAN MULTIPLAYER  •  v1.0",
            origin=(0, 0),
            y=-0.49,
            scale=0.55,
            color=color.rgb(75, 190, 195)
        )

        self.howto_panel = None
        self._build_howto()

    def _make_button(self, text, y):
        return Text(
            parent=self.root,
            text=text,
            origin=(0, 0),
            y=y,
            scale=1.08,
            color=color.rgb(220, 232, 235)
        )

    def _hovered(self, button, width=0.20, height=0.045):
        return (
            button.x - width <= mouse.x <= button.x + width
            and button.y - height <= mouse.y <= button.y + height
        )

    def update(self):
        if not self.root.enabled:
            return

        buttons = [
            self.host_button,
            self.join_button,
            self.howto_button
        ]

        for button in buttons:
            if self._hovered(button):
                button.color = color.rgb(75, 235, 225)
                button.scale = 1.16
            else:
                button.color = color.rgb(220, 232, 235)
                button.scale = 1.08

        if self._hovered(self.quit_button):
            self.quit_button.color = color.rgb(255, 90, 80)
            self.quit_button.scale = 1.16
        else:
            self.quit_button.color = color.rgb(220, 205, 205)
            self.quit_button.scale = 1.08

    def input(self, key):
        if not self.root.enabled:
            return

        if key != "left mouse down":
            return

        if self.howto_panel and self.howto_panel.enabled:
            if (
                -0.22 <= mouse.x <= 0.22
                and -0.43 <= mouse.y <= -0.34
            ):
                self._close_howto()
            return

        if self._hovered(self.host_button):
            self.on_host()
            return

        if self._hovered(self.join_button):
            self.on_join()
            return

        if self._hovered(self.howto_button):
            self._open_howto()
            return

        if self._hovered(self.quit_button):
            self.on_quit()
            return

    def _open_howto(self):
        for item in (
            self.title,
            self.subtitle,
            self.tagline,
            self.host_button,
            self.join_button,
            self.howto_button,
            self.quit_button,
            self.footer,
        ):
            item.enabled = False

        self.howto_panel.enabled = True

    def _close_howto(self):
        self.howto_panel.enabled = False

        for item in (
            self.title,
            self.subtitle,
            self.tagline,
            self.host_button,
            self.join_button,
            self.howto_button,
            self.quit_button,
            self.footer,
        ):
            item.enabled = True
    
    def _build_howto(self):
        self.howto_panel = Entity(
            parent=self.root,
            enabled=False
        )

        Text(
            parent=self.howto_panel,
            text="HOW TO PLAY",
            origin=(0, 0),
            y=0.28,
            scale=1.55,
            color=color.rgb(75, 235, 225)
        )

        Text(
            parent=self.howto_panel,
            text=(
                "HIDERS\n"
                "Morph into objects around the map and stay hidden.\n"
                "Complete objectives while avoiding the Hunter.\n\n"
                "HUNTERS\n"
                "Search for suspicious objects and eliminate Hiders.\n"
                "Use your scanner to locate clues.\n\n"
                "CONTROLS\n"
                "WASD   Move\n"
                "Mouse   Look\n"
                "Shift   Sprint\n"
                "Space   Jump\n"
                "1-9   Morph\n"
                "E   Interact\n"
                "Q   Scanner\n"
                "Left Click   Attack\n"
                "ESC   Pause"
            ),
            origin=(0, 0),
            y=0.015,
            scale=0.68,
            line_height=1.35,
            color=color.rgb(210, 225, 228)
        )

        self.back_button = Text(
            parent=self.howto_panel,
            text="BACK",
            origin=(0, 0),
            y=-0.38,
            scale=1.0,
            color=color.rgb(75, 235, 225)
        )

    def show(self):
        self.root.enabled = True
        self._close_howto()

    def hide(self):
        self.root.enabled = False


class ConnectDialog:
    def __init__(self, on_submit, on_cancel, mode="join"):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.mode = mode

        self.root = Entity(
            parent=camera.ui,
            enabled=True
        )

        self.title = Text(
            parent=self.root,
            text="HOST GAME" if mode == "host" else "JOIN GAME",
            origin=(0, 0),
            y=0.27,
            scale=1.9,
            color=color.rgb(75, 235, 225)
        )

        self.subtitle = Text(
            parent=self.root,
            text=(
                "CREATE A LOCAL MULTIPLAYER LOBBY"
                if mode == "host"
                else "CONNECT TO A MORPH HUNT SERVER"
            ),
            origin=(0, 0),
            y=0.20,
            scale=0.65,
            color=color.rgb(150, 190, 195)
        )

        self.name_label = Text(
            parent=self.root,
            text="PLAYER NAME",
            origin=(0, 0),
            x=-0.20,
            y=0.105,
            scale=0.72,
            color=color.rgb(110, 220, 215)
        )

        self.name_field = InputField(
            parent=self.root,
            default_value="Player",
            y=0.035,
            scale=(0.48, 0.06)
        )

        if mode == "join":
            field_label = "SERVER ADDRESS"
            field_default = "127.0.0.1:5555"
            submit_text = "JOIN SERVER"
        else:
            field_label = "SERVER PORT"
            field_default = "5555"
            submit_text = "START HOSTING"

        self.address_label = Text(
            parent=self.root,
            text=field_label,
            origin=(0, 0),
            x=-0.20,
            y=-0.055,
            scale=0.72,
            color=color.rgb(110, 220, 215)
        )

        self.addr_field = InputField(
            parent=self.root,
            default_value=field_default,
            y=-0.125,
            scale=(0.48, 0.06)
        )

        self.submit_button = Text(
            parent=self.root,
            text=submit_text,
            origin=(0, 0),
            y=-0.235,
            scale=0.95,
            color=color.rgb(75, 235, 225)
        )

        self.cancel_button = Text(
            parent=self.root,
            text="CANCEL",
            origin=(0, 0),
            y=-0.335,
            scale=0.88,
            color=color.rgb(210, 115, 115)
        )

        self.status = Text(
            parent=self.root,
            text="",
            origin=(0, 0),
            y=-0.42,
            scale=0.62,
            color=color.rgb(180, 195, 200)
        )

    def _hovered_submit(self):
        return (
            -0.27 <= mouse.x <= 0.27
            and -0.285 <= mouse.y <= -0.185
        )

    def _hovered_cancel(self):
        return (
            -0.22 <= mouse.x <= 0.22
            and -0.385 <= mouse.y <= -0.285
        )

    def update(self):
        if not self.root.enabled:
            return

        if self._hovered_submit():
            self.submit_button.color = color.rgb(75, 255, 240)
            self.submit_button.scale = 1.02
        else:
            self.submit_button.color = color.rgb(75, 235, 225)
            self.submit_button.scale = 0.95

        if self._hovered_cancel():
            self.cancel_button.color = color.rgb(255, 145, 145)
            self.cancel_button.scale = 0.96
        else:
            self.cancel_button.color = color.rgb(210, 115, 115)
            self.cancel_button.scale = 0.88

    def input(self, key):
        if not self.root.enabled:
            return

        if key != "left mouse down":
            return

        if self._hovered_submit():
            self._submit()
            return

        if self._hovered_cancel():
            self._cancel()
            return

    def _submit(self):
        name = self.name_field.text.strip() or "Player"
        address = self.addr_field.text.strip()

        if self.mode == "host":
            self.status.text = "STARTING SERVER..."
        else:
            self.status.text = "CONNECTING..."

        self.on_submit(name, address)

    def _cancel(self):
        self.on_cancel()

    def show(self):
        self.root.enabled = True

    def hide(self):
        self.root.enabled = False

    def destroy(self):
        destroy(self.root)