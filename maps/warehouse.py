"""
LEVEL 4 - WAREHOUSE

Large map, multiple distinct areas connected by a central corridor.
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    layout = [
        ("Loading Bay", (-16, 14), (14, 12)),
        ("Storage Block A", (16, 14), (14, 12)),
        ("Storage Block B", (-16, -14), (14, 12)),
        ("Sorting Area", (16, -14), (14, 12)),
        ("Central Corridor", (0, 0), (10, 30)),
    ]
    for name, center, size in layout:
        meta, geo = rectangular_room(name, center, size, wall_height=4.0, color=(110, 110, 120))
        rooms.append(meta)
        geometry.extend(geo)

    geometry.append(prop("crane", (0, 2.5, 0), color=(200, 170, 40), scale=(1, 5, 1)))
    geometry.append(prop("shelf_row", (-16, 1.2, 14), color=(120, 100, 80), scale=(10, 2.4, 1)))
    geometry.append(prop("shelf_row", (16, 1.2, -14), color=(120, 100, 80), scale=(10, 2.4, 1)))

    hider_spawn_objects = [
        hider_object("crate", (-20, 0.5, 16)), hider_object("crate", (-18, 0.5, 12)),
        hider_object("barrel", (-14, 0.6, 18)), hider_object("box", (-12, 0.5, 10)),
        hider_object("crate", (20, 0.5, 16)), hider_object("box", (18, 0.5, 12)),
        hider_object("monitor", (14, 0.85, 18)), hider_object("cart", (12, 0.5, 10)),
        hider_object("barrel", (-20, 0.6, -16)), hider_object("crate", (-18, 0.5, -12)),
        hider_object("bin", (-14, 0.5, -18)), hider_object("box", (-12, 0.5, -10)),
        hider_object("cart", (20, 0.5, -16)), hider_object("crate", (18, 0.5, -12)),
        hider_object("barrel", (14, 0.6, -18)), hider_object("box", (12, 0.5, -10)),
        hider_object("crate", (0, 0.5, 12)), hider_object("crate", (0, 0.5, -12)),
        hider_object("bin", (2, 0.5, 4)), hider_object("box", (-2, 0.5, -4)),
    ]

    hunter_spawns = [(0, 1, 0), (0, 1, 2)]

    objectives = [
        objective("switch_1", "switch", (-16, 1.0, 14), "Loading Bay Switch"),
        objective("terminal_1", "terminal", (16, 1.0, 14), "Block A Terminal"),
        objective("panel_1", "panel", (-16, 1.0, -14), "Block B Panel"),
        objective("fragment_1", "fragment", (16, 1.0, -14), "Sorting Area Fragment"),
    ]

    return {
        "name": "Warehouse",
        "bounds": (40, 36),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
