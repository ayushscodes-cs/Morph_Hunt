"""
LEVEL 4 - WAREHOUSE

A massive industrial distribution hub with high ceilings:
- Central Gantry Crane Corridor (connecting all bays)
- Loading Bay 1 & 2 (with yellow caution floor stripes)
- Storage Block A (high-tier metal pallet racks)
- Storage Block B (chemical barrel storage)
- Sorting & Packaging Area (roller conveyor lines)
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    # 1. Central Corridor
    corridor_meta, corridor_geo = rectangular_room(
        "Central Bay", (0, 0), (10, 30),
        wall_height=4.5,
        floor_color=(70, 72, 78),          # polished warehouse concrete
        wall_color=(90, 95, 105),          # industrial steel
        door_wall="none"
    )
    rooms.append(corridor_meta)
    geometry.extend(corridor_geo)

    # Overhead yellow gantry crane fixture
    geometry.append(prop("overhead_crane_beam", (0, 4.0, 0), color=(230, 180, 20), scale=(9.5, 0.6, 1.0), solid=False))
    geometry.append(prop("crane_hoist", (0, 3.2, 0), color=(40, 40, 45), scale=(1.2, 1.2, 1.2)))

    # 2. Loading Bay (Left-Front)
    bay_meta, bay_geo = rectangular_room(
        "Loading Bay", (-14, 10), (14, 10),
        wall_height=4.5,
        floor_color=(60, 62, 68),          # heavy loading concrete
        wall_color=(105, 108, 115),
        door_wall="right", door_width=3.5
    )
    rooms.append(bay_meta)
    geometry.extend(bay_geo)

    # Yellow caution stripe at bay entrance
    geometry.append(prop("caution_stripe", (-14, 0.05, 5.2), color=(235, 195, 30), scale=(12.0, 0.1, 0.6), solid=False))

    # 3. Storage Block A (Right-Front)
    block_a_meta, block_a_geo = rectangular_room(
        "Storage Block A", (14, 10), (14, 10),
        wall_height=4.5,
        floor_color=(65, 68, 72),
        wall_color=(100, 105, 110),
        door_wall="left", door_width=3.5
    )
    rooms.append(block_a_meta)
    geometry.extend(block_a_geo)

    # Multi-tier racks in Block A
    geometry.append(prop("high_rack_1", (14, 2.0, 12), color=(180, 90, 30), scale=(10.0, 4.0, 1.5)))
    geometry.append(prop("high_rack_2", (14, 2.0, 8), color=(180, 90, 30), scale=(10.0, 4.0, 1.5)))

    # 4. Storage Block B (Left-Back)
    block_b_meta, block_b_geo = rectangular_room(
        "Storage Block B", (-14, -10), (14, 10),
        wall_height=4.5,
        floor_color=(55, 58, 62),
        wall_color=(95, 100, 105),
        door_wall="right", door_width=3.5
    )
    rooms.append(block_b_meta)
    geometry.extend(block_b_geo)

    # Heavy pallet stacks in Block B
    geometry.append(prop("pallet_stack_1", (-14, 1.0, -12), color=(140, 105, 65), scale=(4.0, 2.0, 3.0)))
    geometry.append(prop("pallet_stack_2", (-14, 1.0, -8), color=(140, 105, 65), scale=(4.0, 2.0, 3.0)))

    # 5. Sorting & Packaging (Right-Back)
    sort_meta, sort_geo = rectangular_room(
        "Sorting Area", (14, -10), (14, 10),
        wall_height=4.5,
        floor_color=(68, 70, 75),
        wall_color=(100, 105, 110),
        door_wall="left", door_width=3.5
    )
    rooms.append(sort_meta)
    geometry.extend(sort_geo)

    # Sorting roller conveyor
    geometry.append(prop("conveyor_line", (14, 0.6, -10), color=(50, 110, 160), scale=(10.0, 0.8, 1.6)))

    # ------------------------------------------------------------------
    # HIDER SPAWN OBJECTS
    # ------------------------------------------------------------------
    hider_spawn_objects = [
        # Central Corridor
        hider_object("crate", (-3, 0.5, 12)),
        hider_object("crate", (3, 0.5, 12)),
        hider_object("barrel", (-3, 0.6, -12)),
        hider_object("barrel", (3, 0.6, -12)),
        hider_object("cart", (0, 0.5, 6)),
        hider_object("cart", (0, 0.5, -6)),
        hider_object("bin", (-3, 0.5, 0)),
        hider_object("bin", (3, 0.5, 0)),

        # Loading Bay
        hider_object("crate", (-18, 0.5, 12)),
        hider_object("crate", (-16, 0.5, 8)),
        hider_object("barrel", (-12, 0.6, 13)),
        hider_object("box", (-10, 0.5, 7)),
        hider_object("cart", (-18, 0.5, 7)),

        # Storage Block A
        hider_object("box", (10, 0.5, 12)),
        hider_object("crate", (18, 0.5, 12)),
        hider_object("box", (10, 0.5, 8)),
        hider_object("crate", (18, 0.5, 8)),
        hider_object("barrel", (14, 0.6, 6)),

        # Storage Block B
        hider_object("barrel", (-18, 0.6, -12)),
        hider_object("barrel", (-16, 0.6, -8)),
        hider_object("barrel", (-12, 0.6, -13)),
        hider_object("crate", (-18, 0.5, -7)),
        hider_object("box", (-10, 0.5, -8)),

        # Sorting Area
        hider_object("box", (10, 0.5, -13)),
        hider_object("box", (18, 0.5, -13)),
        hider_object("crate", (14, 0.5, -7)),
        hider_object("cart", (18, 0.5, -7)),
        hider_object("bin", (10, 0.5, -7)),
        hider_object("monitor", (16, 0.85, -10)),
    ]

    hunter_spawns = [(0, 1.0, 0), (0, 1.0, 3)]

    objectives = [
        objective("crane_control", "terminal", (0, 1.0, 0), "Gantry Crane Terminal"),
        objective("bay_shutter", "switch", (-19.0, 1.0, 10.0), "Loading Bay Shutter"),
        objective("rack_lift", "panel", (19.0, 1.0, 10.0), "Block A Forklift Panel"),
        objective("chemical_shutoff", "valve", (-19.0, 1.0, -10.0), "Block B Emergency Shutoff"),
        objective("sorter_power", "switch", (19.0, 1.0, -10.0), "Conveyor Sorter Switch"),
    ]

    return {
        "name": "Warehouse",
        "bounds": (38, 38),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
