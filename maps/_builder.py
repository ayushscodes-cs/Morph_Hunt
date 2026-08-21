"""
Reusable modular level-building helpers shared by every map module.

Maps are described purely as data (lists of dicts) so both the server
and client build identical layouts, visuals, and collisions.
"""

def floor(position, size, color=(90, 90, 95)):
    """size = (width, depth). Floor height is fixed at y=0, thickness 0.2."""
    return {"type": "floor", "position": (position[0], 0, position[1]), "scale": (size[0], 0.2, size[1]), "color": color, "solid": True}


def wall(position, size, color=(120, 120, 130)):
    """size = (width, height, thickness)"""
    return {"type": "wall", "position": position, "scale": size, "color": color, "solid": True}


def prop(kind, position, color=(150, 130, 100), scale=(1, 1, 1), solid=True):
    """A static (non-hideable) decorative structure prop."""
    return {"type": "prop", "kind": kind, "position": position, "scale": scale, "color": color, "solid": solid}


def hider_object(key, position):
    """A spawn point where a Hider-controlled object may appear/hide."""
    return {"key": key, "position": position}


def objective(obj_id, kind, position, label):
    return {"id": obj_id, "kind": kind, "position": position, "label": label}


def rectangular_room(name, center, size, wall_height=3.2, floor_color=(75, 75, 82), wall_color=(150, 150, 160), door_wall="front", door_width=2.4, color=None):
    if color is not None:
        floor_color = color
        wall_color = color

    cx, cz = center
    w, d = size
    geo = [floor((cx, cz), (w, d), color=floor_color)]
    t = 0.3
    hw = wall_height / 2

    if door_wall == "back":
        seg = (w - door_width) / 2
        geo.append(wall((cx - door_width / 2 - seg / 2, hw, cz + d / 2), (seg, wall_height, t), color=wall_color))
        geo.append(wall((cx + door_width / 2 + seg / 2, hw, cz + d / 2), (seg, wall_height, t), color=wall_color))
    else:
        geo.append(wall((cx, hw, cz + d / 2), (w, wall_height, t), color=wall_color))

    if door_wall == "front":
        seg = (w - door_width) / 2
        geo.append(wall((cx - door_width / 2 - seg / 2, hw, cz - d / 2), (seg, wall_height, t), color=wall_color))
        geo.append(wall((cx + door_width / 2 + seg / 2, hw, cz - d / 2), (seg, wall_height, t), color=wall_color))
    else:
        geo.append(wall((cx, hw, cz - d / 2), (w, wall_height, t), color=wall_color))

    if door_wall == "left":
        seg = (d - door_width) / 2
        geo.append(wall((cx - w / 2, hw, cz - door_width / 2 - seg / 2), (t, wall_height, seg), color=wall_color))
        geo.append(wall((cx - w / 2, hw, cz + door_width / 2 + seg / 2), (t, wall_height, seg), color=wall_color))
    else:
        geo.append(wall((cx - w / 2, hw, cz), (t, wall_height, d), color=wall_color))

    if door_wall == "right":
        seg = (d - door_width) / 2
        geo.append(wall((cx + w / 2, hw, cz - door_width / 2 - seg / 2), (t, wall_height, seg), color=wall_color))
        geo.append(wall((cx + w / 2, hw, cz + door_width / 2 + seg / 2), (t, wall_height, seg), color=wall_color))
    else:
        geo.append(wall((cx + w / 2, hw, cz), (t, wall_height, d), color=wall_color))

    room_meta = {
        "name": name,
        "position": (cx, cz),
        "size": (w, d)
    }

    return room_meta, geo
