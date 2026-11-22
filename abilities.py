"""
abilities.py

This script file handles Pokémon abilities and ability unlocks. It also contains helper functions related to Pokémon abilities.
"""

import random

ALIAS_MAP: dict[str, str] = {
    "Shed Skin": "Natural Cure",
    "Gooey": "Tangling Hair",
    "Air Lock": "Cloud Nine",
    "Vital Spirit": "Insomnia",
    "Power of Alchemy": "Receiver",
    "Shell Armor": "Battle Armor",
}

ABILITIES_DB: dict[str, str] = {
    "Overgrow": "Boosts Grass moves by 50% when HP is low.",
    "Chlorophyll": "Moves strike twice per turn in Sunny or Harsh Sunlight.",
    "Blaze": "Boosts Fire moves by 50% when HP is low.",
    "Solar Power": "+50% Sp. Atk in Sunny weather, but HP is slowly lost.",
    "Torrent": "Boosts Water moves by +50% when HP is low.",
    "Rain Dish": "Greatly boosts natural HP regen in wet weather.",
    "Shield Dust": "Blocks additional effects of incoming damaging moves.",
    "Run Away": "Immune to getting stuck. +1 Movement Speed once per floor when HP drops below 50%.",
    "Natural Cure": "Negative status effects expire twice as fast.",
    "Compound Eyes": "Starts each floor with +2 Accuracy levels.",
    "Tinted Lens": "Greatly reduces damage penalty from using ineffective moves.",
    "Swarm": "Boosts Bug moves by +50% when HP is low.",
    "Sniper": "Critical hits deal 2x damage instead of 1.5x.",
    "Keen Eye": "Prevents enemies from lowering Accuracy, and moves ignore target's Evasion stat.",
    "Tangled Feet": "Greatly increases Evasion when confused.",
    "Big Pecks": "Prevents enemies from lowering Defense.",
    "Guts": "+50% Attack when poisoned, burned, confused, asleep, or paralyzed, and eliminates Attack penalty from burn.",
    "Hustle": "+50% Attack but -20% Accuracy.",
    "Gluttony": "Belly drains 2x faster, but eating restores more Belly, heals 25% HP, and Grimy Food is less likely to have a bad effect.",
    "Thick Fat": "Increases resistance to Fire-type and Ice-type moves.",
    "Intimidate": "Lowers adjacent enemies' Attack by 1 level while nearby.",
    "Unnerve": "Nearby enemies cannot consume edible items.",
    "Static": "30% chance to paralyze attackers that make contact.",
    "Lightning Rod": "Pulls in Electric-type moves from the floor to raise Sp. Atk.",
    "Surge Surfer": "Movement speed is increased in Electric Terrain.",
    "Sand Veil": "Makes Pokémon immune to Sandstorm damage and raises Evasion in a Sandstorm.",
    "Sand Rush": "Movement speed is increased in a Sandstorm.",
    "Snow Cloak": "Makes Pokémon immune to Hail damage and raises Evasion in Hail or Snow.",
    "Poison Point": "30% chance to poison attackers that make contact.",
    "Rivalry": "+25% damage to opposite gender, -25% to same gender.",
    "Sheer Force": "Disables secondary effects of damaging moves for +30% move power.",
    "Cute Charm": "30% chance to infatuate attackers of the opposite gender that make contact.",
    "Magic Guard": "Immune to indirect damage (from statuses, weather, move recoil, explosions, etc.).",
    "Friend Guard": "Adjacent allies gain +25% Defense and Sp. Defense.",
    "Unaware": "This Pokémon's attacks ignore the target's stat changes.",
    "Flash Fire": "Immune to damage from Fire-type moves. Getting hit by a Fire-type attack boosts next Fire-type move by +50%.",
    "Drought": "Changes weather to Sunny when entering the floor.",
    "Snow Warning": "Changes weather to Snow when entering the floor.",
    "Competitive": "+2 Sp. Attack if a foe lowers one of this Pokémon's stats.",
    "Inner Focus": "Immune to flinching and unaffected by Intimidate.",
    "Infiltrator": "Moves bypass Reflect, Light Screen, Safeguard, Mist, and Aurora Veil.",
    "Stench": "10% chance to terrify adjacent attackers that hit this Pokémon.",
    "Effect Spore": "10% chance each to poison, paralyze or sleep attackers that make contact.",
    "Dry Skin": "Absorbs Water-type moves, but is weak to Fire-type moves. Boosts HP regeneration in Rain, but causes damage in Sun.",
    "Damp": "Prevents all explosions on the floor.",
    "Wonder Skin": "Reduces accuracy of incoming status moves to 50% if greater.",
    "Arena Trap": "Traps adjacent foes.",
    "Sand Force": "Immune to Sandstorm damage. +30% Rock, Ground, and Steel power in Sandstorm.",
    "Tangling Hair": "Slows attackers that make contact.",
    "Pickup": "10% chance to find an item when entering a new floor.",
    "Technician": "Boosts the power of damaging moves by +50% (max 80).",
    "Rattled": "Raises Movement Speed if hit by a Bug, Dark or Ghost move.",
    "Tough Claws": "Boosts the power of contact moves by +30%.",
    "Limber": "Prevents this Pokémon from becoming paralyzed.",
    "Fur Coat": "Doubles Defense.",
    "Cloud Nine": "This Pokémon is completely unaffected by weather conditions.",
    "Insomnia": "Immune to sleep and prevents resting.",
    "Anger Point": "Attack is maximized if this Pokémon takes a critical hit.",
    "Defiant": "+2 Attack if a foe lowers one of this Pokémon's stats.",
    "Justified": "+1 Attack if hit by a Dark-type move.",
    "Rock Head": "Immune to move recoil damage. Does not affect Struggle or crash damage.",
    "Water Absorb": "Absorbs damaging Water-type moves, restoring HP.",
    "Swift Swim": "+1 Movement Speed in Rain; +2 in Heavy Rain and Thunderstorm.",
    "Drizzle": "Changes the weather to Rain when entering a floor.",
    "Synchronize": "Passes poison, burn, or paralysis to all adjacent foes.",
    "No Guard": "All moves made by and against this Pokémon will never miss.",
    "Steadfast": "Raises Movement Speed when flinching or consuming a Crosseye Seed.",
    "Clear Body": "Prevents enemies from lowering this Pokémon's stats.",
    "Liquid Ooze": "HP-draining moves against this Pokémon damage the attacker instead.",
    "Sturdy": "Immune to OHKO moves, and can endure lethal hits from full HP.",
    "Magnet Pull": "Pulls Steel-type foes within 3 tiles adjacent and traps them.",
    "Galvanize": "Turns Normal-type moves into Electric-type with +20% power.",
    "Flame Body": "30% chance to burn attackers that make contact.",
    "Pastel Veil": "Protects this Pokemon and all allies from being poisoned.",
    "Anticipation": "Reveals the locations of all enemies on the dungeon map.",
    "Oblivious": "Immune to Infatuation, Taunt, and Intimidate.",
    "Own Tempo": "Prevents this Pokémon from becoming confused.",
    "Regenerator": "Restores 25% HP when entering a new floor.",
    "Quick Draw": "30% chance for damaging moves to strike twice per turn.",
    "Curious Medicine": "Once per floor, resets any lowered stats of all allies at turn start.",
    "Analytic": "+50% move power while slowed, and allows exact enemy HP to be viewed.",
    "Scrappy": "Normal and Fighting moves hit Ghost-types normally. Immune to Intimidate.",
    "Early Bird": "Wakes from sleep twice as fast. Resting takes 1 turn less.",
    "Hydration": "Cures negative status effects immediately in rainy weather.",
    "Ice Body": "Prevents Hail damage and boosts HP recovery in hail or snow.",
    "Sticky Hold": "Prevents this Pokémon's held item from being stolen or knocked off.",
    "Poison Touch": "30% chance to poison targets hit by this Pokémon's contact moves.",
    "Receiver": "When an ally faints, copies the ally's first ability.",
    "Battle Armor": "Incoming critical hits become normal hits.",
    "Skill Link": "Multi-hit moves always strike the maximum number of times.",
    "Overcoat": "Immune to weather damage, Powder/Spore moves, and Effect Spore.",
    "Levitate": "Makes the Pokémon airborne and immune to Ground-type moves.",
    "Cursed Body": "30% chance to disable a damaging move that hits this Pokémon.",
    "Weak Armor": "When hit by a Physical move, lowers Defense and raises Speed and movement speed.",
    "Forewarn": "Reveals all known moves of enemies when examining them.",
    "Hyper Cutter": "Prevents enemies from lowering Attack.",
    "Soundproof": "Immune to all sound-based moves.",
    "Aftermath": "Explodes when defeated by a contact move. Explosion power depends on amount of overkill.",
    "Harvest": "May duplicate an eaten berry. Chance is higher in sunny weather.",
    "Reckless": "+20% power to moves that have recoil or crash damage.",
    "Unburden": "If not holding an item, moves can be used twice per turn.",
    "Iron Fist": "Boosts the power of punching moves by +20%.",
    "Neutralizing Gas": "Suppresses the abilities of all other Pokémon in the room.",
    "Misty Surge": "Starts Misty Terrain when entering a floor.",
    "Serene Grace": "Damaging moves are more likely to trigger their additional effects.",
    "Healer": "Negative status conditions expire twice as quickly for adjacent allies.",
    "Leaf Guard": "Blocks some bad status effects in sunny weather.",
    "Water Veil": "Protects this Pokémon and all allies from being burned.",
    "Illuminate": "Increases the visibility range in corridors.",
    "Filter": "Reduces the damage bonus from super effective moves hitting this Pokémon from +25% to +10%.",
    "Screen Cleaner": "Moves remove Reflect, Light Screen, and Aurora Veil from targets.",
    "Mold Breaker": "Moves ignore defensive and on-move abilities on targets.",
    "Moxie": "30% chance to raise Attack by one level when defeating an enemy.",
    "Cud Chew": "Eaten Berries trigger their effect a second time after a few turns.",
    "Imposter": "Causes this Pokémon to transform into a random species when entering the floor.",
    "Adaptability": "Increases STAB damage bonus from +50% to +100%.",
    "Volt Absorb": "Absorbs damaging Electric-type moves, restoring HP instead.",
    "Quick Feet": "Boosts movement speed when affected by a bad status condition, and ignores Speed penalty from Paralysis.",
    "Trace": "When hit by an adjacent move, replaces Trace with the attacker's first ability.",
    "Download": "When attacking a foe, may raise Attack or Sp. Atk depending on the foe's defenses.",
    "Pressure": "Moves hitting this Pokemon cost +50% PP.",
    "Immunity": "Prevents this Pokémon from being poisoned.",
    "Berserk": "+1 Sp. Attack once per floor if HP falls below 50%.",
    "Marvel Scale": "+50% Defense when affected by a bad status condition, and ignores Defense penalty from Sleep.",
    "Multiscale": "Halves incoming move damage when at full HP.",
    "Super Luck": "Doubles this Pokémon's base critical hit chance.",
    "Magic Bounce": "Reflects incoming Status moves back to the attacker.",
    "Sap Sipper": "Immune to Grass-type moves, instead raising Attack by 1 stage.",
    "Huge Power": "Doubles Attack.",
    "Speed Boost": "Raises Speed by 1 stage when damaged by an enemy move.",
    "Prankster": "Status moves strike twice per turn unless targeting a Dark-type.",
    "Shadow Tag": "Traps adjacent foes.",
    "Telepathy": "Damaging moves used by allies always miss this Pokémon.",
    "Light Metal": "Halves this Pokémon's weight.",
    "Contrary": "Reverses stat changes caused by moves.",
    "Pickpocket": "If holding no item, steals held item from attackers that make contact.",
    "Honey Gather": "10% chance to find Nectar when entering a new floor.",
    "Magma Armor": "Destroys incoming thrown items.",
    "Moody": "After attack, raises a random stat by 1 level and lowers another by 1 level.",
    "Suction Cups": "Cannot be warped, thrown, or blown away by enemies.",
    "Sand Stream": "Changes weather to Sandstorm when entering the floor.",
    "Slush Rush": "Raises movement speed in snow or hail.",
}

#List of abilities that Mold Breaker ignores
MOLD_BREAKER_IGNORED_ABILITIES: set[str] = {
    "Battle Armor",
    "Big Pecks",
    "Clear Body",
    "Dry Skin",
    "Filter",
    "Flash Fire",
    "Fur Coat",
    "Hyper Cutter",
    "Immunity",
    "Inner Focus",
    "Insomnia",
    "Keen Eye",
    "Leaf Guard",
    "Levitate",
    "Lightning Rod",
    "Limber",
    "Magic Bounce",
    "Marvel Scale",
    "Multiscale",
    "Oblivious",
    "Overcoat",
    "Own Tempo",
    "Pastel Veil",
    "Sand Veil",
    "Sap Sipper",
    "Shield Dust",
    "Snow Cloak",
    "Soundproof",
    "Sturdy",
    "Tangled Feet",
    "Thick Fat",
    "Unaware",
    "Volt Absorb",
    "Water Absorb",
    "Water Veil",
    "Wonder Skin",
}


def canonicalize_ability_name(name: str | None) -> str | None:
    """Resolves ability aliases to their canonical name."""
    if not name:
        return None
    return ALIAS_MAP.get(name, name)


def get_ability_description(name: str) -> str:
    """Returns an ability's description."""
    canon = canonicalize_ability_name(name)
    if canon and canon in ABILITIES_DB:
        return ABILITIES_DB[canon]
    return "BUG: INVALID/MISSING ABILITY DESCRIPTION!"


def assign_ability_slots(species_data: dict) -> list[str]:
    """Builds ability slots for Pokémon. A Pokémon has up to 3 abilities, here llabeled a0, a1 and a2

    - 1 ability: [a0] (Always unlocked)
    - 2 abilities: [a0, a1] (0% IQ, 100% IQ)
    - 3 abilities: shuffle [a0, a1], a2 last (0% IQ, 50% IQ, 100% IQ)
    """
    raw_list = list(species_data.get("abilities") or [])
    cleaned = [canonicalize_ability_name(a) for a in raw_list if a]
    cleaned = [a for a in cleaned if a is not None]
    if not cleaned:
        return []
    if len(cleaned) == 1:
        return [cleaned[0]]
    if len(cleaned) == 2:
        return [cleaned[0], cleaned[1]]
    first_two = [cleaned[0], cleaned[1]]
    random.shuffle(first_two)
    return first_two + cleaned[2:]


def get_ability_unlock_thresholds(slots: list[str]) -> list[tuple[str, int]]:
    """Returns (ability_name, required_iq) pairs for a Pokémon's slot list"""
    n = len(slots)
    if n == 0:
        return []
    if n == 1:
        return [(slots[0], 0)]
    if n == 2:
        return [(slots[0], 0), (slots[1], 100)]
    result = [(slots[0], 0), (slots[1], 50)]
    for ab in slots[2:]:
        result.append((ab, 100))
    return result


def get_effective_ability_slots_with_thresholds(pokemon) -> list[tuple[str, int]]:
    """Returns (effective_ability_name, required_iq) pairs, including temporary overrides"""
    slots = getattr(pokemon, "ability_slots", None)
    if slots is None:
        slots = assign_ability_slots(getattr(pokemon, "species_data", {}) or {})
        pokemon.ability_slots = slots
    base_pairs = get_ability_unlock_thresholds(slots)
    replaced = getattr(pokemon, "replaced_abilities", None) or {}
    return [
        (canonicalize_ability_name(replaced.get(idx, ab)) or ab, req_iq)
        for idx, (ab, req_iq) in enumerate(base_pairs)
    ]


def get_unlocked_abilities(pokemon) -> list[str]:
    """Returns names of all abilities currently unlocked on pokemon instance"""
    if pokemon is None:
        return []
    iq = max(0, min(100, int(getattr(pokemon, "iq", 0))))
    unlocked = [
        ab for ab, req_iq in get_effective_ability_slots_with_thresholds(pokemon)
        if iq >= req_iq
    ]
    #For save files from before 0.3.0
    legacy = canonicalize_ability_name(getattr(pokemon, "ability", None))
    if legacy and legacy not in unlocked and not getattr(pokemon, "ability_slots", None):
        unlocked.append(legacy)
    return unlocked


def get_first_base_ability(pokemon) -> str | None:
    """Returns the Pokémon's first ability"""
    if pokemon is None:
        return None
    slots = getattr(pokemon, "ability_slots", None)
    if slots is None:
        slots = assign_ability_slots(getattr(pokemon, "species_data", {}) or {})
        pokemon.ability_slots = slots
    if slots:
        return canonicalize_ability_name(slots[0])
    legacy = canonicalize_ability_name(getattr(pokemon, "ability", None))
    return legacy


def get_pokemon_room_mates(game, pokemon) -> list:
    """Returns all other living Pokémon entities on the floor within room range of pokemon."""
    if game is None or pokemon is None or not getattr(game, "floor", None):
        return []
    from targeting import get_pokemon_position, get_room_tiles_at

    ax, ay = get_pokemon_position(game, pokemon)
    room_tiles = get_room_tiles_at(game.floor, ax, ay)
    all_pokes = list(getattr(game, "party", []) or []) + list(getattr(game, "spawned_pokemon", []) or [])
    seen = set()
    mates = []
    for other in all_pokes:
        if other is pokemon or other in seen:
            continue
        seen.add(other)
        if int(getattr(other, "current_hp", 0)) <= 0:
            continue
        ox, oy = get_pokemon_position(game, other)
        if room_tiles:
            if (ox, oy) in room_tiles:
                mates.append(other)
        else:
            if max(abs(ox - ax), abs(oy - ay)) <= 5:
                mates.append(other)
    return mates


def is_neutralizing_gas_active_near(pokemon, game=None) -> bool:
    """Returns True if another living Pokémon in room range has Neutralizing Gas active"""
    if game is None or pokemon is None:
        return False
    for other in get_pokemon_room_mates(game, pokemon):
        if "Neutralizing Gas" in get_unlocked_abilities(other):
            return True
    return False


def has_ability(pokemon, ability_name: str, game=None, attacker=None) -> bool:
    """Returns True if pokemon has the given ability unlocked and active."""
    if pokemon is None:
        return False
    canon = canonicalize_ability_name(ability_name)
    if not canon:
        return False
    if canon not in get_unlocked_abilities(pokemon):
        return False
    #Ability suppressed by Neutralizing Gas
    if canon != "Neutralizing Gas" and is_neutralizing_gas_active_near(pokemon, game=game):
        return False
    #Ability suppressed by Mold Breaker
    if attacker is not None and attacker is not pokemon and canon in MOLD_BREAKER_IGNORED_ABILITIES:
        if has_ability(attacker, "Mold Breaker", game=game):
            return False
    return True


def get_effective_weather(pokemon, game=None) -> str:
    """Returns the weather condition experienced by pokemon. This is to handle Cloud Nine (which treats all weathers as clear)"""
    if game is None:
        return "Clear"
    if has_ability(pokemon, "Cloud Nine", game=game):
        return "Clear"
    return getattr(game, "weather", "Clear") or "Clear"


def get_allies_of(pokemon, game=None) -> list:
    """Returns living Pokémon on the same side (including pokemon itself)"""
    if pokemon is None:
        return []
    if game is None:
        return [pokemon] if int(getattr(pokemon, "current_hp", 0)) > 0 else []
    party = getattr(game, "party", []) or []
    spawned = getattr(game, "spawned_pokemon", []) or []
    pool = party if pokemon in party else spawned
    res = [p for p in pool if int(getattr(p, "current_hp", 0)) > 0]
    if pokemon not in res and int(getattr(pokemon, "current_hp", 0)) > 0:
        res.append(pokemon)
    return res


def get_enemies_of(pokemon, game=None) -> list:
    """Returns living opposing Pokémon on the floor"""
    if game is None or pokemon is None:
        return []
    party = getattr(game, "party", []) or []
    spawned = getattr(game, "spawned_pokemon", []) or []
    pool = spawned if pokemon in party else party
    return [p for p in pool if p is not pokemon and int(getattr(p, "current_hp", 0)) > 0]


def any_side_has_ability(pokemon, ability_name: str, game=None, attacker=None) -> bool:
    """Returns True if pokemon or any ally on its side has ability_name active"""
    for ally in get_allies_of(pokemon, game=game):
        if has_ability(ally, ability_name, game=game, attacker=attacker):
            return True
    return False


def any_adjacent_ally_has_ability(pokemon, ability_name: str, game=None, attacker=None) -> bool:
    """Returns True if any living ally (excluding self) within 1 tile has ability_name"""
    if game is None or pokemon is None:
        return False
    from targeting import get_pokemon_position

    px, py = get_pokemon_position(game, pokemon)
    for ally in get_allies_of(pokemon, game=game):
        if ally is pokemon:
            continue
        ax, ay = get_pokemon_position(game, ally)
        if max(abs(ax - px), abs(ay - py)) <= 1:
            if has_ability(ally, ability_name, game=game, attacker=attacker):
                return True
    return False


def count_adjacent_allies_with_ability(pokemon, ability_name: str, game=None, attacker=None) -> int:
    """Counts living allies (excluding self) within 1 tile that have ability_name"""
    if game is None or pokemon is None:
        return 0
    from targeting import get_pokemon_position

    px, py = get_pokemon_position(game, pokemon)
    count = 0
    for ally in get_allies_of(pokemon, game=game):
        if ally is pokemon:
            continue
        ax, ay = get_pokemon_position(game, ally)
        if max(abs(ax - px), abs(ay - py)) <= 1:
            if has_ability(ally, ability_name, game=game, attacker=attacker):
                count += 1
    return count


def any_floor_pokemon_has_ability(ability_name: str, game=None) -> bool:
    """Returns True if any living Pokémon on the floor has ability_name active"""
    if game is None:
        return False
    all_pokes = list(getattr(game, "party", []) or []) + list(getattr(game, "spawned_pokemon", []) or [])
    for p in all_pokes:
        if int(getattr(p, "current_hp", 0)) > 0 and has_ability(p, ability_name, game=game):
            return True
    return False


def get_team_ability_count(game, ability_name: str) -> int:
    """Counts living party members that have ability_name active"""
    if game is None:
        return 0
    count = 0
    for member in getattr(game, "party", []) or []:
        if int(getattr(member, "current_hp", 0)) > 0 and has_ability(member, ability_name, game=game):
            count += 1
    return count


def has_any_major_status(pokemon) -> bool:
    """Returns True if pokémon has a major status condition"""
    st = getattr(pokemon, "status_effects", {}) or {}
    return bool(
        st.get("Poison")
        or st.get("Toxic")
        or st.get("Burn")
        or st.get("Confusion", 0) > 0
        or st.get("Sleep", 0) > 0
        or st.get("Resting", 0) > 0
        or st.get("Paralysis", 0) > 0
    )


def get_effective_movement_speed_stage(pokemon, game=None) -> int:
    """Calculates effective movement speed stage, including from weather and abilities"""
    stage = int(getattr(pokemon, "movement_speed_stage", 0))
    weather = get_effective_weather(pokemon, game)
    p_types = getattr(pokemon, "types", pokemon.species_data.get("types", []))

    if weather == "Blizzard" and "Ice" in p_types:
        stage += 1
    elif weather == "Strong Winds" and "Flying" in p_types:
        stage += 1

    if weather == "Electric Terrain" and has_ability(pokemon, "Surge Surfer", game=game):
        stage += 1
    if weather == "Sandstorm" and has_ability(pokemon, "Sand Rush", game=game):
        stage += 1
    if has_ability(pokemon, "Swift Swim", game=game):
        if weather == "Rain":
            stage += 1
        elif weather in ("Heavy Rain", "Thunderstorm"):
            stage += 2
    if has_ability(pokemon, "Slush Rush", game=game):
        if weather in ("Snow", "Hail"):
            stage += 1
        elif weather == "Blizzard":
            stage += 2
    if has_any_major_status(pokemon) and has_ability(pokemon, "Quick Feet", game=game):
        stage += 1
    from iq_skills import has_iq_skill
    if has_iq_skill(pokemon, "Time Tripper", game=game):
        stage += 1

    return min(3, max(-1, stage))


def is_immune_to_status_by_ability(pokemon, status: str, game=None, attacker=None) -> bool:
    """Returns True if an ability grants immunity to the given status condition"""
    if pokemon is None:
        return False

    if status == "Stuck" and has_ability(pokemon, "Run Away", game=game, attacker=attacker):
        return True
    if status == "Flinch" and has_ability(pokemon, "Inner Focus", game=game, attacker=attacker):
        return True
    if status in ("Paralysis", "Paralyzed") and has_ability(pokemon, "Limber", game=game, attacker=attacker):
        return True
    if status in ("Sleep", "Resting") and has_ability(pokemon, "Insomnia", game=game, attacker=attacker):
        return True
    if status in ("Infatuated", "Taunted") and has_ability(pokemon, "Oblivious", game=game, attacker=attacker):
        return True
    if status in ("Confusion", "Confused") and has_ability(pokemon, "Own Tempo", game=game, attacker=attacker):
        return True
    if status in ("Poison", "Toxic", "Toxic Poison"):
        if has_ability(pokemon, "Immunity", game=game, attacker=attacker):
            return True
        if any_side_has_ability(pokemon, "Pastel Veil", game=game, attacker=attacker):
            return True
    if status == "Burn" and any_side_has_ability(pokemon, "Water Veil", game=game, attacker=attacker):
        return True
    if status == "Frozen" and has_ability(pokemon, "Magma Armor", game=game, attacker=attacker):
        return True

    eff_weather = get_effective_weather(pokemon, game)
    leaf_guard_statuses = (
        "Poison", "Toxic", "Toxic Poison", "Burn", "Confusion", "Confused",
        "Sleep", "Resting", "Paralysis", "Paralyzed"
    )
    if eff_weather in ("Sunny", "Harsh Sunlight") and status in leaf_guard_statuses:
        if has_ability(pokemon, "Leaf Guard", game=game, attacker=attacker):
            return True

    hydration_statuses = (
        "Poison", "Toxic", "Toxic Poison", "Burn", "Paralysis", "Paralyzed",
        "Sleep", "Resting", "Confusion", "Confused", "Frozen"
    )
    if eff_weather in ("Rain", "Heavy Rain", "Thunderstorm") and status in hydration_statuses:
        if has_ability(pokemon, "Hydration", game=game, attacker=attacker):
            return True

    return False


def is_immune_to_intimidate(pokemon, game=None) -> bool:
    """Returns True if pokemon cannot have Attack lowered by Intimidate"""
    return (
        has_ability(pokemon, "Inner Focus", game=game)
        or has_ability(pokemon, "Oblivious", game=game)
        or has_ability(pokemon, "Scrappy", game=game)
        or has_ability(pokemon, "Clear Body", game=game)
        or has_ability(pokemon, "Hyper Cutter", game=game)
    )


def has_adjacent_enemy_with_ability(pokemon, ability_name: str, game=None) -> bool:
    """Returns True if any living enemy within 1 tile has ability_name active"""
    if game is None or pokemon is None:
        return False
    from targeting import get_pokemon_position

    px, py = get_pokemon_position(game, pokemon)
    for foe in get_enemies_of(pokemon, game=game):
        fx, fy = get_pokemon_position(game, foe)
        if max(abs(fx - px), abs(fy - py)) <= 1:
            if has_ability(foe, ability_name, game=game):
                return True
    return False


def is_trapped_by_ability(pokemon, game=None) -> tuple[bool, str | None]:
    """Checks if an adjacent foe's Arena Trap, Shadow Tag, or Magnet Pull prevents movement"""
    if game is None or pokemon is None:
        return False, None
    from targeting import get_pokemon_position

    px, py = get_pokemon_position(game, pokemon)
    p_types = getattr(pokemon, "types", pokemon.species_data.get("types", []))
    has_run_away = has_ability(pokemon, "Run Away", game=game)
    has_levitate = has_ability(pokemon, "Levitate", game=game)

    for foe in get_enemies_of(pokemon, game=game):
        fx, fy = get_pokemon_position(game, foe)
        if max(abs(fx - px), abs(fy - py)) > 1:
            continue
        if has_ability(foe, "Arena Trap", game=game):
            if "Flying" not in p_types and "Ghost" not in p_types and not has_levitate and not has_run_away:
                return True, f"{foe.name}'s Arena Trap"
        if has_ability(foe, "Shadow Tag", game=game):
            if "Ghost" not in p_types and not has_run_away:
                return True, f"{foe.name}'s Shadow Tag"
        if has_ability(foe, "Magnet Pull", game=game):
            if "Steel" in p_types:
                return True, f"{foe.name}'s Magnet Pull"
    return False, None


def get_effective_weight(pokemon, game=None) -> float:
    """Returns pokemon's effective weight (used for Light Metal)"""
    weight = float(pokemon.species_data.get("weight", 10.0))
    if has_ability(pokemon, "Light Metal", game=game):
        weight *= 0.5
    return max(0.1, weight)


def is_powder_move(move: dict) -> bool:
    """Returns True if move is a powder or spore move. Powder Snow is explicitly ignored (lmao)"""
    m_name = str(move.get("name", "")).lower()
    if m_name == "powder snow":
        return False
    return "powder" in m_name or "spore" in m_name


def apply_hydration_check(pokemon, game=None) -> None:
    """Immediately cures qualifying status ailments if Hydration is active in Rain"""
    if pokemon is None or int(getattr(pokemon, "current_hp", 0)) <= 0:
        return
    if not has_ability(pokemon, "Hydration", game=game):
        return
    if get_effective_weather(pokemon, game) not in ("Rain", "Heavy Rain", "Thunderstorm"):
        return
    for st in ("Poison", "Toxic", "Burn", "Paralysis", "Sleep", "Resting", "Confusion", "Frozen"):
        val = pokemon.status_effects.get(st)
        if (isinstance(val, bool) and val) or (isinstance(val, (int, float)) and val > 0):
            pokemon.cure_status(st, game)


def is_sheer_force_effect(eff: dict) -> bool:
    """Returns True if an effect dict represents a secondary effect that interacts with Sheer Force"""
    if not isinstance(eff, dict):
        return False
    etype = eff.get("effect_type")
    target = eff.get("target", "defender")
    if etype in ("status", "status_apply", "status_condition", "tri_attack_effects"):
        if target == "attacker" and etype != "tri_attack_effects":
            return False
        return True
    if etype == "stat_change":
        stages = eff.get("stages", 0)
        if target == "attacker" and stages < 0:
            return False
        return True
    return False


def has_sheer_force_boosted_effect(move: dict) -> bool:
    """Returns True if a damaging move qualifies for Sheer Force's power boost"""
    if not isinstance(move, dict):
        return False
    if move.get("category") not in ("Physical", "Special"):
        return False
    if move.get("ohko") or move.get("name") in ("Explosion", "Self-Destruct", "Fissure", "Guillotine", "Horn Drill", "Sheer Cold"):
        return False
    return any(is_sheer_force_effect(eff) for eff in move.get("effects", []))


def is_reckless_move(move: dict) -> bool:
    """Returns True if move causes recoil/crash damage and qualifies for Reckless"""
    if not isinstance(move, dict):
        return False
    m_name = move.get("name", "")
    if m_name == "Struggle":
        return False
    if m_name in ("High Jump Kick", "Axe Kick", "Jump Kick", "Supercell Slam"):
        return True
    return any(eff.get("effect_type") == "recoil" for eff in move.get("effects", []))


def resolve_move_with_abilities(attacker, move: dict, game=None) -> dict:
    """Returns effective move dict after attacker type-changing abilities (e.g., Galvanize)"""
    if not isinstance(move, dict) or attacker is None:
        return move
    eff_weather = get_effective_weather(attacker, game)
    if eff_weather == "Shadowy Aura":
        return move
    if move.get("type") == "Normal" and not move.get("_galvanized") and has_ability(attacker, "Galvanize", game=game):
        new_move = dict(move)
        new_move["type"] = "Electric"
        new_move["_galvanized"] = True
        if new_move.get("category") in ("Physical", "Special") and new_move.get("power"):
            new_move["power"] = float(new_move["power"]) * 1.2
        return new_move
    return move
