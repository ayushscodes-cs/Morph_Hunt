from maps._builder import rectangular_room, hider_object, objective, prop, floor, wall


def _room_with_doors(name, center, size, wall_height, floor_color, wall_color, doors=None):
    cx, cz = center
    w, d = size
    t = 0.3
    hw = wall_height / 2
    geo = [floor((cx, cz), (w, d), color=floor_color)]

    door_cfg = doors or {}

    front_doors = door_cfg.get("front", [])
    back_doors = door_cfg.get("back", [])
    left_doors = door_cfg.get("left", [])
    right_doors = door_cfg.get("right", [])

    def _wall_with_openings(wall_pos_fn, wall_length, openings, axis):
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
        return wall((cx + offset, hw, cz - d / 2), (length, wall_height, t), color=wall_color)

    def back_wall_fn(offset, length):
        return wall((cx + offset, hw, cz + d / 2), (length, wall_height, t), color=wall_color)

    def left_wall_fn(offset, length):
        return wall((cx - w / 2, hw, cz + offset), (t, wall_height, length), color=wall_color)

    def right_wall_fn(offset, length):
        return wall((cx + w / 2, hw, cz + offset), (t, wall_height, length), color=wall_color)

    _wall_with_openings(front_wall_fn, w, front_doors, "x")
    _wall_with_openings(back_wall_fn, w, back_doors, "x")
    _wall_with_openings(left_wall_fn, d, left_doors, "z")
    _wall_with_openings(right_wall_fn, d, right_doors, "z")

    room_meta = {"name": name, "position": (cx, cz), "size": (w, d)}
    return room_meta, geo


def build():
    geometry = []
    rooms = []

    wh = 3.6
    wt = 0.3

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
        doors={"front": [(0, 3.0)], "left": [(-1, 2.6)], "right": [(1, 2.6)]}
    )
    rooms.append(dining_m)
    geometry.extend(dining_g)

    family_m, family_g = _room_with_doors(
        "Family Room", (-12, 10), (12, 8), wh,
        (205, 195, 180), (200, 192, 178),
        doors={"right": [(-1, 2.6)]}
    )
    rooms.append(family_m)
    geometry.extend(family_g)

    pantry_m, pantry_g = _room_with_doors(
        "Pantry", (12, 10), (8, 6), wh,
        (188, 192, 185), (192, 195, 190),
        doors={"left": [(0, 2.4)]}
    )
    rooms.append(pantry_m)
    geometry.extend(pantry_g)

    hall_m, hall_g = _room_with_doors(
        "Main Hallway", (0, -8), (24, 4), wh,
        (200, 195, 185), (198, 192, 182),
        doors={"front": [(-8, 2.6), (0, 2.6), (8, 2.6)], "back": [(0, 3.0)]}
    )
    rooms.append(hall_m)
    geometry.extend(hall_g)

    master_m, master_g = _room_with_doors(
        "Master Bedroom", (-10, -16), (14, 12), wh,
        (198, 190, 205), (195, 188, 200),
        doors={"back": [(-3, 2.6)], "right": [(3, 2.2)]}
    )
    rooms.append(master_m)
    geometry.extend(master_g)

    bed2_m, bed2_g = _room_with_doors(
        "Bedroom 2", (0, -16), (8, 10), wh,
        (200, 198, 210), (198, 195, 205),
        doors={"back": [(0, 2.6)]}
    )
    rooms.append(bed2_m)
    geometry.extend(bed2_g)

    bed3_m, bed3_g = _room_with_doors(
        "Bedroom 3", (10, -16), (12, 10), wh,
        (205, 200, 195), (200, 198, 192),
        doors={"back": [(0, 2.6)]}
    )
    rooms.append(bed3_m)
    geometry.extend(bed3_g)

    bath1_m, bath1_g = _room_with_doors(
        "Master Bathroom", (-3, -16), (6, 5), wh,
        (185, 200, 205), (188, 198, 202),
        doors={"left": [(0, 2.2)]}
    )
    rooms.append(bath1_m)
    geometry.extend(bath1_g)

    bath2_m, bath2_g = _room_with_doors(
        "Hallway Bathroom", (8, -16), (5, 5), wh,
        (182, 198, 202), (185, 195, 200),
        doors={"back": [(0, 2.2)]}
    )
    rooms.append(bath2_m)
    geometry.extend(bath2_g)

    storage_m, storage_g = _room_with_doors(
        "Storage Room", (16, -16), (6, 6), wh,
        (180, 180, 185), (185, 185, 188),
        doors={"back": [(0, 2.2)]}
    )
    rooms.append(storage_m)
    geometry.extend(storage_g)

    garage_m, garage_g = _room_with_doors(
        "Garage", (22, 0), (10, 14), wh,
        (140, 140, 145), (150, 150, 155),
        doors={"left": [(0, 3.5)], "front": [(0, 5.0)]}
    )
    rooms.append(garage_m)
    geometry.extend(garage_g)

    geometry.extend([
        prop("sofa", (-14, 0.6, 2), (75, 82, 110), (5.5, 1.2, 1.5)),
        prop("sofa_side", (-18, 0.6, -1), (75, 82, 110), (1.3, 1.2, 3.5)),
        prop("coffee_table", (-13, 0.4, -0.5), (110, 78, 50), (3.0, 0.5, 1.6)),
        prop("tv_stand", (-14, 0.85, -5.5), (50, 50, 55), (5.5, 1.0, 0.7)),
        prop("tv", (-14, 1.8, -5.2), (28, 30, 35), (3.2, 1.8, 0.15)),
        prop("bookshelf", (-19.5, 1.7, 0), (100, 70, 45), (0.5, 3.2, 5.0)),
    ])

    geometry.extend([
        prop("counter_l", (7, 0.85, -5.5), (155, 155, 150), (4.0, 1.0, 1.2)),
        prop("counter_r", (17, 0.85, -5.5), (155, 155, 150), (4.0, 1.0, 1.2)),
        prop("island", (12, 0.75, -1.5), (180, 175, 165), (5.0, 1.0, 1.8)),
        prop("fridge", (18.5, 1.4, -6.0), (210, 215, 218), (1.3, 2.8, 1.3)),
        prop("stove", (9, 0.85, -5.5), (60, 62, 68), (2.0, 1.0, 1.5)),
        prop("sink", (14, 1.0, -5.5), (195, 198, 200), (1.8, 0.7, 1.3)),
    ])

    geometry.extend([
        prop("dining_table", (0, 0.75, 10.5), (125, 85, 55), (5.0, 0.9, 3.0)),
        prop("dining_chair_1", (-3, 0.65, 10.5), (108, 78, 52), (0.7, 1.2, 0.7)),
        prop("dining_chair_2", (3, 0.65, 10.5), (108, 78, 52), (0.7, 1.2, 0.7)),
        prop("dining_chair_3", (0, 0.65, 8.5), (108, 78, 52), (0.7, 1.2, 0.7)),
        prop("dining_chair_4", (0, 0.65, 12.5), (108, 78, 52), (0.7, 1.2, 0.7)),
    ])

    geometry.extend([
        prop("family_sofa", (-14, 0.6, 11), (85, 78, 95), (5.0, 1.2, 1.5)),
        prop("family_table", (-11, 0.4, 8.5), (115, 80, 52), (2.5, 0.5, 1.4)),
        prop("armchair", (-17, 0.6, 8), (90, 85, 100), (1.4, 1.2, 1.4)),
    ])

    geometry.extend([
        prop("bed_master", (-12, 0.75, -18), (125, 68, 78), (5.5, 1.2, 3.2)),
        prop("wardrobe_master", (-16.5, 1.7, -13.5), (105, 72, 48), (0.8, 3.2, 3.5)),
        prop("nightstand_1", (-7, 0.5, -18), (105, 72, 48), (1.0, 1.0, 1.0)),
        prop("nightstand_2", (-16, 0.5, -18), (105, 72, 48), (1.0, 1.0, 1.0)),
    ])

    geometry.extend([
        prop("bed_2", (0, 0.75, -18), (78, 88, 118), (4.0, 1.2, 2.6)),
        prop("desk_2", (-3.5, 0.7, -13), (108, 75, 48), (2.0, 1.0, 0.8)),
        prop("wardrobe_2", (3.5, 1.6, -13), (110, 78, 52), (0.7, 3.0, 2.8)),
    ])

    geometry.extend([
        prop("bed_3", (10, 0.75, -18), (70, 95, 120), (4.5, 1.2, 2.8)),
        prop("desk_3", (14, 0.7, -13.5), (112, 78, 50), (2.5, 1.0, 0.8)),
        prop("shelf_3", (6, 1.5, -13), (95, 68, 45), (0.5, 2.8, 3.0)),
    ])

    geometry.extend([
        prop("bath_sink_1", (-4, 0.85, -17), (215, 218, 220), (1.3, 0.8, 1.0)),
        prop("bath_tub", (-1.5, 0.65, -15), (200, 205, 210), (2.5, 0.8, 1.3)),
    ])

    geometry.extend([
        prop("bath_sink_2", (7.5, 0.85, -17), (215, 218, 220), (1.3, 0.8, 1.0)),
        prop("bath_toilet", (9, 0.55, -17), (215, 218, 220), (0.7, 0.9, 0.7)),
    ])

    geometry.extend([
        prop("garage_car", (22, 0.8, -1), (50, 55, 65), (4.0, 1.6, 2.5)),
        prop("garage_shelf", (26.5, 1.5, 4), (90, 85, 78), (0.5, 2.8, 5.0)),
        prop("garage_toolbox", (19, 0.5, 5), (140, 50, 50), (1.5, 1.0, 0.8)),
    ])

    bmt_y = -3.6
    bmt_floor_y = bmt_y

    bmt_main_m, bmt_main_g = _room_with_doors(
        "Basement Main", (0, -30), (28, 16), 3.2,
        (55, 58, 65), (75, 78, 85),
        doors={"back": [(-8, 2.8), (8, 2.8)], "front": [(0, 3.0)]}
    )
    rooms.append(bmt_main_m)
    for g in bmt_main_g:
        if g["type"] == "floor":
            g["position"] = (g["position"][0], bmt_floor_y, g["position"][2])
        elif g["type"] == "wall":
            g["position"] = (g["position"][0], g["position"][1] + bmt_floor_y, g["position"][2])
    geometry.extend(bmt_main_g)

    bmt_store_m, bmt_store_g = _room_with_doors(
        "Basement Storage", (-10, -42), (12, 8), 3.2,
        (50, 52, 58), (70, 72, 78),
        doors={"front": [(0, 2.6)]}
    )
    rooms.append(bmt_store_m)
    for g in bmt_store_g:
        if g["type"] == "floor":
            g["position"] = (g["position"][0], bmt_floor_y, g["position"][2])
        elif g["type"] == "wall":
            g["position"] = (g["position"][0], g["position"][1] + bmt_floor_y, g["position"][2])
    geometry.extend(bmt_store_g)

    bmt_util_m, bmt_util_g = _room_with_doors(
        "Basement Utility", (10, -42), (12, 8), 3.2,
        (52, 55, 60), (72, 75, 80),
        doors={"front": [(0, 2.6)]}
    )
    rooms.append(bmt_util_m)
    for g in bmt_util_g:
        if g["type"] == "floor":
            g["position"] = (g["position"][0], bmt_floor_y, g["position"][2])
        elif g["type"] == "wall":
            g["position"] = (g["position"][0], g["position"][1] + bmt_floor_y, g["position"][2])
    geometry.extend(bmt_util_g)

    bmt_hall_m, bmt_hall_g = _room_with_doors(
        "Basement Hallway", (0, -40), (20, 4), 3.2,
        (48, 50, 55), (68, 70, 75),
        doors={"front": [(-8, 2.8), (8, 2.8)], "left": [(0, 2.6)], "right": [(0, 2.6)]}
    )
    rooms.append(bmt_hall_m)
    for g in bmt_hall_g:
        if g["type"] == "floor":
            g["position"] = (g["position"][0], bmt_floor_y, g["position"][2])
        elif g["type"] == "wall":
            g["position"] = (g["position"][0], g["position"][1] + bmt_floor_y, g["position"][2])
    geometry.extend(bmt_hall_g)

    num_stairs_down = 10
    for i in range(num_stairs_down):
        step_y = 0.0 - i * (3.6 / num_stairs_down)
        step_z = -10.5 - i * (12.0 / num_stairs_down)
        geometry.append(
            prop(f"bstair_{i}", (0, step_y - 0.15, step_z), (115, 115, 110), (4.0, 0.35, 1.3))
        )

    geometry.extend([
        prop("bmt_pillar_1", (-8, bmt_y + 1.4, -28), (68, 72, 78), (0.8, 3.0, 0.8)),
        prop("bmt_pillar_2", (8, bmt_y + 1.4, -28), (68, 72, 78), (0.8, 3.0, 0.8)),
        prop("bmt_pillar_3", (-8, bmt_y + 1.4, -34), (68, 72, 78), (0.8, 3.0, 0.8)),
        prop("bmt_pillar_4", (8, bmt_y + 1.4, -34), (68, 72, 78), (0.8, 3.0, 0.8)),
        prop("bmt_shelf_1", (-12, bmt_y + 1.2, -37), (85, 68, 52), (4.0, 2.5, 0.6)),
        prop("bmt_shelf_2", (12, bmt_y + 1.2, -37), (85, 68, 52), (4.0, 2.5, 0.6)),
        prop("bmt_workbench", (0, bmt_y + 0.7, -37), (95, 68, 48), (6.0, 1.0, 1.2)),
        prop("bmt_boiler", (-12, bmt_y + 1.3, -44), (78, 82, 88), (2.2, 2.6, 2.2)),
        prop("bmt_storage_rack", (12, bmt_y + 1.2, -44), (105, 82, 52), (4.0, 2.2, 2.2)),
    ])

    terrace_y = wh + 0.2
    terrace_floor = {
        "type": "floor",
        "position": (0, terrace_y, 0),
        "scale": (32, 0.25, 26),
        "color": (115, 115, 120),
        "solid": True,
    }
    geometry.append(terrace_floor)

    rail_h = 1.2
    geometry.extend([
        wall((-15.85, terrace_y + rail_h / 2, 0), (wt, rail_h, 26), (155, 155, 160)),
        wall((15.85, terrace_y + rail_h / 2, 0), (wt, rail_h, 26), (155, 155, 160)),
        wall((0, terrace_y + rail_h / 2, 12.85), (31.4, rail_h, wt), (155, 155, 160)),
        wall((0, terrace_y + rail_h / 2, -12.85), (31.4, rail_h, wt), (155, 155, 160)),
    ])

    num_stairs_up = 10
    for i in range(num_stairs_up):
        step_y_t = 0.0 + i * (terrace_y / num_stairs_up)
        step_z_t = -10.5 + i * (8.0 / num_stairs_up)
        geometry.append(
            prop(f"tstair_{i}", (18, step_y_t + 0.15, step_z_t), (120, 120, 115), (3.5, 0.35, 0.9))
        )

    geometry.extend([
        prop("terrace_table", (-6, terrace_y + 0.6, 4), (115, 82, 52), (3.5, 0.8, 2.0)),
        prop("terrace_chair_1", (-9.5, terrace_y + 0.6, 4), (88, 88, 95), (0.9, 1.3, 0.9)),
        prop("terrace_chair_2", (-2.5, terrace_y + 0.6, 4), (88, 88, 95), (0.9, 1.3, 0.9)),
        prop("terrace_planter_1", (10, terrace_y + 0.5, 10), (85, 115, 75), (1.8, 0.9, 1.8)),
        prop("terrace_planter_2", (10, terrace_y + 0.5, -8), (85, 115, 75), (1.8, 0.9, 1.8)),
        prop("terrace_bench", (-10, terrace_y + 0.5, -8), (85, 85, 90), (5.0, 1.0, 1.5)),
    ])

    yard_front = floor((0, 26), (60, 20), (60, 130, 62))
    geometry.append(yard_front)

    yard_back = floor((0, -50), (60, 20), (55, 125, 58))
    geometry.append(yard_back)

    fence_h = 2.2
    geometry.extend([
        wall((-30, fence_h / 2, 0), (0.35, fence_h, 60), (110, 80, 52)),
        wall((30, fence_h / 2, 0), (0.35, fence_h, 60), (110, 80, 52)),
        wall((0, fence_h / 2, 36), (60, fence_h, 0.35), (110, 80, 52)),
        wall((0, fence_h / 2, -60), (60, fence_h, 0.35), (110, 80, 52)),
        wall((-30, fence_h / 2, -30), (0.35, fence_h, 60), (110, 80, 52)),
        wall((30, fence_h / 2, -30), (0.35, fence_h, 60), (110, 80, 52)),
    ])

    geometry.extend([
        prop("front_path", (0, 0.05, 20), (160, 155, 145), (4.0, 0.1, 12.0), solid=False),
        prop("driveway", (20, 0.05, 20), (145, 142, 135), (6.0, 0.1, 14.0), solid=False),
    ])

    geometry.extend([
        prop("yard_tree_1", (-22, 2.8, 28), (72, 110, 58), (2.2, 5.5, 2.2)),
        prop("yard_tree_2", (22, 2.8, 30), (68, 105, 55), (2.5, 6.0, 2.5)),
        prop("yard_tree_3", (-24, 2.8, -52), (68, 105, 55), (2.2, 5.5, 2.2)),
        prop("yard_tree_4", (24, 2.8, -55), (68, 105, 55), (2.2, 5.5, 2.2)),
        prop("garden_bench", (-10, 0.55, 28), (110, 75, 45), (4.0, 0.9, 0.9)),
        prop("garden_table", (8, 0.55, 28), (120, 82, 48), (3.0, 0.8, 2.0)),
        prop("garden_chair_1", (5, 0.6, 28), (98, 72, 48), (0.8, 1.2, 0.8)),
        prop("garden_chair_2", (11, 0.6, 28), (98, 72, 48), (0.8, 1.2, 0.8)),
        prop("garden_shed", (22, 1.8, -52), (130, 95, 58), (5.5, 3.8, 4.5)),
        prop("garden_swing", (-20, 2.2, -48), (75, 75, 78), (4.5, 4.0, 1.2)),
        prop("garden_fountain", (0, 0.8, -48), (125, 150, 155), (3.5, 1.3, 3.5)),
        prop("mailbox", (-4, 0.8, 34), (60, 60, 65), (0.5, 1.6, 0.4)),
        prop("garden_gnome", (6, 0.4, 32), (140, 90, 70), (0.5, 0.8, 0.5)),
    ])

    hider_spawn_objects = [
        hider_object("chair", (-14, 0.7, 2)),
        hider_object("plant", (-19, 0.9, 3)),
        hider_object("lamp", (-10, 0.8, 4)),
        hider_object("box", (-13, 0.7, -2)),

        hider_object("bin", (17, 0.7, -4)),
        hider_object("chair", (10, 0.7, -3)),
        hider_object("box", (15, 0.7, -6)),
        hider_object("lamp", (18, 0.8, -6)),

        hider_object("chair", (-2, 0.7, 10)),
        hider_object("chair", (2, 0.7, 10)),
        hider_object("plant", (4, 0.9, 13)),

        hider_object("chair", (-14, 0.7, 11)),
        hider_object("plant", (-17, 0.9, 13)),
        hider_object("box", (-10, 0.7, 9)),

        hider_object("chair", (-8, 0.7, -16)),
        hider_object("plant", (-16, 0.9, -14)),
        hider_object("lamp", (-16, 0.8, -20)),
        hider_object("monitor", (-7, 0.9, -20)),

        hider_object("chair", (0, 0.7, -18)),
        hider_object("box", (-3, 0.7, -13)),
        hider_object("lamp", (3, 0.8, -13)),

        hider_object("chair", (12, 0.7, -18)),
        hider_object("box", (8, 0.7, -14)),
        hider_object("monitor", (14, 0.9, -14)),

        hider_object("barrel", (23, 0.7, 3)),
        hider_object("crate", (20, 0.7, 5)),
        hider_object("box", (24, 0.7, -4)),

        hider_object("crate", (-10, bmt_y + 0.5, -28)),
        hider_object("barrel", (10, bmt_y + 0.5, -28)),
        hider_object("crate", (-8, bmt_y + 0.5, -35)),
        hider_object("barrel", (8, bmt_y + 0.5, -35)),
        hider_object("box", (0, bmt_y + 0.5, -34)),
        hider_object("cart", (-4, bmt_y + 0.5, -42)),
        hider_object("crate", (4, bmt_y + 0.5, -42)),
        hider_object("box", (-10, bmt_y + 0.5, -44)),
        hider_object("barrel", (10, bmt_y + 0.5, -44)),

        hider_object("chair", (-6, terrace_y + 0.7, 4)),
        hider_object("plant", (10, terrace_y + 0.7, 10)),
        hider_object("box", (10, terrace_y + 0.7, -8)),
        hider_object("table", (-6, terrace_y + 0.6, 4)),

        hider_object("plant", (-22, 0.8, 28)),
        hider_object("plant", (22, 0.8, 30)),
        hider_object("barrel", (-22, 0.8, -52)),
        hider_object("box", (20, 0.8, -50)),
        hider_object("chair", (8, 0.8, 28)),
        hider_object("crate", (22, 0.8, -52)),
    ]

    hunter_spawns = [
        (0, 1.0, 2),
        (-2, 1.0, 2),
        (2, 1.0, 2),
    ]

    objectives = [
        objective("living_tv", "switch", (-14, 1.0, -5.2), "Living Room TV"),
        objective("kitchen_panel", "panel", (18.0, 1.0, -5.5), "Kitchen Control Panel"),
        objective("bedroom_terminal", "terminal", (-7.0, 1.0, -20.0), "Master Bedroom Terminal"),
        objective("basement_valve", "valve", (12.0, bmt_y + 1.0, -44.0), "Basement Valve"),
        objective("yard_box", "switch", (22.0, 1.0, -52.0), "Garden Shed Panel"),
        objective("garage_breaker", "panel", (26.0, 1.0, 4.0), "Garage Breaker"),
    ]

    return {
        "name": "House",
        "bounds": (62, 100),
        "rooms": rooms,
        "geometry": geometry,
        "hider_spawn_objects": hider_spawn_objects,
        "hunter_spawns": hunter_spawns,
        "objectives": objectives,
    }