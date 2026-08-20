"""
LEVEL 2 - OFFICE

A modern corporate office with distinct zones:
- Reception Lobby (welcoming counter, waiting sofa, potted plants)
- Open Cubicles (office desks, computer setups, trash bins)
- Meeting Conference Room (large conference table, whiteboard)
- Break Room (tiled cafeteria, coffee bar, vending counter)
- Server Room (metal floor, glowing server racks, cables)
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    # 1. Reception & Main Hall
    rec_meta, rec_geo = rectangular_room(
        "Reception", (0, 0), (8, 8),
        wall_height=3.2,
        floor_color=(195, 195, 200),      # polished white marble
        wall_color=(90, 110, 130),        # corporate blue/slate
        door_wall="none"
    )
    rooms.append(rec_meta)
    geometry.extend(rec_geo)

    # Reception furniture
    geometry.append(prop("reception_desk", (0, 0.5, 2), color=(140, 100, 65), scale=(4.0, 1.0, 1.2)))
    geometry.append(prop("waiting_sofa", (0, 0.4, -2.5), color=(50, 65, 85), scale=(4.2, 0.8, 1.2)))

    # 2. Open Cubicles (Left-Front)
    cub_meta, cub_geo = rectangular_room(
        "Cubicles", (-10, 7), (10, 8),
        wall_height=3.2,
        floor_color=(95, 100, 110),       # office carpet
        wall_color=(205, 210, 215),       # clean off-white
        door_wall="right", door_width=2.5
    )
    rooms.append(cub_meta)
    geometry.extend(cub_geo)

    # Cubicle desk partitions
    geometry.append(prop("desk_row_1", (-10, 0.45, 8.5), color=(170, 175, 180), scale=(6.0, 0.9, 1.2)))
    geometry.append(prop("desk_divider", (-10, 0.9, 8.5), color=(60, 120, 160), scale=(6.0, 0.6, 0.1)))
    geometry.append(prop("desk_row_2", (-10, 0.45, 5.5), color=(170, 175, 180), scale=(6.0, 0.9, 1.2)))

    # 3. Meeting Room (Right-Front)
    meet_meta, meet_geo = rectangular_room(
        "Meeting Room", (10, 7), (10, 8),
        wall_height=3.2,
        floor_color=(120, 75, 50),        # mahogany wood
        wall_color=(75, 90, 115),         # navy feature wall
        door_wall="left", door_width=2.5
    )
    rooms.append(meet_meta)
    geometry.extend(meet_geo)

    # Meeting room furniture
    geometry.append(prop("conf_table", (10, 0.45, 7), color=(90, 50, 30), scale=(5.0, 0.9, 2.2)))
    geometry.append(prop("whiteboard", (14.7, 1.5, 7), color=(240, 240, 245), scale=(0.1, 1.8, 3.5)))

    # 4. Break Room (Left-Back)
    break_meta, break_geo = rectangular_room(
        "Break Room", (-10, -7), (10, 8),
        wall_height=3.2,
        floor_color=(170, 160, 150),      # checkered cafe tile
        wall_color=(215, 185, 150),       # warm peach/latte
        door_wall="right", door_width=2.5
    )
    rooms.append(break_meta)
    geometry.extend(break_geo)

    # Break room furniture
    geometry.append(prop("coffee_counter", (-10, 0.5, -9.5), color=(70, 60, 55), scale=(4.5, 1.0, 1.2)))
    geometry.append(prop("vending_machine", (-14.5, 1.1, -6), color=(40, 120, 180), scale=(1.2, 2.2, 1.2)))
    geometry.append(prop("dining_table", (-8, 0.4, -6), color=(180, 160, 130), scale=(2.2, 0.8, 2.2)))

    # 5. Server Room (Right-Back)
    serv_meta, serv_geo = rectangular_room(
        "Server Room", (10, -7), (10, 8),
        wall_height=3.2,
        floor_color=(45, 50, 60),         # industrial steel grate
        wall_color=(35, 40, 50),          # dark high-tech slate
        door_wall="left", door_width=2.5
    )
    rooms.append(serv_meta)
    geometry.extend(serv_geo)

    # Server racks
    geometry.append(prop("rack_1", (8, 1.4, -8.5), color=(25, 30, 40), scale=(1.0, 2.8, 3.5)))
    geometry.append(prop("rack_2", (12, 1.4, -8.5), color=(25, 30, 40), scale=(1.0, 2.8, 3.5)))
    geometry.append(prop("rack_glow", (8, 1.4, -8.5), color=(40, 200, 220), scale=(0.1, 2.4, 3.2), solid=False))

    # ------------------------------------------------------------------
    # HIDER SPAWN OBJECTS
    # ------------------------------------------------------------------
    hider_spawn_objects = [
        # Reception
        hider_object("plant", (3.2, 0.7, 3.2)),
        hider_object("plant", (-3.2, 0.7, 3.2)),
        hider_object("bin", (3.2, 0.5, -3.2)),
        hider_object("chair", (-3.2, 0.5, 0)),

        # Cubicles
        hider_object("monitor", (-12, 0.85, 8.5)),
        hider_object("monitor", (-8, 0.85, 8.5)),
        hider_object("monitor", (-10, 0.85, 5.5)),
        hider_object("chair", (-12, 0.5, 7.2)),
        hider_object("chair", (-8, 0.5, 7.2)),
        hider_object("chair", (-10, 0.5, 4.2)),
        hider_object("bin", (-14, 0.5, 4)),
        hider_object("plant", (-6, 0.7, 10)),
        hider_object("box", (-13, 0.5, 10)),

        # Meeting Room
        hider_object("chair", (8, 0.5, 6)),
        hider_object("chair", (10, 0.5, 6)),
        hider_object("chair", (12, 0.5, 6)),
        hider_object("chair", (8, 0.5, 8)),
        hider_object("chair", (10, 0.5, 8)),
        hider_object("chair", (12, 0.5, 8)),
        hider_object("lamp", (14, 0.65, 10)),
        hider_object("plant", (6, 0.7, 10)),
        hider_object("monitor", (10, 0.85, 7)),

        # Break Room
        hider_object("chair", (-7, 0.5, -5)),
        hider_object("chair", (-9, 0.5, -5)),
        hider_object("bin", (-6, 0.5, -9.5)),
        hider_object("box", (-14, 0.5, -9.5)),
        hider_object("lamp", (-6, 0.65, -4)),

        # Server Room
        hider_object("box", (10, 0.5, -5)),
        hider_object("crate", (13, 0.5, -5)),
        hider_object("monitor", (6, 0.85, -6)),
        hider_object("bin", (6, 0.5, -9)),
        hider_object("barrel", (14, 0.6, -9)),
    ]

    hunter_spawns = [(0, 1.0, -1), (0, 1.0, 1)]

    objectives = [
        objective("reception_pc", "terminal", (0, 1.0, 2.2), "Reception Guest Terminal"),
        objective("server_main", "switch", (10.0, 1.0, -9.0), "Mainframe Server Breaker"),
        objective("conf_projector", "panel", (14.5, 1.0, 7.0), "Conference AV Panel"),
        objective("coffee_machine", "switch", (-10.0, 1.0, -9.5), "Breakroom Power Switch"),
    ]

    return {
        "name": "Office",
        "bounds": (28, 26),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
