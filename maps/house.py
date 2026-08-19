"""
LEVEL 1 - HOUSE

The polished, fully hand-laid-out starter level. Small abandoned house:
living room, kitchen, bedroom, hallway, storage room, basement (represented
as a sunken room), and an outdoor yard. Introduces basic transformation.
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    # Layout (grid, each room 8x8, arranged around a central hallway)
    living_meta, living_geo = rectangular_room("Living Room", (-9, 9), (8, 8))
    kitchen_meta, kitchen_geo = rectangular_room("Kitchen", (9, 9), (8, 8))
    bedroom_meta, bedroom_geo = rectangular_room("Bedroom", (-9, -9), (8, 8))
    storage_meta, storage_geo = rectangular_room("Storage Room", (9, -9), (8, 8))
    hallway_meta, hallway_geo = rectangular_room("Hallway", (0, 0), (6, 6))
    basement_meta, basement_geo = rectangular_room("Basement", (0, -20), (10, 10), wall_height=3.2, color=(60, 60, 70))
    yard_meta, yard_geo = rectangular_room("Outdoor Yard", (0, 22), (16, 12), wall_height=0.1, color=(40, 90, 45))

    for meta, geo in (
        (living_meta, living_geo), (kitchen_meta, kitchen_geo),
        (bedroom_meta, bedroom_geo), (storage_meta, storage_geo),
        (hallway_meta, hallway_geo), (basement_meta, basement_geo),
        (yard_meta, yard_geo),
    ):
        rooms.append(meta)
        geometry.extend(geo)

    # decorative non-hideable structural props
    geometry.append(prop("counter", (9, 0.5, 7), color=(180, 180, 190), scale=(3, 1, 1)))
    geometry.append(prop("bookshelf", (-12.5, 1.5, 9), color=(90, 60, 40), scale=(0.5, 3, 2)))
    geometry.append(prop("stairs", (0, 0.5, -12), color=(110, 100, 90), scale=(3, 1, 6)))

    hider_spawn_objects = [
        hider_object("chair", (-11, 0.5, 11)),
        hider_object("chair", (-7, 0.5, 11)),
        hider_object("table", (-9, 0.4, 7)),
        hider_object("plant", (-12, 0.7, 6)),
        hider_object("lamp", (11, 0.65, 6)),
        hider_object("bin", (12, 0.5, 12)),
        hider_object("box", (7, 0.5, 12)),
        hider_object("crate", (6, 0.5, 6)),
        hider_object("chair", (-11, 0.5, -11)),
        hider_object("box", (-7, 0.5, -12)),
        hider_object("barrel", (12, 0.6, -11)),
        hider_object("crate", (6, 0.5, -6)),
        hider_object("monitor", (9, 0.85, -6)),
        hider_object("plant", (2, 0.7, 21)),
        hider_object("barrel", (-4, 0.6, 24)),
        hider_object("box", (0, 0.5, -18)),
        hider_object("crate", (3, 0.5, -22)),
    ]

    hunter_spawns = [(0, 1, 0), (0, 1, 2), (-1, 1, 1)]

    objectives = [
        objective("switch_1", "switch", (-11, 1.0, 6), "Fuse Switch"),
        objective("terminal_1", "terminal", (11, 1.0, -11), "Storage Terminal"),
        objective("panel_1", "panel", (0, 1.0, -20), "Basement Control Panel"),
        objective("fragment_1", "fragment", (2, 1.0, 24), "Energy Fragment"),
    ]

    return {
        "name": "House",
        "bounds": (30, 40),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
