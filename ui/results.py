"""
Results screen: winning team, players eliminated, objectives completed,
survival time, XP/score.
"""
from ursina import Entity, Text, Button, color, camera


class ResultsScreen:
    def __init__(self, on_continue):
        self.on_continue = on_continue
        self.root = Entity(parent=camera.ui, enabled=False)
        Entity(parent=self.root, model="quad", scale=(2, 1), color=color.rgb(10, 10, 16), z=1)

        self.winner_text = Text(parent=self.root, text="", y=0.35, origin=(0, 0), scale=2.2, color=color.rgb(240, 210, 90))
        self.reason_text = Text(parent=self.root, text="", y=0.26, origin=(0, 0), scale=1.1, color=color.white)
        self.table_text = Text(parent=self.root, text="", y=0.10, x=-0.5, scale=1.0, color=color.white, line_height=1.4)

        Button(parent=self.root, text="RETURN TO LOBBY", y=-0.42, scale=(0.34, 0.08),
               color=color.rgb(50, 90, 60), on_click=self._continue)

    def _continue(self):
        self.on_continue()

    def display(self, result: dict):
        winner = result.get("winner", "?").upper()
        self.winner_text.text = f"{winner} WIN!"
        self.reason_text.text = result.get("reason", "")

        rows = ["NAME            ROLE      SURVIVED  ELIMS  OBJ  XP"]
        for p in result.get("players", []):
            rows.append(
                f"{p['name'][:14]:<15} {p['role']:<9} {'yes' if p['survived'] else 'no':<9}"
                f"{p['eliminations']:<7}{p['objectives_completed']:<5}{p['xp']}"
            )
        self.table_text.text = "\n".join(rows)

    def show(self):
        self.root.enabled = True

    def hide(self):
        self.root.enabled = False
