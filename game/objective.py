"""
Hider objectives: switches, energy fragments, terminals, control panels.

Objectives force Hiders to leave safe hiding spots, creating risk/reward.
Fully data-driven: each level defines its own objective positions.
"""
import math
import time

from config import settings


class Objective:
    def __init__(self, obj_id: str, kind: str, position, label: str):
        self.obj_id = obj_id
        self.kind = kind          # "switch" | "fragment" | "terminal" | "panel"
        self.position = list(position)
        self.label = label
        self.completed = False
        self.progress = 0.0                # 0..OBJECTIVE_HOLD_SECONDS
        self.active_player_id = None

    def to_dict(self):
        return {
            "obj_id": self.obj_id,
            "kind": self.kind,
            "position": self.position,
            "label": self.label,
            "completed": self.completed,
            "progress": round(self.progress, 2),
        }


class ObjectiveManager:
    def __init__(self):
        self.objectives = []

    def load_for_level(self, level_def: dict):
        self.objectives = []
        for spec in level_def.get("objectives", []):
            self.objectives.append(
                Objective(spec["id"], spec["kind"], spec["position"], spec["label"])
            )

    def reset(self):
        for o in self.objectives:
            o.completed = False
            o.progress = 0.0
            o.active_player_id = None

    def completed_count(self):
        return sum(1 for o in self.objectives if o.completed)

    def required_count(self, mode: str):
        needed = settings.OBJECTIVES_TO_WIN.get(mode, 0)
        return min(needed, len(self.objectives)) if needed else 0

    def find_nearby(self, position, max_range=settings.OBJECTIVE_INTERACT_RANGE):
        best = None
        best_dist = max_range
        for o in self.objectives:
            if o.completed:
                continue
            dist = math.sqrt(
                (o.position[0] - position[0]) ** 2
                + (o.position[1] - position[1]) ** 2
                + (o.position[2] - position[2]) ** 2
            )
            if dist <= best_dist:
                best = o
                best_dist = dist
        return best

    def tick(self, dt, interacting_map):
        """
        interacting_map: {player_id: objective_id or None} — which objective
        each hider is currently holding interact near, computed by the
        server each tick from position + input.
        """
        active_by_obj = {}
        for pid, obj_id in interacting_map.items():
            if obj_id:
                active_by_obj.setdefault(obj_id, []).append(pid)

        newly_completed = []
        for o in self.objectives:
            if o.completed:
                continue
            if o.obj_id in active_by_obj and active_by_obj[o.obj_id]:
                o.progress = min(settings.OBJECTIVE_HOLD_SECONDS, o.progress + dt)
                o.active_player_id = active_by_obj[o.obj_id][0]
                if o.progress >= settings.OBJECTIVE_HOLD_SECONDS:
                    o.completed = True
                    newly_completed.append(o)
            else:
                o.progress = max(0.0, o.progress - dt * 0.5)
                o.active_player_id = None
        return newly_completed
