# Prop Manager

def get_level_props(level_key: str) -> list[dict]:
    """
    Returns a list of prop definitions for a given level.
    Each prop is a dict with:
    - type: The model name from PROP_MODEL_MAP
    - pos: (x, y, z)
    - scale: float or (sx, sy, sz)
    - hpr: (h, p, r) rotation
    - morphable: bool (if True, players can scan and morph into it)
    """
    
    props = []
    
    if level_key == "house":
        props = [
            # Outdoor courtyard props (spawn is around 0, 0)
            {"type": "bench", "pos": (5, 5, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "bench", "pos": (-5, 5, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "trashcan", "pos": (7, 5, 0), "hpr": (0, 0, 0), "scale": 1.2, "collision": True, "morphable": True},
            {"type": "pottedPlant", "pos": (-7, 5, 0), "hpr": (0, 0, 0), "scale": 1.0, "collision": True, "morphable": True},
            {"type": "cardboardBoxClosed", "pos": (6, 6, 0), "hpr": (45, 0, 0), "scale": 1.0, "collision": True, "morphable": True},
            {"type": "lampRoundFloor", "pos": (0, 8, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": False},
            
            # Interior House (Assuming a house exists around X=15, Y=15)
            # Living Room
            {"type": "loungeSofa", "pos": (15, 15, 0), "hpr": (90, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "tableCoffee", "pos": (17, 15, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "televisionModern", "pos": (19, 15, 0.5), "hpr": (-90, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "cabinetTelevision", "pos": (19, 15, 0), "hpr": (-90, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "bookcaseOpen", "pos": (15, 12, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "plantSmall1", "pos": (15, 12, 1.5), "hpr": (0, 0, 0), "scale": 1.0, "collision": False, "morphable": True},
            
            # Bedroom
            {"type": "bedDouble", "pos": (15, 20, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "sideTable", "pos": (13, 20, 0), "hpr": (0, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
            {"type": "lampRoundTable", "pos": (13, 20, 0.6), "hpr": (0, 0, 0), "scale": 1.5, "collision": False, "morphable": True},
            {"type": "cabinetBed", "pos": (18, 20, 0), "hpr": (180, 0, 0), "scale": 1.5, "collision": True, "morphable": True},
        ]
    elif level_key == "office":
        pass
        
    return props
