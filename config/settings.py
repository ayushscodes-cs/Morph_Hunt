DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5555
CONNECT_TIMEOUT = 5.0
MAX_PLAYERS = 10
MIN_PLAYERS_TO_START = 2
TICK_RATE = 20
SNAPSHOT_RATE = 12
TAUNT_COOLDOWN = 6.0
TAUNT_BONUS_XP = 20

COUNTDOWN_SECONDS = 5
HIDING_PHASE_SECONDS = 30
HUNTING_PHASE_SECONDS = 300
RESULTS_SCREEN_SECONDS = 15

PLAYER_WALK_SPEED = 5.0
PLAYER_SPRINT_MULTIPLIER = 1.6
PLAYER_JUMP_HEIGHT = 1.5
GRAVITY = 24.0
PLAYER_START_HEALTH = 100
MOUSE_SENSITIVITY = 40

MORPH_ENERGY_MAX = 100
MORPH_ENERGY_TRANSFORM_COST = 20
MORPH_ENERGY_SWITCH_COST = 15
MORPH_ENERGY_MOVE_DRAIN_PER_SEC = 4
MORPH_ENERGY_ABILITY_COST = 10
MORPH_ENERGY_REGEN_PER_SEC = 8
MORPH_ENERGY_REGEN_DELAY = 1.5
MORPH_SWITCH_COOLDOWN = 3.0
MIN_ENERGY_TO_TRANSFORM = 5

SCANNER_RANGE = 14.0
SCANNER_COOLDOWN = 8.0
SCANNER_MAX_CHARGES = 3
SCANNER_CHARGE_REGEN_SECONDS = 25
SCANNER_CLUE_RADIUS_BUCKETS = [3, 7, 14]

ATTACK_RANGE = 150.0
ATTACK_COOLDOWN = 1.2
ATTACK_DAMAGE = 34
ATTACK_FALSE_HIT_PENALTY = 5

OBJECT_PERSONALITIES = {
    "TrashCommercial": {"display": "Dumpster", "camouflage": 0.8, "speed_mult": 0.7, "scale": (1.8, 1.2, 1.2), "energy_mult": 0.8, "model": "TrashCommercial"},
    "Bench": {"display": "Bench", "camouflage": 0.5, "speed_mult": 0.8, "scale": (1.5, 0.6, 0.8), "energy_mult": 1.0, "model": "Bench"},
    "FireHydrant": {"display": "Fire Hydrant", "camouflage": 0.9, "speed_mult": 1.1, "scale": (0.5, 0.5, 1.0), "energy_mult": 0.7, "model": "FireHydrant"},
    "ParkingMeter": {"display": "Parking Meter", "camouflage": 0.9, "speed_mult": 1.1, "scale": (0.3, 0.3, 1.2), "energy_mult": 0.7, "model": "ParkingMeter"},
    "PostBox": {"display": "Post Box", "camouflage": 0.7, "speed_mult": 0.9, "scale": (0.8, 0.8, 1.5), "energy_mult": 0.9, "model": "PostBox"},
    "pallet1": {"display": "Pallet", "camouflage": 0.85, "speed_mult": 1.0, "scale": (1.5, 1.5, 0.2), "energy_mult": 0.85, "model": "pallet1"},
    "Utility": {"display": "Utility Box", "camouflage": 0.75, "speed_mult": 0.8, "scale": (1.0, 1.0, 1.5), "energy_mult": 0.9, "model": "Utility"},
    "ConcreteBench": {"display": "Concrete Bench", "camouflage": 0.6, "speed_mult": 0.8, "scale": (1.5, 0.6, 0.6), "energy_mult": 1.0, "model": "ConcreteBench"},
    "TrashCanSmall": {"display": "Trash Can", "camouflage": 0.85, "speed_mult": 1.0, "scale": (0.6, 0.6, 0.8), "energy_mult": 0.8, "model": "TrashCanSmall"},
    "Couch": {"display": "Couch", "camouflage": 0.8, "speed_mult": 0.7, "scale": (2.0, 1.0, 1.2), "energy_mult": 0.8, "model": "Couch"},
    "TV": {"display": "Television", "camouflage": 0.9, "speed_mult": 1.1, "scale": (1.0, 0.2, 0.7), "energy_mult": 0.7, "model": "TV"},
    "Bed": {"display": "Bed", "camouflage": 0.6, "speed_mult": 0.6, "scale": (2.2, 2.0, 0.8), "energy_mult": 0.9, "model": "Bed"},
    "Refrigerator": {"display": "Fridge", "camouflage": 0.7, "speed_mult": 0.7, "scale": (1.2, 1.2, 2.4), "energy_mult": 0.85, "model": "Refrigerator"},
    "Tree": {"display": "Tree", "camouflage": 0.95, "speed_mult": 0.4, "scale": (3.0, 3.0, 8.0), "energy_mult": 1.2, "model": "Tree"},
    "Toilet": {"display": "Toilet", "camouflage": 0.8, "speed_mult": 0.9, "scale": (0.6, 0.8, 1.0), "energy_mult": 0.8, "model": "Toilet"},
    "Fence": {"display": "Fence", "camouflage": 0.85, "speed_mult": 0.7, "scale": (3.0, 0.2, 1.5), "energy_mult": 0.8, "model": "Fence"}
}

OBJECTIVES_TO_WIN = {
    "classic": 0,
    "object_rush": 3,
    "infection": 2,
}
OBJECTIVE_INTERACT_RANGE = 2.2
OBJECTIVE_HOLD_SECONDS = 3.0

GAME_MODES = ["classic", "object_rush", "infection", "clash_squad"]

MODE_UNLOCK_LEVELS = {
    "classic": 1,
    "object_rush": 2,
    "infection": 3,
    "clash_squad": 5
}

LEVELS = ["house"]

XP_SURVIVE_ROUND = 50
XP_PER_OBJECTIVE = 25
XP_PER_ELIMINATION = 30
XP_WIN_BONUS = 40
XP_PARTICIPATION = 50
DB_PATH = "morph_hunt_stats.db"
