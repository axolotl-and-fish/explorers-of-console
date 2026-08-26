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
    #Moves where damage = user's level
    if move.get("name") == "Night Shade":
        raw_dmg = float(attacker.level)
        m_type = move.get("type", "Ghost")
        if defender.status_effects.get("All Resist") or defender.status_effects.get(f"{m_type} Resist"):
            raw_dmg *= 0.5
        if is_multi_target:
            raw_dmg *= 0.75
        return max(1, int(raw_dmg)), False, 1.0

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
    #TODO: May need to adjust this formula because this move might be too damaging too quickly lmao
    if move.get("name") in ("Reversal", "Flail"):
        max_hp = float(max(1.0, float(attacker.stats.get("HP", 1.0))))
        curr_hp = float(max(1.0, min(max_hp, attacker.current_hp)))
        if max_hp <= 1.0 or curr_hp <= 1.0:
            power = 250
        elif curr_hp >= max_hp:
            power = 5
        else:
            x = (max_hp - curr_hp) / (max_hp - 1.0)
            x = max(0.0, min(1.0, x))
            power = int(5 + 245 * (x ** 2))
            power = max(5, min(250, power))

    #Low Kick power scale based on target weight (no fancy formulae here, just simple if/else checks)
    if move.get("name") == "Low Kick":
        weight = float(defender.species_data.get("weight", 10.0))
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
        u_speed = attacker.get_modified_stat("Speed", game)
        t_speed = defender.get_modified_stat("Speed", game)
        
        u_stage = attacker.movement_speed_stage
        u_mult = 0.5 if u_stage == -1 else float(1 + u_stage)
        
        t_stage = defender.movement_speed_stage
        t_mult = 0.5 if t_stage == -1 else float(1 + t_stage)
        
        u_speed_eff = u_speed * u_mult
        t_speed_eff = t_speed * t_mult
        
        ratio = u_speed_eff / max(1.0, float(t_speed_eff))
        power = min(250, int(40 * ratio))
        power = max(1, power)

    #Gyro Ball power calculation. Slower attacker = higher power (opposite of Electro Ball)
    if move.get("name") == "Gyro Ball":
        u_speed = attacker.get_modified_stat("Speed", game)
        t_speed = defender.get_modified_stat("Speed", game)
        
        u_stage = attacker.movement_speed_stage
        u_mult = 0.5 if u_stage == -1 else float(1 + u_stage)
        
        t_stage = defender.movement_speed_stage
        t_mult = 0.5 if t_stage == -1 else float(1 + t_stage)
        
        u_speed_eff = u_speed * u_mult
        t_speed_eff = t_speed * t_mult
        
        ratio = t_speed_eff / max(1.0, float(u_speed_eff))
        power = min(250, int(40 * ratio))
        power = max(1, power)

    #Heavy Slam power calculation. Heavier attacker = higher power
    if move.get("name") == "Heavy Slam":
        u_weight = max(0.1, float(attacker.species_data.get("weight", 10.0)))
        t_weight = max(0.1, float(defender.species_data.get("weight", 10.0)))
        ratio = u_weight / t_weight
        power = int(80 * math.sqrt(ratio))
        power = max(2, min(250, power))

    #Same-Type Attack Bonus (STAB)
    attacker_types = getattr(attacker, "types", attacker.species_data.get("types", []))
    #Unique/multi-type moves
    if move.get("name") == "Muddy Water":
        if any(t in attacker_types for t in ["Water", "Ground"]):
            power = power * 1.5
    elif move.get("name") == "Tri Attack":
        if any(t in attacker_types for t in ["Fire", "Ice", "Electric"]):
            power = power * 1.5
    elif move.get("type") in attacker_types:
        power = power * 1.5

    #Boosts & penalties from weather
    if game and hasattr(game, "weather"):
        m_type = move.get("type")
        if game.weather == "Sunny":
            if m_type == "Fire":
                power = power * 1.5
            elif m_type == "Water":
                power = power * 0.5
        elif game.weather == "Rain":
            if m_type == "Water":
                power = power * 1.5
            elif m_type == "Fire":
                power = power * 0.5
        elif game.weather == "Grassy Terrain":
            if m_type == "Ground":
                power = power * 0.5
            elif m_type == "Grass":
                if "Flying" not in attacker.species_data.get("types", []):
                    power = power * 1.3
        elif game.weather == "Electric Terrain":
            if m_type == "Electric":
                if "Flying" not in attacker.species_data.get("types", []):
                    power = power * 1.3

    #Determine which stats to use
    if category == "Physical":
        atk = attacker.get_modified_stat("Attack", game)
        def_stat = defender.get_modified_stat("Defense", game)
    elif category == "Special":
        atk = attacker.get_modified_stat("Special_Attack", game)
        if move.get("name") == "Psyshock" or move.get("name") == "Psystrike":
            def_stat = defender.get_modified_stat("Defense", game)
        else:
            def_stat = defender.get_modified_stat("Special_Defense", game)

    #Failsafe to prevent DIV/0 or negative damage values
    atk = max(1, atk)
    def_stat = max(1, def_stat)
    power = max(0, power)

    #Calculate base damage
    base_damage = ((((2 * attacker.level) / 5) + 2) * power * (atk / def_stat)) / 50

    #Calculate critical hit chance: 12.5% * (attacker speed / defender speed)
    atk_speed = max(1, attacker.get_modified_stat("Speed", game))
    def_speed = max(1, defender.get_modified_stat("Speed", game))
    
    if move.get("always_crit") or attacker.status_effects.get("Laser Focus") or defender.status_effects.get("Curse"):
        is_critical = True
    else:
        crit_chance = 0.125 * (atk_speed / def_speed)
        if move.get("high_crit_ratio") or move.get("name") == "Razor Leaf":
            crit_chance *= 2
        if attacker.status_effects.get("Focus Energy", 0) > 0:
            crit_chance *= 4
        is_critical = random.random() < crit_chance

    crit_multiplier = 1.5 if is_critical else 1.0

    #Calculate type effectiveness multiplier
    target_types = getattr(defender, "types", defender.species_data.get("types", ["typeless"]))
    is_grounded = bool((game and getattr(game, "gravity", False)) or defender.status_effects.get("Landed", 0) > 0)
    if is_grounded:
        target_types = [t for t in target_types if t != "Flying"]
        if not target_types:
            target_types = ["typeless"]
    move_type_key = str(move.get("name")) if move.get("name") in ("Muddy Water", "Freeze-Dry") else str(move.get("type", "typeless"))
    type_multiplier = get_effectiveness_multiplier(move_type_key, target_types)
    if move.get("type") == "Ground" and defender.status_effects.get("Magnet Rise", 0) > 0 and not is_grounded:
        type_multiplier = 0.0

    #Apply all multipliers
    total_damage = base_damage * crit_multiplier * type_multiplier

    #Multi-target damage penalty: -25% damage if hitting multiple targets
    if is_multi_target:
        total_damage = total_damage * 0.75

    #Light Screen halves Special damage
    if category == "Special" and defender.status_effects.get("Light Screen", 0) > 0 and move.get("name") != "Brick Break":
        total_damage = total_damage * 0.5

    #Reflect halves Physical damage
    if category == "Physical" and defender.status_effects.get("Reflect", 0) > 0 and move.get("name") != "Brick Break":
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

    #Type resistance berries (Occa, Passho, Wacan, etc.) halve damage from matching move type or All types
    m_type = move.get("type", "Normal")
    if defender.status_effects.get("All Resist") or defender.status_effects.get(f"{m_type} Resist"):
        total_damage = total_damage * 0.5

    #Apply damage variance (85%-100%) and round up
    final_damage = math.ceil(total_damage * random.uniform(0.85, 1.0))

    #Whew, all done!
    return final_damage, is_critical, type_multiplier
