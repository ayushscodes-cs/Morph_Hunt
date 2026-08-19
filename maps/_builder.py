"""
Reusable modular level-building helpers shared by every map module.

Maps are described purely as data (lists of dicts) so both the headless
server and the Ursina client can build identical layouts/collision from
the exact same source of truth.
"""


def floor(position, size, color=(90, 90, 95)):
    return {"type": "floor", "position": position, "scale": (size[0], 0.2, size[1]), "color": color, "solid": True}


def wall(position, size, color=(120, 120, 130)):
    """size = (width, height, thickness)"""
    return {"type": "wall", "position": position, "scale": size, "color": color, "solid": True}


def prop(kind, position, color=(150, 130, 100), scale=(1, 1, 1)):
    """A static (non-hideable) decorative prop, purely visual."""
    return {"type": "prop", "kind": kind, "position": position, "scale": scale, "color": color, "solid": True}


def hider_object(key, position):
    """A spawn point where a Hider-controlled object may appear/hide."""
    return {"key": key, "position": position}


def objective(obj_id, kind, position, label):
    return {"id": obj_id, "kind": kind, "position": position, "label": label}


def rectangular_room(name, center, size, wall_height=3.0, color=(150, 150, 160)):
    """
    Builds a simple rectangular room: floor + 4 perimeter walls with one
    open side left as a doorway gap (front, -z side).
    Returns (room_meta, geometry_list).
    """
    cx, cz = center
    w, d = size
    geo = [floor((cx, 0, cz), (w, d), color=(70, 70, 78))]
    t = 0.3
    # back wall
    geo.append(wall((cx, wall_height / 2, cz + d / 2), (w, wall_height, t), color=color))
    # left wall
    geo.append(wall((cx - w / 2, wall_height / 2, cz), (t, wall_height, d), color=color))
    # right wall
    geo.append(wall((cx + w / 2, wall_height / 2, cz), (t, wall_height, d), color=color))
    # front wall split with a doorway gap in the middle
    gap = min(2.2, w * 0.3)
    seg = (w - gap) / 2
    geo.append(wall((cx - gap / 2 - seg / 2, wall_height / 2, cz - d / 2), (seg, wall_height, t), color=color))
    geo.append(wall((cx + gap / 2 + seg / 2, wall_height / 2, cz - d / 2), (seg, wall_height, t), color=color))
    room_meta = {"name": name, "position": (cx, cz), "size": (w, d)}
    return room_meta, geo
