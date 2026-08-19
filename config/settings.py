"""
MORPH HUNT
Central configuration & balance file.

Every tunable value used by the game lives here so the game can be
rebalanced without touching gameplay code.
"""

# ----------------------------------------------------------------------
# NETWORK
# ----------------------------------------------------------------------
DEFAULT_HOST = "0.0.0.0"       # server bind address
DEFAULT_PORT = 5555
CONNECT_TIMEOUT = 5.0
MAX_PLAYERS = 8
MIN_PLAYERS_TO_START = 2
TICK_RATE = 20                  # server ticks per second
SNAPSHOT_RATE = 12              # state broadcasts per second

# ----------------------------------------------------------------------
# ROUND / PHASE TIMERS (seconds) - tweak freely
# ----------------------------------------------------------------------
COUNTDOWN_SECONDS = 5
HIDING_PHASE_SECONDS = 30
HUNTING_PHASE_SECONDS = 300      # 5 minutes
RESULTS_SCREEN_SECONDS = 15

# ----------------------------------------------------------------------
# PLAYER MOVEMENT
# ----------------------------------------------------------------------
PLAYER_WALK_SPEED = 5.0
PLAYER_SPRINT_MULTIPLIER = 1.6
PLAYER_JUMP_HEIGHT = 1.5
GRAVITY = 24.0
PLAYER_START_HEALTH = 100
MOUSE_SENSITIVITY = 40

# ----------------------------------------------------------------------
# MORPH ENERGY
# ----------------------------------------------------------------------
MORPH_ENERGY_MAX = 100
MORPH_ENERGY_TRANSFORM_COST = 20      # cost of the FIRST transform in a round
MORPH_ENERGY_SWITCH_COST = 15         # cost to switch to a different object
MORPH_ENERGY_MOVE_DRAIN_PER_SEC = 4   # drained while moving disguised
MORPH_ENERGY_ABILITY_COST = 10
MORPH_ENERGY_REGEN_PER_SEC = 8        # regen while standing still
MORPH_ENERGY_REGEN_DELAY = 1.5        # seconds of stillness before regen starts
MORPH_SWITCH_COOLDOWN = 3.0           # seconds between object switches
MIN_ENERGY_TO_TRANSFORM = 5

# ----------------------------------------------------------------------
# HUNTER SCANNER
# ----------------------------------------------------------------------
SCANNER_RANGE = 14.0
SCANNER_COOLDOWN = 8.0
SCANNER_MAX_CHARGES = 3
SCANNER_CHARGE_REGEN_SECONDS = 25      # time to regain one charge
SCANNER_CLUE_RADIUS_BUCKETS = [3, 7, 14]   # near / medium / far clue wording

# ----------------------------------------------------------------------
# HUNTER ATTACK (generic energy blaster - NOT a real world weapon)
# ----------------------------------------------------------------------
ATTACK_RANGE = 6.0
ATTACK_COOLDOWN = 1.2
ATTACK_DAMAGE = 34            # 3 hits to eliminate a hider
ATTACK_FALSE_HIT_PENALTY = 5  # small self-slow penalty for hitting a real prop (not a player)

# ----------------------------------------------------------------------
# OBJECT PERSONALITIES
# Every hideable prop type has: display name, camouflage (0-1, higher = harder
# to spot via scanner clue precision), speed multiplier applied to base
# player walk speed while disguised, scale (x,y,z) and morph_energy upkeep
# multiplier (some objects are "heavier" to hold as a disguise).
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# OBJECTIVES
# ----------------------------------------------------------------------
OBJECTIVES_TO_WIN = {
    "classic": 0,          # classic mode does not require objectives to win
    "object_rush": 3,      # hiders must complete 3 objectives
    "infection": 2,
}
OBJECTIVE_INTERACT_RANGE = 2.2
OBJECTIVE_HOLD_SECONDS = 3.0     # time an interacting hider must stay near the objective

# ----------------------------------------------------------------------
# GAME MODES
# ----------------------------------------------------------------------
GAME_MODES = ["classic", "object_rush", "infection"]

# ----------------------------------------------------------------------
# LEVELS (data-driven — see maps/*.py for concrete layouts)
# ----------------------------------------------------------------------
LEVELS = ["house", "office", "supermarket", "warehouse", "factory"]

# ----------------------------------------------------------------------
# SCORING / PROGRESSION
# ----------------------------------------------------------------------
XP_SURVIVE_ROUND = 50
XP_PER_OBJECTIVE = 25
XP_PER_ELIMINATION = 30
XP_WIN_BONUS = 40
DB_PATH = "morph_hunt_stats.db"
