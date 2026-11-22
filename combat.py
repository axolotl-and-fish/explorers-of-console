"""
combat.py

Everything related to damage calculation goes here, basically.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import math
import random
from pokemon import Pokemon
from type_chart import get_effectiveness_multiplier
from abilities import (
    has_ability,
    get_effective_weather,
    get_effective_weight,
    get_effective_movement_speed_stage,
    has_sheer_force_boosted_effect,
    is_reckless_move,
    resolve_move_with_abilities,
)


def is_pokemon_grounded(pokemon: Pokemon, game=None, attacker=None) -> bool:
    """Returns True if the Pokémon is grounded (affected by terrain, etc)."""
    if (game and getattr(game, "gravity", False)) or pokemon.status_effects.get("Landed", 0) > 0:
        return True
    if pokemon.status_effects.get("Magnet Rise", 0) > 0 or pokemon.status_effects.get("Telekinesis", 0) > 0:
        return False
    if has_ability(pokemon, "Levitate", game=game, attacker=attacker) or getattr(pokemon, "is_floating", False):
        return False
    p_types = getattr(pokemon, "temp_types", None) or getattr(pokemon, "types", pokemon.species_data.get("types", []))
    if "Flying" in p_types:
        return False
    return True


def calculate_damage(attacker: Pokemon, defender: Pokemon, move: dict, game=None, is_multi_target: bool = False) -> tuple[int, bool, float]:
    """Calculates battle damage for a move used by attacker against defender.
    It's based on the main series damage calc, NOT Mystery Dungeon. (PMD's damage calc is not great for several reasons imo)

    Formula:
        base_damage = ((((2 * AttackerLevel) / 5) + 2) * MovePower * (AttackerAttack / DefenderDefense)) / 50
        total_damage = base_damage * crit_multiplier * type_multiplier * random_factor
        
    You may notice that the base damage formula is slightly different from the mainline games... this was done for balance reasons mainly, because damage amounts were too high in the early game :)
    The + 2 part of the mainline game's formula is mainly due to how type effectiveness works, but since that works differently in this game, it's better to just remove that term.

    Returns:
        tuple[int, bool, float]: (final_damage, is_critical, type_multiplier)
    """
    eff_weather = get_effective_weather(attacker, game) if game else None
    if eff_weather != "Clear" and has_ability(defender, "Cloud Nine", game=game, attacker=attacker):
        eff_weather = "Clear"
    if eff_weather == "Shadowy Aura":
        move = dict(move)
        move["type"] = "typeless"
    else:
        move = resolve_move_with_abilities(attacker, move, game=game)
        if eff_weather == "Harsh Sunlight" and move.get("type") == "Water":
            return 0, False, 0.0
        elif eff_weather == "Heavy Rain" and move.get("type") == "Fire":
            return 0, False, 0.0

    #Moves where damage = user's level
    if move.get("name") == "Night Shade":
        raw_dmg = float(attacker.level)
        m_type = move.get("type", "Ghost")
        if defender.status_effects.get("All Resist") or defender.status_effects.get(f"{m_type} Resist"):
            raw_dmg *= 0.5
        if is_multi_target:
            raw_dmg *= 0.75
        return max(1, int(raw_dmg)), False, 1.0

    #Dragon Rage: always deals exactly 40 damage
    if move.get("name") == "Dragon Rage":
        return 40, False, 1.0

    #Vacuum Cut: always deals exactly 20 damage
    if move.get("name") in ("Vacuum Cut", "Vacuum-Cut"):
        return 20, False, 1.0

    #Psywave: deals damage equal to a random number between 1 and user's level x 1.5
    if move.get("name") == "Psywave":
        max_dmg = max(1, int(attacker.level * 1.5))
        return random.randint(1, max_dmg), False, 1.0

    #Shell Side Arm: evaluate Physical vs Special damage and choose the higher one
    if move.get("name") == "Shell Side Arm" and not move.get("_evaluating_category"):
        phys_move = {**move, "category": "Physical", "_evaluating_category": True}
        spec_move = {**move, "category": "Special", "_evaluating_category": True}
        dmg_phys, _, _ = calculate_damage(attacker, defender, phys_move, game, is_multi_target)
        dmg_spec, _, _ = calculate_damage(attacker, defender, spec_move, game, is_multi_target)
        chosen_cat = "Physical" if dmg_phys > dmg_spec else "Special"
        move["category"] = chosen_cat

    category = move.get("category", "Status")
    power = move.get("power", 0)

    #Moves without power deal 0 damage
    if category == "Status" or power is None or power <= 0:
        return 0, False, 1.0

    #Rage Fist: +10 power per hit from damaging moves in last 10 turns (max 250)
    if move.get("name") == "Rage Fist":
        num_hits = 0
        if game and hasattr(attacker, "damage_hit_turns"):
            curr_turn = getattr(game, "turn_number", 0)
            num_hits = sum(1 for t in attacker.damage_hit_turns if curr_turn - t <= 10)
        power = min(250, (move.get("power") or 50) + 10 * num_hits)

    #Stomping Tantrum: 2x power if last move missed or failed on last turn
    if move.get("name") == "Stomping Tantrum":
        if game and getattr(attacker, "last_move_failed_turn", None) == getattr(game, "turn_number", 0) - 1:
            power = power * 2

    #Retaliate: 2x power if teammate defeated during previous turn
    if move.get("name") == "Retaliate":
        if game and getattr(attacker, "last_teammate_fainted_turn", None) in (getattr(game, "turn_number", 0) - 1, getattr(game, "turn_number", 0)):
            power = power * 2

    #Revenge: 2x power if target damaged user in previous turn
    if move.get("name") == "Revenge":
        if game and getattr(attacker, "damaged_by_pokemons", {}).get(defender) == getattr(game, "turn_number", 0) - 1:
            power = power * 2

    #Hex: 2x power if target has status condition or confusion
    if move.get("name") == "Hex":
        has_status = any(
            (isinstance(v, bool) and v) or (isinstance(v, (int, float)) and v > 0)
            for k, v in defender.status_effects.items()
            if k in ("Poison", "Toxic", "Burn", "Paralysis", "Sleep", "Resting", "Confusion")
        )
        if has_status:
            power = power * 2

    #Smack Down: 1.5x power if target is flying / airborne
    if move.get("name") == "Smack Down":
        def_types = getattr(defender, "types", defender.species_data.get("types", []))
        is_airborne_charging = bool(
            defender.charging_move
            and defender.charging_move.get("move", {}).get("name") in ("Fly", "Bounce")
        )
        is_flying = bool(
            "Flying" in def_types
            or defender.status_effects.get("Magnet Rise", 0) > 0
            or is_airborne_charging
        )
        if is_flying:
            power = int(power * 1.5)

    #Brine: 2x power if target HP < 50%
    if move.get("name") == "Brine":
        max_hp = max(1.0, float(defender.stats.get("HP", 1.0)))
        if defender.current_hp / max_hp < 0.5:
            power = power * 2

    #Charge: 2x power for Electric damaging moves while Charging
    if move.get("type") == "Electric" and category in ("Physical", "Special"):
        if attacker.status_effects.get("Charging", 0) > 0:
            power = power * 2

    #Venoshock: 2x power against poisoned targets
    if move.get("name") == "Venoshock":
        if defender.status_effects.get("Poison") or defender.status_effects.get("Toxic"):
            power = power * 2

    #Assurance: 2x power against targets with <50% HP
    if move.get("name") == "Assurance":
        if defender.current_hp / max(1.0, float(defender.stats.get("HP", 1.0))) <= 0.5:
            power = power * 2

    #Reversal & Flail power scale based on user's remaining HP.
    if move.get("name") in ("Reversal", "Flail"):
        max_hp = float(max(1.0, float(attacker.stats.get("HP", 1.0))))
        curr_hp = float(max(1.0, min(max_hp, attacker.current_hp)))
        if max_hp <= 1.0 or curr_hp <= 1.0:
            power = 200
        elif curr_hp >= max_hp:
            power = 5
        else:
            x = (max_hp - curr_hp) / (max_hp - 1.0)
            x = max(0.0, min(1.0, x))
            power = int(5 + 195 * (x ** 2))
            power = max(5, min(200, power))

    #Low Kick power scale based on target weight (no fancy formulae here, just simple if/else checks)
    if move.get("name") == "Low Kick":
        weight = get_effective_weight(defender, game)
        if weight < 10.0:
            power = 20
        elif weight < 25.0:
            power = 40
        elif weight < 50.0:
            power = 60
        elif weight < 100.0:
            power = 80
        elif weight <= 200.0:
            power = 100
        else:
            power = 120

    #Electro Ball power calculation. Faster attacker = higher power
    if move.get("name") == "Electro Ball":
        ignore_def_stages = has_ability(attacker, "Unaware", game=game)
        u_speed = attacker.get_modified_stat("Speed", game)
        t_speed = defender.get_modified_stat("Speed", game, attacker=attacker, ignore_stages=ignore_def_stages)
        
        u_stage = get_effective_movement_speed_stage(attacker, game)
        u_mult = 0.5 if u_stage == -1 else float(1 + u_stage)
        
        t_stage = get_effective_movement_speed_stage(defender, game)
        t_mult = 0.5 if t_stage == -1 else float(1 + t_stage)
        
        u_speed_eff = u_speed * u_mult
        t_speed_eff = t_speed * t_mult
        
        ratio = u_speed_eff / max(1.0, float(t_speed_eff))
        power = min(250, int(40 * ratio))
        power = max(1, power)

    #Gyro Ball power calculation. Slower attacker = higher power (opposite of Electro Ball)
    if move.get("name") == "Gyro Ball":
        ignore_def_stages = has_ability(attacker, "Unaware", game=game)
        u_speed = attacker.get_modified_stat("Speed", game)
        t_speed = defender.get_modified_stat("Speed", game, attacker=attacker, ignore_stages=ignore_def_stages)
        
        u_stage = get_effective_movement_speed_stage(attacker, game)
        u_mult = 0.5 if u_stage == -1 else float(1 + u_stage)
        
        t_stage = get_effective_movement_speed_stage(defender, game)
        t_mult = 0.5 if t_stage == -1 else float(1 + t_stage)
        
        u_speed_eff = u_speed * u_mult
        t_speed_eff = t_speed * t_mult
        
        ratio = t_speed_eff / max(1.0, float(u_speed_eff))
        power = min(250, int(40 * ratio))
        power = max(1, power)

    #Heavy Slam power calculation. Heavier attacker = higher power
    if move.get("name") == "Heavy Slam":
        u_weight = get_effective_weight(attacker, game)
        t_weight = get_effective_weight(defender, game)
        ratio = u_weight / t_weight
        power = int(80 * math.sqrt(ratio))
        power = max(2, min(250, power))

    #Knock Off: 1.5x power if defender holds an item
    if move.get("name") == "Knock Off" and getattr(defender, "held_item", None) is not None:
        power = float(power) * 1.5

    #Technician: moves with < 80 Power get +50% Power up to 80
    if float(power) < 80.0 and has_ability(attacker, "Technician", game=game):
        power = min(80.0, float(power) * 1.5)

    #Sheer Force: +30% power on eligible damaging moves
    if has_ability(attacker, "Sheer Force", game=game) and has_sheer_force_boosted_effect(move):
        power = float(power) * 1.3

    #Tough Claws: +30% power for contact moves
    if move.get("contact") and has_ability(attacker, "Tough Claws", game=game):
        power = float(power) * 1.3

    #Iron Fist: +20% power for punching moves
    if move.get("punching") and has_ability(attacker, "Iron Fist", game=game):
        power = float(power) * 1.2

    #Reckless: +20% power for recoil/crash moves (not Struggle)
    if is_reckless_move(move) and has_ability(attacker, "Reckless", game=game):
        power = float(power) * 1.2

    #Analytic: +50% power when user has negative movement speed stage
    if has_ability(attacker, "Analytic", game=game) and get_effective_movement_speed_stage(attacker, game) < 0:
        power = float(power) * 1.5

    #Sand Force: +30% power for Rock/Ground/Steel moves in Sandstorm
    if eff_weather == "Sandstorm" and move.get("type") in ("Rock", "Ground", "Steel") and has_ability(attacker, "Sand Force", game=game):
        power = float(power) * 1.3

    #Pinch type boosters (Overgrow, Blaze, Torrent, Swarm) at <= 20% max HP
    pinch_map = {
        "Overgrow": "Grass",
        "Blaze": "Fire",
        "Torrent": "Water",
        "Swarm": "Bug",
    }
    max_atk_hp = max(1.0, float(attacker.stats.get("HP", 1.0)))
    if float(attacker.current_hp) <= 0.20 * max_atk_hp:
        m_t = move.get("type")
        for ab_name, ab_type in pinch_map.items():
            if m_t == ab_type and has_ability(attacker, ab_name, game=game):
                power = float(power) * 1.5

    #Flash Fire: +50% Fire power when charged
    if getattr(attacker, "flash_fire_boosted", False) and move.get("type") == "Fire" and has_ability(attacker, "Flash Fire", game=game):
        power = float(power) * 1.5

    #Same-Type Attack Bonus (STAB)
    attacker_types = getattr(attacker, "types", attacker.species_data.get("types", []))
    stab_mult = 2.0 if has_ability(attacker, "Adaptability", game=game) else 1.5
    if eff_weather != "Shadowy Aura":
        #Unique/multi-type moves
        if move.get("name") == "Muddy Water":
            if any(t in attacker_types for t in ["Water", "Ground"]):
                power = power * stab_mult
        elif move.get("name") == "Tri Attack":
            if any(t in attacker_types for t in ["Fire", "Ice", "Electric"]):
                power = power * stab_mult
        elif move.get("type") in attacker_types:
            power = power * stab_mult

    #Boosts & penalties from weather
    if eff_weather:
        m_type = move.get("type")
        if eff_weather == "Sunny":
            if m_type == "Fire":
                power = power * 1.5
            elif m_type == "Water":
                power = power * 0.5
        elif eff_weather == "Rain":
            if m_type == "Water":
                power = power * 1.5
            elif m_type == "Fire":
                power = power * 0.5
        elif eff_weather == "Cloudy":
            if m_type == "Normal":
                power = power * 1.33
        elif eff_weather in ("Snow", "Blizzard"):
            if m_type == "Ice":
                power = power * 1.5
        elif eff_weather == "Thunderstorm":
            if m_type in ("Water", "Electric"):
                power = power * 1.5
            elif m_type == "Fire":
                power = power * 0.5
        elif eff_weather == "Harsh Sunlight":
            if m_type == "Fire":
                power = power * 2.0
            elif m_type == "Water":
                return 0, False, 0.0
        elif eff_weather == "Heavy Rain":
            if m_type == "Water":
                power = power * 2.0
            elif m_type == "Fire":
                return 0, False, 0.0
        elif eff_weather == "Grassy Terrain":
            if m_type == "Ground":
                power = power * 0.5
            elif m_type == "Grass":
                if is_pokemon_grounded(attacker, game):
                    power = power * 1.3
        elif eff_weather == "Electric Terrain":
            if m_type == "Electric":
                if is_pokemon_grounded(attacker, game):
                    power = power * 1.3

    #Determine which stats to use
    ignore_def_stages = has_ability(attacker, "Unaware", game=game)
    if category == "Physical":
        atk = attacker.get_modified_stat("Attack", game)
        def_stat = defender.get_modified_stat("Defense", game, attacker=attacker, ignore_stages=ignore_def_stages)
    elif category == "Special":
        atk = attacker.get_modified_stat("Special_Attack", game)
        if move.get("name") == "Psyshock" or move.get("name") == "Psystrike":
            def_stat = defender.get_modified_stat("Defense", game, attacker=attacker, ignore_stages=ignore_def_stages)
        else:
            def_stat = defender.get_modified_stat("Special_Defense", game, attacker=attacker, ignore_stages=ignore_def_stages)

    #Failsafe to prevent DIV/0 or negative damage values
    atk = max(1, atk)
    def_stat = max(1, def_stat)
    power = max(0, power)

    #Calculate base damage
    if getattr(attacker, "practice_swinger_active", False):
        from iq_skills import get_iq_skill_value
        power = float(power) * float(get_iq_skill_value(attacker, "Practice Swinger", game=game, default=1.0))

    base_damage = ((((2 * attacker.level) / 5) + 2) * power * (atk / def_stat)) / 50

    from iq_skills import get_iq_skill_value, has_iq_skill

    #Calculate type effectiveness multiplier
    target_types = list(getattr(defender, "types", defender.species_data.get("types", ["typeless"])))
    is_grounded = is_pokemon_grounded(defender, game, attacker=attacker)
    if is_grounded:
        target_types = [t for t in target_types if t != "Flying"]
        if not target_types:
            target_types = ["typeless"]
    if has_ability(attacker, "Scrappy", game=game) and move.get("type") in ("Normal", "Fighting"):
        target_types = [t for t in target_types if t != "Ghost"]
        if not target_types:
            target_types = ["typeless"]
    if eff_weather == "Shadowy Aura":
        move_type_key = "typeless"
    else:
        move_type_key = str(move.get("name")) if move.get("name") in ("Muddy Water", "Freeze-Dry") else str(move.get("type", "typeless"))
    type_multiplier = get_effectiveness_multiplier(move_type_key, target_types)
    if move.get("type") == "Ground" and not is_grounded and (defender.status_effects.get("Magnet Rise", 0) > 0 or has_ability(defender, "Levitate", game=game, attacker=attacker)):
        type_multiplier = 0.0

    #Erratic Player modifies base SE, NVE, and little-effect multipliers
    if has_iq_skill(attacker, "Erratic Player", game=game) and type_multiplier > 0.0:
        if type_multiplier > 1.0:
            type_multiplier = round(1.0 + (type_multiplier - 1.0) * 2.0, 4)
        elif type_multiplier <= 0.25:
            type_multiplier = 0.10
        elif type_multiplier < 1.0:
            #Normal -25% tier -> -40% tier
            type_multiplier = max(0.10, round(1.0 - (1.0 - type_multiplier) * 1.6, 4))

    if type_multiplier > 0.0:
        if move.get("type") in ("Fire", "Ice") and has_ability(defender, "Thick Fat", game=game, attacker=attacker):
            type_multiplier = max(0.25, round(type_multiplier - 0.25, 4))
        if move.get("type") == "Fire" and has_ability(defender, "Dry Skin", game=game, attacker=attacker):
            type_multiplier = min(1.75, round(type_multiplier + 0.25, 4))

    if 0.0 < type_multiplier < 1.0 and has_ability(attacker, "Tinted Lens", game=game):
        if type_multiplier <= 0.25:
            type_multiplier = 0.5
        elif type_multiplier <= 0.50:
            type_multiplier = 0.9
        else:
            type_multiplier = 0.95

    if type_multiplier > 1.0 and has_ability(defender, "Filter", game=game, attacker=attacker):
        tiers = round((type_multiplier - 1.0) / 0.25)
        type_multiplier = round(1.0 + 0.10 * tiers, 4)

    #Calculate critical hit chance: 12.5% * (attacker speed / defender speed)
    atk_speed = max(1, attacker.get_modified_stat("Speed", game))
    def_speed = max(1, defender.get_modified_stat("Speed", game, attacker=attacker, ignore_stages=ignore_def_stages))
    has_crit_block = has_ability(defender, "Battle Armor", game=game, attacker=attacker) or has_iq_skill(defender, "Critical Dodger", game=game)
    crit_power = 2.0 if has_ability(attacker, "Sniper", game=game) else 1.5

    if move.get("_evaluating_category") or has_crit_block:
        is_critical = False
        crit_multiplier = 1.0
    elif move.get("always_crit") or move.get("guaranteed_crit") or attacker.status_effects.get("Laser Focus") or defender.status_effects.get("Curse"):
        is_critical = True
        crit_multiplier = crit_power
    else:
        crit_chance = 0.125 * (atk_speed / def_speed)
        crit_chance += float(get_iq_skill_value(attacker, "Sharpshooter", game=game, default=0.0))
        if type_multiplier > 1.0:
            crit_chance += float(get_iq_skill_value(attacker, "Type-Advantage Master", game=game, default=0.0))
        if int(getattr(attacker, "iq", 0)) >= 100:
            crit_chance *= 2
        if has_ability(attacker, "Super Luck", game=game):
            crit_chance *= 2
        if move.get("high_crit_ratio") or move.get("name") == "Razor Leaf":
            crit_chance *= 2
        if attacker.status_effects.get("Focus Energy", 0) > 0:
            crit_chance *= 4
        is_critical = random.random() < crit_chance
        crit_multiplier = crit_power if is_critical else 1.0

    #Apply all multipliers
    total_damage = base_damage * crit_multiplier * type_multiplier

    #Multi-target damage penalty: -25% damage if hitting multiple targets
    if is_multi_target:
        total_damage = total_damage * 0.75

    bypass_screens = has_ability(attacker, "Infiltrator", game=game)

    #Light Screen halves Special damage
    if not bypass_screens and category == "Special" and defender.status_effects.get("Light Screen", 0) > 0 and move.get("name") != "Brick Break":
        total_damage = total_damage * 0.5

    #Reflect halves Physical damage
    if not bypass_screens and category == "Physical" and defender.status_effects.get("Reflect", 0) > 0 and move.get("name") != "Brick Break":
        total_damage = total_damage * 0.5

    #Skull Bash: user takes half damage from Physical moves while charging
    if category == "Physical" and defender.charging_move and defender.charging_move.get("move", {}).get("name") == "Skull Bash":
        total_damage = total_damage * 0.5

    #2x damage against Digging targets for Earthquake & Bulldoze
    if defender.status_effects.get("Digging", 0) > 0 and move.get("name") in ("Earthquake", "Bulldoze"):
        total_damage = total_damage * 2.0

    #2x damage against Diving targets for Surf & Whirlpool
    if defender.status_effects.get("Diving", 0) > 0 and move.get("name") in ("Surf", "Whirlpool"):
        total_damage = total_damage * 2.0

    #2x damage against Minimized targets for specific moves
    minimized_double_moves = ("Body Slam", "Stomp", "Astonish", "Extrasensory", "Dragon Rush", "Heavy Slam")
    if defender.status_effects.get("Minimized") and move.get("name") in minimized_double_moves:
        total_damage = total_damage * 2.0

    #Aurora Veil reduces damage taken by 1/3
    if not bypass_screens and defender.status_effects.get("Aurora Veil", 0) > 0 and move.get("name") not in ("Brick Break", "Raging Bull"):
        total_damage = total_damage * (2.0 / 3.0)

    #Multiscale halves damage taken when at full HP
    if float(defender.current_hp) >= float(defender.stats.get("HP", 1)) and has_ability(defender, "Multiscale", game=game, attacker=attacker):
        total_damage = total_damage * 0.5

    #Rivalry modifies damage based on gender
    atk_gender = getattr(attacker, "gender", None)
    def_gender = getattr(defender, "gender", None)
    if atk_gender in ("Male", "Female") and def_gender in ("Male", "Female") and has_ability(attacker, "Rivalry", game=game):
        if atk_gender == def_gender:
            total_damage = total_damage * 0.75
        else:
            total_damage = total_damage * 1.25

    #Misty Terrain halves Dragon-type move damage against grounded Pokémon
    if eff_weather == "Misty Terrain" and move.get("type") == "Dragon":
        if is_pokemon_grounded(defender, game, attacker=attacker):
            total_damage = total_damage * 0.5

    #Type resistance berries (Occa, Passho, Wacan, etc.) halve damage from matching move type or All types
    m_type = move.get("type", "Normal")
    if defender.status_effects.get("All Resist") or defender.status_effects.get(f"{m_type} Resist"):
        total_damage = total_damage * 0.5

    if move.get("_evaluating_category"):
        final_damage = math.ceil(total_damage)
    else:
        #Apply damage variance (85%-100%) and round up
        final_damage = math.ceil(total_damage * random.uniform(0.85, 1.0))

    #Whew, all done!
    return final_damage, is_critical, type_multiplier
