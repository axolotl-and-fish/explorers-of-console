"""
pokemon_db.py

Handles, parses and validates pokemon.json
Written by C437RP13

WARNING: Changing this code may lead to a lot of stuff breaking if pokemon.json is not valid!
"""

import os
import json
from data_utils import get_data_file_path

#Allowed set of experience groups. The first and last ones are unused currently, but will be used real soon!
VALID_EXPERIENCE_GROUPS = {
    "Erratic",
    "Fast",
    "Medium Fast",
    "Medium Slow",
    "Slow",
    "Fluctuating",
}

#Allowed set of Pokémon and move types
VALID_TYPES = {
    "Normal",
    "Fire",
    "Fighting",
    "Water",
    "Flying",
    "Grass",
    "Poison",
    "Electric",
    "Ground",
    "Psychic",
    "Rock",
    "Ice",
    "Bug",
    "Dragon",
    "Ghost",
    "Dark",
    "Steel",
    "Fairy",
    "typeless",
    "Unique",
}

#Allowed set of base stats / EV yield names
VALID_STATS = {
    "HP",
    "Attack",
    "Defense",
    "Special_Attack",
    "Special_Defense",
    "Speed",
}


def load_pokemon_database(filepath: str | None = None) -> list[dict]:
    """Loads and validates the Pokémon species database from a JSON file (pokemon.json)

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON data violates format or domain rules.
    """
    if filepath is None:
        filepath = get_data_file_path("pokemon.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Pokémon database file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file format: {e}")

    if not isinstance(data, list):
        raise ValueError("Pokémon database must be a JSON list of species objects.")

    validated_species = []

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("Each species entry must be a JSON object.")

        #1. Required Fields & Type Checks
        required_fields = {
            "id": str,
            "name": str,
            "base_stats": dict,
            "types": list,
            "ev_yield": dict,
            "exp_yield": int,
            "experience_group": str,
            "description": str,
            "level_up_moves": list,
            "tm_moves": list,
        }

        for field, expected_type in required_fields.items():
            if field not in entry:
                raise ValueError(f"Missing required field '{field}' in species entry: {entry.get('name', 'Unknown')}")
            val = entry[field]
            if not isinstance(val, expected_type):
                raise ValueError(
                    f"Field '{field}' must be of type {expected_type.__name__}, got {type(val).__name__} "
                    f"in species '{entry.get('name', 'Unknown')}'"
                )

        #2. Gender Ratio Check (can be null [genderless] or a float between 0.0 and 1.0)
        if "gender_ratio" not in entry:
            raise ValueError(f"Missing required field 'gender_ratio' in species '{entry['name']}'")
        gr = entry["gender_ratio"]
        if gr is not None:
            if not isinstance(gr, (int, float)):
                raise ValueError(f"Field 'gender_ratio' must be a float or null, got {type(gr).__name__} in '{entry['name']}'")
            if not (0.0 <= gr <= 1.0):
                raise ValueError(f"Field 'gender_ratio' must be between 0.0 and 1.0, got {gr} in '{entry['name']}'")

        #3. Stats Validation
        stats = entry["base_stats"]
        for stat in VALID_STATS:
            if stat not in stats:
                raise ValueError(f"Missing stat '{stat}' in base_stats for '{entry['name']}'")
            if not isinstance(stats[stat], int) or stats[stat] < 0:
                raise ValueError(f"Stat '{stat}' must be a non-negative integer, got {stats[stat]} in '{entry['name']}'")

        #4. Types Validation (1 or 2 types, must be in VALID_TYPES)
        types = entry["types"]
        if not (1 <= len(types) <= 2):
            raise ValueError(f"Field 'types' must contain 1 or 2 types, got {len(types)} in '{entry['name']}'")
        for t in types:
            if t not in VALID_TYPES:
                raise ValueError(f"Invalid type '{t}' in species '{entry['name']}'")

        #5. EV Yield Validation (keys must be valid stats, values non-negative integers)
        evs = entry["ev_yield"]
        for key, val in evs.items():
            if key not in VALID_STATS:
                raise ValueError(f"Invalid stat name '{key}' in ev_yield for '{entry['name']}'")
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"EV yield for '{key}' must be a non-negative int, got {val} in '{entry['name']}'")

        #6. Experience Group Validation
        exp_grp = entry["experience_group"]
        if exp_grp not in VALID_EXPERIENCE_GROUPS:
            raise ValueError(f"Invalid experience group '{exp_grp}' in species '{entry['name']}'")

        #7. Level Up Moves Validation
        moves = entry["level_up_moves"]
        for item in moves:
            if not isinstance(item, list) or len(item) != 2:
                raise ValueError(f"Each element in level_up_moves must be a [level, name] list in '{entry['name']}'")
            lvl, move_name = item
            if not isinstance(lvl, int) or lvl < 0:
                raise ValueError(f"Level up move level must be a non-negative integer, got {lvl} in '{entry['name']}'")
            if not isinstance(move_name, str):
                raise ValueError(f"Level up move name must be a string, got {type(move_name).__name__} in '{entry['name']}'")

        #8. TM Moves Validation
        tm_moves = entry["tm_moves"]
        for tm in tm_moves:
            if not isinstance(tm, str):
                raise ValueError(f"Each TM move name must be a string, got {type(tm).__name__} in '{entry['name']}'")

        validated_species.append(entry)

    return validated_species


def get_parent_map(pokemon_db: list[dict]) -> dict[str, tuple[str, int]]:
    """Builds a mapping from child_species_name to (parent_species_name, min_evolution_level)
    based on evolution requirements in pokemon_db"""
    parent_map = {}
    for sp in pokemon_db:
        parent_name = sp.get("name")
        if not parent_name:
            continue
        for evo in sp.get("evolutions", []):
            child_name = evo.get("to")
            if not child_name or child_name == parent_name:
                continue
            min_lvl = evo.get("min_level")
            item = evo.get("item") or evo.get("evolution_item")

            if item:
                if str(item).strip().lower() == "link cable":
                    req_lvl = max(min_lvl, 35) if min_lvl is not None else 35
                else:
                    req_lvl = max(min_lvl, 30) if min_lvl is not None else 30
            elif min_lvl is not None:
                req_lvl = min_lvl
            else:
                req_lvl = 1

            parent_map[child_name] = (parent_name, req_lvl)
    return parent_map


def get_valid_evolution_stage(species_name: str, level: int, pokemon_db: list[dict]) -> str:
    """Returns the species name that the given species would have evolved into by the given level. Used for the floor spawning algo.
    If the Pokémon would not have evolved yet, recurses down to its pre-evolution stage"""
    parent_map = get_parent_map(pokemon_db)
    curr = species_name
    visited = set()
    while curr in parent_map and curr not in visited:
        visited.add(curr)
        parent_name, req_lvl = parent_map[curr]
        if level < req_lvl:
            curr = parent_name
        else:
            break
    return curr
