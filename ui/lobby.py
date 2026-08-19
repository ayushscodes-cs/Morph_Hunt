from ursina import Entity, Text, color, camera, mouse

from config import settings


class LobbyScreen:
    def __init__(self, on_ready_toggle, on_set_map, on_set_mode, on_start, on_leave):
        self.on_ready_toggle = on_ready_toggle
        self.on_set_map = on_set_map
        self.on_set_mode = on_set_mode
        self.on_start = on_start
        self.on_leave = on_leave

        self.root = Entity(parent=camera.ui, enabled=False)

        Text(parent=self.root, text="LOBBY", y=0.43, origin=(0, 0), scale=2.2, color=color.rgb(240, 210, 90))
        Text(parent=self.root, text="PLAYERS", x=-0.58, y=0.32, scale=1.15, color=color.rgb(80, 220, 240))

        self.player_list_text = Text(
            parent=self.root,
            text="",
            x=-0.58,
            y=0.25,
            scale=1.05,
            color=color.white
        )

        self.map_label = Text(
            parent=self.root,
            text="Map: house",
            x=0.18,
            y=0.31,
            scale=1.15,
            color=color.rgb(80, 220, 240)
        )

        self.mode_label = Text(
            parent=self.root,
            text="Mode: classic",
            x=0.18,
            y=0.23,
            scale=1.15,
            color=color.rgb(80, 220, 240)
        )

        self.map_btn = self._make_button(
            "CYCLE MAP",
            0.35,
            0.13,
            color.rgb(220, 232, 235),
            color.rgb(75, 235, 225)
        )

        self.mode_btn = self._make_button(
            "CYCLE MODE",
            0.35,
            0.04,
            color.rgb(220, 232, 235),
            color.rgb(75, 235, 225)
        )

        self.ready_btn = self._make_button(
            "READY",
            -0.35,
            -0.29,
            color.rgb(100, 220, 150),
            color.rgb(130, 255, 175)
        )

        self.start_btn = self._make_button(
            "START GAME",
            0.0,
            -0.42,
            color.rgb(220, 190, 110),
            color.rgb(255, 225, 150)
        )

        self.leave_btn = self._make_button(
            "LEAVE",
            0.35,
            -0.29,
            color.rgb(220, 150, 150),
            color.rgb(255, 180, 180)
        )

        self._buttons = [
            (self.map_btn, 0.20, 0.045),
            (self.mode_btn, 0.20, 0.045),
            (self.ready_btn, 0.20, 0.045),
            (self.start_btn, 0.23, 0.05),
            (self.leave_btn, 0.20, 0.045),
        ]

        self._map_idx = 0
        self._mode_idx = 0
        self.is_host = False

    def _make_button(self, text, x, y, normal_color, hover_color):
        button = Text(
            parent=self.root,
            text=text,
            x=x,
            y=y,
            origin=(0, 0),
            scale=1.08,
            color=normal_color
        )
        button.normal_color = normal_color
        button.hover_color = hover_color
        return button

    def _hit(self, button, width, height):
        return (
            button.x - width <= mouse.x <= button.x + width
            and button.y - height <= mouse.y <= button.y + height
        )

    def update(self):
        if not self.root.enabled:
            return

        for button, width, height in self._buttons:
            hovered = self._hit(button, width, height)

            if button is self.start_btn and not self.is_host:
                button.color = color.rgb(120, 120, 120) if hovered else color.rgb(85, 85, 85)
                button.scale = 1.14 if hovered else 1.08
                continue

            button.color = button.hover_color if hovered else button.normal_color
            button.scale = 1.14 if hovered else 1.08

    def input(self, key):
        if not self.root.enabled:
            return

        if key != "left mouse down":
            return

        if self._hit(self.map_btn, 0.20, 0.045):
            self._cycle_map()
            return

        if self._hit(self.mode_btn, 0.20, 0.045):
            self._cycle_mode()
            return

        if self._hit(self.ready_btn, 0.20, 0.045):
            self._toggle_ready()
            return

        if self._hit(self.start_btn, 0.23, 0.05):
            if self.is_host:
                self._start()
            return

        if self._hit(self.leave_btn, 0.20, 0.045):
            self.on_leave()

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

    def update_state(self, players, map_key, mode, host_id, my_id):
        lines = []

        for p in players:
            tag = " (HOST)" if p.get("player_id") == host_id else ""
            ready = "READY" if p.get("ready") else "not ready"
            you = " <-- you" if p.get("player_id") == my_id else ""
            lines.append(f"{p.get('name')}{tag} - {ready}{you}")

        self.player_list_text.text = (
            "\n".join(lines) if lines else "(waiting for players...)"
        )

        self.map_label.text = f"Map: {map_key}"
        self.mode_label.text = f"Mode: {mode}"
        self.is_host = host_id == my_id

        if self.is_host:
            self.start_btn.normal_color = color.rgb(220, 190, 110)
            self.start_btn.hover_color = color.rgb(255, 225, 150)
        else:
            self.start_btn.normal_color = color.rgb(85, 85, 85)
            self.start_btn.hover_color = color.rgb(120, 120, 120)

    def show(self):
        self.root.enabled = True

    def hide(self):
        self.root.enabled = False