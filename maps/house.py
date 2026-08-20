"""
LEVEL 1 - HOUSE

A cozy suburban house with distinct rooms:
- Living Room (wood floor, sofa, bookshelf, TV stand)
- Kitchen (tiled floor, kitchen island counter, cabinets)
- Bedroom (carpet, bed, wardrobe)
- Garage / Storage (concrete, workbench, storage shelves)
- Hallway (connecting central area)
- Outdoor Yard (lush green lawn, wooden fence, bushes)
- Basement (dark stone, stone pillars)
"""
from maps._builder import rectangular_room, hider_object, objective, prop, floor, wall


def build():
    geometry = []
    rooms = []

    # 1. Central Hallway
    hall_meta, hall_geo = rectangular_room(
        "Hallway", (0, 0), (6, 10),
        wall_height=3.2,
        floor_color=(125, 95, 65),       # polished wood
        wall_color=(195, 190, 180),      # warm neutral
        door_wall="none"
    )
    rooms.append(hall_meta)
    geometry.extend(hall_geo)

    # 2. Living Room (Left-Front)
    living_meta, living_geo = rectangular_room(
        "Living Room", (-8, 6), (10, 8),
        wall_height=3.2,
        floor_color=(115, 80, 50),       # rich oak wood
        wall_color=(205, 198, 185),      # warm cream
        door_wall="right", door_width=2.5
    )
    rooms.append(living_meta)
    geometry.extend(living_geo)

    # Living room furniture structures
    geometry.append(prop("sofa", (-8, 0.45, 8.5), color=(65, 85, 120), scale=(3.6, 0.9, 1.2)))      # blue couch
    geometry.append(prop("coffee_table", (-8, 0.25, 6.5), color=(90, 60, 40), scale=(2.2, 0.5, 1.0)))
    geometry.append(prop("tv_unit", (-12.5, 0.7, 6), color=(40, 40, 45), scale=(0.6, 1.4, 2.8)))    # TV entertainment center
    geometry.append(prop("bookshelf", (-8, 1.6, 9.7), color=(100, 68, 42), scale=(3.0, 3.0, 0.4)))

    # 3. Kitchen (Right-Front)
    kitchen_meta, kitchen_geo = rectangular_room(
        "Kitchen", (8, 6), (10, 8),
        wall_height=3.2,
        floor_color=(175, 180, 185),     # light ceramic tile
        wall_color=(160, 185, 180),      # soft sage/mint
        door_wall="left", door_width=2.5
    )
    rooms.append(kitchen_meta)
    geometry.extend(kitchen_geo)

    # Kitchen furniture structures
    geometry.append(prop("island_counter", (8, 0.5, 6), color=(220, 220, 225), scale=(3.2, 1.0, 1.6))) # marble island
    geometry.append(prop("kitchen_cabinet", (12.5, 1.5, 6), color=(95, 105, 105), scale=(0.6, 3.0, 4.0)))
    geometry.append(prop("fridge", (12.5, 1.1, 9.2), color=(210, 215, 220), scale=(0.8, 2.2, 1.0)))

    # 4. Bedroom (Left-Back)
    bedroom_meta, bedroom_geo = rectangular_room(
        "Bedroom", (-8, -6), (10, 8),
        wall_height=3.2,
        floor_color=(70, 85, 110),       # cozy navy carpet
        wall_color=(185, 175, 190),      # soft lavender/gray
        door_wall="right", door_width=2.5
    )
    rooms.append(bedroom_meta)
    geometry.extend(bedroom_geo)

    # Bedroom furniture structures
    geometry.append(prop("bed", (-8, 0.5, -8.5), color=(190, 50, 60), scale=(2.6, 0.8, 3.2)))       # red quilt bed
    geometry.append(prop("wardrobe", (-12.5, 1.5, -6), color=(85, 55, 35), scale=(0.6, 2.8, 2.2)))
    geometry.append(prop("desk", (-4.5, 0.45, -8.5), color=(120, 90, 60), scale=(1.8, 0.9, 1.0)))

    # 5. Garage / Storage (Right-Back)
    garage_meta, garage_geo = rectangular_room(
        "Garage", (8, -6), (10, 8),
        wall_height=3.2,
        floor_color=(75, 75, 80),        # industrial concrete
        wall_color=(140, 135, 130),      # cinderblock gray
        door_wall="left", door_width=2.5
    )
    rooms.append(garage_meta)
    geometry.extend(garage_geo)

    # Garage furniture structures
    geometry.append(prop("workbench", (8, 0.5, -9.5), color=(110, 85, 60), scale=(3.4, 1.0, 1.0)))
    geometry.append(prop("tool_shelf", (12.5, 1.5, -6), color=(60, 80, 100), scale=(0.5, 2.8, 3.0)))

    # 6. Outdoor Yard (Front Garden)
    yard_meta, yard_geo = rectangular_room(
        "Outdoor Yard", (0, 17), (18, 12),
        wall_height=1.2,                 # low wooden fence
        floor_color=(55, 135, 60),       # vibrant green grass
        wall_color=(135, 95, 60),        # wood fence
        door_wall="front", door_width=3.0
    )
    rooms.append(yard_meta)
    geometry.extend(yard_geo)

    # Yard structures
    geometry.append(prop("garden_bench", (-5, 0.4, 18), color=(110, 75, 45), scale=(2.0, 0.7, 0.8)))
    geometry.append(prop("picnic_table", (4, 0.45, 18), color=(130, 95, 60), scale=(2.4, 0.8, 1.6)))

    # 7. Basement (Sunken Room at the back)
    base_meta, base_geo = rectangular_room(
        "Basement", (0, -17), (12, 10),
        wall_height=3.5,
        floor_color=(50, 52, 60),        # dark stone
        wall_color=(85, 88, 95),         # damp brick
        door_wall="front", door_width=2.4
    )
    rooms.append(base_meta)
    geometry.extend(base_geo)

    # Basement pillars
    geometry.append(prop("pillar_1", (-3, 1.75, -17), color=(70, 72, 80), scale=(0.8, 3.5, 0.8)))
    geometry.append(prop("pillar_2", (3, 1.75, -17), color=(70, 72, 80), scale=(0.8, 3.5, 0.8)))

    # ------------------------------------------------------------------
    # HIDER SPAWN OBJECTS (generous variety in every room)
    # ------------------------------------------------------------------
    hider_spawn_objects = [
        # Living Room
        hider_object("chair", (-6, 0.5, 6.5)),
        hider_object("chair", (-10, 0.5, 6.5)),
        hider_object("plant", (-12, 0.7, 9)),
        hider_object("lamp", (-5, 0.65, 9.5)),
        hider_object("table", (-6, 0.4, 4)),

        # Kitchen
        hider_object("bin", (12, 0.5, 4)),
        hider_object("box", (6, 0.5, 9.5)),
        hider_object("lamp", (10, 0.65, 9.5)),
        hider_object("chair", (6, 0.5, 4)),

        # Bedroom
        hider_object("chair", (-4.5, 0.5, -7.5)),
        hider_object("lamp", (-12, 0.65, -9.5)),
        hider_object("plant", (-5, 0.7, -3.5)),
        hider_object("monitor", (-4.5, 0.85, -8.5)),
        hider_object("bin", (-12, 0.5, -3.5)),

        # Garage
        hider_object("crate", (6, 0.5, -4)),
        hider_object("crate", (10, 0.5, -4)),
        hider_object("barrel", (12, 0.6, -9)),
        hider_object("box", (7, 0.5, -8)),
        hider_object("cart", (6, 0.5, -7)),

        # Yard
        hider_object("plant", (-7, 0.7, 14)),
        hider_object("plant", (7, 0.7, 14)),
        hider_object("barrel", (-7, 0.6, 21)),
        hider_object("chair", (2, 0.5, 18)),
        hider_object("box", (7, 0.5, 21)),

        # Basement
        hider_object("crate", (-4.5, 0.5, -14)),
        hider_object("crate", (4.5, 0.5, -14)),
        hider_object("barrel", (0, 0.6, -20)),
        hider_object("box", (-4.5, 0.5, -20)),
        hider_object("cart", (4.5, 0.5, -20)),
        hider_object("bin", (0, 0.5, -14)),

        # Hallway
        hider_object("plant", (2, 0.7, 0)),
        hider_object("lamp", (-2, 0.65, 0)),
    ]

    # Hunter Spawn: in the central hallway
    hunter_spawns = [(0, 1.0, 0), (0, 1.0, 2), (0, 1.0, -2)]

    # Objectives scattered across rooms
    objectives = [
        objective("tv_switch", "switch", (-12.0, 1.0, 6.0), "Living Room Cable Box"),
        objective("kitchen_panel", "panel", (12.0, 1.0, 6.0), "Kitchen Fridge Terminal"),
        objective("bedroom_terminal", "terminal", (-4.5, 1.0, -8.5), "Bedroom PC Terminal"),
        objective("garage_switch", "switch", (12.0, 1.0, -6.0), "Garage Power Box"),
        objective("basement_valve", "valve", (0, 1.0, -20.5), "Basement Water Valve"),
    ]

    return {
        "name": "House",
        "bounds": (30, 42),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
