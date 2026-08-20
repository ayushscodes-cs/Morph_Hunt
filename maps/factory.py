"""
LEVEL 5 - FACTORY

A heavy manufacturing plant with active industrial machinery:
- Main Assembly Line (long automated conveyor with machining blocks)
- Smelting Foundry (furnaces, molten vats with orange warning glow)
- Central Control Room (glass-paneled operations center, computer banks)
- Chemical Vat Storage (large fluid tanks, overhead steel piping)
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    # 1. Main Assembly Hall (Front)
    assem_meta, assem_geo = rectangular_room(
        "Assembly Hall", (0, 10), (22, 12),
        wall_height=4.5,
        floor_color=(60, 62, 65),          # oily industrial steel
        wall_color=(90, 85, 80),           # soot-stained brick
        door_wall="back", door_width=3.5
    )
    rooms.append(assem_meta)
    geometry.extend(assem_geo)

    # Automated assembly line conveyor with machinery
    geometry.append(prop("assembly_conveyor", (0, 0.6, 10), color=(45, 95, 140), scale=(16.0, 0.8, 1.8)))
    geometry.append(prop("machine_block_1", (-4, 1.4, 10), color=(180, 160, 50), scale=(2.0, 2.0, 2.2)))
    geometry.append(prop("machine_block_2", (4, 1.4, 10), color=(180, 160, 50), scale=(2.0, 2.0, 2.2)))

    # 2. Smelting Foundry (Left-Back)
    foundry_meta, foundry_geo = rectangular_room(
        "Foundry", (-12, -8), (14, 12),
        wall_height=4.5,
        floor_color=(45, 40, 42),          # heat-darkened stone
        wall_color=(120, 70, 50),          # rust red furnace wall
        door_wall="front", door_width=3.0
    )
    rooms.append(foundry_meta)
    geometry.extend(foundry_geo)

    # Molten furnace structure & hazard vat
    geometry.append(prop("furnace_core", (-12, 1.5, -12), color=(235, 90, 25), scale=(4.0, 3.0, 3.0)))
    geometry.append(prop("furnace_glow", (-12, 1.5, -10.4), color=(255, 170, 40), scale=(2.4, 1.8, 0.2), solid=False))

    # 3. Chemical Tanker Bay (Right-Back)
    chem_meta, chem_geo = rectangular_room(
        "Chemical Vats", (12, -8), (14, 12),
        wall_height=4.5,
        floor_color=(50, 55, 60),
        wall_color=(75, 90, 85),           # chemical acid green/slate
        door_wall="front", door_width=3.0
    )
    rooms.append(chem_meta)
    geometry.extend(chem_geo)

    # Chemical storage vats & overhead pipes
    geometry.append(prop("chem_vat_1", (10, 1.8, -11), color=(40, 180, 120), scale=(3.0, 3.6, 3.0)))
    geometry.append(prop("chem_vat_2", (15, 1.8, -11), color=(40, 180, 120), scale=(3.0, 3.6, 3.0)))
    geometry.append(prop("overhead_pipes", (12, 3.6, -8), color=(200, 140, 30), scale=(8.0, 0.4, 0.4), solid=False))

    # 4. Central Control Bridge (Midway connecting area)
    ctrl_meta, ctrl_geo = rectangular_room(
        "Control Room", (0, -2), (8, 6),
        wall_height=3.5,
        floor_color=(75, 80, 90),
        wall_color=(60, 75, 95),           # modern tech blue
        door_wall="none"
    )
    rooms.append(ctrl_meta)
    geometry.extend(ctrl_geo)

    # Control console desks
    geometry.append(prop("console_desk", (0, 0.5, -2), color=(40, 45, 55), scale=(4.5, 1.0, 1.2)))

    # ------------------------------------------------------------------
    # HIDER SPAWN OBJECTS
    # ------------------------------------------------------------------
    hider_spawn_objects = [
        # Assembly Hall
        hider_object("crate", (-8, 0.5, 14)),
        hider_object("crate", (-8, 0.5, 6)),
        hider_object("box", (8, 0.5, 14)),
        hider_object("box", (8, 0.5, 6)),
        hider_object("barrel", (0, 0.6, 14)),
        hider_object("cart", (-6, 0.5, 7)),
        hider_object("cart", (6, 0.5, 7)),
        hider_object("bin", (-9, 0.5, 10)),
        hider_object("bin", (9, 0.5, 10)),

        # Foundry
        hider_object("barrel", (-16, 0.6, -6)),
        hider_object("barrel", (-8, 0.6, -6)),
        hider_object("crate", (-16, 0.5, -12)),
        hider_object("box", (-8, 0.5, -12)),
        hider_object("cart", (-12, 0.5, -6)),

        # Chemical Vats
        hider_object("barrel", (8, 0.6, -6)),
        hider_object("barrel", (16, 0.6, -6)),
        hider_object("crate", (8, 0.5, -12)),
        hider_object("crate", (12, 0.5, -5)),
        hider_object("box", (16, 0.5, -5)),
        hider_object("bin", (16, 0.5, -12)),

        # Control Room
        hider_object("chair", (-1.5, 0.5, -3.2)),
        hider_object("chair", (1.5, 0.5, -3.2)),
        hider_object("monitor", (-1.5, 0.85, -2)),
        hider_object("monitor", (1.5, 0.85, -2)),
        hider_object("plant", (-3, 0.7, 0)),
        hider_object("lamp", (3, 0.65, 0)),
    ]

    hunter_spawns = [(0, 1.0, 0), (0, 1.0, 2)]

    objectives = [
        objective("assembly_breaker", "switch", (0, 1.0, 14.5), "Assembly Conveyor Breaker"),
        objective("furnace_temp", "panel", (-12.0, 1.0, -13.5), "Foundry Temp Regulator"),
        objective("vat_release", "valve", (12.0, 1.0, -13.5), "Chemical Pressure Valve"),
        objective("master_terminal", "terminal", (0, 1.0, -2.0), "Factory Master Terminal"),
    ]

    return {
        "name": "Factory",
        "bounds": (32, 34),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
