"""
moves_db.py

Handles, parses and validates moves.json

WARNING: Changing this code may lead to a lot of stuff breaking if moves.json is not valid!
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import json
from data_utils import get_data_file_path
from pokemon_db import VALID_TYPES, VALID_STATS

#Allowed set of move categories
VALID_CATEGORIES = {"Physical", "Special", "Status"}


def load_moves_database(filepath: str | None = None) -> list[dict]:
    """Loads and validates the moves database from a JSON file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON data violates format or domain rules.
    """
    if filepath is None:
        filepath = get_data_file_path("moves.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Moves database file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file format: {e}")

    if not isinstance(data, list):
        raise ValueError("Moves database must be a JSON list of move objects.")

    validated_moves = []

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("Each move entry must be a JSON object.")

        #1. Required Fields & Type Checks
        required_fields = {
            "name": str,
            "type": str,
            "description": str,
            "category": str,
            "range": str,
            "pp_cost": int,
            "effects": list,
        }

        for field, expected_type in required_fields.items():
            if field not in entry:
                raise ValueError(f"Missing required field '{field}' in move entry: {entry.get('name', 'Unknown')}")
            val = entry[field]
            if not isinstance(val, expected_type):
                raise ValueError(
                    f"Field '{field}' must be of type {expected_type.__name__}, got {type(val).__name__} "
                    f"in move '{entry.get('name', 'Unknown')}'"
                )

        #2. pp_cost Check (must be >=0)
        pp_cost = entry["pp_cost"]
        if pp_cost < 0:
            raise ValueError(f"Field 'pp_cost' must be a non-negative integer, got {pp_cost} in '{entry['name']}'")
        category = entry["category"]
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid move category '{category}' in move '{entry['name']}'")

        #3. Type Check (exactly one type)
        move_type = entry["type"]
        if move_type not in VALID_TYPES:
            raise ValueError(f"Invalid move type '{move_type}' in move '{entry['name']}'")

        #4. Power Check (Physical/Special must be a positive integer, Status must be null)
        if "power" not in entry:
            raise ValueError(f"Missing required field 'power' in move '{entry['name']}'")
        power = entry["power"]
        if category == "Status" or entry.get("name") in ("Fissure", "Sheer Cold", "Night Shade", "Guillotine"):
            if power is not None:
                raise ValueError(f"Status moves must have null power, got {power} in '{entry['name']}'")
        else:
            if not isinstance(power, int) or power <= 0:
                raise ValueError(f"Damaging moves must have a positive integer power, got {power} in '{entry['name']}'")

        #5. Accuracy Check (int or float 0-100, or null for moves that bypass accuracy checks)
        if "accuracy" not in entry:
            raise ValueError(f"Missing required field 'accuracy' in move '{entry['name']}'")
        accuracy = entry["accuracy"]
        if accuracy is not None:
            if not isinstance(accuracy, (int, float)):
                raise ValueError(f"Field 'accuracy' must be a number or null, got {type(accuracy).__name__} in '{entry['name']}'")
            if not (0 <= accuracy <= 100):
                raise ValueError(f"Field 'accuracy' must be between 0 and 100, got {accuracy} in '{entry['name']}'")

        #6. Effects list structure check
        effects = entry["effects"]
        for index, eff in enumerate(effects):
            if not isinstance(eff, dict):
                raise ValueError(f"Each effect must be a JSON object, got {type(eff).__name__} in '{entry['name']}' at index {index}")
            
            #Simple validation on stat changes if defined
            eff_type = eff.get("effect_type")
            if eff_type == "stat_change":
                stat = eff.get("stat")
                if stat not in VALID_STATS and stat not in ("Evasion", "Accuracy"):
                    raise ValueError(f"Invalid stat '{stat}' in effect at index {index} in '{entry['name']}'")
                stages = eff.get("stages")
                if not isinstance(stages, int):
                    raise ValueError(f"Field 'stages' in stat change effect must be an integer in '{entry['name']}'")
                chance = eff.get("chance")
                if not isinstance(chance, (int, float)) or not (0.0 <= chance <= 1.0):
                    raise ValueError(f"Field 'chance' in stat change effect must be a float between 0.0 and 1.0 in '{entry['name']}'")
            elif eff_type == "status_apply":
                status = eff.get("status")
                if not isinstance(status, str):
                    raise ValueError(f"Field 'status' in status_apply effect must be a string in '{entry['name']}'")
                chance = eff.get("chance")
                if not isinstance(chance, (int, float)) or not (0.0 <= chance <= 1.0):
                    raise ValueError(f"Field 'chance' in status_apply effect must be a float between 0.0 and 1.0 in '{entry['name']}'")
                duration = eff.get("duration")
                if duration is not None and not isinstance(duration, int):
                    raise ValueError(f"Field 'duration' in status_apply effect must be an integer or null in '{entry['name']}'")
                target = eff.get("target")
                if target is not None and not isinstance(target, str):
                    raise ValueError(f"Field 'target' in status_apply effect must be a string in '{entry['name']}'")
            elif eff_type == "healing":
                heal_percent = eff.get("heal_percent")
                if not isinstance(heal_percent, (int, float)) or not (0.0 <= heal_percent <= 1.0):
                    raise ValueError(f"Field 'heal_percent' in healing effect must be a float between 0.0 and 1.0 in '{entry['name']}'")
                chance = eff.get("chance")
                if not isinstance(chance, (int, float)) or not (0.0 <= chance <= 1.0):
                    raise ValueError(f"Field 'chance' in healing effect must be a float between 0.0 and 1.0 in '{entry['name']}'")
                target = eff.get("target")
                if target is not None and not isinstance(target, str):
                    raise ValueError(f"Field 'target' in healing effect must be a string in '{entry['name']}'")
            elif eff_type == "multi_hit":
                min_hits = eff.get("min_hits")
                max_hits = eff.get("max_hits")
                if not isinstance(min_hits, int) or not isinstance(max_hits, int):
                    raise ValueError(f"Fields 'min_hits' and 'max_hits' in multi_hit effect must be integers in '{entry['name']}'")
                chance = eff.get("chance")
                if not isinstance(chance, (int, float)) or not (0.0 <= chance <= 1.0):
                    raise ValueError(f"Field 'chance' in multi_hit effect must be a float between 0.0 and 1.0 in '{entry['name']}'")
            elif eff_type == "weather_change":
                weather = eff.get("weather")
                if weather not in ("Clear", "Sunny", "Rain", "Hail", "Sandstorm", "Grassy Terrain", "Electric Terrain"):
                    raise ValueError(f"Invalid weather '{weather}' in weather_change effect at index {index} in '{entry['name']}'")
                chance = eff.get("chance")
                if not isinstance(chance, (int, float)) or not (0.0 <= chance <= 1.0):
                    raise ValueError(f"Field 'chance' in weather_change effect must be a float between 0.0 and 1.0 in '{entry['name']}'")

        validated_moves.append(entry)

    return validated_moves
