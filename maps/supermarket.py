"""
LEVEL 3 - SUPERMARKET

A vibrant supermarket filled with dense product aisles, checkouts, and stockroom:
- Sales Floor with multiple parallel grocery aisles (tall shelves, produce bins)
- Checkout Lanes (registers, conveyor belts, shopping carts)
- Bakery & Deli Bar (warm counters, display cases)
- Back Stockroom (pallet stacks, heavy steel storage racks)
"""
from maps._builder import rectangular_room, hider_object, objective, prop


def build():
    geometry = []
    rooms = []

    # 1. Main Sales Floor
    sales_meta, sales_geo = rectangular_room(
        "Sales Floor", (0, 0), (28, 22),
        wall_height=3.8,
        floor_color=(215, 215, 220),      # bright grocery vinyl
        wall_color=(190, 200, 210),      # friendly sky blue/white
        door_wall="back", door_width=4.0
    )
    rooms.append(sales_meta)
    geometry.extend(sales_geo)

    # 2. Back Stockroom (Behind the main floor)
    stock_meta, stock_geo = rectangular_room(
        "Stockroom", (0, 16), (20, 10),
        wall_height=4.0,
        floor_color=(80, 80, 85),         # industrial warehouse concrete
        wall_color=(130, 125, 120),      # cinder block
        door_wall="front", door_width=4.0
    )
    rooms.append(stock_meta)
    geometry.extend(stock_geo)

    # Aisle Shelves on Sales Floor (4 parallel rows with gaps in between)
    aisle_xs = [-9, -3, 3, 9]
    for ax in aisle_xs:
        # Lower shelf base
        geometry.append(prop("shelf_base", (ax, 0.9, 0), color=(140, 145, 155), scale=(1.2, 1.8, 14.0)))
        # Colorful goods on top of shelves (cereal boxes / cans)
        geometry.append(prop("shelf_goods_1", (ax, 1.9, 3), color=(220, 80, 70), scale=(0.8, 0.4, 4.0), solid=False))
        geometry.append(prop("shelf_goods_2", (ax, 1.9, -3), color=(60, 160, 210), scale=(0.8, 0.4, 4.0), solid=False))

    # Checkout Lanes (Front of store at z = -7)
    for cx in (-6, 0, 6):
        geometry.append(prop("checkout_counter", (cx, 0.5, -7), color=(60, 80, 110), scale=(1.6, 1.0, 3.5)))
        geometry.append(prop("register_screen", (cx, 1.1, -8.2), color=(30, 30, 35), scale=(0.6, 0.4, 0.4)))

    # Bakery / Deli Counter (Left wall)
    geometry.append(prop("deli_counter", (-12.5, 0.55, 3), color=(190, 140, 90), scale=(1.2, 1.1, 8.0)))

    # Stockroom Heavy Shelves
    geometry.append(prop("heavy_rack_1", (-6, 1.6, 16), color=(200, 110, 30), scale=(1.4, 3.2, 7.0)))
    geometry.append(prop("heavy_rack_2", (6, 1.6, 16), color=(200, 110, 30), scale=(1.4, 3.2, 7.0)))

    # ------------------------------------------------------------------
    # HIDER SPAWN OBJECTS (Camouflage clusters)
    # ------------------------------------------------------------------
    hider_spawn_objects = [
        # Checkouts
        hider_object("cart", (-4, 0.5, -9)),
        hider_object("cart", (2, 0.5, -9)),
        hider_object("cart", (8, 0.5, -9)),
        hider_object("bin", (-7.5, 0.5, -5.5)),
        hider_object("bin", (7.5, 0.5, -5.5)),

        # Aisle 1 (-9)
        hider_object("box", (-11, 0.5, 5)),
        hider_object("crate", (-11, 0.5, 1)),
        hider_object("box", (-11, 0.5, -4)),
        hider_object("barrel", (-7, 0.6, 6)),

        # Aisle 2 (-3)
        hider_object("crate", (-5, 0.5, 3)),
        hider_object("box", (-5, 0.5, -2)),
        hider_object("cart", (-1, 0.5, 5)),
        hider_object("barrel", (-1, 0.6, -5)),

        # Aisle 3 (3)
        hider_object("box", (1, 0.5, 2)),
        hider_object("crate", (5, 0.5, 6)),
        hider_object("box", (5, 0.5, -4)),
        hider_object("cart", (5, 0.5, 1)),

        # Aisle 4 (9)
        hider_object("barrel", (7, 0.6, 4)),
        hider_object("crate", (11, 0.5, 6)),
        hider_object("box", (11, 0.5, 0)),
        hider_object("bin", (11, 0.5, -5)),

        # Deli & Entrance
        hider_object("plant", (-12, 0.7, -9)),
        hider_object("plant", (12, 0.7, -9)),
        hider_object("lamp", (-12, 0.65, 9)),

        # Stockroom
        hider_object("crate", (-2, 0.5, 14)),
        hider_object("crate", (2, 0.5, 14)),
        hider_object("crate", (-2, 0.5, 18)),
        hider_object("barrel", (2, 0.6, 18)),
        hider_object("barrel", (-8, 0.6, 19)),
        hider_object("box", (8, 0.5, 19)),
        hider_object("cart", (0, 0.5, 16)),
    ]

    hunter_spawns = [(0, 1.0, -9), (1, 1.0, -9)]

    objectives = [
        objective("register_pos", "terminal", (0, 1.0, -7.0), "Main Checkout Register"),
        objective("deli_scale", "switch", (-12.0, 1.0, 3.0), "Deli Slicer Power"),
        objective("stock_forklift", "panel", (0, 1.0, 18.0), "Stockroom Cargo Lift"),
        objective("produce_sprinkler", "valve", (12.0, 1.0, 0.0), "Produce Sprinkler Valve"),
    ]

    return {
        "name": "Supermarket",
        "bounds": (32, 36),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }
