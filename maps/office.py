"""
LEVEL 2 - OFFICE

More objects, tighter hiding spaces. Built from the shared modular room
helper so it's data-driven and easy to extend.
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    layout = [
        ("Open Desks", (-10, 8), (10, 8)),
        ("Meeting Room", (10, 8), (7, 7)),
        ("Break Room", (-10, -8), (7, 7)),
        ("Server Closet", (10, -8), (5, 5)),
        ("Reception", (0, 0), (6, 5)),
    ]
    for name, center, size in layout:
        meta, geo = rectangular_room(name, center, size, color=(140, 140, 150))
        rooms.append(meta)
        geometry.extend(geo)

    geometry.append(prop("desk_row", (-10, 0.5, 10), color=(160, 160, 170), scale=(6, 1, 1)))
    geometry.append(prop("reception_desk", (0, 0.5, -1), color=(170, 150, 120), scale=(3, 1, 1)))

    hider_spawn_objects = [
        hider_object("monitor", (-13, 0.85, 9)),
        hider_object("monitor", (-11, 0.85, 9)),
        hider_object("chair", (-9, 0.5, 6)),
        hider_object("chair", (-13, 0.5, 6)),
        hider_object("box", (10, 0.5, 6)),
        hider_object("table", (10, 0.4, 9)),
        hider_object("plant", (7, 0.7, 11)),
        hider_object("bin", (-13, 0.5, -10)),
        hider_object("crate", (-8, 0.5, -6)),
        hider_object("lamp", (-10, 0.65, -9)),
        hider_object("monitor", (12, 0.85, -8)),
        hider_object("box", (9, 0.5, -6)),
        hider_object("plant", (2, 0.7, 1)),
        hider_object("chair", (-2, 0.5, -1)),
    ]

    hunter_spawns = [(0, 1, -3), (1, 1, -3)]

    objectives = [
        objective("switch_1", "switch", (10, 1.0, -8), "Server Rack Switch"),
        objective("terminal_1", "terminal", (-10, 1.0, -8), "Break Room Terminal"),
        objective("panel_1", "panel", (10, 1.0, 8), "Meeting Room Panel"),
    ]

    return {
        "name": "Office",
        "bounds": (26, 22),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
