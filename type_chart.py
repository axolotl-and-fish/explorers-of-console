"""
type_chart.py

This is where the infamous Pokémon type chart is defined. Oooh, scary!
This part of the code also deals with the damage multipliers for type effectiveness.
Again, the +/- 25% modifier for each type matchup is for game balance reasons.
Written by C437RP13
"""

from pokemon_db import VALID_TYPES

#Matchup score values:
#+1.0 = Super effective (1.25x)
#-1.0 = Not very effective (0.75x)
#None = Immune (0.25x)
#Neutral matchups are omitted and default to 0.0

MATCHUP_RATINGS: dict[str, dict[str, float | None]] = {
    "Normal": {
        "Rock": -1.0,
        "Steel": -1.0,
        "Ghost": None,
    },
    "Fire": {
        "Grass": 1.0,
        "Ice": 1.0,
        "Bug": 1.0,
        "Steel": 1.0,
        "Fire": -1.0,
        "Water": -1.0,
        "Rock": -1.0,
        "Dragon": -1.0,
    },
    "Water": {
        "Fire": 1.0,
        "Ground": 1.0,
        "Rock": 1.0,
        "Water": -1.0,
        "Grass": -1.0,
        "Dragon": -1.0,
    },
    "Grass": {
        "Water": 1.0,
        "Ground": 1.0,
        "Rock": 1.0,
        "Fire": -1.0,
        "Grass": -1.0,
        "Poison": -1.0,
        "Flying": -1.0,
        "Bug": -1.0,
        "Dragon": -1.0,
        "Steel": -1.0,
    },
    "Electric": {
        "Water": 1.0,
        "Flying": 1.0,
        "Grass": -1.0,
        "Electric": -1.0,
        "Dragon": -1.0,
        "Ground": None,
    },
    "Ice": {
        "Grass": 1.0,
        "Ground": 1.0,
        "Flying": 1.0,
        "Dragon": 1.0,
        "Fire": -1.0,
        "Water": -1.0,
        "Ice": -1.0,
        "Steel": -1.0,
    },
    "Fighting": {
        "Normal": 1.0,
        "Ice": 1.0,
        "Rock": 1.0,
        "Dark": 1.0,
        "Steel": 1.0,
        "Poison": -1.0,
        "Flying": -1.0,
        "Psychic": -1.0,
        "Bug": -1.0,
        "Fairy": -1.0,
        "Ghost": None,
    },
    "Poison": {
        "Grass": 1.0,
        "Fairy": 1.0,
        "Poison": -1.0,
        "Ground": -1.0,
        "Rock": -1.0,
        "Ghost": -1.0,
        "Steel": None,
    },
    "Ground": {
        "Fire": 1.0,
        "Electric": 1.0,
        "Poison": 1.0,
        "Rock": 1.0,
        "Steel": 1.0,
        "Grass": -1.0,
        "Bug": -1.0,
        "Flying": None,
    },
    "Flying": {
        "Grass": 1.0,
        "Fighting": 1.0,
        "Bug": 1.0,
        "Electric": -1.0,
        "Rock": -1.0,
        "Steel": -1.0,
    },
    "Psychic": {
        "Fighting": 1.0,
        "Poison": 1.0,
        "Psychic": -1.0,
        "Steel": -1.0,
        "Dark": None,
    },
    "Bug": {
        "Grass": 1.0,
        "Psychic": 1.0,
        "Dark": 1.0,
        "Fire": -1.0,
        "Fighting": -1.0,
        "Poison": -1.0,
        "Flying": -1.0,
        "Ghost": -1.0,
        "Steel": -1.0,
        "Fairy": -1.0,
    },
    "Rock": {
        "Fire": 1.0,
        "Ice": 1.0,
        "Flying": 1.0,
        "Bug": 1.0,
        "Fighting": -1.0,
        "Ground": -1.0,
        "Steel": -1.0,
    },
    "Ghost": {
        "Psychic": 1.0,
        "Ghost": 1.0,
        "Dark": -1.0,
        "Normal": None,
    },
    "Dragon": {
        "Dragon": 1.0,
        "Steel": -1.0,
        "Fairy": None,
    },
    "Steel": {
        "Ice": 1.0,
        "Rock": 1.0,
        "Fairy": 1.0,
        "Fire": -1.0,
        "Water": -1.0,
        "Electric": -1.0,
        "Steel": -1.0,
    },
    "Dark": {
        "Psychic": 1.0,
        "Ghost": 1.0,
        "Fighting": -1.0,
        "Dark": -1.0,
        "Fairy": -1.0,
    },
    "Fairy": {
        "Fighting": 1.0,
        "Dragon": 1.0,
        "Dark": 1.0,
        "Fire": -1.0,
        "Poison": -1.0,
        "Steel": -1.0,
    },
}


def get_effectiveness_multiplier(move_type: str, target_types: list[str]) -> float:
    """Calculates the damage effectiveness multiplier of move_type against target_types.

    Multipliers:
        Triply super effective (score +3) = 1.75 [only possible with combined-type moves and dual-typed Pokémon]
        Doubly super effective (score +2) = 1.50
        Super effective (score +1) = 1.25
        Neutral (score 0) = 1.00
        Not very effective (score -1) = 0.75
        Doubly not very effective (score -2) = 0.50
        Triply not very effective (score -3) = 0.25 [only possible with combined-type moves and dual-typed Pokémon]
        "Immune" = 0.25
    """
    if move_type == "Freeze-Dry":
        mult = 1.0
        ice_map = {
            "Grass": 2.0, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0, "Water": 2.0,
            "Fire": 0.5, "Ice": 0.5, "Steel": 0.5
        }
        for t in target_types:
            mult *= ice_map.get(t, 1.0)
        return mult

    if move_type == "Muddy Water":
        component_types = ["Water", "Ground"]
    elif move_type in ("Tri Attack", "Unique"):
        component_types = ["Fire", "Electric", "Ice"]
    else:
        component_types = [move_type]

    for comp in component_types:
        if comp not in ("Muddy Water", "Tri Attack", "Unique", "Freeze-Dry") and comp not in VALID_TYPES:
            raise ValueError(f"Invalid move type: {comp}")

    if not target_types:
        raise ValueError("Target must have at least one type.")

    for t in target_types:
        if t not in VALID_TYPES:
            raise ValueError(f"Invalid target type: {t}")

    if len(component_types) == 1 and component_types[0] == "typeless":
        return 1.0

    #Check for immunity first. Immunity overrides every other type matchup
    for comp in component_types:
        if comp in ("Muddy Water", "Tri Attack", "Unique", "Freeze-Dry"):
            continue
        for target_type in target_types:
            if target_type == "typeless":
                continue
            move_ratings: dict[str, float | None] = MATCHUP_RATINGS.get(comp, {})
            if target_type in move_ratings and move_ratings[target_type] is None:
                return 0.25

    #Check explicit component immunities for multi-component moves
    if "Ground" in component_types and "Flying" in target_types:
        return 0.25
    if "Electric" in component_types and "Ground" in target_types:
        return 0.25

    total_score = 0.0

    effective_comps: list[str] = []
    for comp in component_types:
        if comp == "Muddy Water":
            effective_comps.extend(["Water", "Ground"])
        elif comp in ("Tri Attack", "Unique"):
            effective_comps.extend(["Fire", "Electric", "Ice"])
        else:
            effective_comps.append(comp)

    for comp in effective_comps:
        if comp == "Freeze-Dry":
            comp_ratings: dict[str, float | None] = dict(MATCHUP_RATINGS["Ice"])
            comp_ratings["Water"] = 1.0
        else:
            comp_ratings = MATCHUP_RATINGS.get(comp, {})

        for target_type in target_types:
            if target_type == "typeless":
                continue
            if target_type in comp_ratings:
                rating = comp_ratings[target_type]
                if rating is not None:
                    total_score += rating

    #Map total rating score to multipliers
    if total_score >= 3.0:
        return 1.75
    elif total_score == 2.0:
        return 1.50
    elif total_score == 1.0:
        return 1.25
    elif total_score == 0.0:
        return 1.00
    elif total_score == -1.0:
        return 0.75
    elif total_score == -2.0:
        return 0.50
    else:  #<=-3.0
        return 0.25


def get_type_effectiveness(move_type: str, target_types: list[str]) -> float:
    """Returns effectiveness multiplier for a single move type against defender types."""
    return get_effectiveness_multiplier(move_type, target_types)

