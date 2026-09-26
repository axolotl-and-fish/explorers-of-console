"""
natures.py

Defines Pokémon natures, their stat modifiers, and helper utilities.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

#Dictionary mapping each nature to a tuple of (increased_stat, decreased_stat).
NATURES: dict[str, tuple[str | None, str | None]] = {
    # Attack increased
    "Lonely": ("Attack", "Defense"),
    "Brave": ("Attack", "Speed"),
    "Adamant": ("Attack", "Special_Attack"),
    "Naughty": ("Attack", "Special_Defense"),
    # Defense increased
    "Bold": ("Defense", "Attack"),
    "Relaxed": ("Defense", "Speed"),
    "Impish": ("Defense", "Special_Attack"),
    "Lax": ("Defense", "Special_Defense"),
    # Speed increased
    "Timid": ("Speed", "Attack"),
    "Hasty": ("Speed", "Defense"),
    "Jolly": ("Speed", "Special_Attack"),
    "Naive": ("Speed", "Special_Defense"),
    # Special Attack increased
    "Modest": ("Special_Attack", "Attack"),
    "Mild": ("Special_Attack", "Defense"),
    "Quiet": ("Special_Attack", "Speed"),
    "Rash": ("Special_Attack", "Special_Defense"),
    # Special Defense increased
    "Calm": ("Special_Defense", "Attack"),
    "Gentle": ("Special_Defense", "Defense"),
    "Sassy": ("Special_Defense", "Speed"),
    "Careful": ("Special_Defense", "Special_Attack"),
    # Neutral natures (no stat changes)
    "Hardy": (None, None),
    "Docile": (None, None),
    "Bashful": (None, None),
    "Quirky": (None, None),
    "Serious": (None, None),
}

NATURE_NAMES: list[str] = list(NATURES.keys())


def get_nature_stat_multiplier(nature: str | None, stat_name: str) -> float:
    """Returns the stat multiplier applied by a nature."""
    if not nature or nature not in NATURES:
        return 1.0
    increased_stat, decreased_stat = NATURES[nature]
    if stat_name == increased_stat:
        return 1.1
    if stat_name == decreased_stat:
        return 0.9
    return 1.0
