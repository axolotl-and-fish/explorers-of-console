"""
save_game.py

Handles everything to do with saving and loading games; saving, encoding, validating, checksumming, loading. Game saves have a .pecsav extension (standing for Pokémon Explorers of Console SAVe)
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

#!!!CAUTION!!!
#Changing anything in this source file will likely break compatability with your existing save files.
#Only modify this file if you know what you're doing and understand that you'll probably not be able to use save files from the previous version.

import os
import json
import base64
import hashlib
import uuid
import datetime
from dungeon import DungeonFloor, Room
from pokemon import Pokemon  # type: ignore
from message_log import MessageLog, wrap_text  # type: ignore

SALT = "SWAMPERT_IS_THE_GOD_OF_ALL_TIME"


def get_save_dir() -> str:
    from data_utils import get_app_base_dir
    save_dir = os.path.join(get_app_base_dir(), "save_data")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def serialize_pokemon(poke: Pokemon) -> dict:
    if poke is None:
        return {}
    poke_id = getattr(poke, "id", None)
    if not poke_id:
        poke_id = str(uuid.uuid4())
        poke.id = poke_id

    moves_data = []
    if hasattr(poke, "moves") and poke.moves:
        for m in poke.moves:
            if isinstance(m, dict):
                moves_data.append(dict(m))

    damaged_by = {}
    for p, turn in getattr(poke, "damaged_by_pokemons", {}).items():
        p_id = getattr(p, "id", None)
        if p_id:
            damaged_by[p_id] = turn
    #So this is fun! The game state needs to be literally 100% identical when loaded, so we need to store basically EVERYTHING.
    #There's more explanations for most of this stuff in game.py
    return {
        "id": poke_id,
        "species_name": getattr(poke, "species_name", "") or poke.name,
        "name": getattr(poke, "name", ""),
        "nickname": getattr(poke, "nickname", None),
        "level": getattr(poke, "level", 1),
        "experience": getattr(poke, "experience", 0),
        "exp": getattr(poke, "experience", 0),
        "current_hp": getattr(poke, "current_hp", 0),
        "max_pp": getattr(poke, "max_pp", 100),
        "current_pp": getattr(poke, "current_pp", 100),
        "max_belly": getattr(poke, "max_belly", 100.0),
        "current_belly": getattr(poke, "current_belly", 100.0),
        "warned_20": getattr(poke, "warned_20", False),
        "warned_10": getattr(poke, "warned_10", False),
        "warned_0": getattr(poke, "warned_0", False),
        "ivs": dict(getattr(poke, "ivs", {})),
        "evs": dict(getattr(poke, "evs", {})),
        "stats": dict(getattr(poke, "stats", {})),
        "stat_modifiers": dict(getattr(poke, "stat_modifiers", {})),
        "stat_stages": dict(getattr(poke, "stat_modifiers", {})),
        "status_effects": dict(getattr(poke, "status_effects", {})),
        "movement_speed_stage": getattr(poke, "movement_speed_stage", 0),
        "movement_speed_duration": getattr(poke, "movement_speed_duration", 0),
        "slow_turn_toggle": getattr(poke, "slow_turn_toggle", False),
        "moves": moves_data,
        "fake_out_used_this_floor": getattr(poke, "fake_out_used_this_floor", False),
        "disable_move_effect": getattr(poke, "disable_move_effect", None),
        "imprisoned_moves": list(getattr(poke, "imprisoned_moves", [])),
        "last_used_move": getattr(poke, "last_used_move", None),
        "last_used_move_on_floor": getattr(poke, "last_used_move_on_floor", None),
        "charging_move": dict(poke.charging_move) if getattr(poke, "charging_move", None) else None,
        "seen_moves": list(getattr(poke, "seen_moves", [])),
        "x": getattr(poke, "x", 0),
        "y": getattr(poke, "y", 0),
        "last_dx": getattr(poke, "last_dx", 0),
        "last_dy": getattr(poke, "last_dy", 0),
        "napping": getattr(poke, "napping", False),
        "just_woke_up": getattr(poke, "just_woke_up", False),
        "target_exit": list(poke.target_exit) if getattr(poke, "target_exit", None) else None,
        "is_leader": getattr(poke, "is_leader", False),
        "held_item": dict(poke.held_item) if getattr(poke, "held_item", None) else None,
        "ability": getattr(poke, "ability", None),
        "tactic": getattr(poke, "tactic", None),
        "last_damage_source": getattr(poke, "last_damage_source", None),
        "has_been_attacked_by_team": getattr(poke, "has_been_attacked_by_team", False),
        "cannot_be_revived": getattr(poke, "cannot_be_revived", False),
        "swapped_this_turn": getattr(poke, "swapped_this_turn", False),
        "has_notified_can_evolve": getattr(poke, "has_notified_can_evolve", False),
        "temp_types": list(poke.temp_types) if getattr(poke, "temp_types", None) else None,
        "protect_consecutive": getattr(poke, "protect_consecutive", 0),
        "echoed_voice_count": getattr(poke, "echoed_voice_count", 0),
        "damage_hit_turns": list(getattr(poke, "damage_hit_turns", [])),
        "last_move_failed_turn": getattr(poke, "last_move_failed_turn", None),
        "last_teammate_fainted_turn": getattr(poke, "last_teammate_fainted_turn", None),
        "last_hit_by_move": dict(poke.last_hit_by_move) if getattr(poke, "last_hit_by_move", None) else None,
        "damaged_by_pokemons": damaged_by,
        "mimic_original_state": dict(poke.mimic_original_state) if getattr(poke, "mimic_original_state", None) else None,
        "transform_original_state": dict(poke.transform_original_state) if getattr(poke, "transform_original_state", None) else None,
        "is_transformed": getattr(poke, "is_transformed", False),
        "original_species_name": getattr(poke, "original_species_name", None),
        "original_name": getattr(poke, "original_name", None),
        "original_stats": dict(poke.original_stats) if getattr(poke, "original_stats", None) else None,
        "original_moves": list(poke.original_moves) if getattr(poke, "original_moves", None) else None,
    }


def deserialize_pokemon(data: dict) -> Pokemon:
    """Restores the game state from a loaded save file."""
    if not data:
        return None
    species = data.get("species_name", "Bulbasaur")
    level = data.get("level", 1)
    nickname = data.get("nickname")

    poke = Pokemon(species, level=level, nickname=nickname)
    poke.id = data.get("id", str(uuid.uuid4()))
    if "experience" in data:
        poke.experience = data["experience"]
    elif "exp" in data:
        poke.experience = data["exp"]

    if "ivs" in data and isinstance(data["ivs"], dict):
        poke.ivs = dict(data["ivs"])
    if "evs" in data and isinstance(data["evs"], dict):
        poke.evs = dict(data["evs"])

    if "stats" in data and isinstance(data["stats"], dict):
        poke.stats = dict(data["stats"])
    else:
        poke.recalculate_stats()

    hp_max = poke.stats.get("HP", 10) if hasattr(poke, "stats") and isinstance(poke.stats, dict) else 10
    poke.current_hp = float(data.get("current_hp", hp_max))

    poke.max_pp = data.get("max_pp", 100)
    poke.current_pp = data.get("current_pp", poke.max_pp)

    if "max_belly" in data:
        poke.max_belly = float(data["max_belly"])
    if "current_belly" in data:
        poke.current_belly = float(data["current_belly"])

    poke.warned_20 = data.get("warned_20", False)
    poke.warned_10 = data.get("warned_10", False)
    poke.warned_0 = data.get("warned_0", False)

    if "stat_modifiers" in data and isinstance(data["stat_modifiers"], dict):
        poke.stat_modifiers = dict(data["stat_modifiers"])
    elif "stat_stages" in data and isinstance(data["stat_stages"], dict):
        poke.stat_modifiers = dict(data["stat_stages"])

    if "status_effects" in data and isinstance(data["status_effects"], dict):
        poke.status_effects = dict(data["status_effects"])

    poke.movement_speed_stage = data.get("movement_speed_stage", 0)
    poke.movement_speed_duration = data.get("movement_speed_duration", 0)
    poke.slow_turn_toggle = data.get("slow_turn_toggle", False)

    if "moves" in data and isinstance(data["moves"], list):
        poke.moves = [dict(m) for m in data["moves"]]

    poke.fake_out_used_this_floor = data.get("fake_out_used_this_floor", False)
    poke.disable_move_effect = data.get("disable_move_effect")
    poke.imprisoned_moves = list(data.get("imprisoned_moves", []))
    poke.last_used_move = data.get("last_used_move")
    poke.last_used_move_on_floor = data.get("last_used_move_on_floor")
    poke.charging_move = dict(data["charging_move"]) if data.get("charging_move") else None
    poke.seen_moves = set(data.get("seen_moves", []))

    poke.x = data.get("x", 0)
    poke.y = data.get("y", 0)
    poke.last_dx = data.get("last_dx", 0)
    poke.last_dy = data.get("last_dy", 0)
    poke.napping = data.get("napping", False)
    poke.just_woke_up = data.get("just_woke_up", False)
    target_exit = data.get("target_exit")
    poke.target_exit = tuple(target_exit) if target_exit else None

    poke.is_leader = data.get("is_leader", False)
    poke.held_item = dict(data["held_item"]) if data.get("held_item") else None
    poke.ability = data.get("ability")
    poke.tactic = data.get("tactic")
    poke.last_damage_source = data.get("last_damage_source")
    poke.has_been_attacked_by_team = data.get("has_been_attacked_by_team", False)
    poke.cannot_be_revived = data.get("cannot_be_revived", False)
    poke.swapped_this_turn = data.get("swapped_this_turn", False)
    poke.has_notified_can_evolve = data.get("has_notified_can_evolve", False)
    poke.temp_types = list(data["temp_types"]) if data.get("temp_types") else None
    poke.protect_consecutive = data.get("protect_consecutive", 0)
    poke.echoed_voice_count = data.get("echoed_voice_count", 0)
    poke.damage_hit_turns = list(data.get("damage_hit_turns", []))
    poke.last_move_failed_turn = data.get("last_move_failed_turn")
    poke.last_teammate_fainted_turn = data.get("last_teammate_fainted_turn")
    poke.last_hit_by_move = dict(data["last_hit_by_move"]) if data.get("last_hit_by_move") else None

    poke.mimic_original_state = dict(data["mimic_original_state"]) if data.get("mimic_original_state") else None
    poke.transform_original_state = dict(data["transform_original_state"]) if data.get("transform_original_state") else None
    poke.is_transformed = data.get("is_transformed", False)
    poke.original_species_name = data.get("original_species_name")
    poke.original_name = data.get("original_name")
    poke.original_stats = dict(data["original_stats"]) if data.get("original_stats") else None
    poke.original_moves = list(data["original_moves"]) if data.get("original_moves") else None

    return poke


def serialize_room(r: Room) -> dict:
    """Encodes room data for the current floor for saving. Thankfully since room data is quite efficient, there's really not a whole lot that needs to be added."""
    return {
        "x1": r.x1,
        "y1": r.y1,
        "x2": r.x2,
        "y2": r.y2,
        "cell_x": r.cell_x,
        "cell_y": r.cell_y,
        "merged_with": [list(m) for m in getattr(r, "merged_with", set())]
    }


def deserialize_room(data: dict) -> Room:
    """Decodes room data for the current floor for loading."""
    r = Room(data["x1"], data["y1"], data["x2"], data["y2"], data["cell_x"], data["cell_y"])
    r.merged_with = set(tuple(m) for m in data.get("merged_with", []))
    return r


def serialize_binding(b: dict) -> dict:
    """Encodes move bindings for Pokémon on the current floor for saving."""
    return {
        "attacker_id": getattr(b.get("attacker"), "id", None),
        "defender_id": getattr(b.get("defender"), "id", None),
        "turns_left": b.get("turns_left", 0),
        "move": dict(b.get("move", {})) if b.get("move") else {}
    }


def deserialize_binding(b: dict, poke_map: dict) -> dict | None:
    """Decodes move bindings for Pokémon on the current floor for loading."""
    attacker = poke_map.get(b.get("attacker_id"))
    defender = poke_map.get(b.get("defender_id"))
    if attacker and defender:
        return {
            "attacker": attacker,
            "defender": defender,
            "turns_left": b.get("turns_left", 0),
            "move": dict(b.get("move", {}))
        }
    return None


def serialize_future_sight(fs: dict) -> dict:
    #Because Future Sight is special, it needs its own handling
    return {
        "tile": list(fs.get("tile", (0, 0))),
        "turns_left": fs.get("turns_left", 0),
        "user_id": getattr(fs.get("user"), "id", None),
        "move": dict(fs.get("move", {})) if fs.get("move") else {}
    }


def deserialize_future_sight(fs: dict, poke_map: dict) -> dict | None:
    tile = tuple(fs.get("tile", [0, 0]))
    user = poke_map.get(fs.get("user_id"))
    if user:
        return {
            "tile": tile,
            "turns_left": fs.get("turns_left", 0),
            "user": user,
            "move": dict(fs.get("move", {}))
        }
    return None


def serialize_game_state(game) -> dict:
    """Converts entire Game object into a JSON-serializable dictionary, which is how save files are stored before encoding."""
    floor = game.floor
    rooms_data = {}
    if hasattr(floor, "rooms") and floor.rooms:
        for cell, room in floor.rooms.items():
            cell_key = f"{cell[0]},{cell[1]}"
            rooms_data[cell_key] = serialize_room(room)

    bounds_data = {}
    if hasattr(floor, "cell_bounds") and floor.cell_bounds:
        for cell, bounds in floor.cell_bounds.items():
            cell_key = f"{cell[0]},{cell[1]}"
            bounds_data[cell_key] = dict(bounds)

    floor_data = {
        "width": floor.width,
        "height": floor.height,
        "grid": [list(row) for row in floor.grid],
        "rooms": rooms_data,
        "cell_bounds": bounds_data,
        "corridor_tiles": [list(c) for c in getattr(floor, "corridor_tiles", set())],
        "dead_end_tiles": [list(d) for d in getattr(floor, "dead_end_tiles", set())],
    }

    party_data = [serialize_pokemon(p) for p in getattr(game, "party", [])]
    spawned_data = [serialize_pokemon(p) for p in getattr(game, "spawned_pokemon", [])]

    items_floor_data = {}
    items_on_floor = getattr(game, "items_on_floor", {})
    for pos, item in items_on_floor.items():
        pos_key = f"{pos[0]},{pos[1]}"
        items_floor_data[pos_key] = dict(item)

    history_data = []
    for rec in getattr(game, "all_team_members", []):
        entry = dict(rec)
        poke_obj = entry.get("pokemon")
        if poke_obj is not None:
            p_id = getattr(poke_obj, "id", None)
            if not p_id:
                p_id = str(uuid.uuid4())
                poke_obj.id = p_id
            entry["pokemon_id"] = p_id
            entry["serialized_pokemon"] = serialize_pokemon(poke_obj)
            del entry["pokemon"]
        elif "pokemon" in entry:
            del entry["pokemon"]
        history_data.append(entry)

    leech_seed_data = {}
    for target, source in getattr(game, "leech_seed_sources", {}).items():
        t_id = getattr(target, "id", None)
        s_id = getattr(source, "id", None)
        if t_id and s_id:
            leech_seed_data[t_id] = s_id

    taunt_data = {}
    for target, source in getattr(game, "taunt_sources", {}).items():
        t_id = getattr(target, "id", None)
        s_id = getattr(source, "id", None)
        if t_id and s_id:
            taunt_data[t_id] = s_id

    future_sight_data = [serialize_future_sight(fs) for fs in getattr(game, "future_sight_effects", [])]

    play_time = game.get_elapsed_play_time() if hasattr(game, "get_elapsed_play_time") else getattr(game, "accumulated_play_time", 0.0)

    weather_turns = getattr(game, "weather_turns_left", getattr(game, "weather_turns", 0))

    return {
        "compatibility_mode": getattr(game, "compatibility_mode", False),
        "player_pokemon_id": getattr(getattr(game, "player_pokemon", None), "id", None),
        "floor_number": getattr(game, "floor_number", 1),
        "turn_number": getattr(game, "turn_number", 0),
        "player_action_number": getattr(game, "player_action_number", 0),
        "turn_count": getattr(game, "turn_count", 0),
        "start_time": getattr(game, "start_time", 0.0),
        "accumulated_play_time": play_time,
        "weather": getattr(game, "weather", "Clear"),
        "weather_turns_left": weather_turns,
        "weather_turns": weather_turns,
        "wonder_room_turns": getattr(game, "wonder_room_turns", 0),
        "future_sight_effects": future_sight_data,
        "gravity": getattr(game, "gravity", False),
        "radar_active": getattr(game, "radar_active", False),
        "scanner_active": getattr(game, "scanner_active", False),
        "money": getattr(game, "money", 0),
        "total_enemy_exp": getattr(game, "total_enemy_exp", 0),
        "total_recruited_count": getattr(game, "total_recruited_count", 0),
        "game_ended": getattr(game, "game_ended", False),
        "game_won": getattr(game, "game_won", False),
        "stairs_position": list(getattr(game, "stairs_position", (0, 0))),
        "stairs_revealed": getattr(game, "stairs_revealed", False),
        "wonder_tile_position": list(getattr(game, "wonder_tile_position", (0, 0))),
        "wonder_tile_used": getattr(game, "wonder_tile_used", False),
        "explored_tiles": [list(pos) for pos in getattr(game, "explored_tiles", set())],
        "floor_spawn_list": list(getattr(game, "floor_spawn_list", [])),
        "inventory": [dict(item) for item in getattr(game, "inventory", [])],
        "items_on_floor": items_floor_data,
        "floor": floor_data,
        "party": party_data,
        "spawned_pokemon": spawned_data,
        "all_team_members": history_data,
        "encountered_species": getattr(game, "encountered_species", {}),
        "raw_messages": list(getattr(game.message_log, "raw_messages", [])),
        "message_log": list(getattr(game.message_log, "raw_messages", [])),
        "leech_seed_sources": leech_seed_data,
        "taunt_sources": taunt_data,
        "fire_spin_bindings": [serialize_binding(b) for b in getattr(game, "fire_spin_bindings", [])],
        "wrap_bindings": [serialize_binding(b) for b in getattr(game, "wrap_bindings", [])],
        "sand_tomb_bindings": [serialize_binding(b) for b in getattr(game, "sand_tomb_bindings", [])],
        "whirlpool_bindings": [serialize_binding(b) for b in getattr(game, "whirlpool_bindings", [])],
    }


def apply_game_state(game, state_dict: dict):
    """Restores a Game instance to match the serialized state_dict (when loading a save)"""
    import time
    game.floor_number = state_dict.get("floor_number", 1)
    game.turn_number = state_dict.get("turn_number", 0)
    game.player_action_number = state_dict.get("player_action_number", state_dict.get("turn_number", 0))
    game.turn_count = state_dict.get("turn_count", 0)
    game.start_time = state_dict.get("start_time", 0.0)
    if "accumulated_play_time" in state_dict:
        game.accumulated_play_time = float(state_dict["accumulated_play_time"])
    else:
        game.accumulated_play_time = 0.0
    game.session_start_time = time.time()
    game.compatibility_mode = state_dict.get("compatibility_mode", getattr(game, "compatibility_mode", False))
    game.weather = state_dict.get("weather", "Clear")
    weather_turns = state_dict.get("weather_turns_left", state_dict.get("weather_turns", 0))
    game.weather_turns_left = weather_turns
    game.weather_turns = weather_turns
    game.wonder_room_turns = state_dict.get("wonder_room_turns", 0)
    game.gravity = state_dict.get("gravity", False)
    game.radar_active = state_dict.get("radar_active", False)
    game.scanner_active = state_dict.get("scanner_active", False)
    game.money = state_dict.get("money", 0)
    game.total_enemy_exp = state_dict.get("total_enemy_exp", 0)
    game.total_recruited_count = state_dict.get("total_recruited_count", 0)
    game.game_ended = state_dict.get("game_ended", False)
    game.game_won = state_dict.get("game_won", False)
    game.stairs_position = tuple(state_dict.get("stairs_position", [0, 0]))
    game.stairs_revealed = state_dict.get("stairs_revealed", False)
    game.wonder_tile_position = tuple(state_dict.get("wonder_tile_position", [0, 0]))
    game.wonder_tile_used = state_dict.get("wonder_tile_used", False)
    game.explored_tiles = set(tuple(pos) for pos in state_dict.get("explored_tiles", []))
    game.floor_spawn_list = list(state_dict.get("floor_spawn_list", []))
    game.inventory = [dict(item) for item in state_dict.get("inventory", [])]

    game.items_on_floor = {}
    for pos_key, item in state_dict.get("items_on_floor", {}).items():
        parts = pos_key.split(",")
        pos = (int(parts[0]), int(parts[1]))
        game.items_on_floor[pos] = dict(item)

    floor_data = state_dict.get("floor", {})
    width = floor_data.get("width", 56)
    height = floor_data.get("height", 32)

    game.floor = DungeonFloor.__new__(DungeonFloor)
    game.floor.width = width
    game.floor.height = height
    if "grid" in floor_data:
        game.floor.grid = [list(row) for row in floor_data["grid"]]

    rooms_dict = {}
    if "rooms" in floor_data:
        for cell_key, r_data in floor_data["rooms"].items():
            parts = cell_key.split(",")
            cell = (int(parts[0]), int(parts[1]))
            rooms_dict[cell] = deserialize_room(r_data)
    game.floor.rooms = rooms_dict

    bounds_dict = {}
    if "cell_bounds" in floor_data:
        for cell_key, b_data in floor_data["cell_bounds"].items():
            parts = cell_key.split(",")
            cell = (int(parts[0]), int(parts[1]))
            bounds_dict[cell] = dict(b_data)
    game.floor.cell_bounds = bounds_dict

    game.floor.corridor_tiles = set(tuple(c) for c in floor_data.get("corridor_tiles", []))
    game.floor.dead_end_tiles = set(tuple(d) for d in floor_data.get("dead_end_tiles", []))

    poke_map = {}
    party_list = []
    for p_data in state_dict.get("party", []):
        poke = deserialize_pokemon(p_data)
        party_list.append(poke)
        poke_map[poke.id] = poke

    game.party = party_list

    #Determine the true leader
    target_leader_id = state_dict.get("player_pokemon_id")
    leader = None
    if target_leader_id and target_leader_id in poke_map and poke_map[target_leader_id] in party_list:
        leader = poke_map[target_leader_id]
    else:
        # Check if any deserialized party member has is the leader
        leader = next((p for p in party_list if getattr(p, "is_leader", False)), None)
        if leader is None and party_list:
            leader = party_list[0]

    game.player_pokemon = leader
    for p in party_list:
        p.is_leader = (p is leader)

    if game.player_pokemon:
        game.player_x, game.player_y = game.player_pokemon.x, game.player_pokemon.y

    spawned_list = []
    for p_data in state_dict.get("spawned_pokemon", []):
        poke = deserialize_pokemon(p_data)
        spawned_list.append(poke)
        poke_map[poke.id] = poke
    game.spawned_pokemon = spawned_list

    #Restore damaged_by_pokemons references
    for p_data in state_dict.get("party", []) + state_dict.get("spawned_pokemon", []):
        p_id = p_data.get("id")
        if p_id in poke_map:
            poke = poke_map[p_id]
            poke.damaged_by_pokemons = {}
            for att_id, turn in p_data.get("damaged_by_pokemons", {}).items():
                if att_id in poke_map:
                    poke.damaged_by_pokemons[poke_map[att_id]] = turn

    history_list = []
    for h_data in state_dict.get("all_team_members", []):
        entry = dict(h_data)
        p_id = entry.get("pokemon_id")
        serialized_poke = entry.pop("serialized_pokemon", None)
        if p_id and p_id in poke_map:
            entry["pokemon"] = poke_map[p_id]
        elif serialized_poke:
            restored_poke = deserialize_pokemon(serialized_poke)
            entry["pokemon"] = restored_poke
            poke_map[restored_poke.id] = restored_poke
        else:
            entry["pokemon"] = None
        history_list.append(entry)
    game.all_team_members = history_list

    game.encountered_species = state_dict.get("encountered_species", {})

    game.message_log = MessageLog()
    raw_msgs = state_dict.get("raw_messages", state_dict.get("message_log", []))
    game.message_log.raw_messages = []
    for msg in raw_msgs:
        if isinstance(msg, (tuple, list)):
            txt = msg[0]
            turn_num = msg[1] if len(msg) > 1 else 0
            imp = msg[2] if len(msg) > 2 else False
            game.message_log.raw_messages.append((txt, turn_num, imp))
        else:
            game.message_log.raw_messages.append((str(msg), game.turn_number, False))
    if len(game.message_log.raw_messages) > 99:
        game.message_log.raw_messages = game.message_log.raw_messages[-99:]

    #Populate the message history window with the last four messages...
    game.message_log.history = []
    last_four = game.message_log.raw_messages[-4:]
    for txt, turn_num, imp in last_four:
        wrapped = wrap_text(txt, max_width=56)
        for line in wrapped:
            game.message_log.history.append((line, turn_num, imp))

    #...then add "Game loaded successfully."
    game.message_log.log("Game loaded successfully.", getattr(game, "player_action_number", game.turn_number), False)
    game.message_log.step_page()
    game.message_log.pending_lines = []
    game.message_log.has_more_page = False

    game.leech_seed_sources = {}
    for t_id, s_id in state_dict.get("leech_seed_sources", {}).items():
        if t_id in poke_map and s_id in poke_map:
            game.leech_seed_sources[poke_map[t_id]] = poke_map[s_id]

    game.taunt_sources = {}
    for t_id, s_id in state_dict.get("taunt_sources", {}).items():
        if t_id in poke_map and s_id in poke_map:
            game.taunt_sources[poke_map[t_id]] = poke_map[s_id]

    game.future_sight_effects = []
    for fs_data in state_dict.get("future_sight_effects", []):
        fs = deserialize_future_sight(fs_data, poke_map)
        if fs:
            game.future_sight_effects.append(fs)

    game.fire_spin_bindings = []
    for b in state_dict.get("fire_spin_bindings", []):
        if "attacker_id" in b:
            des = deserialize_binding(b, poke_map)
            if des:
                game.fire_spin_bindings.append(des)
        elif "attacker" in b:
            game.fire_spin_bindings.append(b)

    game.wrap_bindings = []
    for b in state_dict.get("wrap_bindings", []):
        if "attacker_id" in b:
            des = deserialize_binding(b, poke_map)
            if des:
                game.wrap_bindings.append(des)
        elif "attacker" in b:
            game.wrap_bindings.append(b)

    game.sand_tomb_bindings = []
    for b in state_dict.get("sand_tomb_bindings", []):
        if "attacker_id" in b:
            des = deserialize_binding(b, poke_map)
            if des:
                game.sand_tomb_bindings.append(des)
        elif "attacker" in b:
            game.sand_tomb_bindings.append(b)

    game.whirlpool_bindings = []
    for b in state_dict.get("whirlpool_bindings", []):
        if "attacker_id" in b:
            des = deserialize_binding(b, poke_map)
            if des:
                game.whirlpool_bindings.append(des)
        elif "attacker" in b:
            game.whirlpool_bindings.append(b)

    #We are in-game now, hand control back to the user.
    game.title_screen_state = None
    game.starter_select_state = None
    game.high_scores_state = None
    game.pause_menu_state = None
    game.load_game_state = None
    game.is_running = True


def save_game(game) -> str:
    """Serializes and saves the game state to a PECSAV file (it's just plaintext)"""
    save_dir = get_save_dir()
    dt_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"save-{dt_str}.pecsav"
    filepath = os.path.join(save_dir, filename)

    state_dict = serialize_game_state(game)
    payload_json = json.dumps(state_dict, sort_keys=True, separators=(",", ":"))

    checksum_input = payload_json + SALT
    checksum = hashlib.sha256(checksum_input.encode("utf-8")).hexdigest()

    container = {
        "checksum": checksum,
        "payload": state_dict
    }

    container_json = json.dumps(container, sort_keys=True, separators=(",", ":"))
    encoded_bytes = base64.b64encode(container_json.encode("utf-8"))

    with open(filepath, "wb") as f:
        f.write(encoded_bytes)

    return filepath


def validate_save_file(filepath: str) -> tuple[bool, dict | None]:
    """Validates a save file's checksum."""
    if not os.path.exists(filepath):
        return False, None
    try:
        with open(filepath, "rb") as f:
            encoded_bytes = f.read()

        container_json = base64.b64decode(encoded_bytes).decode("utf-8")
        container = json.loads(container_json)

        checksum = container.get("checksum")
        payload = container.get("payload")

        if not checksum or payload is None:
            return False, None

        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected_checksum = hashlib.sha256((payload_json + SALT).encode("utf-8")).hexdigest()

        if checksum != expected_checksum:
            return False, None

        return True, payload
    except Exception:
        return False, None


def load_game_from_file(filepath: str, game=None) -> tuple[bool, str, object]:
    """Validates, loads, and deletes a save file.

    Returns tuple (success: bool, error_message: str, game_instance)
    """
    valid, payload = validate_save_file(filepath)
    if not valid or payload is None:
        return False, "Save file is corrupt!", game

    try:
        if game is None:
            from game import Game
            game = Game()
        apply_game_state(game, payload)

        #Delete save file ONLY upon successful loading
        try:
            os.remove(filepath)
        except Exception:
            pass

        return True, "", game
    except Exception as e:
        return False, f"Failed to load save file: {str(e)}", game


def list_save_files() -> list[dict]:
    """Lists all available .pecsav save files in save_data directory - used for the Load Game screen"""
    save_dir = get_save_dir()
    files = []
    if not os.path.exists(save_dir):
        return files

    for fname in os.listdir(save_dir):
        if fname.startswith("save-") and fname.endswith(".pecsav"):
            fpath = os.path.join(save_dir, fname)
            mtime = os.path.getmtime(fpath)

            #Peek payload summary if possible, to display a summary of the game to the player
            valid, payload = validate_save_file(fpath)
            info_str = "Unknown"
            if valid and payload:
                fl = payload.get("floor_number", 1)
                party = payload.get("party", [])
                target_leader_id = payload.get("player_pokemon_id")
                leader_poke = None
                if target_leader_id and party:
                    leader_poke = next((p for p in party if p.get("id") == target_leader_id), None)
                if leader_poke is None and party:
                    leader_poke = next((p for p in party if p.get("is_leader", False)), party[0])
                leader_name = leader_poke.get("name", "Pokemon") if leader_poke else "Pokemon"
                lvl = leader_poke.get("level", 1) if leader_poke else 1
                info_str = f"Floor {fl:02d} - {leader_name} Lv {lvl}"
            else:
                info_str = "CORRUPT SAVE FILE"

            files.append({
                "filename": fname,
                "filepath": fpath,
                "mtime": mtime,
                "info": info_str,
                "is_valid": valid,
            })

    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files


def attempt_emergency_save(game) -> str | None:
    """Attempts to automatically save the game during an unhandled exception or crash.
    
    Returns the saved file path on success, or None if saving failed or no active game was in progress.
    
    Probably extremely unreliable given that the game would be in an error state, needs further testing
    """
    if game is None:
        return None
    #Only save if an actual run is in progress and player is alive
    if getattr(game, "player_pokemon", None) is None:
        return None
    if getattr(game, "game_ended", False) or getattr(game, "game_won", False):
        return None
    if int(getattr(game.player_pokemon, "current_hp", 0)) <= 0:
        return None

    try:
        return save_game(game)
    except Exception:
        return None