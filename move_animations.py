"""
move_animations.py

Defines visual animations for moves executed by Pokémon.
Programming this was an absolute pain in the rear. Hope it was worth it!
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pokemon import Pokemon

#Defines the 16 ANSI colors
ANSI_RESET = "\033[0m"

COLOR_BLACK = "\033[30m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_MAGENTA = "\033[35m"
COLOR_WHITE = "\033[37m"

COLOR_BRIGHT_BLACK = "\033[90m"
COLOR_BRIGHT_RED = "\033[91m"
COLOR_BRIGHT_GREEN = "\033[92m"
COLOR_BRIGHT_YELLOW = "\033[93m"
COLOR_BRIGHT_BLUE = "\033[94m"
COLOR_BRIGHT_MAGENTA = "\033[95m"
COLOR_BRIGHT_CYAN = "\033[96m"
COLOR_BRIGHT_WHITE = "\033[97m"

VALID_16_COLORS: set[str] = {
    COLOR_BLACK,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_BLUE,
    COLOR_MAGENTA,
    COLOR_CYAN := "\033[36m",
    COLOR_WHITE,
    COLOR_BRIGHT_BLACK,
    COLOR_BRIGHT_RED,
    COLOR_BRIGHT_GREEN,
    COLOR_BRIGHT_YELLOW,
    COLOR_BRIGHT_BLUE,
    COLOR_BRIGHT_MAGENTA,
    COLOR_BRIGHT_CYAN,
    COLOR_BRIGHT_WHITE,
}

#Type to fallback color map
TYPE_COLOR_MAP: dict[str, str] = {
    "Normal": COLOR_BRIGHT_WHITE,
    "Fire": COLOR_BRIGHT_RED,
    "Water": COLOR_BRIGHT_BLUE,
    "Electric": COLOR_BRIGHT_YELLOW,
    "Grass": COLOR_BRIGHT_GREEN,
    "Ice": COLOR_BRIGHT_CYAN,
    "Fighting": COLOR_RED,
    "Poison": COLOR_MAGENTA,
    "Ground": COLOR_YELLOW,
    "Flying": COLOR_BRIGHT_CYAN,
    "Psychic": COLOR_BRIGHT_MAGENTA,
    "Bug": COLOR_BRIGHT_GREEN,
    "Rock": COLOR_YELLOW,
    "Ghost": COLOR_MAGENTA,
    "Dragon": COLOR_BRIGHT_BLUE,
    "Dark": COLOR_BRIGHT_BLACK,
    "Steel": COLOR_WHITE,
    "Fairy": COLOR_BRIGHT_MAGENTA,
    "typeless": COLOR_WHITE,
    "Unique": COLOR_BRIGHT_BLUE,
}

#All valid CP437 Characters
_CP437_VALID_CHARS: set[str] = set()
_CP437_IBM_GLYPHS: dict[str, str] = {
    "\x00": " ", "\x01": "☺", "\x02": "☻", "\x03": "♥", "\x04": "♦", "\x05": "♣", "\x06": "♠",
    "\x07": "•", "\x08": "◘", "\x09": "○", "\x0a": "◙", "\x0b": "♂", "\x0c": "♀", "\x0d": "♪",
    "\x0e": "♫", "\x0f": "☼", "\x10": "►", "\x11": "◄", "\x12": "↕", "\x13": "‼", "\x14": "¶",
    "\x15": "§", "\x16": "▬", "\x17": "↨", "\x18": "↑", "\x19": "↓", "\x1a": "→", "\x1b": "←",
    "\x1c": "∟", "\x1d": "↔", "\x1e": "▲", "\x1f": "▼", "\x7f": "⌂",
}
for _b in range(256):
    try:
        _raw = bytes([_b]).decode("cp437")
        _CP437_VALID_CHARS.add(_raw)
        if _raw in _CP437_IBM_GLYPHS:
            _CP437_VALID_CHARS.add(_CP437_IBM_GLYPHS[_raw])
    except Exception:
        pass


def is_cp437_char(char: str) -> bool:
    """Checks whether a character belongs to the Code Page 437 character set. Used for debugging"""
    return char in _CP437_VALID_CHARS


@dataclass
class MoveAnimationFrame:
    """Represents a single frame of a visual move animation.

    Attributes:
        overlays: Dict mapping (x, y) coordinates to rendered ANSI character strings.
        delay: Sleep delay in seconds for this frame.
        shake: Screen shake magnitude (0 = none, 1 = slight, 2 = heavy).
    """

    overlays: dict[tuple[int, int], str]
    delay: float = 0.035
    shake: int = 0

# ------------------------------------
# Geometry and Ray Calculation Helpers
# ------------------------------------

def clamp_to_floor(floor: Any, x: int, y: int) -> bool:
    """Returns True if (x, y) is within floor boundaries."""
    if floor is None:
        return False
    w = getattr(floor, "width", 56)
    h = getattr(floor, "height", 32)
    return 0 <= x < w and 0 <= y < h


def get_line_tiles(
    x0: int, y0: int, x1: int, y1: int, floor: Any = None, stop_at_wall: bool = True
) -> list[tuple[int, int]]:
    """Computes straight line coordinates from (x0, y0) to (x1, y1) using Bresenham's algorithm, excluding the starting point (x0, y0)"""
    tiles: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    curr_x, curr_y = x0, y0

    while True:
        if (curr_x, curr_y) == (x1, y1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

        if floor is not None:
            if not clamp_to_floor(floor, curr_x, curr_y):
                break
            if stop_at_wall and getattr(floor, "grid", None):
                if floor.grid[curr_y][curr_x] == "#":
                    tiles.append((curr_x, curr_y))
                    break

        tiles.append((curr_x, curr_y))

    return tiles


def get_facing_ray_tiles(
    floor: Any, ax: int, ay: int, dx: int, dy: int, max_len: int = 4, stop_at_wall: bool = True
) -> list[tuple[int, int]]:
    """Generates ray tiles extending from (ax, ay) in direction (dx, dy)"""
    tiles: list[tuple[int, int]] = []
    if dx == 0 and dy == 0:
        return tiles

    for step in range(1, max_len + 1):
        nx = ax + step * dx
        ny = ay + step * dy
        if floor is not None:
            if not clamp_to_floor(floor, nx, ny):
                break
            if stop_at_wall and getattr(floor, "grid", None):
                if floor.grid[ny][nx] == "#":
                    tiles.append((nx, ny))
                    break
        tiles.append((nx, ny))

    return tiles


def get_pokemon_pos(game: Any, poke: Pokemon) -> tuple[int, int]:
    """Retrieves (x, y) coordinates for a given Pokémon."""
    if poke is getattr(game, "player_pokemon", None):
        return getattr(game, "player_x", 0), getattr(game, "player_y", 0)
    return getattr(poke, "x", 0), getattr(poke, "y", 0)


def get_facing_vector(game: Any, attacker: Pokemon, target_poke: Pokemon | None = None) -> tuple[int, int]:
    """Determines (dx, dy) direction vector from attacker towards target or attacker facing."""
    ax, ay = get_pokemon_pos(game, attacker)
    if target_poke is not None:
        tx, ty = get_pokemon_pos(game, target_poke)
        if (tx, ty) != (ax, ay):
            dx = 1 if tx > ax else (-1 if tx < ax else 0)
            dy = 1 if ty > ay else (-1 if ty < ay else 0)
            return dx, dy

    if attacker is getattr(game, "player_pokemon", None):
        return getattr(game, "player_facing", (0, 1))

    facing = getattr(attacker, "facing", None)
    if facing and isinstance(facing, (tuple, list)) and len(facing) == 2 and (facing[0] != 0 or facing[1] != 0):
        return facing[0], facing[1]

    return 0, 1


# -----------------------------
# Frame Builders for Categories
# -----------------------------

def _build_projectile_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for a projectile flying from attacker towards the target(s)"""
    frames: list[MoveAnimationFrame] = []
    ax, ay = get_pokemon_pos(game, attacker)
    target_poke = targets[0] if targets else None

    dx, dy = get_facing_vector(game, attacker, target_poke)

    if target_poke is not None:
        tx, ty = get_pokemon_pos(game, target_poke)
        path = get_line_tiles(ax, ay, tx, ty, floor=game.floor, stop_at_wall=True)
    else:
        max_dist = 4
        range_str = move.get("range", "")
        if "2 tiles" in range_str:
            max_dist = 2
        elif "3 tiles" in range_str:
            max_dist = 3
        path = get_facing_ray_tiles(game.floor, ax, ay, dx, dy, max_len=max_dist, stop_at_wall=True)

    if not path:
        path = [(ax + dx, ay + dy)] if clamp_to_floor(game.floor, ax + dx, ay + dy) else []

    if not path:
        return frames

    flight_chars = cfg.get("char", "•")
    if isinstance(flight_chars, str):
        flight_chars = [flight_chars]
    color = cfg.get("color", COLOR_BRIGHT_WHITE)
    trail_char = cfg.get("trail_char", "·")
    trail_color = cfg.get("trail_color", COLOR_BRIGHT_BLACK)
    impact_char = cfg.get("impact_char", "*")
    impact_color = cfg.get("impact_color", COLOR_BRIGHT_YELLOW)
    power = move.get("power") or 50

    #Flight frames
    prev_tile: tuple[int, int] | None = None
    for idx, (px, py) in enumerate(path):
        if not clamp_to_floor(game.floor, px, py):
            continue
        overlays: dict[tuple[int, int], str] = {}
        if prev_tile is not None and clamp_to_floor(game.floor, prev_tile[0], prev_tile[1]):
            overlays[prev_tile] = f"{trail_color}{trail_char}{ANSI_RESET}"

        char = flight_chars[idx % len(flight_chars)]
        #Directional adjustment for arrows
        if char == "ARROW":
            if dx > 0 and dy == 0:
                char = "►"
            elif dx < 0 and dy == 0:
                char = "◄"
            elif dy < 0:
                char = "▲"
            elif dy > 0:
                char = "▼"
            else:
                char = "•"

        overlays[(px, py)] = f"{color}{char}{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=overlays, delay=0.03))
        prev_tile = (px, py)

    #Impact burst on final tile
    last_x, last_y = path[-1]
    impact_overlays: dict[tuple[int, int], str] = {}
    if clamp_to_floor(game.floor, last_x, last_y):
        impact_overlays[(last_x, last_y)] = f"{impact_color}{impact_char}{ANSI_RESET}"

    #Power scaling: larger blast for power >= 90
    if power >= 90:
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cx, cy = last_x + ox, last_y + oy
            if clamp_to_floor(game.floor, cx, cy) and game.floor.grid[cy][cx] != "#":
                impact_overlays[(cx, cy)] = f"{color}·{ANSI_RESET}"
        shake = 1 if power >= 120 else 0
        frames.append(MoveAnimationFrame(overlays=impact_overlays, delay=0.04, shake=shake))
        #Dissipation frame
        fade_overlays: dict[tuple[int, int], str] = {}
        if clamp_to_floor(game.floor, last_x, last_y):
            fade_overlays[(last_x, last_y)] = f"{impact_color}+{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=fade_overlays, delay=0.03))
    else:
        frames.append(MoveAnimationFrame(overlays=impact_overlays, delay=0.04))

    return frames


def _build_beam_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for a continuous piercing beam/ray"""
    frames: list[MoveAnimationFrame] = []
    ax, ay = get_pokemon_pos(game, attacker)
    target_poke = targets[0] if targets else None

    dx, dy = get_facing_vector(game, attacker, target_poke)
    if dx == 0 and dy == 0:
        dx, dy = 1, 0

    max_dist = cfg.get("max_range", 6)
    ray_tiles = get_facing_ray_tiles(game.floor, ax, ay, dx, dy, max_len=max_dist, stop_at_wall=True)
    if not ray_tiles:
        return frames

    color = cfg.get("color", COLOR_BRIGHT_WHITE)
    core_char = cfg.get("core_char", "█")
    core_color = cfg.get("core_color", COLOR_BRIGHT_YELLOW)
    power = move.get("power") or 80

    #Directional glyphs
    if dy == 0:
        beam_char = cfg.get("horiz_char", "═")
    elif dx == 0:
        beam_char = cfg.get("vert_char", "║")
    elif dx * dy > 0:
        beam_char = cfg.get("diag1_char", "\\")
    else:
        beam_char = cfg.get("diag2_char", "/")

    #First frame: Beam charges up
    half_count = max(1, len(ray_tiles) // 2)
    f1_overlays: dict[tuple[int, int], str] = {}
    for tx, ty in ray_tiles[:half_count]:
        if clamp_to_floor(game.floor, tx, ty):
            f1_overlays[(tx, ty)] = f"{color}{beam_char}{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f1_overlays, delay=0.03))

    #Second frame: Unleash beam
    f2_overlays: dict[tuple[int, int], str] = {}
    for tx, ty in ray_tiles:
        if clamp_to_floor(game.floor, tx, ty):
            f2_overlays[(tx, ty)] = f"{color}{beam_char}{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f2_overlays, delay=0.04))

    #Third frame: Beam flies out
    f3_overlays: dict[tuple[int, int], str] = {}
    for tx, ty in ray_tiles:
        if clamp_to_floor(game.floor, tx, ty):
            f3_overlays[(tx, ty)] = f"{core_color}{core_char}{ANSI_RESET}"
    #Impact sparks on target pokemon
    for t in targets:
        px, py = get_pokemon_pos(game, t)
        if clamp_to_floor(game.floor, px, py):
            f3_overlays[(px, py)] = f"{COLOR_BRIGHT_WHITE}*{ANSI_RESET}"

    shake = cfg.get("shake", 0)
    if power >= 120 and shake == 0:
        shake = 1
    if power >= 150:
        shake = 2

    frames.append(MoveAnimationFrame(overlays=f3_overlays, delay=0.05, shake=shake))

    #Fourth frame: Beam dissipates
    f4_overlays: dict[tuple[int, int], str] = {}
    dissipate_char = cfg.get("dissipate_char", "░")
    for tx, ty in ray_tiles:
        if clamp_to_floor(game.floor, tx, ty):
            f4_overlays[(tx, ty)] = f"{color}{dissipate_char}{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f4_overlays, delay=0.03))

    return frames


def _build_room_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for room-wide or floor-wide wave moves"""
    frames: list[MoveAnimationFrame] = []
    ax, ay = get_pokemon_pos(game, attacker)

    from targeting import get_room_tiles_at
    room_tiles = get_room_tiles_at(game.floor, ax, ay)
    if not room_tiles:
        #Corridor fallback: 5x5 area around attacker
        room_tiles = {
            (ax + ox, ay + oy)
            for ox in range(-3, 4)
            for oy in range(-3, 4)
            if clamp_to_floor(game.floor, ax + ox, ay + oy) and game.floor.grid[ay + oy][ax + ox] != "#"
        }

    #Animations should be filtered within the floor boundaries
    valid_tiles = [
        (x, y)
        for (x, y) in room_tiles
        if clamp_to_floor(game.floor, x, y) and game.floor.grid[y][x] != "#"
    ]
    if not valid_tiles:
        return frames

    chars = cfg.get("chars", ["*", "•"])
    colors = cfg.get("colors", [COLOR_BRIGHT_WHITE])
    power = move.get("power") or 80
    base_shake = cfg.get("shake", 0)
    if power >= 100 and base_shake == 0:
        base_shake = 1

    #1st frame: Create wave around user (radius 1)
    f1_overlays: dict[tuple[int, int], str] = {}
    for x, y in valid_tiles:
        if max(abs(x - ax), abs(y - ay)) <= 1:
            ch = chars[0]
            col = colors[0]
            f1_overlays[(x, y)] = f"{col}{ch}{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f1_overlays, delay=0.04))

    #2nd frame: Expand to the full room
    f2_overlays: dict[tuple[int, int], str] = {}
    for idx, (x, y) in enumerate(valid_tiles):
        ch = chars[(idx + 1) % len(chars)]
        col = colors[(idx + 1) % len(colors)]
        f2_overlays[(x, y)] = f"{col}{ch}{ANSI_RESET}"
    #Attacker stays visually marked
    if clamp_to_floor(game.floor, ax, ay):
        f2_overlays[(ax, ay)] = f"{colors[0]}☼{ANSI_RESET}"

    frames.append(MoveAnimationFrame(overlays=f2_overlays, delay=0.06, shake=base_shake))

    #3rd frame: Impact target Pokémon, secondary pulse
    f3_overlays: dict[tuple[int, int], str] = {}
    for idx, (x, y) in enumerate(valid_tiles):
        if idx % 2 == 0:
            ch = chars[-1]
            col = colors[-1]
            f3_overlays[(x, y)] = f"{col}{ch}{ANSI_RESET}"
    for t in targets:
        px, py = get_pokemon_pos(game, t)
        if clamp_to_floor(game.floor, px, py):
            f3_overlays[(px, py)] = f"{COLOR_BRIGHT_WHITE}*{ANSI_RESET}"

    frames.append(MoveAnimationFrame(overlays=f3_overlays, delay=0.04))

    #4th frame: Disperse animation
    f4_overlays: dict[tuple[int, int], str] = {}
    for idx, (x, y) in enumerate(valid_tiles):
        if idx % 3 == 0:
            f4_overlays[(x, y)] = f"{colors[0]}·{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f4_overlays, delay=0.03))

    return frames


def _build_adjacent_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for attacks striking all adjacent tiles around attacker"""
    frames: list[MoveAnimationFrame] = []
    ax, ay = get_pokemon_pos(game, attacker)

    adjacent_tiles: list[tuple[int, int]] = []
    for ox in [-1, 0, 1]:
        for oy in [-1, 0, 1]:
            if ox == 0 and oy == 0:
                continue
            cx, cy = ax + ox, ay + oy
            if clamp_to_floor(game.floor, cx, cy) and game.floor.grid[cy][cx] != "#":
                adjacent_tiles.append((cx, cy))

    if not adjacent_tiles:
        return frames

    chars = cfg.get("chars", ["*", "+"])
    colors = cfg.get("colors", [COLOR_BRIGHT_YELLOW])
    power = move.get("power") or 70
    shake = cfg.get("shake", 0)
    if power >= 120 and shake == 0:
        shake = 1

    #1st frame: Gather energy at center
    f1_overlays: dict[tuple[int, int], str] = {}
    f1_overlays[(ax, ay)] = f"{colors[0]}*{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f1_overlays, delay=0.03))

    #2nd frame: Radial burst on all adjacent tiles
    f2_overlays: dict[tuple[int, int], str] = {}
    for idx, (cx, cy) in enumerate(adjacent_tiles):
        ch = chars[idx % len(chars)]
        col = colors[idx % len(colors)]
        f2_overlays[(cx, cy)] = f"{col}{ch}{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f2_overlays, delay=0.04, shake=shake))

    #3rd frame: Impact flash on defenders
    f3_overlays: dict[tuple[int, int], str] = {}
    for cx, cy in adjacent_tiles:
        f3_overlays[(cx, cy)] = f"{colors[-1]}·{ANSI_RESET}"
    for t in targets:
        px, py = get_pokemon_pos(game, t)
        if clamp_to_floor(game.floor, px, py):
            f3_overlays[(px, py)] = f"{COLOR_BRIGHT_WHITE}*{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f3_overlays, delay=0.03))

    return frames


def _build_aura_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for support, heal, shield, and stat buff/debuff auras."""
    frames: list[MoveAnimationFrame] = []
    aura_targets = targets if targets else [attacker]

    chars = cfg.get("chars", ["+", "*", "·"])
    colors = cfg.get("colors", [COLOR_BRIGHT_GREEN])

    #1st frame: Gathering sparkles around targets
    f1_overlays: dict[tuple[int, int], str] = {}
    for p in aura_targets:
        px, py = get_pokemon_pos(game, p)
        if clamp_to_floor(game.floor, px, py):
            f1_overlays[(px, py)] = f"{colors[0]}.{ANSI_RESET}"
        if clamp_to_floor(game.floor, px, py + 1) and game.floor.grid[py + 1][px] != "#":
            f1_overlays[(px, py + 1)] = f"{colors[0]}·{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f1_overlays, delay=0.04))

    #2nd frame: Radiant sparkle aura rising
    f2_overlays: dict[tuple[int, int], str] = {}
    for p in aura_targets:
        px, py = get_pokemon_pos(game, p)
        if clamp_to_floor(game.floor, px, py):
            ch = chars[1 % len(chars)]
            col = colors[1 % len(colors)]
            f2_overlays[(px, py)] = f"{col}{ch}{ANSI_RESET}"
        for ox, oy in [(-1, 0), (1, 0), (0, -1)]:
            cx, cy = px + ox, py + oy
            if clamp_to_floor(game.floor, cx, cy) and game.floor.grid[cy][cx] != "#":
                f2_overlays[(cx, cy)] = f"{colors[0]}·{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f2_overlays, delay=0.05))

    #3rd frame: Aura ascending and softly dissipating
    f3_overlays: dict[tuple[int, int], str] = {}
    for p in aura_targets:
        px, py = get_pokemon_pos(game, p)
        if clamp_to_floor(game.floor, px, py - 1) and game.floor.grid[py - 1][px] != "#":
            f3_overlays[(px, py - 1)] = f"{colors[0]}^{ANSI_RESET}"
        if clamp_to_floor(game.floor, px, py):
            f3_overlays[(px, py)] = f"{colors[-1]}·{ANSI_RESET}"
    frames.append(MoveAnimationFrame(overlays=f3_overlays, delay=0.03))

    return frames


def _build_contact_frames(
    game: Any, attacker: Pokemon, targets: list[Pokemon], move: dict, cfg: dict
) -> list[MoveAnimationFrame]:
    """Builds frames for select iconic melee moves (Slash, Bite, Punch)"""
    frames: list[MoveAnimationFrame] = []
    contact_type = cfg.get("contact_type", "slash")
    colors = cfg.get("colors", [COLOR_BRIGHT_WHITE])
    primary_color = colors[0]

    if not targets:
        ax, ay = get_pokemon_pos(game, attacker)
        dx, dy = get_facing_vector(game, attacker)
        target_coords = [(ax + dx, ay + dy)] if clamp_to_floor(game.floor, ax + dx, ay + dy) else []
    else:
        target_coords = [get_pokemon_pos(game, t) for t in targets]

    if not target_coords:
        return frames

    if contact_type == "slash":
        #1st frame: Forward slash
        f1: dict[tuple[int, int], str] = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f1[(tx, ty)] = f"{primary_color}/{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f1, delay=0.03))

        #2nd frame: Backslash creating cross X
        f2: dict[tuple[int, int], str] = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f2[(tx, ty)] = f"{primary_color}X{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f2, delay=0.04))

        #3rd frame: Slash spark
        f3: dict[tuple[int, int], str] = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f3[(tx, ty)] = f"{primary_color}*{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f3, delay=0.03))

    elif contact_type == "bite":
        #1st frame: Clamping jaws opening around target
        f1 = {}
        for tx, ty in target_coords:
            for ox, oy, ch in [(0, -1, "v"), (0, 1, "^"), (-1, 0, ">"), (1, 0, "<")]:
                cx, cy = tx + ox, ty + oy
                if clamp_to_floor(game.floor, cx, cy) and game.floor.grid[cy][cx] != "#":
                    f1[(cx, cy)] = f"{primary_color}{ch}{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f1, delay=0.03))

        #2nd frame: Jaws snap shut on target
        f2 = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f2[(tx, ty)] = f"{COLOR_BRIGHT_RED}X{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f2, delay=0.04))

        #3rd frame: Lingering bite mark (BRUTAL!)
        f3 = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f3[(tx, ty)] = f"{primary_color}*{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f3, delay=0.03))

    elif contact_type == "punch":
        #1st frame: Fist strike impact
        f1 = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f1[(tx, ty)] = f"{primary_color}■{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f1, delay=0.04))

        #2nd frame: Heavy shockwave flash
        f2 = {}
        for tx, ty in target_coords:
            if clamp_to_floor(game.floor, tx, ty):
                f2[(tx, ty)] = f"{primary_color}*{ANSI_RESET}"
            for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                cx, cy = tx + ox, ty + oy
                if clamp_to_floor(game.floor, cx, cy) and game.floor.grid[cy][cx] != "#":
                    f2[(cx, cy)] = f"{primary_color}·{ANSI_RESET}"
        frames.append(MoveAnimationFrame(overlays=f2, delay=0.03))

    return frames


# ------------------
# Animation Registry
# ------------------

ANIMATION_REGISTRY: dict[str, dict[str, Any]] = {
    #Projectiles
    "projectile": {
        "builder": _build_projectile_frames,
        "char": "•",
        "color": COLOR_BRIGHT_WHITE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "water_gun": {
        "builder": _build_projectile_frames,
        "char": "~",
        "color": COLOR_BRIGHT_BLUE,
        "trail_char": "·",
        "trail_color": COLOR_CYAN,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_CYAN,
    },
    "water_pulse": {
        "builder": _build_projectile_frames,
        "char": "○",
        "color": COLOR_BRIGHT_CYAN,
        "trail_char": "~",
        "trail_color": COLOR_BRIGHT_BLUE,
        "impact_char": "○",
        "impact_color": COLOR_BRIGHT_CYAN,
    },
    "bubble_beam": {
        "builder": _build_projectile_frames,
        "char": ["○", "o", "•"],
        "color": COLOR_BRIGHT_CYAN,
        "trail_char": "o",
        "trail_color": COLOR_BRIGHT_BLUE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "ember": {
        "builder": _build_projectile_frames,
        "char": "*",
        "color": COLOR_BRIGHT_RED,
        "trail_char": ".",
        "trail_color": COLOR_BRIGHT_YELLOW,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "pin_missile": {
        "builder": _build_projectile_frames,
        "char": "ARROW",
        "color": COLOR_BRIGHT_YELLOW,
        "trail_char": "-",
        "trail_color": COLOR_YELLOW,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "bullet_seed": {
        "builder": _build_projectile_frames,
        "char": "•",
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": ".",
        "trail_color": COLOR_GREEN,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_GREEN,
    },
    "energy_ball": {
        "builder": _build_projectile_frames,
        "char": "☼",
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": "•",
        "trail_color": COLOR_GREEN,
        "impact_char": "☼",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "shadow_ball": {
        "builder": _build_projectile_frames,
        "char": "◙",
        "color": COLOR_MAGENTA,
        "trail_char": "░",
        "trail_color": COLOR_BRIGHT_BLACK,
        "impact_char": "○",
        "impact_color": COLOR_BRIGHT_MAGENTA,
    },
    "sludge_bomb": {
        "builder": _build_projectile_frames,
        "char": "■",
        "color": COLOR_MAGENTA,
        "trail_char": "▒",
        "trail_color": COLOR_MAGENTA,
        "impact_char": "▓",
        "impact_color": COLOR_BRIGHT_MAGENTA,
    },
    "gunk_shot": {
        "builder": _build_projectile_frames,
        "char": "▓",
        "color": COLOR_MAGENTA,
        "trail_char": "▒",
        "trail_color": COLOR_MAGENTA,
        "impact_char": "█",
        "impact_color": COLOR_BRIGHT_MAGENTA,
    },
    "ice_shard": {
        "builder": _build_projectile_frames,
        "char": "ARROW",
        "color": COLOR_BRIGHT_CYAN,
        "trail_char": "*",
        "trail_color": COLOR_BRIGHT_BLUE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "bonemerang": {
        "builder": _build_projectile_frames,
        "char": ["/", "-", "\\", "|"],
        "color": COLOR_BRIGHT_YELLOW,
        "trail_char": "·",
        "trail_color": COLOR_YELLOW,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "swift": {
        "builder": _build_projectile_frames,
        "char": "*",
        "color": COLOR_BRIGHT_YELLOW,
        "trail_char": "·",
        "trail_color": COLOR_BRIGHT_WHITE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "quick_attack": {
        "builder": _build_projectile_frames,
        "char": "═",
        "color": COLOR_BRIGHT_WHITE,
        "trail_char": "·",
        "trail_color": COLOR_WHITE,
        "impact_char": "X",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "aqua_jet": {
        "builder": _build_projectile_frames,
        "char": "~",
        "color": COLOR_BRIGHT_BLUE,
        "trail_char": "~",
        "trail_color": COLOR_BRIGHT_CYAN,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_CYAN,
    },
    "extreme_speed": {
        "builder": _build_projectile_frames,
        "char": "═",
        "color": COLOR_BRIGHT_WHITE,
        "trail_char": "-",
        "trail_color": COLOR_BRIGHT_YELLOW,
        "impact_char": "X",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "vine_whip": {
        "builder": _build_projectile_frames,
        "char": "~",
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": "~",
        "trail_color": COLOR_GREEN,
        "impact_char": "!",
        "impact_color": COLOR_BRIGHT_GREEN,
    },
    "razor_leaf": {
        "builder": _build_projectile_frames,
        "char": ["*", "\\", "/"],
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": "·",
        "trail_color": COLOR_GREEN,
        "impact_char": "X",
        "impact_color": COLOR_BRIGHT_GREEN,
    },
    "seed_bomb": {
        "builder": _build_projectile_frames,
        "char": "○",
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": "•",
        "trail_color": COLOR_GREEN,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "leech_seed": {
        "builder": _build_projectile_frames,
        "char": "•",
        "color": COLOR_GREEN,
        "trail_char": "~",
        "trail_color": COLOR_GREEN,
        "impact_char": "~",
        "impact_color": COLOR_BRIGHT_GREEN,
    },
    "worry_seed": {
        "builder": _build_projectile_frames,
        "char": "•",
        "color": COLOR_BRIGHT_GREEN,
        "trail_char": ".",
        "trail_color": COLOR_GREEN,
        "impact_char": "?",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "strange_steam": {
        "builder": _build_projectile_frames,
        "char": ["~", "░"],
        "color": COLOR_BRIGHT_MAGENTA,
        "trail_char": "░",
        "trail_color": COLOR_MAGENTA,
        "impact_char": "▒",
        "impact_color": COLOR_BRIGHT_MAGENTA,
    },
    "freezing_glare": {
        "builder": _build_projectile_frames,
        "char": "◙",
        "color": COLOR_BRIGHT_CYAN,
        "trail_char": "☼",
        "trail_color": COLOR_BRIGHT_MAGENTA,
        "impact_char": "☼",
        "impact_color": COLOR_BRIGHT_CYAN,
    },
    "vacuum_wave": {
        "builder": _build_projectile_frames,
        "char": ")",
        "color": COLOR_BRIGHT_WHITE,
        "trail_char": "-",
        "trail_color": COLOR_WHITE,
        "impact_char": "X",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "bullet_punch": {
        "builder": _build_projectile_frames,
        "char": "■",
        "color": COLOR_BRIGHT_CYAN,
        "trail_char": "·",
        "trail_color": COLOR_WHITE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "mach_punch": {
        "builder": _build_projectile_frames,
        "char": "■",
        "color": COLOR_BRIGHT_RED,
        "trail_char": "·",
        "trail_color": COLOR_RED,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },
    "sucker_punch": {
        "builder": _build_projectile_frames,
        "char": "X",
        "color": COLOR_MAGENTA,
        "trail_char": "·",
        "trail_color": COLOR_BRIGHT_BLACK,
        "impact_char": "X",
        "impact_color": COLOR_BRIGHT_MAGENTA,
    },
    "feint": {
        "builder": _build_projectile_frames,
        "char": "-",
        "color": COLOR_BRIGHT_WHITE,
        "trail_char": "·",
        "trail_color": COLOR_WHITE,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_WHITE,
    },
    "meteor_mash": {
        "builder": _build_projectile_frames,
        "char": "█",
        "color": COLOR_BRIGHT_WHITE,
        "trail_char": "▓",
        "trail_color": COLOR_BRIGHT_YELLOW,
        "impact_char": "*",
        "impact_color": COLOR_BRIGHT_YELLOW,
    },

    #Beams
    "beam": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_WHITE,
        "core_char": "█",
        "core_color": COLOR_BRIGHT_YELLOW,
        "max_range": 5,
    },
    "hyper_beam": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_WHITE,
        "core_char": "█",
        "core_color": COLOR_BRIGHT_YELLOW,
        "shake": 2,
        "max_range": 5,
    },
    "solar_beam": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_YELLOW,
        "core_char": "☼",
        "core_color": COLOR_BRIGHT_GREEN,
        "shake": 1,
        "max_range": 5,
    },
    "flamethrower": {
        "builder": _build_beam_frames,
        "horiz_char": "▓",
        "vert_char": "▓",
        "diag1_char": "▓",
        "diag2_char": "▓",
        "color": COLOR_BRIGHT_RED,
        "core_char": "▒",
        "core_color": COLOR_BRIGHT_YELLOW,
        "dissipate_char": "░",
        "max_range": 5,
    },
    "ice_beam": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_CYAN,
        "core_char": "┼",
        "core_color": COLOR_BRIGHT_WHITE,
        "dissipate_char": "░",
        "max_range": 5,
    },
    "aurora_beam": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_CYAN,
        "core_char": "~",
        "core_color": COLOR_BRIGHT_MAGENTA,
        "dissipate_char": "·",
        "max_range": 5,
    },
    "hydro_pump": {
        "builder": _build_beam_frames,
        "horiz_char": "█",
        "vert_char": "█",
        "diag1_char": "█",
        "diag2_char": "█",
        "color": COLOR_BRIGHT_BLUE,
        "core_char": "~",
        "core_color": COLOR_BRIGHT_CYAN,
        "shake": 1,
        "max_range": 6,
    },
    "psybeam": {
        "builder": _build_beam_frames,
        "horiz_char": "~",
        "vert_char": "~",
        "diag1_char": "~",
        "diag2_char": "~",
        "color": COLOR_BRIGHT_MAGENTA,
        "core_char": "≡",
        "core_color": COLOR_BRIGHT_WHITE,
        "max_range": 5,
    },
    "dragon_breath": {
        "builder": _build_beam_frames,
        "horiz_char": "▒",
        "vert_char": "▒",
        "diag1_char": "▒",
        "diag2_char": "▒",
        "color": COLOR_BRIGHT_BLUE,
        "core_char": "*",
        "core_color": COLOR_BRIGHT_RED,
        "max_range": 5,
    },
    "zap_cannon": {
        "builder": _build_beam_frames,
        "horiz_char": "═",
        "vert_char": "║",
        "diag1_char": "\\",
        "diag2_char": "/",
        "color": COLOR_BRIGHT_YELLOW,
        "core_char": "‼",
        "core_color": COLOR_BRIGHT_WHITE,
        "shake": 1,
        "max_range": 5,
    },
    "leaf_storm": {
        "builder": _build_beam_frames,
        "horiz_char": "*",
        "vert_char": "*",
        "diag1_char": "*",
        "diag2_char": "*",
        "color": COLOR_BRIGHT_GREEN,
        "core_char": "~",
        "core_color": COLOR_GREEN,
        "max_range": 5,
    },
    "sky_attack": {
        "builder": _build_beam_frames,
        "horiz_char": "█",
        "vert_char": "█",
        "diag1_char": "█",
        "diag2_char": "█",
        "color": COLOR_BRIGHT_WHITE,
        "core_char": "▲",
        "core_color": COLOR_BRIGHT_YELLOW,
        "shake": 2,
        "max_range": 6,
    },
    "chloroblast": {
        "builder": _build_beam_frames,
        "horiz_char": "█",
        "vert_char": "█",
        "diag1_char": "█",
        "diag2_char": "█",
        "color": COLOR_BRIGHT_GREEN,
        "core_char": "☼",
        "core_color": COLOR_BRIGHT_YELLOW,
        "shake": 2,
        "max_range": 6,
    },
    "shell_side_arm": {
        "builder": _build_beam_frames,
        "horiz_char": "▓",
        "vert_char": "▓",
        "diag1_char": "▓",
        "diag2_char": "▓",
        "color": COLOR_BRIGHT_MAGENTA,
        "core_char": "■",
        "core_color": COLOR_MAGENTA,
        "max_range": 5,
    },
    "psywave": {
        "builder": _build_beam_frames,
        "horiz_char": "~",
        "vert_char": "~",
        "diag1_char": "~",
        "diag2_char": "~",
        "color": COLOR_BRIGHT_MAGENTA,
        "core_char": "~",
        "core_color": COLOR_MAGENTA,
        "max_range": 4,
    },
    "icy_wind": {
        "builder": _build_beam_frames,
        "horiz_char": "~",
        "vert_char": "~",
        "diag1_char": "~",
        "diag2_char": "~",
        "color": COLOR_BRIGHT_CYAN,
        "core_char": "░",
        "core_color": COLOR_BRIGHT_WHITE,
        "max_range": 5,
    },

    #Room and area waves
    "blizzard": {
        "builder": _build_room_frames,
        "chars": ["☼", "*", "•"],
        "colors": [COLOR_BRIGHT_CYAN, COLOR_BRIGHT_WHITE],
        "shake": 1,
    },
    "heat_wave": {
        "builder": _build_room_frames,
        "chars": ["~", "░", "▒"],
        "colors": [COLOR_BRIGHT_RED, COLOR_BRIGHT_YELLOW],
    },
    "earthquake": {
        "builder": _build_room_frames,
        "chars": ["_", "=", "▒"],
        "colors": [COLOR_YELLOW, COLOR_BRIGHT_YELLOW],
        "shake": 2,
    },
    "earth_power": {
        "builder": _build_room_frames,
        "chars": ["▲", "▓", "▒"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_YELLOW],
        "shake": 1,
    },
    "surf": {
        "builder": _build_room_frames,
        "chars": ["~", "█", "▒"],
        "colors": [COLOR_BRIGHT_BLUE, COLOR_BRIGHT_CYAN],
        "shake": 1,
    },
    "muddy_water": {
        "builder": _build_room_frames,
        "chars": ["▒", "~", "░"],
        "colors": [COLOR_YELLOW, COLOR_BRIGHT_BLACK],
    },
    "discharge": {
        "builder": _build_room_frames,
        "chars": ["*", "‼", "+"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_BRIGHT_WHITE],
    },
    "petal_blizzard": {
        "builder": _build_room_frames,
        "chars": ["*", "•", "·"],
        "colors": [COLOR_BRIGHT_MAGENTA, COLOR_BRIGHT_GREEN],
    },
    "razor_wind": {
        "builder": _build_room_frames,
        "chars": [")", "(", "X"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_WHITE],
    },
    "powder_snow": {
        "builder": _build_room_frames,
        "chars": ["*", "·", "•"],
        "colors": [COLOR_BRIGHT_CYAN, COLOR_BRIGHT_WHITE],
    },
    "uproar": {
        "builder": _build_room_frames,
        "chars": ["♫", "♪", "!"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_BRIGHT_WHITE],
    },
    "vacuum_cut": {
        "builder": _build_room_frames,
        "chars": ["X", "/", "\\"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_WHITE],
    },
    "flash": {
        "builder": _build_room_frames,
        "chars": ["☼", "*", "·"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_BRIGHT_YELLOW],
    },
    "spore": {
        "builder": _build_room_frames,
        "chars": ["░", "•", "▒"],
        "colors": [COLOR_BRIGHT_GREEN, COLOR_BRIGHT_YELLOW],
    },
    "perish_song": {
        "builder": _build_room_frames,
        "chars": ["♫", "♪", "·"],
        "colors": [COLOR_MAGENTA, COLOR_BRIGHT_BLACK],
    },

    #Adjacent bursts
    "thunderbolt": {
        "builder": _build_adjacent_frames,
        "chars": ["*", "‼", "+"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_BRIGHT_WHITE],
        "shake": 1,
    },
    "shock_wave": {
        "builder": _build_adjacent_frames,
        "chars": ["*", "+"],
        "colors": [COLOR_BRIGHT_YELLOW],
    },
    "lava_plume": {
        "builder": _build_adjacent_frames,
        "chars": ["▲", "*", "▒"],
        "colors": [COLOR_BRIGHT_RED, COLOR_BRIGHT_YELLOW],
    },
    "overheat": {
        "builder": _build_adjacent_frames,
        "chars": ["▓", "█", "*"],
        "colors": [COLOR_BRIGHT_RED, COLOR_BRIGHT_YELLOW],
        "shake": 2,
    },
    "sludge_wave": {
        "builder": _build_adjacent_frames,
        "chars": ["■", "▓", "▒"],
        "colors": [COLOR_MAGENTA, COLOR_BRIGHT_MAGENTA],
    },
    "bulldoze": {
        "builder": _build_adjacent_frames,
        "chars": ["▲", "═", "▒"],
        "colors": [COLOR_YELLOW, COLOR_BRIGHT_YELLOW],
    },
    "dark_pulse": {
        "builder": _build_adjacent_frames,
        "chars": ["○", "◙", "·"],
        "colors": [COLOR_MAGENTA, COLOR_BRIGHT_BLACK],
    },
    "night_shade": {
        "builder": _build_adjacent_frames,
        "chars": ["░", "▒", "·"],
        "colors": [COLOR_MAGENTA, COLOR_BRIGHT_BLACK],
    },
    "dazzling_gleam": {
        "builder": _build_adjacent_frames,
        "chars": ["☼", "*", "·"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_BRIGHT_MAGENTA],
    },
    "brutal_swing": {
        "builder": _build_adjacent_frames,
        "chars": ["■", "O", "X"],
        "colors": [COLOR_RED, COLOR_BRIGHT_BLACK],
    },
    "fiery_wrath": {
        "builder": _build_adjacent_frames,
        "chars": ["▲", "*", "!"],
        "colors": [COLOR_BRIGHT_RED, COLOR_RED],
    },
    "bug_buzz": {
        "builder": _build_adjacent_frames,
        "chars": ["~", ")", "("],
        "colors": [COLOR_BRIGHT_GREEN, COLOR_GREEN],
    },
    "voice_wave": {
        "builder": _build_adjacent_frames,
        "chars": ["♪", "♫", "~"],
        "colors": [COLOR_BRIGHT_CYAN, COLOR_BRIGHT_WHITE],
    },
    "spin_slash": {
        "builder": _build_adjacent_frames,
        "chars": ["/", "─", "\\", "|"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_WHITE],
    },
    "wide_slash": {
        "builder": _build_adjacent_frames,
        "chars": ["(", "/", ")"],
        "colors": [COLOR_BRIGHT_WHITE, COLOR_WHITE],
    },
    "poison_gas": {
        "builder": _build_adjacent_frames,
        "chars": ["░", "▒", "·"],
        "colors": [COLOR_MAGENTA, COLOR_BRIGHT_MAGENTA],
    },
    "slash_adjacent": {
        "builder": _build_adjacent_frames,
        "chars": ["/", "\\", "X"],
        "colors": [COLOR_BRIGHT_WHITE],
    },

    #Support auras
    "heal_aura": {
        "builder": _build_aura_frames,
        "chars": [".", "+", "*"],
        "colors": [COLOR_BRIGHT_GREEN, COLOR_BRIGHT_CYAN],
    },
    "shield_aura": {
        "builder": _build_aura_frames,
        "chars": [".", "■", "░"],
        "colors": [COLOR_BRIGHT_CYAN, COLOR_BRIGHT_MAGENTA],
    },
    "buff_aura": {
        "builder": _build_aura_frames,
        "chars": [".", "▲", "^"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_BRIGHT_WHITE],
    },
    "status_wave": {
        "builder": _build_aura_frames,
        "chars": ["~", "?", "!"],
        "colors": [COLOR_BRIGHT_YELLOW, COLOR_BRIGHT_MAGENTA],
    },

    #Melee(?) moves
    "slash": {
        "builder": _build_contact_frames,
        "contact_type": "slash",
        "colors": [COLOR_BRIGHT_WHITE],
    },
    "bite": {
        "builder": _build_contact_frames,
        "contact_type": "bite",
        "colors": [COLOR_BRIGHT_WHITE, COLOR_BRIGHT_RED],
    },
    "punch": {
        "builder": _build_contact_frames,
        "contact_type": "punch",
        "colors": [COLOR_BRIGHT_WHITE],
    },
}


# -----------------------------
# Fallback Mapping & Resolution
# -----------------------------

DEFAULT_MOVE_ANIMATIONS: dict[str, str] = {
    #Projectiles
    "Water Gun": "water_gun",
    "Water Pulse": "water_pulse",
    "Bubble Beam": "bubble_beam",
    "Ember": "ember",
    "Pin Missile": "pin_missile",
    "Bullet Seed": "bullet_seed",
    "Energy Ball": "energy_ball",
    "Shadow Ball": "shadow_ball",
    "Sludge Bomb": "sludge_bomb",
    "Gunk Shot": "gunk_shot",
    "Ice Shard": "ice_shard",
    "Bonemerang": "bonemerang",
    "Swift": "swift",
    "Quick Attack": "quick_attack",
    "Aqua Jet": "aqua_jet",
    "Extreme Speed": "extreme_speed",
    "Vine Whip": "vine_whip",
    "Razor Leaf": "razor_leaf",
    "Seed Bomb": "seed_bomb",
    "Leech Seed": "leech_seed",
    "Worry Seed": "worry_seed",
    "Strange Steam": "strange_steam",
    "Freezing Glare": "freezing_glare",
    "Vacuum Wave": "vacuum_wave",
    "Bullet Punch": "bullet_punch",
    "Mach Punch": "mach_punch",
    "Sucker Punch": "sucker_punch",
    "Feint": "feint",
    "Meteor Mash": "meteor_mash",

    #Beams
    "Hyper Beam": "hyper_beam",
    "Solar Beam": "solar_beam",
    "Flamethrower": "flamethrower",
    "Ice Beam": "ice_beam",
    "Aurora Beam": "aurora_beam",
    "Hydro Pump": "hydro_pump",
    "Psybeam": "psybeam",
    "Dragon Breath": "dragon_breath",
    "Zap Cannon": "zap_cannon",
    "Leaf Storm": "leaf_storm",
    "Sky Attack": "sky_attack",
    "Chloroblast": "chloroblast",
    "Shell Side Arm": "shell_side_arm",
    "Psywave": "psywave",
    "Icy Wind": "icy_wind",

    #Room and area waves
    "Blizzard": "blizzard",
    "Heat Wave": "heat_wave",
    "Earthquake": "earthquake",
    "Earth Power": "earth_power",
    "Surf": "surf",
    "Muddy Water": "muddy_water",
    "Discharge": "discharge",
    "Petal Blizzard": "petal_blizzard",
    "Razor Wind": "razor_wind",
    "Powder Snow": "powder_snow",
    "Uproar": "uproar",
    "Vacuum Cut": "vacuum_cut",
    "Vacuum-Cut": "vacuum_cut",
    "Flash": "flash",
    "Spore": "spore",
    "Perish Song": "perish_song",

    #Adjacent bursts
    "Thunderbolt": "thunderbolt",
    "Shock Wave": "shock_wave",
    "Lava Plume": "lava_plume",
    "Overheat": "overheat",
    "Sludge Wave": "sludge_wave",
    "Bulldoze": "bulldoze",
    "Dark Pulse": "dark_pulse",
    "Night Shade": "night_shade",
    "Dazzling Gleam": "dazzling_gleam",
    "Brutal Swing": "brutal_swing",
    "Fiery Wrath": "fiery_wrath",
    "Bug Buzz": "bug_buzz",
    "Disarming Voice": "voice_wave",
    "Echoed Voice": "voice_wave",
    "Hyper Voice": "voice_wave",
    "Snore": "voice_wave",
    "Spin Slash": "spin_slash",
    "Wide Slash": "wide_slash",
    "Wide-Slash": "wide_slash",
    "Poison Gas": "poison_gas",
    "Cut": "slash_adjacent",

    #Support auras
    "Life Dew": "heal_aura",
    "Moonlight": "heal_aura",
    "Aromatherapy": "heal_aura",
    "Heal Pulse": "heal_aura",
    "Safeguard": "shield_aura",
    "Light Screen": "shield_aura",
    "Reflect": "shield_aura",
    "Aurora Veil": "shield_aura",
    "Quick Guard": "shield_aura",
    "Wide Guard": "shield_aura",
    "Magnetic Flux": "shield_aura",
    "Helping Hand": "buff_aura",
    "Howl": "buff_aura",
    "Agility": "buff_aura",
    "Tailwind": "buff_aura",
    "Acupressure": "buff_aura",
    "Baton Pass": "buff_aura",
    "Growl": "status_wave",
    "Leer": "status_wave",
    "Sweet Scent": "status_wave",
    "Defog": "status_wave",
    "Haze": "status_wave",
    "Teeter Dance": "status_wave",
    "Lovely Kiss": "status_wave",
    "Imprison": "status_wave",
    "Memento": "status_wave",

    #Contact moves
    "Slash": "slash",
    "Night Slash": "slash",
    "Air Slash": "slash",
    "Psycho Cut": "slash",
    "Crush Claw": "slash",
    "Dragon Claw": "slash",
    "Metal Claw": "slash",
    "Fury Swipes": "slash",
    "Iron Tail": "slash",
    "Aqua Tail": "slash",
    "Bite": "bite",
    "Crunch": "bite",
    "Fire Fang": "bite",
    "Thunder Fang": "bite",
    "Ice Fang": "bite",
    "Poison Fang": "bite",
    "Super Fang": "bite",
    "Mega Punch": "punch",
    "Fire Punch": "punch",
    "Ice Punch": "punch",
    "Thunder Punch": "punch",
    "Shadow Punch": "punch",
    "Drain Punch": "punch",
    "Dynamic Punch": "punch",
    "Hammer Arm": "punch",
    "Poison Sting": "pin_missile",
    "Rock Throw": "meteor_mash",
    "Rock Slide": "meteor_mash",
    "Stone Edge": "meteor_mash",
    "Ancient Power": "meteor_mash",
    "Power Gem": "dazzling_gleam",
}


def get_animation_id_for_move(move: dict) -> str | None:
    """Returns the internal animation ID for a given move, or None if none assigned"""
    if not move:
        return None
    #1. Explicit internal ID set in moves.json
    anim_id = move.get("animation")
    if anim_id:
        return anim_id

    #2. Name-based fallback lookup
    name = move.get("name", "")
    if name in DEFAULT_MOVE_ANIMATIONS:
        return DEFAULT_MOVE_ANIMATIONS[name]

    #3. Range-based generic fallback
    range_str = move.get("range", "")
    if "room" in range_str.lower() or "floor" in range_str.lower():
        return "heat_wave" if move.get("type") == "Fire" else "blizzard"
    if "Straight line" in range_str:
        return "beam" if move.get("category") == "Special" else "projectile"
    if "tiles away" in range_str:
        return "projectile"
    if range_str.startswith("All adjacent"):
        return "shock_wave"

    return None


def get_move_animation_frames(
    game: Any,
    attacker: Pokemon,
    targets: Pokemon | list[Pokemon] | None,
    move: dict,
    animation_id: str | None = None,
) -> list[MoveAnimationFrame]:
    """Retrieves the list of animation frames for a move execution.

    Args:
        game: The active Game instance.
        attacker: The Pokemon executing the move.
        targets: Target defender(s) (Pokemon, list of Pokemon, or None).
        move: The move dictionary.
        animation_id: Optional explicit animation ID override.

    Returns:
        List of MoveAnimationFrame objects.
    """
    if targets is None:
        target_list: list[Pokemon] = []
    elif isinstance(targets, list):
        target_list = list(targets)
    else:
        target_list = [targets]

    anim_id = animation_id or get_animation_id_for_move(move)
    if not anim_id or anim_id not in ANIMATION_REGISTRY:
        return []

    cfg = dict(ANIMATION_REGISTRY[anim_id])
    builder = cfg.get("builder")
    if not builder:
        return []

    #Customize color dynamically for generic moves if appropriate
    if anim_id in ("projectile", "beam", "punch"):
        m_type = move.get("type", "Normal")
        type_col = TYPE_COLOR_MAP.get(m_type, COLOR_BRIGHT_WHITE)
        if "color" in cfg:
            cfg["color"] = type_col
        if "colors" in cfg:
            cfg["colors"] = [type_col]

    frames = builder(game, attacker, target_list, move, cfg)

    #Sanity check: Ensure all coordinates in frames are strictly inside floor bounds
    for frame in frames:
        invalid_keys = [
            (x, y) for (x, y) in frame.overlays.keys() if not clamp_to_floor(game.floor, x, y)
        ]
        for k in invalid_keys:
            del frame.overlays[k]

    return frames
