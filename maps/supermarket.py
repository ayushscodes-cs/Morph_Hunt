"""
LEVEL 3 - SUPERMARKET

Many similar objects (crates, boxes, carts) packed into aisles, making it
hard for Hunters to visually tell disguised Hiders apart from real props.
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    meta, geo = rectangular_room("Sales Floor", (0, 0), (26, 22), color=(150, 150, 140))
    rooms.append(meta)
    geometry.extend(geo)

    meta2, geo2 = rectangular_room("Stock Room", (0, 16), (12, 8), color=(130, 120, 110))
    rooms.append(meta2)
    geometry.extend(geo2)

    # Aisle shelf props (visual, non-hideable) laid out in rows
    aisle_xs = [-9, -3, 3, 9]
    for ax in aisle_xs:
        geometry.append(prop("shelf", (ax, 0.9, 0), color=(120, 100, 80), scale=(1, 1.8, 16)))

    hider_spawn_objects = []
    # Fill aisles with crates/boxes/carts/barrels to create camouflage clusters
    row_zs = [-8, -4, 0, 4, 8]
    keys_cycle = ["crate", "box", "barrel", "cart", "bin"]
    i = 0
    for ax in (-11, -1, 1, 11):
        for z in row_zs:
            key = keys_cycle[i % len(keys_cycle)]
            hider_spawn_objects.append(hider_object(key, (ax, 0.55, z)))
            i += 1

    hider_spawn_objects.append(hider_object("plant", (0, 0.7, 9)))
    hider_spawn_objects.append(hider_object("lamp", (0, 0.65, -9)))
    hider_spawn_objects.append(hider_object("crate", (0, 0.5, 16)))
    hider_spawn_objects.append(hider_object("box", (3, 0.5, 17)))

    hunter_spawns = [(0, 1, -10), (1, 1, -10)]

    objectives = [
        objective("switch_1", "switch", (-9, 1.0, 10), "Loading Dock Switch"),
        objective("terminal_1", "terminal", (9, 1.0, 10), "Register Terminal"),
        objective("panel_1", "panel", (0, 1.0, 18), "Stock Room Panel"),
    ]

    return {
        "name": "Supermarket",
        "bounds": (30, 34),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
