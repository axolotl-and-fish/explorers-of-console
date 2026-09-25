"""
tms_db.py

Handles, parses, and validates tms.json, and generates TM item definitions.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import json
from data_utils import get_data_file_path

VALID_RARITIES = {"Common", "Uncommon", "Rare", "Very Rare", "Epic", "Legendary"}


def load_tms_raw(filepath: str | None = None) -> list[dict]:
    """Loads and validates the raw TMs database from a JSON file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON data violates schema rules (must only have move_name, value, rarity).
    """
    if filepath is None:
        filepath = get_data_file_path("tms.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"TMs database file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file format: {e}")

    if not isinstance(data, list):
        raise ValueError("TMs database must be a JSON list of TM objects.")

    validated = []
    for idx, entry in enumerate(data, 1):
        if not isinstance(entry, dict):
            raise ValueError(f"TM entry #{idx} must be a JSON object.")

        # Check allowed keys: only move_name, value, rarity
        allowed_keys = {"move_name", "value", "rarity"}
        # Support 'name' or 'move' as aliases for 'move_name'
        keys_present = set(entry.keys())
        norm_keys = set()
        for k in keys_present:
            if k in ("name", "move"):
                norm_keys.add("move_name")
            else:
                norm_keys.add(k)

        extra_keys = norm_keys - allowed_keys
        if extra_keys:
            raise ValueError(f"TM entry #{idx} contains disallowed fields: {extra_keys}")

        move_name = entry.get("move_name") or entry.get("move") or entry.get("name")
        if not isinstance(move_name, str) or not move_name.strip():
            raise ValueError(f"TM entry #{idx} 'move_name' must be a non-empty string.")

        value = entry.get("value")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"TM entry #{idx} 'value' must be a non-negative integer.")

        rarity = entry.get("rarity")
        if rarity not in VALID_RARITIES:
            raise ValueError(f"TM entry #{idx} 'rarity' '{rarity}' must be one of {VALID_RARITIES}.")

        validated.append({
            "move_name": move_name.strip(),
            "value": value,
            "rarity": rarity
        })

    return validated


def _build_tm_description(move_name: str, move_desc: str) -> str:
    """Builds the standardized TM inventory description."""
    prefix = f"This Technical Machine can be used to teach the move {move_name}."
    move_desc = move_desc.strip() if move_desc else ""
    if not move_desc:
        return prefix
    if move_desc.startswith((".", "!", "?")):
        return f"{prefix}{move_desc}"
    return f"{prefix} {move_desc}"


def load_tms_database(tms_filepath: str | None = None, moves_filepath: str | None = None) -> list[dict]:
    """Loads and builds all TM item dictionaries with sequential numbering TM01-TM58."""
    raw_tms = load_tms_raw(tms_filepath)

    from moves_db import load_moves_database
    moves_list = load_moves_database(moves_filepath)
    moves_by_name: dict[str, dict] = {}
    for m in moves_list:
        name_lower = m["name"].lower()
        moves_by_name[name_lower] = m
        moves_by_name[name_lower.replace("-", " ")] = m
        moves_by_name[name_lower.replace(" ", "-")] = m

    tm_items = []
    for idx, entry in enumerate(raw_tms, 1):
        move_name = entry["move_name"]
        move_key = move_name.lower()
        move_data = moves_by_name.get(move_key)
        move_desc = move_data.get("description", "") if move_data else ""

        full_desc = _build_tm_description(move_name, move_desc)
        tm_name = f"TM{idx:02d} {move_name}"

        tm_item = {
            "name": tm_name,
            "move_name": move_name,
            "tm_number": idx,
            "type": "TM",
            "is_tm": True,
            "usable": True,
            "edible": False,
            "appearance": "•",
            "color": "yellow",
            "value": entry["value"],
            "rarity": entry["rarity"],
            "description": full_desc,
        }
        tm_items.append(tm_item)

    return tm_items


def get_tms_dict(tms_filepath: str | None = None, moves_filepath: str | None = None) -> dict[str, dict]:
    """Returns a dictionary mapping TM item names to their item dicts."""
    tms = load_tms_database(tms_filepath, moves_filepath)
    return {tm["name"]: tm for tm in tms}
