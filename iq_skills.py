"""
iq_skills.py

This script handles Pokémon IQ skills and their descriptions.
"""

from __future__ import annotations
import math
import random


IQ_THRESHOLDS: tuple[int, ...] = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
MAX_IQ_SKILLS = 10 #For future use

#IQ skills are defined here
IQ_SKILLS_DB: dict[str, dict] = {
    "Efficiency Expert": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": True,
        "team_only": False,
        "conflicts": {"Weak-Type Picker", "EXP Go Getter"},
        "description": "Ally skill: Prioritizes targeting the foe with the lowest HP.",
    },
    "Nontraitor": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "Attacks used by this Pokemon won't harm its allies.",
    },
    "Type-Advantage Master": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Super-effective attacks are a little more likely to be a critical hit.",
            2: "Super-effective attacks are more likely to be a critical hit.",
            3: "Super-effective attacks are much more likely to be a critical hit.",
        },
        "values": (0.10, 0.20, 0.30),
    },
    "Weak-Type Picker": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": True,
        "team_only": False,
        "conflicts": {"Efficiency Expert", "EXP Go Getter"},
        "description": "Ally skill: Prioritizes targets and moves that exploit type weaknesses.",
    },
    "Nonsleeper": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Prevents sleep.",
    },
    "EXP Go Getter": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": True,
        "team_only": False,
        "conflicts": {"Efficiency Expert", "Weak-Type Picker"},
        "description": "Ally skill: Prioritizes targeting the foe worth the most EXP.",
    },
    "Energy Saver": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Belly depletes 20% slower.",
            2: "Belly depletes 35% slower.",
            3: "Belly depletes 50% slower.",
        },
        "values": (0.80, 0.65, 0.50),
    },
    "Absolute Mover": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Allows walking through walls.",
    },
    "Cheerleader": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Boosts adjacent allies' Attack and Sp. Attack by 1 level.",
            2: "Boosts adjacent allies' Attack and Sp. Attack by 2 levels.",
            3: "Boosts adjacent allies' Attack and Sp. Attack by 3 levels.",
        },
        "values": (1, 2, 3),
    },
    "Acute Sniffer": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "Displays number of items on each floor entered.",
    },
    "PP Saver": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Reduces move PP cost by 1.",
            2: "Reduces move PP cost by 2.",
            3: "Reduces move PP cost by 3.",
        },
        "values": (1, 2, 3),
    },
    "Bodyguard": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Takes attacks for allies when their HP is low.",
    },
    "Self-Curer": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Negative status conditions heal faster.",
    },
    "Brick Tough": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Raises max HP by +10%.",
            2: "Raises max HP by +20%.",
            3: "Raises max HP by +30%.",
        },
        "values": (1.10, 1.20, 1.30),
    },
    "Power Pitcher": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Increases damage dealt by thrown items by +20%.",
            2: "Increases damage dealt by thrown items by +35%.",
            3: "Increases damage dealt by thrown items by +50%.",
        },
        "values": (1.20, 1.35, 1.50),
    },
    "Survivalist": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "+20% Belly from food, Grimy Food is less likely to have negative effects.",
            2: "+40% Belly from food, Grimy Food is much less likely to have negative effects.",
            3: "+60% Belly from food, Grimy Food will almost never have a negative effect.",
        },
        "values": ((1.20, 0.50), (1.40, 0.30), (1.60, 0.10)),
    },
    "Coin Watcher": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Gain +15% more Poké when picking up money items.",
            2: "Gain +25% more Poké when picking up money items.",
            3: "Gain +35% more Poké when picking up money items.",
        },
        "values": (1.15, 1.25, 1.35),
    },
    "Wise Healer": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Increases HP restored by items and healing moves by +10%.",
            2: "Increases HP restored by items and healing moves by +20%.",
            3: "Increases HP restored by items and healing moves by +30%.",
        },
        "values": (1.10, 1.20, 1.30),
    },
    "Concentrator": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "+1 Accuracy stage, -1 Evasion stage when moving to a new floor.",
            2: "+2 Accuracy stages, -2 Evasion stages when moving to a new floor.",
            3: "+3 Accuracy stages, -3 Accuracy stages when moving to a new floor.",
        },
        "values": (1, 2, 3),
    },
    "Deep Breather": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Restores 4 PP on entering a new floor.",
            2: "Restores 7 PP on entering a new floor.",
            3: "Restores 10 PP on entering a new floor.",
        },
        "values": (4, 7, 10),
    },
    "Practice Swinger": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Missing a damaging move boosts the next move's power by +20%.",
            2: "Missing a damaging move boosts the next move's power by +35%.",
            3: "Missing a damaging move boosts the next move's power by +50%.",
        },
        "values": (1.20, 1.35, 1.50),
    },
    "Aggressor": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": {"Defender"},
        "tiers": {
            1: "+1 Attack & Sp. Attack stages, -1 Defense & Sp. Defense stages when moving to a new floor.",
            2: "+2 Attack & Sp. Attack stages, -2 Defense & Sp. Defense stages when moving to a new floor.",
            3: "+3 Attack & Sp. Attack stages, -3 Defense & Sp. Defense stages when moving to a new floor.",
        },
        "values": (1, 2, 3),
    },
    "Defender": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": {"Aggressor"},
        "tiers": {
            1: "+1 Defense & Sp. Defense stages, -1 Attack & Sp. Attack stages when moving to a new floor.",
            2: "+2 Defense & Sp. Defense stages, -2 Attack & Sp. Attack stages when moving to a new floor.",
            3: "+3 Defense & Sp. Defense stages, -3 Attack & Sp. Attack stages when moving to a new floor.",
        },
        "values": (1, 2, 3),
    },
    "Sharpshooter": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Raises critical hit rate a little.",
            2: "Raises critical hit rate.",
            3: "Raises critical hit rate a lot.",
        },
        "values": (0.025, 0.050, 0.075),
    },
    "Hit-and-Runner": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "20% chance to avoid counterattacks.",
            2: "35% chance to avoid counterattacks.",
            3: "50% chance to avoid counterattacks.",
        },
        "values": (0.20, 0.35, 0.50),
    },
    "Counter Basher": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "15% chance to counter adjacent Physical damage.",
            2: "25% chance to counter adjacent Physical damage.",
            3: "35% chance to counter adjacent Physical damage.",
        },
        "values": (0.15, 0.25, 0.35),
    },
    "Quick Healer": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Increases natural HP regeneration by +50%.",
            2: "Increases natural HP regeneration by +100%.",
            3: "Increases natural HP regeneration by +150%.",
        },
        "values": (1.50, 2.00, 2.50),
    },
    "Multitalent": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Raises maximum PP by +10.",
            2: "Raises maximum PP by +20.",
            3: "Raises maximum PP by +30.",
        },
        "values": (10, 20, 30),
    },
    "EXP Elite": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Grants a +10% bonus to EXP.",
            2: "Grants a +20% bonus to EXP.",
            3: "Grants a +30% bonus to EXP.",
        },
        "values": (1.10, 1.20, 1.30),
    },
    "Erratic Player": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Raises power of super effective moves but lowers power of not very effective moves.",
    },
    "Clutch Player": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "incompatible_abilities": {"No Guard"},
        "tiers": {
            1: "Boosts Evasion by +1 stage when HP is low.",
            2: "Boosts Evasion by +2 stages when HP is low.",
            3: "Boosts Evasion by +3 stages when HP is low.",
        },
        "values": (1, 2, 3),
    },
    "Collector": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "10% chance for defeated foes to drop a bonus item.",
            2: "20% chance for defeated foes to drop a bonus item.",
            3: "30% chance for defeated foes to drop a bonus item.",
        },
        "values": (0.10, 0.20, 0.30),
    },
    "Critical Dodger": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Prevents this Pokemon from taking critical hits.",
    },
    "Stair Sensor": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "Locates the direction of the stairs when entering a floor.",
    },
    "Extra Striker": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "10% chance to use a move twice in one turn.",
            2: "20% chance to use a move twice in one turn.",
            3: "30% chance to use a move twice in one turn.",
        },
        "values": (0.10, 0.20, 0.30),
    },
    "Quick Dodger": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Raises Evasion by +1 stage when entering a new floor.",
            2: "Raises Evasion by +2 stages when entering a new floor.",
            3: "Raises Evasion by +3 stages when entering a new floor.",
        },
        "values": (1, 2, 3),
    },
    "Fast Friend": {
        "upgradeable": True,
        "leader_only": True,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "tiers": {
            1: "Leader skill: Slightly increases chance of successful recruitment.",
            2: "Leader skill: Increases chance of successful recruitment.",
            3: "Leader skill: Greatly increases chance of successful recruitment.",
        },
        "values": (1.2, 1.4, 1.5),
    },
    "Intimidator": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "15% chance for adjacent foes to fail a move.",
            2: "25% chance for adjacent foes to fail a move.",
            3: "35% chance for adjacent foes to fail a move.",
        },
        "values": (0.15, 0.25, 0.35),
    },
    "No-Charger": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Charging moves cost more PP but don't need to charge.",
    },
    "Map Surveyor": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "When entering a floor, partially reveals its layout.",
    },
    "Pierce Hurler": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Thrown items can pierce through Pokémon.",
    },
    "Nature Gifter": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Spreads the effects of eaten items to all allies.",
    },
    "Time Tripper": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "Permanently increases Movement Speed.",
    },
    "Slip-Through": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "description": "Attacks can pass through allies without harming them.",
    },
    "Sneaky": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "Moving adjacent to sleeping foes does not wake them up.",
    },
    "Retaliatory": {
        "upgradeable": False,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": True,
        "conflicts": set(),
        "description": "If an ally is defeated, Attack, Sp. Attack & Accuracy increases +3 stages.",
    },
    "Gourmand": {
        "upgradeable": True,
        "leader_only": False,
        "non_leader_only": False,
        "team_only": False,
        "conflicts": set(),
        "tiers": {
            1: "Eating any item also restores 15% HP and PP.",
            2: "Eating any item also restores 25% HP and PP.",
            3: "Eating any item also restores 35% HP and PP.",
        },
        "values": (0.15, 0.25, 0.35),
    },
}


def parse_iq_skill_name(skill_str: str) -> tuple[str, int]:
    """Appends + symbols to an upgraded IQ skill's name"""
    if not skill_str:
        return ("", 0)
    if skill_str.endswith("++"):
        return (skill_str[:-2], 3)
    if skill_str.endswith("+"):
        return (skill_str[:-1], 2)
    return (skill_str, 1)


def format_iq_skill_name(base_name: str, level: int) -> str:
    """Formats the name of IQ skills for display"""
    if level >= 3:
        return f"{base_name}++"
    if level == 2:
        return f"{base_name}+"
    return base_name


def get_iq_skill_description(skill_display_name: str) -> str:
    """Returns a short 1-line pure ASCII description for any IQ skill or tier."""
    base, lvl = parse_iq_skill_name(skill_display_name)
    meta = IQ_SKILLS_DB.get(base)
    if not meta:
        return "BUG: MISSING SKILL DESCRIPTION!!!!!!!"
    if "tiers" in meta:
        return meta["tiers"].get(max(1, min(3, lvl)), meta["tiers"][1])
    return meta.get("description", "BUG: MISSING SKILL DESCRIPTION!!!!!!!")


def _is_pokemon_leader(pokemon, game=None) -> bool:
    """Returns True if pokemon is the player-controlled pokemon."""
    if pokemon is None:
        return False
    if game is not None and getattr(game, "player_pokemon", None) is not None:
        return pokemon is game.player_pokemon
    return bool(getattr(pokemon, "is_leader", False))


def get_learned_iq_skill_level(pokemon, base_name: str) -> int:
    """Returns the IQ skill's tier (ignoring Leader/Non-Leader stuff)"""
    if pokemon is None:
        return 0
    for s in getattr(pokemon, "iq_skills", []) or []:
        s_base, s_lvl = parse_iq_skill_name(s)
        if s_base == base_name:
            return s_lvl
    return 0


def get_iq_skill_level(pokemon, base_name: str, game=None) -> int:
    """Returns the active IQ skill's tier"""
    if pokemon is None:
        return 0
    meta = IQ_SKILLS_DB.get(base_name)
    if not meta:
        return 0
    lvl = get_learned_iq_skill_level(pokemon, base_name)
    if lvl <= 0:
        return 0
    if game is not None:
        is_leader = _is_pokemon_leader(pokemon, game=game)
        if meta.get("leader_only", False) and not is_leader:
            return 0
        if meta.get("non_leader_only", False) and is_leader:
            return 0
    return lvl


def has_iq_skill(pokemon, base_name: str, game=None) -> bool:
    """Returns True if pokemon currently has base_name active."""
    return get_iq_skill_level(pokemon, base_name, game=game) > 0


def get_iq_skill_value(pokemon, base_name: str, game=None, default=None):
    """Returns the numeric/tuple value corresponding to pokemon's active tier for base_name."""
    lvl = get_iq_skill_level(pokemon, base_name, game=game)
    if lvl <= 0:
        return default
    meta = IQ_SKILLS_DB.get(base_name)
    if not meta or "values" not in meta:
        return default
    vals = meta["values"]
    return vals[min(len(vals) - 1, lvl - 1)]


def any_team_has_iq_skill(game, base_name: str) -> bool:
    """Returns True if at least one living team member has base_name (IQ skill) active"""
    if game is None:
        return False
    for member in getattr(game, "party", []) or []:
        if int(getattr(member, "current_hp", 0)) > 0 and has_iq_skill(member, base_name, game=game):
            return True
    return False


def get_next_iq_skill_threshold(iq: int) -> int | None:
    """Returns next IQ percentage needed for an IQ skill, or None if maxed"""
    iq_val = max(0, min(100, int(iq)))
    if iq_val >= 100:
        return None
    return ((iq_val // 10) + 1) * 10


def _pokemon_has_incompatible_ability(pokemon, incompatible_set: set[str], game=None) -> bool:
    if not incompatible_set or pokemon is None:
        return False
    from abilities import canonicalize_ability_name, get_unlocked_abilities
    slots = getattr(pokemon, "ability_slots", None) or []
    for raw_ab in slots:
        canon = canonicalize_ability_name(raw_ab)
        if canon in incompatible_set:
            return True
    for raw_ab in get_unlocked_abilities(pokemon):
        canon = canonicalize_ability_name(raw_ab)
        if canon in incompatible_set:
            return True
    return False


def get_eligible_iq_skill_choices(pokemon, game=None) -> list[tuple[str, float]]:
    """Returns [(display_name, weight), ...] of eligible next IQ skill options for pokemon."""
    if pokemon is None:
        return []
    is_leader = _is_pokemon_leader(pokemon, game=game)
    learned_bases = {parse_iq_skill_name(s)[0] for s in (getattr(pokemon, "iq_skills", []) or [])}
    num_skills = len(learned_bases)

    candidates: list[tuple[str, float]] = []
    for base_name, meta in IQ_SKILLS_DB.items():
        if meta.get("leader_only", False) and not is_leader:
            continue
        if meta.get("non_leader_only", False) and is_leader:
            continue
        conflicts = meta.get("conflicts", set())
        if any(c in learned_bases for c in conflicts):
            continue
        incompat_abs = meta.get("incompatible_abilities")
        if incompat_abs and _pokemon_has_incompatible_ability(pokemon, incompat_abs, game=game):
            continue

        curr_lvl = get_learned_iq_skill_level(pokemon, base_name)
        if curr_lvl == 0:
            if num_skills >= MAX_IQ_SKILLS:
                continue
            candidates.append((format_iq_skill_name(base_name, 1), 1.0))
        elif meta.get("upgradeable", False) and curr_lvl < 3:
            #Next upgraded tier is more likely to appear
            candidates.append((format_iq_skill_name(base_name, curr_lvl + 1), 2.0))

    return candidates


def roll_iq_skill_choices(pokemon, game=None, count: int = 3) -> list[str]:
    """Populates IQ skill selection list by randomly selecting up to `count` eligible IQ skill choices"""
    pool = get_eligible_iq_skill_choices(pokemon, game=game)
    if not pool:
        return []
    chosen: list[str] = []
    remaining = list(pool)
    for _ in range(min(count, len(remaining))):
        weights = [w for _, w in remaining]
        picked = random.choices(remaining, weights=weights, k=1)[0]
        chosen.append(picked[0])
        remaining.remove(picked)
    return chosen


def add_or_upgrade_iq_skill(pokemon, skill_display_name: str, game=None) -> bool:
    """Adds or upgrades `skill_display_name` on `pokemon`"""
    if pokemon is None or not skill_display_name:
        return False
    base, new_lvl = parse_iq_skill_name(skill_display_name)
    if base not in IQ_SKILLS_DB:
        return False
    if not hasattr(pokemon, "iq_skills") or pokemon.iq_skills is None:
        pokemon.iq_skills = []

    old_lvl = get_learned_iq_skill_level(pokemon, base)
    replaced = False
    for idx, existing in enumerate(pokemon.iq_skills):
        ex_base, _ = parse_iq_skill_name(existing)
        if ex_base == base:
            pokemon.iq_skills[idx] = format_iq_skill_name(base, new_lvl)
            replaced = True
            break
    if not replaced:
        if len(pokemon.iq_skills) >= MAX_IQ_SKILLS:
            return False
        pokemon.iq_skills.append(format_iq_skill_name(base, new_lvl))

    if base == "Brick Tough" and hasattr(pokemon, "recalculate_stats"):
        pokemon.recalculate_stats()
    elif base == "Multitalent" and new_lvl > old_lvl:
        vals = IQ_SKILLS_DB["Multitalent"]["values"]
        old_bonus = vals[old_lvl - 1] if old_lvl > 0 else 0
        new_bonus = vals[min(2, new_lvl - 1)]
        delta_pp = new_bonus - old_bonus
        if delta_pp > 0:
            pokemon.max_pp = int(getattr(pokemon, "max_pp", 100)) + delta_pp
            pokemon.current_pp = min(pokemon.max_pp, int(getattr(pokemon, "current_pp", 0)) + delta_pp)

    return True


def score_move_for_weak_type_picker(attacker, move: dict, target, game) -> tuple[int, float]:
    """Handles the move and target selection for AI Pokémon with Weak Type Picker

    Returns (tier, score) where:
      tier 2 = Super-effective move
      tier 1 = Neutral / not very effective move (not absorbed/immune)
      tier 0 = Status move
      tier -1 = Immune / absorbed move. Only used as a last resort
    """
    from abilities import resolve_move_with_abilities, get_effective_weather, has_ability
    from combat import is_pokemon_grounded
    from type_chart import get_effectiveness_multiplier

    eff_move = resolve_move_with_abilities(attacker, move, game=game)
    cat = eff_move.get("category", "Status")
    if cat not in ("Physical", "Special") and eff_move.get("power") is None:
        return (0, 0.0)

    m_type = eff_move.get("type", "Normal")
    eff_w = get_effective_weather(attacker, game)
    def_w = get_effective_weather(target, game)

    #Check immunities and absorptions
    if m_type == "Fire" and (has_ability(target, "Flash Fire", game=game, attacker=attacker) or eff_w == "Heavy Rain"):
        return (-1, 0.0)
    if m_type == "Water" and (
        has_ability(target, "Water Absorb", game=game, attacker=attacker)
        or has_ability(target, "Dry Skin", game=game, attacker=attacker)
        or eff_w == "Harsh Sunlight"
    ):
        return (-1, 0.0)
    if m_type == "Electric" and (
        has_ability(target, "Volt Absorb", game=game, attacker=attacker)
        or has_ability(target, "Lightning Rod", game=game, attacker=attacker)
    ):
        return (-1, 0.0)
    if m_type == "Grass" and has_ability(target, "Sap Sipper", game=game, attacker=attacker):
        return (-1, 0.0)

    is_grounded = is_pokemon_grounded(target, game, attacker=attacker)
    if m_type == "Ground" and not is_grounded and (
        target.status_effects.get("Magnet Rise", 0) > 0
        or has_ability(target, "Levitate", game=game, attacker=attacker)
    ):
        return (-1, 0.0)

    target_types = list(getattr(target, "types", target.species_data.get("types", ["typeless"])))
    if is_grounded:
        target_types = [t for t in target_types if t != "Flying"] or ["typeless"]
    if has_ability(attacker, "Scrappy", game=game) and m_type in ("Normal", "Fighting"):
        target_types = [t for t in target_types if t != "Ghost"] or ["typeless"]

    move_type_key = "typeless" if eff_w == "Shadowy Aura" else (
        str(eff_move.get("name")) if eff_move.get("name") in ("Muddy Water", "Freeze-Dry") else str(m_type)
    )
    eff = get_effectiveness_multiplier(move_type_key, target_types)
    if eff <= 0.0 or (m_type == "Ground" and not is_grounded and has_ability(target, "Levitate", game=game, attacker=attacker)):
        return (-1, 0.0)

    #Thick Fat counts as a resistance for Fire and Ice
    if m_type in ("Fire", "Ice") and has_ability(target, "Thick Fat", game=game, attacker=attacker):
        eff = max(0.25, round(eff - 0.25, 4))
    if m_type == "Fire" and has_ability(target, "Dry Skin", game=game, attacker=attacker):
        eff = min(1.75, round(eff + 0.25, 4))

    #Weather modifiers on type power
    weather_mult = 1.0
    if def_w == "Sunny" or eff_w == "Sunny":
        if m_type == "Fire":
            weather_mult = 1.5
        elif m_type == "Water":
            weather_mult = 0.5
    elif def_w == "Rain" or eff_w == "Rain":
        if m_type == "Water":
            weather_mult = 1.5
        elif m_type == "Fire":
            weather_mult = 0.5
    elif eff_w in ("Snow", "Blizzard") and m_type == "Ice":
        weather_mult = 1.5
    elif eff_w == "Cloudy" and m_type == "Normal":
        weather_mult = 1.33
    elif eff_w == "Thunderstorm":
        if m_type in ("Water", "Electric"):
            weather_mult = 1.5
        elif m_type == "Fire":
            weather_mult = 0.5

    #STAB and attacker ability multipliers for a given type/move
    atk_types = getattr(attacker, "types", attacker.species_data.get("types", []))
    stab_mult = 1.0
    if eff_w != "Shadowy Aura":
        if m_type in atk_types or (eff_move.get("name") == "Muddy Water" and any(t in atk_types for t in ("Water", "Ground"))) or (eff_move.get("name") == "Tri Attack" and any(t in atk_types for t in ("Fire", "Ice", "Electric"))):
            stab_mult = 2.0 if has_ability(attacker, "Adaptability", game=game) else 1.5

    ab_mult = 1.0
    max_hp = max(1.0, float(attacker.stats.get("HP", 1.0)))
    if float(attacker.current_hp) <= 0.20 * max_hp:
        pinch = {"Grass": "Overgrow", "Fire": "Blaze", "Water": "Torrent", "Bug": "Swarm"}.get(m_type)
        if pinch and has_ability(attacker, pinch, game=game):
            ab_mult *= 1.5
    if getattr(attacker, "flash_fire_boosted", False) and m_type == "Fire" and has_ability(attacker, "Flash Fire", game=game):
        ab_mult *= 1.5
    if eff_w == "Sandstorm" and m_type in ("Rock", "Ground", "Steel") and has_ability(attacker, "Sand Force", game=game):
        ab_mult *= 1.3
    if eff_move.get("contact") and has_ability(attacker, "Tough Claws", game=game):
        ab_mult *= 1.3
    if eff_move.get("punching") and has_ability(attacker, "Iron Fist", game=game):
        ab_mult *= 1.2

    raw_pwr = float(eff_move.get("power") or 40.0)
    if raw_pwr < 80.0 and has_ability(attacker, "Technician", game=game):
        raw_pwr = min(80.0, raw_pwr * 1.5)

    score = eff * weather_mult * stab_mult * ab_mult * raw_pwr
    #Priority tier based on effective type weakness vs normal/resisted
    effective_weakness = eff * (weather_mult if m_type in ("Fire", "Water") and weather_mult < 1.0 else 1.0)
    tier = 2 if effective_weakness > 1.0 else 1
    return (tier, score)


def get_thrown_damage_multiplier(attacker, game=None) -> float:
    """Returns thrown item damage multiplier for Power Pitcher."""
    return float(get_iq_skill_value(attacker, "Power Pitcher", game=game, default=1.0))
