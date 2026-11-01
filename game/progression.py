from config import settings

def get_level(total_xp: int) -> int:
    """
    Calculate player level based on total XP.
    Level 1: 0 XP
    Level 2: 100 XP
    Level 3: 250 XP
    Level 4: 475 XP
    Level 5: 800 XP
    ... (gap increases by 50, then 75, etc. We use a formula)
    """
    level = 1
    xp_needed = 0
    increment = 100
    
    while total_xp >= xp_needed + increment:
        xp_needed += increment
        level += 1
        increment += 50
        
    return level

def get_xp_for_next_level(current_level: int) -> int:
    """Return the total XP required to reach the next level."""
    xp_needed = 0
    increment = 100
    
    for _ in range(1, current_level + 1):
        xp_needed += increment
        increment += 50
        
    return xp_needed

def is_mode_unlocked(mode: str, level: int) -> bool:
    """Return True if the mode is unlocked at the given level."""
    required = settings.MODE_UNLOCK_LEVELS.get(mode, 1)
    return level >= required
