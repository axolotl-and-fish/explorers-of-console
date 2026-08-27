"""
items.py

This code handles items, item effects and item spawning within the dungeon.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import json
from data_utils import get_data_file_path

def load_items_database(filepath: str | None = None) -> dict:
    """Loads items database from a JSON file and builds a dictionary mapping item name to item dict"""
    if filepath is None:
        filepath = get_data_file_path("items.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Items database file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["name"]: entry for entry in data}

_items_json_path = get_data_file_path("items.json")
ITEMS_DB = load_items_database(_items_json_path)

#Used for the UI
RARITY_COLORS = {
    "Common": "\033[37m",
    "Uncommon": "\033[92m",
    "Rare": "\033[94m",
    "Very Rare": "\033[91m",
    "Epic": "\033[95m",
    "Legendary": "\033[93m"
}

#Weights of how often items should spawn of each rarity tier
RARITY_WEIGHTS = {
    "Common": 50,
    "Uncommon": 30,
    "Rare": 12,
    "Very Rare": 6,
    "Epic": 3,
    "Legendary": 1
}

def get_item_display_name(item: dict) -> str:
    """Returns formatted name of an item, appending a count if item is stackable"""
    if item.get("type") == "Money" or item.get("name") == "Poke":
        amount = item.get("amount", 0)
        return f"{amount} \033[30;43mP\033[0m"
    name = item["name"]
    if item.get("stackable", False):
        cnt = item.get("count", 1)
        return f"{name} ({cnt})"
    return name


def is_evolution_item(item: dict) -> bool:
    """Returns True if the item is an evolution item"""
    return item.get("evolution_item", False) or item.get("name") in (
        "Fire Stone", "Water Stone", "Thunder Stone", "Leaf Stone", "Moon Stone", "Sun Stone", "Link Cable"
    )


def can_use_evolution_item(item: dict, target) -> bool:
    """Returns True if an evolution item is compatible with target"""
    item_name = item.get("name")
    if not is_evolution_item(item):
        return False
    species_data = getattr(target, "species_data", {})
    for evo in species_data.get("evolutions", []):
        req_item = evo.get("item", evo.get("evolution_item"))
        if req_item == item_name:
            min_lvl = evo.get("min_level", evo.get("level"))
            if min_lvl is None or getattr(target, "level", 1) >= min_lvl:
                return True
    return False


def apply_item_effect(item: dict, target, game, is_thrown: bool = False):
    """Applies the use or throw effect of an item to a target Pokémon"""
    if hasattr(game, "party") and target not in game.party:
        target.has_been_attacked_by_team = True

    if is_thrown and hasattr(target, "napping") and target.napping:
        target.napping = False
        target.just_woke_up = True

    name = item["name"]
    edible = item.get("edible", False)
    
    if not is_thrown and edible and getattr(target, "current_belly", 0) > getattr(target, "max_belly", 100):
        game.log_message(f"{target.name} is too full to eat any more.")
        return

    #Edible items eaten by a team Pokemon restore 5% of max Belly (except food-type and apricorn items)
    if not is_thrown and edible and target in game.party:
        if hasattr(target, "current_belly") and name not in ("Apple", "Big Apple", "Huge Apple", "Banana", "Chestnut", "Grimy Food", "HP Up", "Protein", "Iron", "Calcium", "Zinc", "Carbos", "PP Up", "PP Max", "Hunger Seed", "Reviver Seed", "Tiny Reviver Seed", "Possess Orb") and not item.get("apricorn", False):
            restore_amount = 0.05 * target.max_belly
            target.current_belly = min(target.max_belly, target.current_belly + restore_amount)
            game.log_message(f"{target.name}'s belly was filled slightly!")

    if item.get("apricorn", False):
        if not is_thrown and hasattr(target, "current_belly"):
            ap_type = item.get("type", "Normal")
            target_types = getattr(target, "types", [])
            if ap_type == "Rainbow" or ap_type in target_types:
                percent = 0.10
            else:
                from type_chart import get_type_effectiveness
                eff = get_type_effectiveness(ap_type, target_types)
                if eff > 1.0:
                    percent = 0.08
                elif eff == 1.0:
                    percent = 0.06
                elif eff > 0.0:
                    percent = 0.04
                else:
                    percent = 0.02
            restore_amount = percent * target.max_belly
            target.current_belly = min(target.max_belly, target.current_belly + restore_amount)
            game.log_message(f"{target.name}'s belly was filled slightly!")

    if name == "Oran Berry":
        old_hp = target.current_hp
        target.current_hp = min(target.stats["HP"], target.current_hp + 100.0)
        healed = target.current_hp - old_hp
        from targeting import get_pokemon_position
        tx, ty = get_pokemon_position(game, target)
        game.flash_damages[(tx, ty)] = (f"{int(healed)}", "HEAL")
        game.trigger_damage_flash()
        game.log_message(f"{target.name}'s HP was restored.")
        
    elif name == "Apple":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 50.0)
            game.log_message(f"{target.name}'s belly was filled!")
        else:
            game.log_message("But nothing happened.")
            
    elif name == "Big Apple":
        if hasattr(target, "current_belly"):
            target.current_belly = target.max_belly
            game.log_message(f"{target.name}'s belly was fully filled!")
        else:
            game.log_message("But nothing happened.")

    elif name == "Huge Apple":
        if hasattr(target, "current_belly"):
            target.current_belly = target.max_belly * 1.20
            game.log_message(f"Whoa! {target.name}'s belly is unbelievably full!")
        else:
            game.log_message("But nothing happened.")

    elif name == "Banana":
        if hasattr(target, "current_belly"):
            target.current_belly = target.max_belly * 1.50
            game.log_message(f"Whoa! {target.name}'s belly is unbelievably full!")
        else:
            game.log_message("But nothing happened.")

    elif name == "Chestnut":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 0.10 * target.max_belly)
        target.last_damage_source = "Chestnut"
        target.current_hp -= 1.0
        from targeting import get_pokemon_position
        tx, ty = get_pokemon_position(game, target)
        game.flash_damages[(tx, ty)] = ("1", "\033[91m")
        game.trigger_damage_flash()
        game.log_message(f"Ouch, that's prickly!")
        if target.current_hp <= 0 and hasattr(game, "remove_party_member"):
            game.remove_party_member(target)

    elif name == "Grimy Food":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 0.30 * target.max_belly)
        import random
        if random.random() < 0.75:
            effects = [
                "poison", "toxic", "burn", "paralysis", "confusion",
                "slow", "lower_all_stats", "lower_atk_spatk_speed",
                "lower_def_spdef_evasion", "reduce_pp"
            ]
            chosen = random.choice(effects)
            if chosen == "poison":
                target.apply_status("Poison", game)
            elif chosen == "toxic":
                target.apply_status("Toxic", game)
            elif chosen == "burn":
                target.apply_status("Burn", game)
            elif chosen == "paralysis":
                target.apply_status("Paralysis", game)
            elif chosen == "confusion":
                target.apply_status("Confusion", game)
            elif chosen == "slow":
                target.apply_status("Slow", game)
            elif chosen == "lower_all_stats":
                for stat in ["Attack", "Defense", "Special_Attack", "Special_Defense", "Speed", "Accuracy", "Evasion"]:
                    target.apply_stat_modifier(stat, -1, game)
            elif chosen == "lower_atk_spatk_speed":
                for stat in ["Attack", "Special_Attack", "Speed"]:
                    target.apply_stat_modifier(stat, -3, game)
            elif chosen == "lower_def_spdef_evasion":
                for stat in ["Defense", "Special_Defense", "Evasion"]:
                    target.apply_stat_modifier(stat, -3, game)
            elif chosen == "reduce_pp":
                old_pp = getattr(target, "current_pp", 100)
                target.current_pp = max(0, old_pp - 30)
                game.log_message(f"{target.name}'s PP was drained!")
            
    elif name == "Pecha Berry":
        #Check if poisoned
        is_poisoned = target.status_effects.get("Poison") or target.status_effects.get("Toxic")
        if is_poisoned:
            target.cure_status("Poison", game)
            target.cure_status("Toxic", game)
        else:
            game.log_message("But nothing happened.")
            
    elif name == "Cheri Berry":
        #Check if paralyzed
        is_paralyzed = target.status_effects.get("Paralysis", 0) > 0
        if is_paralyzed:
            target.cure_status("Paralysis", game)
        else:
            game.log_message(f"But nothing happened.")

    elif name == "Chesto Berry":
        #Check if asleep. If not, give Sleepless instead
        has_sleep = target.status_effects.get("Sleep", 0) > 0 or target.status_effects.get("Resting", 0) > 0
        if has_sleep:
            target.cure_status("Sleep", game)
            target.cure_status("Resting", game)
        else:
            target.apply_status("Sleepless", game)

    elif name == "Rawst Berry":
        #Check if burned
        if target.status_effects.get("Burn"):
            target.cure_status("Burn", game)
        else:
            game.log_message("But nothing happened.")

    elif name == "Leppa Berry":
        if hasattr(target, "current_pp"):
            target.current_pp = min(target.max_pp, target.current_pp + 20)
            game.log_message(f"{target.name}'s PP was restored.")
        else:
            game.log_message("But nothing happened.")

    elif name == "Persim Berry":
        #Check if confused
        if target.status_effects.get("Confusion", 0) > 0:
            target.cure_status("Confusion", game)
        else:
            game.log_message("But nothing happened.")

    elif name == "Lum Berry":
        #All negative status effects go here.
        neg_statuses = ["Sleep", "Paralysis", "Poison", "Toxic", "Burn", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Fire Spin", "Slow", "Stuck", "Curse", "Drowsy", "Whirlpool", "Perishing", "Terrified", "Puppet", "Hallucinating", "Blind"]
        cured_any = False
        for st in neg_statuses:
            val = target.status_effects.get(st)
            if (isinstance(val, bool) and val) or (isinstance(val, (int, float)) and (val > 0 or val == -1)):
                target.cure_status(st, game)
                cured_any = True
        if not cured_any:
            game.log_message("But nothing happened.")

    elif name == "Sitrus Berry":
        target.gain_evs({"HP": 5}, game=game)
        old_hp = target.current_hp
        target.current_hp = float(target.stats["HP"])
        healed = target.current_hp - old_hp
        from targeting import get_pokemon_position
        tx, ty = get_pokemon_position(game, target)
        game.flash_damages[(tx, ty)] = (f"{int(healed)}", "HEAL")
        game.trigger_damage_flash()
        game.log_message(f"{target.name}'s HP was fully restored!")

    elif name == "Razz Berry":
        old_hp = target.current_hp
        target.current_hp = min(float(target.stats["HP"]), target.current_hp + 100.0)
        healed = target.current_hp - old_hp
        if healed > 0:
            from targeting import get_pokemon_position
            tx, ty = get_pokemon_position(game, target)
            game.flash_damages[(tx, ty)] = (f"{int(healed)}", "HEAL")
            game.trigger_damage_flash()
            game.log_message(f"{target.name}'s HP was restored.")
        target.status_effects["Friendly"] = True
        game.log_message(f"{target.name} feels more friendly!")

    elif name == "Nanab Berry":
        old_hp = target.current_hp
        target.current_hp = min(float(target.stats["HP"]), target.current_hp + 100.0)
        healed = target.current_hp - old_hp
        if healed > 0:
            from targeting import get_pokemon_position
            tx, ty = get_pokemon_position(game, target)
            game.flash_damages[(tx, ty)] = (f"{int(healed)}", "HEAL")
            game.trigger_damage_flash()
            game.log_message(f"{target.name}'s HP was restored.")
        target.change_movement_speed(target.movement_speed_stage + 1, game)

    elif name == "Pinap Berry":
        old_hp = target.current_hp
        target.current_hp = min(float(target.stats["HP"]), target.current_hp + 100.0)
        healed = target.current_hp - old_hp
        if healed > 0:
            from targeting import get_pokemon_position
            tx, ty = get_pokemon_position(game, target)
            game.flash_damages[(tx, ty)] = (f"{int(healed)}", "HEAL")
            game.trigger_damage_flash()
            game.log_message(f"{target.name}'s HP was restored.")
        target.status_effects["EXP Up"] = True
        game.log_message(f"{target.name} feels more experienced.")

    elif name == "Lansat Berry":
        target.apply_status("Focus Energy", game, duration=99999)

    elif name == "Jaboca Berry":
        target.apply_status("Counter", game, duration=99999)

    elif name == "Rowap Berry":
        target.apply_status("Mirror Coat", game, duration=99999)

    elif name == "Kee Berry":
        target.apply_status("Reflect", game, duration=99999)

    elif name == "Maranga Berry":
        target.apply_status("Light Screen", game, duration=99999)

    elif name == "Blinker Seed":
        target.apply_status("Blind", game, duration=10)

    elif name == "Crosseye Seed":
        target.apply_status("Hallucinating", game, duration=10)

    elif name == "Doom Seed":
        if target.level > 1:
            prev_level = target.level
            target._level = prev_level - 1
            target.experience = target.get_experience_required_for_level(prev_level) - 1
            target.recalculate_stats()
            game.log_message(f"{target.name} dropped to level {target.level}!")
        else:
            game.log_message(f"{target.name}'s level can't go any lower!")

    elif name == "Eyedrop Seed":
        if target.status_effects.get("Blind", 0) > 0:
            target.cure_status("Blind", game)
            game.log_message(f"{target.name}'s vision was restored!")
        elif target.status_effects.get("Hallucinating", 0) > 0:
            target.cure_status("Hallucinating", game)
        else:
            game.log_message(f"{target.name}'s vision is already clear.")

    elif name == "Hunger Seed":
        if target in game.party:
            if hasattr(target, "current_belly"):
                target.current_belly = max(0.0, target.current_belly * 0.5)
            game.log_message(f"Ugh! Disgusting! {target.name} feels really hungry!")
        else:
            target.apply_status("Sluggish", game, duration=99999)
            target.change_movement_speed(target.movement_speed_stage - 1, game)
            game.log_message(f"{target.name} was slowed!")

    elif name in ("Reviver Seed", "Tiny Reviver Seed", "Possess Orb"):
        game.log_message("But nothing happened.")

    elif name == "Warp Seed":
        from dungeon import FLOOR_CHAR
        valid_tiles = []
        for ry in range(game.floor.height):
            for rx in range(game.floor.width):
                if game.floor.grid[ry][rx] == FLOOR_CHAR:
                    if (rx, ry) != getattr(game, "stairs_position", None):
                        valid_tiles.append((rx, ry))
        if valid_tiles:
            import random
            wx, wy = random.choice(valid_tiles)
            game.set_poke_pos(target, wx, wy)
            game.log_message(f"{target.name} warped!")
        else:
            game.log_message("But nothing happened.")

    elif name == "Rare Candy":
        if target.level < 99:
            req_next = target.get_experience_required_for_level(target.level + 1)
            diff = max(1, req_next - target.experience)
            target.gain_experience(diff, game=game)
        else:
            game.log_message(f"{target.name} is already at the maximum level.")

    elif name in ("Occa Berry", "Passho Berry", "Wacan Berry", "Rindo Berry", "Yache Berry", "Chople Berry", "Kebia Berry", "Shuca Berry", "Coba Berry", "Payapa Berry", "Tanga Berry", "Charti Berry", "Kasib Berry", "Haban Berry", "Colbur Berry", "Babiri Berry", "Roseli Berry", "Chilan Berry", "Enigma Berry"):
        #Type-resistance berries
        berry_type_map = {
            "Occa Berry": ("Fire", "Fire Resist"),
            "Passho Berry": ("Water", "Water Resist"),
            "Wacan Berry": ("Electric", "Electric Resist"),
            "Rindo Berry": ("Grass", "Grass Resist"),
            "Yache Berry": ("Ice", "Ice Resist"),
            "Chople Berry": ("Fighting", "Fighting Resist"),
            "Kebia Berry": ("Poison", "Poison Resist"),
            "Shuca Berry": ("Ground", "Ground Resist"),
            "Coba Berry": ("Flying", "Flying Resist"),
            "Payapa Berry": ("Psychic", "Psychic Resist"),
            "Tanga Berry": ("Bug", "Bug Resist"),
            "Charti Berry": ("Rock", "Rock Resist"),
            "Kasib Berry": ("Ghost", "Ghost Resist"),
            "Haban Berry": ("Dragon", "Dragon Resist"),
            "Colbur Berry": ("Dark", "Dark Resist"),
            "Babiri Berry": ("Steel", "Steel Resist"),
            "Roseli Berry": ("Fairy", "Fairy Resist"),
            "Chilan Berry": ("Normal", "Normal Resist"),
            "Enigma Berry": ("All", "All Resist"),
        }
        t_label, st_key = berry_type_map[name]
        target.status_effects[st_key] = True
        if t_label == "All":
            game.log_message(f"{target.name} gained resistance to all types!")
        else:
            game.log_message(f"{target.name} gained {t_label} resistance!")
            
    elif name == "Max Elixir":
        if hasattr(target, "current_pp"):
            target.current_pp = target.max_pp
            game.log_message(f"{target.name}'s PP was fully restored!")
        else:
            game.log_message("But nothing happened.")
        
    elif name == "Elixir":
        if hasattr(target, "current_pp"):
            target.current_pp = min(target.max_pp, target.current_pp + 50)
            game.log_message(f"{target.name}'s PP was restored!")
        else:
            game.log_message("But nothing happened.")

    elif is_evolution_item(item):
        #Evolution items
        matching_evo = None
        for evo in target.species_data.get("evolutions", []):
            req_item = evo.get("item", evo.get("evolution_item"))
            if req_item == name:
                min_lvl = evo.get("min_level", evo.get("level"))
                if min_lvl is None or target.level >= min_lvl:
                    matching_evo = evo
                    break

        if matching_evo:
            target.evolve(matching_evo["to"], game=game, consumed_item_name=None)
        else:
            game.log_message(f"This item can't be used on {target.name}.")
        
    elif name == "Blast Seed":
        from targeting import get_pokemon_position
        tx, ty = get_pokemon_position(game, target)
        game.log_message("The Blast Seed exploded!")
        game.trigger_explosion(
            tx, ty,
            size=3,
            attacker=getattr(game, "player_pokemon", None),
            cause_name="Blast Seed",
            fixed_center_damage=20,
            fixed_adjacent_damage=10
        )
            
    #Fixed-damage throwing items
    elif name == "Geo Pebble":
        if is_thrown:
            game.log_message(f"The Geo Pebble hit {target.name}!")
            attacker = getattr(game, "player_pokemon", None)
            dmg = 10
            if attacker and attacker.status_effects.get("Power Toss", 0) > 0:
                dmg *= 2
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, dmg, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")

    elif name == "Gravelerock":
        if is_thrown:
            game.log_message(f"The Gravelerock hit {target.name}!")
            attacker = getattr(game, "player_pokemon", None)
            dmg = 20
            if attacker and attacker.status_effects.get("Power Toss", 0) > 0:
                dmg *= 2
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, dmg, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")

    #Variable-damage throwing items
    elif name == "Iron Thorn":
        if is_thrown:
            game.log_message(f"The Iron Thorn hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Iron Thorn", "category": "Physical", "type": "typeless", "power": 40}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")
            
    elif name == "Stick":
        if is_thrown:
            game.log_message(f"The Stick hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Stick", "category": "Physical", "type": "typeless", "power": 20}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")
            
    elif name == "Silver Spike":
        if is_thrown:
            game.log_message(f"The Silver Spike hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Silver Spike", "category": "Physical", "type": "typeless", "power": 60}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")
            
    elif name == "Gold Fang":
        if is_thrown:
            game.log_message(f"The Gold Fang hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Gold Fang", "category": "Physical", "type": "typeless", "power": 200}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")
            
    elif name == "Cacnea Spike":
        if is_thrown:
            game.log_message(f"The Cacnea Spike hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Cacnea Spike", "category": "Physical", "type": "typeless", "power": 100}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")

    elif name == "Corsola Twig":
        if is_thrown:
            game.log_message(f"The Corsola Twig hit {target.name}!")
            from combat import calculate_damage
            attacker = game.player_pokemon
            thorn_move = {"name": "Corsola Twig", "category": "Physical", "type": "typeless", "power": 150}
            damage, is_critical, type_mult = calculate_damage(attacker, target, thorn_move, game)
            if is_critical:
                game.log_message("A critical hit!")
            src = f"{attacker.name}'s {name}" if attacker else name
            game.apply_direct_damage(target, damage, attacker=attacker, damage_source=src)
        else:
            game.log_message(f"This message should never appear. If you see it, please contact C4!")
            
    elif name == "Pomeg Berry":
        target.gain_evs({"HP": 10}, game=game)
        game.log_message(f"{target.name}'s HP was trained!")
        
    elif name == "Kelpsy Berry":
        target.gain_evs({"Attack": 10}, game=game)
        game.log_message(f"{target.name}'s Attack was trained!")
        
    elif name == "Qualot Berry":
        target.gain_evs({"Defense": 10}, game=game)
        game.log_message(f"{target.name}'s Defense was trained!")
        
    elif name == "Hondew Berry":
        target.gain_evs({"Special_Attack": 10}, game=game)
        game.log_message(f"{target.name}'s Special Attack was trained!")
        
    elif name == "Grepa Berry":
        target.gain_evs({"Special_Defense": 10}, game=game)
        game.log_message(f"{target.name}'s Special Defense was trained!")
        
    elif name == "Tamato Berry":
        target.gain_evs({"Speed": 10}, game=game)
        game.log_message(f"{target.name}'s Speed was trained!")
        
    elif name == "Liechi Berry":
        target.apply_stat_modifier("Attack", 2, game)
        
    elif name == "Ganlon Berry":
        target.apply_stat_modifier("Defense", 2, game)
        
    elif name == "Petaya Berry":
        target.apply_stat_modifier("Special_Attack", 2, game)
        
    elif name == "Apicot Berry":
        target.apply_stat_modifier("Special_Defense", 2, game)
        
    elif name == "Salac Berry":
        target.apply_stat_modifier("Speed", 2, game)
        
    elif name == "Micle Berry":
        target.apply_stat_modifier("Accuracy", 2, game)
        
    elif name == "Starf Berry":
        for stat in ["Attack", "Defense", "Special_Attack", "Special_Defense", "Speed", "Accuracy", "Evasion"]:
            target.apply_stat_modifier(stat, 1, game)
            
    elif name == "Hopo Berry":
        target.change_movement_speed(target.movement_speed_stage + 1, game)
        if hasattr(target, "current_pp"):
            target.current_pp = min(target.max_pp, target.current_pp + 30)
            game.log_message(f"{target.name}'s PP was restored.")
            
    elif name == "Plain Seed":
        game.log_message("Nothing happened.")
        
    elif name == "Quick Seed":
        target.change_movement_speed(target.movement_speed_stage + 1, game)
        
    elif name == "Sleep Seed":
        target.apply_status("Sleep", game)
        
    elif name == "Stun Seed":
        target.apply_status("Petrified", game)
        
    elif name == "Totter Seed":
        target.apply_status("Confused", game)
        
    elif name == "HP Up":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"HP": 10}, game=game)
        game.log_message(f"{target.name}'s HP was greatly trained!")
        
    elif name == "Protein":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"Attack": 20}, game=game)
        game.log_message(f"{target.name}'s Attack was greatly trained!")
        
    elif name == "Iron":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"Defense": 20}, game=game)
        game.log_message(f"{target.name}'s Defense was greatly trained!")
        
    elif name == "Calcium":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"Special_Attack": 20}, game=game)
        game.log_message(f"{target.name}'s Special Attack was greatly trained!")
        
    elif name == "Zinc":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"Special_Defense": 20}, game=game)
        game.log_message(f"{target.name}'s Special Defense was greatly trained!")
        
    elif name == "Carbos":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        target.gain_evs({"Speed": 20}, game=game)
        game.log_message(f"{target.name}'s Speed was greatly trained!")
        
    elif name == "PP Up":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        if hasattr(target, "max_pp"):
            target.max_pp += 10
            target.current_pp = min(target.max_pp, target.current_pp + 10)
            game.log_message(f"{target.name}'s maximum PP was boosted.")
        else:
            game.log_message("But nothing happened.")
            
    elif name == "PP Max":
        if hasattr(target, "current_belly"):
            target.current_belly = min(target.max_belly, target.current_belly + 10.0)
            game.log_message(f"{target.name}'s belly was filled slightly!")
        if hasattr(target, "max_pp"):
            target.max_pp += 30
            target.current_pp = min(target.max_pp, target.current_pp + 30)
            game.log_message(f"{target.name}'s maximum PP was greatly boosted.")
        else:
            game.log_message("But nothing happened.")

    elif name == "Hail Orb":
        game.weather = "Hail"
        game.log_message("It started to hail!")
        
    elif name == "Rainy Orb":
        game.weather = "Rain"
        game.log_message("It started to rain!")
        
    elif name == "Sandy Orb":
        game.weather = "Sandstorm"
        game.log_message("A sandstorm kicked up!")
        
    elif name == "Sunny Orb":
        game.weather = "Sunny"
        game.log_message("The sunlight got bright!")

    elif name == "Invisify Orb":
        for member in game.party:
            member.apply_status("Invisible", game, duration=10)
        game.log_message("The team turned invisible!")

    elif name == "Power Toss Orb":
        target.apply_status("Power Toss", game, duration=99999)
        game.log_message(f"{target.name}'s thrown attacks were powered up!")

    elif name == "Luminous Orb":
        game.floor_luminous = True
        game.log_message("The floor was illuminated!")

    elif name == "Mobile Orb":
        for member in game.party:
            member.apply_status("Mobile", game, duration=99999)
        game.log_message("The team can now travel anywhere!")
        
    elif name == "All Mach Orb":
        for member in game.party:
            member.change_movement_speed(member.movement_speed_stage + 1, game)

    elif name == "One Room Orb":
        from dungeon import WALL_CHAR, FLOOR_CHAR
        for y in range(game.floor.height):
            for x in range(game.floor.width):
                if x == 0 or x == game.floor.width - 1 or y == 0 or y == game.floor.height - 1:
                    continue
                if game.floor.grid[y][x] == WALL_CHAR:
                    game.floor.grid[y][x] = FLOOR_CHAR
        game.log_message("All walls crumbled into a single room!")

    elif name == "Petrify Orb":
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        enemy.apply_status("Petrified", game)
                else:
                    if max(abs(ex - px), abs(ey - py)) <= 5:
                        enemy.apply_status("Petrified", game)

    elif name == "Pierce Orb":
        target.apply_status("Pierce Throw", game)

    elif name == "Radar Orb":
        game.radar_active = True
        game.log_message("The locations of all enemies appeared on the map!")

    elif name == "Rebound Orb":
        target.apply_status("Rebound", game, duration=10)

    elif name == "Rollcall Orb":
        px, py = game.player_x, game.player_y
        adj_tiles = []
        for c_dy in (-1, 0, 1):
            for c_dx in (-1, 0, 1):
                if c_dx == 0 and c_dy == 0:
                    continue
                nx, ny = px + c_dx, py + c_dy
                if 0 <= nx < game.floor.width and 0 <= ny < game.floor.height:
                    if game.floor.grid[ny][nx] == "." and game.get_poke_at(nx, ny) is None:
                        adj_tiles.append((nx, ny))
        for member in game.party:
            if member is not game.player_pokemon and int(getattr(member, "current_hp", 0)) > 0:
                if adj_tiles:
                    tx, ty = adj_tiles.pop(0)
                    game.set_poke_pos(member, tx, ty)
                    game.log_message(f"{member.name} was warped to {target.name}'s side!")
                else:
                    game.ensure_valid_position(member)
                    game.log_message(f"{member.name} warped!")
                    
    elif name == "Slow Orb":
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        enemy.change_movement_speed(enemy.movement_speed_stage - 1, game)
                else:
                    if max(abs(ex - px), abs(ey - py)) <= 5:
                        enemy.change_movement_speed(enemy.movement_speed_stage - 1, game)
                        
    elif name == "Slumber Orb":
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        enemy.apply_status("Sleep", game)
                else:
                    if max(abs(ex - px), abs(ey - py)) <= 5:
                        enemy.apply_status("Sleep", game)
                        
    elif name == "Totter Orb":
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        enemy.apply_status("Confusion", game)
                else:
                    if max(abs(ex - px), abs(ey - py)) <= 5:
                        enemy.apply_status("Confusion", game)

    elif name == "Scanner Orb":
        game.scanner_active = True
        game.log_message("The locations of all items appeared on the map!")

    elif name == "Snatch Orb":
        import random
        target.apply_status("Snatch", game, duration=random.randint(10, 15))

    elif name == "Stairs Orb":
        game.stairs_revealed = True
        game.log_message("The location of the stairs appeared on the map!")

    elif name == "Transform Orb":
        import random
        possible_species: list[dict] = []
        if hasattr(game.floor, "spawn_table") and game.floor.spawn_table:
            for s_entry in game.floor.spawn_table:
                if isinstance(s_entry, dict) and "name" in s_entry:
                    possible_species.append(s_entry)
        if not possible_species:
            try:
                from pokemon_db import load_pokemon_database
                from data_utils import get_data_file_path
                db_path = get_data_file_path("pokemon.json")
                if os.path.exists(db_path):
                    possible_species = load_pokemon_database(db_path)
            except Exception:
                pass
        if not possible_species:
            possible_species = [target.species_data]

        chosen_species = random.choice(possible_species)
        orig_name = target.name
        if getattr(target, "transform_original_state", None) is None:
            target.transform_original_state = {
                "species_data": target.species_data,
                "nickname": target.nickname,
                "temp_types": list(target.temp_types) if getattr(target, "temp_types", None) is not None else None,
                "moves": [dict(m) for m in target.moves],
                "stat_modifiers": dict(target.stat_modifiers) if getattr(target, "stat_modifiers", None) is not None else {},
                "stats": dict(target.stats),
            }
        target.species_data = chosen_species
        target.learn_level_up_moves()
        target.recalculate_stats()
        game.log_message(f"{orig_name} transformed into {target.name}!")

    elif name == "Trawl Orb":
        import time
        from dungeon import FLOOR_CHAR
        px, py = game.player_x, game.player_y
        cand_tiles = []
        for r in range(1, 6):
            for c_dy in range(-r, r + 1):
                for c_dx in range(-r, r + 1):
                    if max(abs(c_dx), abs(c_dy)) == r:
                        nx, ny = px + c_dx, py + c_dy
                        if 0 <= nx < game.floor.width and 0 <= ny < game.floor.height:
                            if game.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) not in game.items_on_floor and game.get_poke_at(nx, ny) is None:
                                cand_tiles.append((nx, ny))

        item_coords = list(game.items_on_floor.keys())
        warped_count = 0
        for ox, oy in item_coords:
            if not cand_tiles:
                break
            tx, ty = cand_tiles.pop(0)
            item_data = game.items_on_floor.pop((ox, oy))

            steps = max(abs(tx - ox), abs(ty - oy), 1)
            currently_visible = game._compute_currently_visible()
            for s in range(1, steps + 1):
                anim_x = int(ox + (tx - ox) * s / steps)
                anim_y = int(oy + (ty - oy) * s / steps)
                if (anim_x, anim_y) in currently_visible:
                    game.flying_item_animation = {
                        "x": anim_x,
                        "y": anim_y,
                        "char": "*",
                        "color": "\033[93m"
                    }
                    game.render()
                    if not getattr(game, "suppress_animation_delay", False):
                        time.sleep(0.01)
            game.flying_item_animation = None
            game.items_on_floor[(tx, ty)] = item_data
            warped_count += 1

        game.log_message("Items on the floor were drawn close!")

    elif name == "Double-Edge Orb":
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        hit_enemies = []
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        hit_enemies.append(enemy)
                else:
                    if max(abs(ex - px), abs(ey - py)) <= 5:
                        hit_enemies.append(enemy)

        num_hit = len(hit_enemies)
        for enemy in hit_enemies:
            enemy.current_hp = 1.0
            ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
            game.flash_damages[(ex, ey)] = ("☼", "1 HP")

        if num_hit > 0:
            game.trigger_damage_flash()
            for _ in range(num_hit):
                target.current_hp = max(1.0, float(int(target.current_hp) // 2))
            game.log_message(f"{target.name} was hit with recoil!")
        else:
            game.log_message("But nothing happened.")

    elif name == "Warp Orb":
        from dungeon import FLOOR_CHAR
        from targeting import get_room_tiles_at
        room_tiles = get_room_tiles_at(game.floor, game.player_x, game.player_y)
        px, py = game.player_x, game.player_y
        v_radius = 100 if getattr(game, "floor_luminous", False) else 5

        valid_tiles = []
        for ry in range(game.floor.height):
            for rx in range(game.floor.width):
                if game.floor.grid[ry][rx] == FLOOR_CHAR and (rx, ry) != getattr(game, "stairs_position", None) and game.get_poke_at(rx, ry) is None:
                    valid_tiles.append((rx, ry))

        warped_any = False
        for enemy in list(game.spawned_pokemon):
            if int(getattr(enemy, "current_hp", 0)) > 0:
                ex, ey = enemy.x if hasattr(enemy, "x") else px, enemy.y if hasattr(enemy, "y") else py
                should_warp = False
                if room_tiles:
                    if (ex, ey) in room_tiles:
                        should_warp = True
                else:
                    if max(abs(ex - px), abs(ey - py)) <= v_radius:
                        should_warp = True
                if should_warp and valid_tiles:
                    import random
                    wx, wy = random.choice(valid_tiles)
                    valid_tiles.remove((wx, wy))
                    game.set_poke_pos(enemy, wx, wy)
                    warped_any = True

        if warped_any:
            game.log_message("Enemies in the room were warped away!")
        else:
            game.log_message("But nothing happened.")

    else:
        game.log_message("But nothing happened.")
