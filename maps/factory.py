"""
LEVEL 5 - FACTORY

Hazards (visual only in this MVP — flagged as "hazard" props hunters/hiders
should route around, reserved for future damage-over-time expansion) and
more control-panel objectives requiring Hiders to spread across the map.
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    layout = [
        ("Assembly Line", (0, 12), (20, 10)),
        ("Foundry", (-16, -6), (10, 10)),
        ("Control Room", (16, -6), (8, 8)),
        ("Chemical Storage", (0, -18), (12, 8)),
    ]
    for name, center, size in layout:
        meta, geo = rectangular_room(name, center, size, wall_height=4.5, color=(100, 90, 90))
        rooms.append(meta)
        geometry.extend(geo)

    # hazard markers (visual only, non-hideable) - glowing orange
    geometry.append(prop("hazard_vat", (-16, 0.8, -8), color=(230, 110, 20), scale=(2, 1.6, 2)))
    geometry.append(prop("hazard_conveyor", (0, 0.5, 12), color=(200, 90, 20), scale=(14, 0.6, 1.5)))
    geometry.append(prop("hazard_pipes", (16, 1.0, -8), color=(210, 100, 20), scale=(1, 2, 6)))

    hider_spawn_objects = [
        hider_object("crate", (-6, 0.5, 12)), hider_object("box", (-2, 0.5, 14)),
        hider_object("barrel", (4, 0.6, 14)), hider_object("monitor", (8, 0.85, 12)),
        hider_object("crate", (-16, 0.5, -3)), hider_object("barrel", (-19, 0.6, -8)),
        hider_object("box", (-13, 0.5, -9)), hider_object("bin", (-16, 0.5, -10)),
        hider_object("monitor", (16, 0.85, -3)), hider_object("chair", (14, 0.5, -6)),
        hider_object("table", (18, 0.4, -8)), hider_object("lamp", (16, 0.65, -9)),
        hider_object("barrel", (-4, 0.6, -18)), hider_object("crate", (2, 0.5, -20)),
        hider_object("box", (4, 0.5, -16)), hider_object("bin", (-2, 0.5, -16)),
    ]

    hunter_spawns = [(0, 1, 0), (1, 1, 0)]

    objectives = [
        objective("panel_1", "panel", (0, 1.0, 12), "Assembly Line Panel"),
        objective("switch_1", "switch", (-16, 1.0, -6), "Foundry Switch"),
        objective("terminal_1", "terminal", (16, 1.0, -6), "Control Room Terminal"),
        objective("panel_2", "panel", (0, 1.0, -18), "Chemical Storage Panel"),
    ]

    return {
        "name": "Factory",
        "bounds": (34, 34),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
