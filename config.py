"""
config.py

This file handles the game's configuration options and handles the saving and loading of settings to/from disk.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import re

DEFAULT_CONFIG: dict[str, str] = {
    "suppress_more_prompts": "No",
    "move_animations": "1.0x",
    "weather_animations": "On",
    "other_animations": "On",
    "damage_popups": "All",
    "party_window_flashing": "On",
    "compatibility_mode": "Off",
}

VALID_OPTIONS: dict[str, list[str]] = {
    "suppress_more_prompts": ["Yes", "Some", "No"],
    "move_animations": ["0.5x", "1.0x", "1.5x", "2.0x", "Off"],
    "weather_animations": ["On", "Off"],
    "other_animations": ["On", "Off"],
    "damage_popups": ["All", "Some", "Damage Only", "Off"],
    "party_window_flashing": ["On", "Off"],
    "compatibility_mode": ["On", "Off"],
}

OPTION_KEYS: list[str] = [
    "suppress_more_prompts",
    "move_animations",
    "weather_animations",
    "other_animations",
    "damage_popups",
    "party_window_flashing",
    "compatibility_mode",
]

OPTION_DISPLAY_NAMES: dict[str, str] = {
    "suppress_more_prompts": "Suppress [MORE] Prompts",
    "move_animations": "Move Animations",
    "weather_animations": "Weather Animations",
    "other_animations": "Other Animations",
    "damage_popups": "Damage Pop-ups",
    "party_window_flashing": "Party Window Flashing",
    "compatibility_mode": "Compatibility Mode",
}

OPTION_LABELS = OPTION_DISPLAY_NAMES

OPTION_DESCRIPTIONS: dict[str, list[str]] = {
    "suppress_more_prompts": [
        "Controls display of [MORE] prompts in the message log.",
        "Yes: Almost all [MORE] prompts are skipped.",
        "Some: Skips some [MORE] prompts but will still display",
        "prompts for important messages."
    ],
    "move_animations": [
        "Sets the playback speed of move animations.",
        "Higher speeds play faster (0.5x, 1.0x, 1.5x, 2.0x).",
        "Off: Move animations are skipped entirely."
    ],
    "weather_animations": [
        "Toggles animations related to the weather."
    ],
    "other_animations": [
        "Toggles animations for explosions and thrown items."
    ],
    "damage_popups": [
        "Controls which floating damage numbers and pop-ups appear.",
        "All: All types of pop-ups are displayed.",
        "Some: Only displays EXP popups and damage popups.",
        "Damage Only: Only displays damage popups."
    ],
    "party_window_flashing": [
        "Toggles flashing warning frames around party member windows.",
        "Windows will flash when HP is critically low (<20%) or if",
        "Belly is empty."
    ],
    "compatibility_mode": [
        "Toggles compatibility mode, which removes all ANSI colors",
        "and formatting. Only recommended for terminals with limited",
        "ANSI support. You should really just use a different terminal!"
    ],
}


def get_config_filepath() -> str:
    """Returns the absolute path to save_data/CONFIG."""
    from save_game import get_save_dir
    save_dir = get_save_dir()
    return os.path.join(save_dir, "CONFIG")


get_config_path = get_config_filepath


def _normalize_key(raw_key: str) -> str | None:
    """Maps various possible user key strings to the canonical config key."""
    cleaned = re.sub(r"[^a-z0-9]", "", raw_key.lower())
    for key in OPTION_KEYS:
        canonical_cleaned = re.sub(r"[^a-z0-9]", "", key.lower())
        if cleaned == canonical_cleaned:
            return key
    return None


def _normalize_value(key: str, raw_val: str) -> str | None:
    """Matches a user value string case-insensitively against valid options for key."""
    allowed = VALID_OPTIONS.get(key, [])
    cleaned = raw_val.strip().lower()
    # Support common aliases
    if key in ("weather_animations", "other_animations", "party_window_flashing", "compatibility_mode"):
        if cleaned in ("true", "1", "yes", "y", "enable", "enabled", "on"):
            cleaned = "on"
        elif cleaned in ("false", "0", "no", "n", "disable", "disabled", "off"):
            cleaned = "off"

    for opt in allowed:
        if cleaned == opt.lower():
            return opt
    return None


def load_config(filepath: str | None = None) -> dict[str, str]:
    """Loads and validates the options configuration from save_data/CONFIG. If the CONFIG file isn't present, it is created by this function
    
    Since the user can easily modify this file outside the game (and potentially do naughty things), this function also validates all of the options here and resets them to their defaults if any are set to invalid values.
    """
    if filepath is None:
        filepath = get_config_filepath()

    config = dict(DEFAULT_CONFIG)
    needs_rewrite = False

    if not os.path.exists(filepath):
        save_config(config, filepath)
        return config

    raw_text = ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except Exception:
        #If unreadable, recreate with defaults
        save_config(config, filepath)
        return config

    found_keys: set[str] = set()

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        sep = "=" if "=" in line else (":" if ":" in line else None)
        if sep is None:
            needs_rewrite = True
            continue

        raw_k, raw_v = line.split(sep, 1)
        k = _normalize_key(raw_k.strip())
        if not k:
            needs_rewrite = True
            continue

        v = _normalize_value(k, raw_v.strip())
        if v is None:
            #Value is invalid, reset it to its default!
            needs_rewrite = True
            config[k] = DEFAULT_CONFIG[k]
        else:
            config[k] = v
        found_keys.add(k)

    #Check for missing keys
    for k in OPTION_KEYS:
        if k not in found_keys:
            needs_rewrite = True
            config[k] = DEFAULT_CONFIG[k]

    if needs_rewrite:
        save_config(config, filepath)

    return config


def save_config(config: dict[str, str], filepath: str | None = None) -> None:
    """Writes configuration to save_data/CONFIG in plain."""
    if filepath is None:
        filepath = get_config_filepath()

    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    lines = [
        "# Explorers of the Console Configuration File",
        "#",
        "# Available options:",
        "#   suppress_more_prompts: Yes, Some, No (default: No)",
        "#   move_animations: 0.5x, 1.0x, 1.5x, 2.0x, Off (default: 1.0x)",
        "#   weather_animations: On, Off (default: On)",
        "#   other_animations: On, Off (default: On)",
        "#   damage_popups: All, Some, Damage Only, Off (default: All)",
        "#   party_window_flashing: On, Off (default: On)",
        "#   compatibility_mode: On, Off (default: Off)",
        "",
    ]

    for k in OPTION_KEYS:
        val = config.get(k, DEFAULT_CONFIG[k])
        #Validate before writing
        norm_v = _normalize_value(k, str(val))
        if norm_v is None:
            norm_v = DEFAULT_CONFIG[k]
        lines.append(f"{k} = {norm_v}")

    lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def cycle_option(key: str, current_value: str, forward: bool = True) -> str:
    """Cycles an option value to the next or previous valid value."""
    options = VALID_OPTIONS.get(key, [])
    if not options:
        return current_value

    try:
        idx = options.index(current_value)
    except ValueError:
        idx = 0

    if forward:
        next_idx = (idx + 1) % len(options)
    else:
        next_idx = (idx - 1) % len(options)

    return options[next_idx]
