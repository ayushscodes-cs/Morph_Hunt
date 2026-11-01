"""
Hider personal tasks: behaviors players must perform to win Object Rush.
Tasks are randomly assigned per player.
"""
import random
import math
from config import settings
from game.object_prop import REGISTRY

class PersonalTask:
    def __init__(self, task_type, target_val, description, **kwargs):
        self.task_type = task_type
        self.target_val = target_val
        self.current_val = 0.0
        self.description = description
        self.completed = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "type": self.task_type,
            "desc": self.description,
            "cur": round(self.current_val, 1),
            "tgt": round(self.target_val, 1),
            "done": self.completed
        }

    def add_progress(self, amount):
        if not self.completed:
            self.current_val += amount
            if self.current_val >= self.target_val:
                self.current_val = self.target_val
                self.completed = True
                return True
        return False

class ObjectiveManager:
    def __init__(self):
        # We don't store global objectives anymore, tasks are on PlayerState
        pass

    def assign_tasks(self, players):
        props = list(REGISTRY.keys())
        for p in players:
            if p.role == "hider":
                p.personal_tasks = []
                pool = ["morph", "move", "unmorphed", "jump", "taunt"]
                random.shuffle(pool)
                # Pick 3 tasks
                for task_type in pool[:3]:
                    if task_type == "morph":
                        prop = random.choice(props)
                        prop_name = prop.replace("_", " ").title()
                        p.personal_tasks.append(PersonalTask("morph", 15.0, f"Morph into {prop_name} (15s)", prop=prop))
                    elif task_type == "move":
                        p.personal_tasks.append(PersonalTask("move", 50.0, "Travel 50m while morphed"))
                    elif task_type == "unmorphed":
                        p.personal_tasks.append(PersonalTask("unmorphed", 20.0, "Stay unmorphed (20s)"))
                    elif task_type == "jump":
                        p.personal_tasks.append(PersonalTask("jump", 10.0, "Jump 10 times while morphed"))
                    elif task_type == "taunt":
                        p.personal_tasks.append(PersonalTask("taunt", 3.0, "Taunt 3 times"))

                # Extra state for tracking movement delta
                p._last_pos = list(p.position)

    def tick(self, dt, players):
        completed_tasks = []
        for p in players:
            if p.role != "hider" or not p.alive or not getattr(p, "personal_tasks", None):
                continue
            
            # Calc distance moved this tick
            dx = p.position[0] - getattr(p, "_last_pos", p.position)[0]
            dy = p.position[1] - getattr(p, "_last_pos", p.position)[1]
            dz = p.position[2] - getattr(p, "_last_pos", p.position)[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            p._last_pos = list(p.position)

            is_morphed = bool(p.transformed_into)

            for task in p.personal_tasks:
                if task.completed:
                    continue
                
                just_completed = False
                if task.task_type == "morph":
                    target_prop = getattr(task, "prop", None)
                    if p.transformed_into == target_prop:
                        just_completed = task.add_progress(dt)
                
                elif task.task_type == "move":
                    if is_morphed:
                        just_completed = task.add_progress(dist)
                
                elif task.task_type == "unmorphed":
                    if not is_morphed:
                        just_completed = task.add_progress(dt)

                if just_completed:
                    completed_tasks.append((p, task))
                    
        return completed_tasks

    def handle_event(self, player, event_type):
        """Called when a jump or taunt occurs."""
        if not getattr(player, "personal_tasks", None):
            return []
            
        completed_tasks = []
        is_morphed = bool(player.transformed_into)
        
        for task in player.personal_tasks:
            if task.completed:
                continue
                
            just_completed = False
            if event_type == "jump" and task.task_type == "jump" and is_morphed:
                just_completed = task.add_progress(1.0)
            elif event_type == "taunt" and task.task_type == "taunt":
                just_completed = task.add_progress(1.0)
                
            if just_completed:
                completed_tasks.append((player, task))
                
        return completed_tasks

    def required_count(self, mode):
        return 0
