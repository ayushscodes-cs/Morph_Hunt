DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5555
CONNECT_TIMEOUT = 5.0
MAX_PLAYERS = 8
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

ATTACK_RANGE = 6.0
ATTACK_COOLDOWN = 1.2
ATTACK_DAMAGE = 34
ATTACK_FALSE_HIT_PENALTY = 5

OBJECT_PERSONALITIES = {
    "chair":   {"display": "Chair",        "camouflage": 0.55, "speed_mult": 0.85, "scale": (0.8, 1.0, 0.8), "energy_mult": 1.0, "model": "cube", "color": (140, 90, 50)},
    "box":     {"display": "Box",          "camouflage": 0.85, "speed_mult": 0.55, "scale": (1.0, 1.0, 1.0), "energy_mult": 0.8, "model": "cube", "color": (170, 140, 90)},
    "plant":   {"display": "Plant",        "camouflage": 0.9,  "speed_mult": 0.35, "scale": (0.6, 1.4, 0.6), "energy_mult": 0.7, "model": "cube", "color": (40, 120, 50)},
    "lamp":    {"display": "Lamp",         "camouflage": 0.6,  "speed_mult": 0.5,  "scale": (0.4, 1.3, 0.4), "energy_mult": 0.9, "model": "cube", "color": (230, 210, 140)},
    "bin":     {"display": "Trash Bin",    "camouflage": 0.8,  "speed_mult": 0.6,  "scale": (0.7, 1.0, 0.7), "energy_mult": 0.85,"model": "cube", "color": (90, 90, 90)},
    "barrel":  {"display": "Barrel",       "camouflage": 0.65, "speed_mult": 0.55, "scale": (0.8, 1.2, 0.8), "energy_mult": 0.9, "model": "cube", "color": (120, 60, 40)},
    "crate":   {"display": "Crate",        "camouflage": 0.7,  "speed_mult": 0.6,  "scale": (1.0, 1.0, 1.0), "energy_mult": 0.85,"model": "cube", "color": (150, 110, 60)},
    "monitor": {"display": "Monitor",      "camouflage": 0.5,  "speed_mult": 0.4,  "scale": (0.9, 0.7, 0.15),"energy_mult": 1.1, "model": "cube", "color": (30, 30, 30)},
    "table":   {"display": "Table",        "camouflage": 0.3,  "speed_mult": 0.3,  "scale": (1.6, 0.8, 1.0), "energy_mult": 1.3, "model": "cube", "color": (110, 75, 45)},
    "cart":    {"display": "Cart",         "camouflage": 0.4,  "speed_mult": 1.15, "scale": (1.2, 1.0, 0.7), "energy_mult": 1.2, "model": "cube", "color": (100, 100, 110)},
}

OBJECTIVES_TO_WIN = {
    "classic": 0,
    "object_rush": 3,
    "infection": 2,
}
OBJECTIVE_INTERACT_RANGE = 2.2
OBJECTIVE_HOLD_SECONDS = 3.0

GAME_MODES = ["classic", "object_rush", "infection"]

LEVELS = ["house"]

XP_SURVIVE_ROUND = 50
XP_PER_OBJECTIVE = 25
XP_PER_ELIMINATION = 30
XP_WIN_BONUS = 40
DB_PATH = "morph_hunt_stats.db"
