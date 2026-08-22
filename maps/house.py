from maps._builder import hider_object, objective, prop, floor, wall

def _room_with_doors(name, center, size, wall_height, floor_color, wall_color, doors=None, floor_y=0.0):
    cx, cz = center
    w, d = size
    t = 0.3
    hw = wall_height / 2
    
    geo = [{"type": "floor", "position": (cx, floor_y, cz), "scale": (w, 0.2, d), "color": floor_color, "solid": True, "rotation": (0,0,0)}]

    door_cfg = doors or {}

    front_doors = door_cfg.get("front", [])
    back_doors = door_cfg.get("back", [])
    left_doors = door_cfg.get("left", [])
    right_doors = door_cfg.get("right", [])

    def _wall_with_openings(wall_pos_fn, wall_length, openings):
        if not openings:
            geo.append(wall_pos_fn(0, wall_length))
            return
        openings = sorted(openings)
        segments = []
        cursor = -wall_length / 2
        for door_offset, door_w in openings:
            door_start = door_offset - door_w / 2
            door_end = door_offset + door_w / 2
            if door_start > cursor + 0.01:
                seg_len = door_start - cursor
                seg_center = cursor + seg_len / 2
                segments.append((seg_center, seg_len))
            cursor = door_end
        if cursor < wall_length / 2 - 0.01:
            seg_len = wall_length / 2 - cursor
            seg_center = cursor + seg_len / 2
            segments.append((seg_center, seg_len))

        for seg_center, seg_len in segments:
            geo.append(wall_pos_fn(seg_center, seg_len))

    def front_wall_fn(offset, length):
        # Shift slightly inwards to avoid z-fighting at corners
        return wall((cx + offset, floor_y + hw, cz - d / 2 + t / 2), (length - 0.01, wall_height, t), color=wall_color)

    def back_wall_fn(offset, length):
        return wall((cx + offset, floor_y + hw, cz + d / 2 - t / 2), (length - 0.01, wall_height, t), color=wall_color)

    def left_wall_fn(offset, length):
        return wall((cx - w / 2 + t / 2, floor_y + hw, cz + offset), (t, wall_height, length - 0.01), color=wall_color)

    def right_wall_fn(offset, length):
        return wall((cx + w / 2 - t / 2, floor_y + hw, cz + offset), (t, wall_height, length - 0.01), color=wall_color)

    _wall_with_openings(front_wall_fn, w, front_doors)
    _wall_with_openings(back_wall_fn, w, back_doors)
    _wall_with_openings(left_wall_fn, d, left_doors)
    _wall_with_openings(right_wall_fn, d, right_doors)

    room_meta = {"name": name, "position": (cx, cz), "size": (w, d)}
    return room_meta, geo


def build():
    geometry = []
    rooms = []

    wh = 3.6
    
    # ------------------
    # GROUND FLOOR (y=0)
    # ------------------

    foyer_m, foyer_g = _room_with_doors(
        "Foyer", (0, 0), (8, 8), wh,
        (195, 185, 170), (200, 192, 180),
        doors={"front": [(0, 3.0)], "back": [(0, 3.0)], "left": [(0, 2.8)], "right": [(0, 2.8)]}
    )
    rooms.append(foyer_m)
    geometry.extend(foyer_g)

    living_m, living_g = _room_with_doors(
        "Living Room", (-12, 0), (16, 12), wh,
        (210, 200, 185), (205, 198, 185),
        doors={"right": [(0, 2.8)], "back": [(4, 2.8)]}
    )
    rooms.append(living_m)
    geometry.extend(living_g)

    kitchen_m, kitchen_g = _room_with_doors(
        "Kitchen", (12, -2), (14, 10), wh,
        (190, 200, 195), (195, 202, 198),
        doors={"left": [(0, 2.8)], "back": [(0, 2.8)]}
    )
    rooms.append(kitchen_m)
    geometry.extend(kitchen_g)

    dining_m, dining_g = _room_with_doors(
        "Dining Room", (0, 10), (10, 8), wh,
        (215, 208, 195), (210, 205, 192),
        doors={"front": [(0, 3.0)], "left": [(-1, 2.6)], "right": [(1, 2.6)], "back": [(3, 2.8)]}
    )
    rooms.append(dining_m)
    geometry.extend(dining_g)

    # ------------------
    # BASEMENT (y=-3.6)
    # ------------------
    base_m, base_g = _room_with_doors(
        "Basement Core", (0, 10), (16, 16), wh,
        (120, 120, 125), (110, 110, 115),
        doors={"front": [(0, 2.8)]}, floor_y=-3.6
    )
    rooms.append(base_m)
    geometry.extend(base_g)
    
    # Stairs to Basement
    # They start in Dining Room (y=0) and go down to Basement (y=-3.6)
    # Let's make an invisible ramp
    # Ramp length in Z is 6. Height diff is 3.6.
    geometry.append(wall((0, -1.8, 14.5), (2.8, 0.2, 10.0), color=(0,0,0), visible=False, solid=True, rotation=(0, 20, 0))) # The ramp
    # Add visible steps
    for i in range(16):
        step_z = -0.225 * i
        step_y = 10.5 + 0.5 * i
        geometry.append(wall((0, step_z, step_y), (2.8, 0.2, 0.5), color=(140, 130, 120), solid=False))

    # ------------------
    # PROPS & FURNITURE
    # ------------------
    geometry.extend([
        prop("loungeSofaLong", (-14, 0.0, 2), (75, 82, 110), (2.5, 2.5, 2.5), rotation=(0,0,0)),
        prop("loungeSofa", (-18, 0.0, -1), (75, 82, 110), (2.5, 2.5, 2.5), rotation=(90,0,0)),
        prop("tableCoffee", (-14, 0.0, -1), (110, 78, 50), (2.5, 2.5, 2.5)),
        prop("televisionModern", (-14, 0.6, -5.5), (50, 50, 55), (2.5, 2.5, 2.5)),
        prop("cabinetTelevision", (-14, 0.0, -5.5), (150, 120, 90), (2.5, 2.5, 2.5)),
        prop("plantSmall1", (-19.5, 0.0, -5.5), (255, 255, 255), (3.0, 3.0, 3.0)),
        prop("lampRoundFloor", (-8, 0.0, 5), (255, 255, 255), (3.0, 3.0, 3.0)),
    ])
    
    geometry.extend([
        prop("kitchenCabinetDrawer", (7, 0.0, -5.5), (255, 255, 255), (2.5, 2.5, 2.5)),
        prop("kitchenCabinetUpper", (7, 2.0, -5.5), (255, 255, 255), (2.5, 2.5, 2.5)),
        prop("kitchenFridge", (18.0, 0.0, -6.0), (210, 215, 218), (2.5, 2.5, 2.5)),
        prop("kitchenStove", (9, 0.0, -5.5), (255, 255, 255), (2.5, 2.5, 2.5)),
        prop("kitchenSink", (14, 0.0, -5.5), (255, 255, 255), (2.5, 2.5, 2.5)),
        prop("kitchenBar", (12, 0.0, -1.5), (255, 255, 255), (2.5, 2.5, 2.5)),
        prop("chairDesk", (11, 0.0, -0.5), (200, 200, 200), (2.5, 2.5, 2.5), rotation=(180,0,0)),
        prop("chairDesk", (13, 0.0, -0.5), (200, 200, 200), (2.5, 2.5, 2.5), rotation=(180,0,0)),
    ])

    geometry.extend([
        prop("tableDining", (0, 0.0, 10.5), (125, 85, 55), (2.5, 2.5, 2.5)),
        prop("chairCushion", (-1.5, 0.0, 10.5), (200, 190, 180), (2.5, 2.5, 2.5), rotation=(90,0,0)),
        prop("chairCushion", (1.5, 0.0, 10.5), (200, 190, 180), (2.5, 2.5, 2.5), rotation=(-90,0,0)),
        prop("chairCushion", (0, 0.0, 9.0), (200, 190, 180), (2.5, 2.5, 2.5), rotation=(0,0,0)),
        prop("chairCushion", (0, 0.0, 12.0), (200, 190, 180), (2.5, 2.5, 2.5), rotation=(180,0,0)),
        prop("plantSmall2", (0, 1.0, 10.5), (255,255,255), (2.5, 2.5, 2.5)),
    ])
    
    # Basement Props
    geometry.extend([
        prop("cardboardBoxClosed", (-4, -3.6, 12), (180, 160, 120), (3.0, 3.0, 3.0)),
        prop("cardboardBoxClosed", (-4, -2.6, 12), (180, 160, 120), (3.0, 3.0, 3.0)),
        prop("cardboardBoxOpen", (-5, -3.6, 13), (180, 160, 120), (3.0, 3.0, 3.0)),
        prop("deskComputer", (4, -3.6, 16), (150, 150, 150), (2.5, 2.5, 2.5)),
        prop("chairDesk", (4, -3.6, 14.5), (100, 100, 100), (2.5, 2.5, 2.5), rotation=(180,0,0)),
    ])

    return {
        "geometry": geometry,
        "rooms": rooms,
        "hider_spawn_objects": [
            hider_object("cardboardBoxClosed", (-14, 0.4, 2)),
            hider_object("cardboardBoxClosed", (0, -3.6, 12)),
            hider_object("chairCushion", (12, 0.4, -1)),
            hider_object("plantSmall1", (-18, 0.4, -3)),
        ],
        "objectives": [
            objective(1, "laptop", (-14, 1.0, -5.5), "Hack the TV"),
            objective(2, "laptop", (12, 1.1, -1.5), "Download Recipes"),
            objective(3, "laptop", (0, 0.8, 10.5), "Steal Dining Plans"),
            objective(4, "laptop", (4, -2.6, 16), "Format Hard Drive"),
        ],
        "hider_spawns": [(-15, 0.5, 0), (14, 0.5, 0), (0, 0.5, 10)],
        "hunter_spawns": [(0, 0.5, -2)],
    }
