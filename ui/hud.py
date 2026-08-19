"""
In-game HUD: role, timer, Morph Energy bar, health, scanner status,
objective progress, player count, and floating scanner clue log.
"""
from ursina import Entity, Text, color, camera, Func, invoke


class HUD:
    def __init__(self):
        self.root = Entity(parent=camera.ui, enabled=False)

        self.role_text = Text(parent=self.root, text="", x=-0.86, y=0.46, scale=1.3, color=color.yellow)
        self.timer_text = Text(parent=self.root, text="", x=-0.06, y=0.46, scale=1.6, color=color.white)
        self.phase_text = Text(parent=self.root, text="", x=-0.12, y=0.40, scale=1.0, color=color.light_gray)
        self.players_text = Text(parent=self.root, text="", x=0.65, y=0.46, scale=1.0, color=color.white)

        # Morph energy bar (hider only)
        self.energy_bg = Entity(parent=self.root, model="quad", color=color.rgb(40, 40, 40),
                                 scale=(0.3, 0.035), x=-0.72, y=-0.42, z=1)
        self.energy_fg = Entity(parent=self.root, model="quad", color=color.rgb(90, 200, 230),
                                 scale=(0.3, 0.035), x=-0.72, y=-0.42, z=0.5, origin=(-0.5, 0))
        self.energy_fg.x = -0.72 - 0.15
        self.energy_label = Text(parent=self.root, text="MORPH ENERGY", x=-0.86, y=-0.37, scale=0.9, color=color.white)

        # Health bar
        self.health_bg = Entity(parent=self.root, model="quad", color=color.rgb(40, 40, 40),
                                 scale=(0.3, 0.035), x=-0.72, y=-0.30, z=1)
        self.health_fg = Entity(parent=self.root, model="quad", color=color.rgb(220, 60, 60),
                                 scale=(0.3, 0.035), x=-0.72, y=-0.30, z=0.5, origin=(-0.5, 0))
        self.health_fg.x = -0.72 - 0.15
        self.health_label = Text(parent=self.root, text="HEALTH", x=-0.86, y=-0.25, scale=0.9, color=color.white)

        self.scanner_text = Text(parent=self.root, text="", x=0.55, y=-0.30, scale=1.0, color=color.cyan)
        self.objective_text = Text(parent=self.root, text="", x=-0.86, y=0.0, scale=1.0, color=color.orange)

        self.clue_log = Text(parent=self.root, text="", x=0.4, y=-0.05, scale=0.9, color=color.rgb(150, 220, 255))
        self._clue_lines = []

        self.transform_hint = Text(
            parent=self.root, text="", x=-0.86, y=-0.46, scale=0.9, color=color.rgb(200, 200, 200)
        )

    def set_role(self, role):
        self.role_text.text = f"ROLE: {role.upper()}"
        self.energy_bg.enabled = role == "hider"
        self.energy_fg.enabled = role == "hider"
        self.energy_label.enabled = role == "hider"
        self.scanner_text.enabled = role == "hunter"

    def set_timer(self, phase, time_left):
        self.phase_text.text = phase.replace("_", " ").upper()
        if time_left and time_left > 0:
            m, s = divmod(int(time_left), 60)
            self.timer_text.text = f"{m:02d}:{s:02d}"
        else:
            self.timer_text.text = "--:--"

    def set_players(self, alive_hiders, total_hunters):
        self.players_text.text = f"Hiders left: {alive_hiders}  |  Hunters: {total_hunters}"

    def set_energy(self, value, max_value=100):
        pct = max(0.0, min(1.0, value / max_value))
        self.energy_fg.scale_x = 0.3 * pct

    def set_health(self, value, max_value=100):
        pct = max(0.0, min(1.0, value / max_value))
        self.health_fg.scale_x = 0.3 * pct

    def set_scanner_status(self, charges, max_charges, cooldown_left):
        if cooldown_left > 0:
            self.scanner_text.text = f"SCANNER: recharging ({cooldown_left:.1f}s) [{charges}/{max_charges}]"
        else:
            self.scanner_text.text = f"SCANNER: ready [{charges}/{max_charges}]"

    def set_objectives(self, completed, required):
        if required > 0:
            self.objective_text.text = f"Objectives: {completed}/{required}"
        else:
            self.objective_text.text = ""

    def push_clue(self, clue):
        self._clue_lines.append(clue)
        self._clue_lines = self._clue_lines[-5:]
        self.clue_log.text = "\n".join(self._clue_lines)

    def set_transform_hint(self, text):
        self.transform_hint.text = text

    def show(self):
        self.root.enabled = True

    def hide(self):
        self.root.enabled = False
