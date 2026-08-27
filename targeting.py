"""
targeting.py

This handles all the move targeting logic, considering room constraints, distance checks, ally/enemy checks et cetera.
Written by C437RP13
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

from pokemon import Pokemon


def get_pokemon_position(game, pokemon: Pokemon) -> tuple[int, int]:
    """Returns the coordinates of the given Pokémon"""
    if pokemon is game.player_pokemon:
        return game.player_x, game.player_y
    return getattr(pokemon, "x", 0), getattr(pokemon, "y", 0)


def get_actual_target(game, attacker: Pokemon, target: Pokemon, move: dict) -> Pokemon:
    """Returns the actual target hit by a move.

    For moves targeting a specific Pokémon >1 tile away (and not a Straight line, Room or Floor range),
    check if any other Pokémon (enemy or ally) is in the way along the path.
    If so, returns the first intermediate Pokémon encountered.
    """
    range_str = move.get("range", "Adjacent enemy")
    if range_str.startswith("Straight line"):
        return target

    ax, ay = get_pokemon_position(game, attacker)
    tx, ty = get_pokemon_position(game, target)

    dist = max(abs(tx - ax), abs(ty - ay))
    if dist <= 1:
        return target

    dx = abs(tx - ax)
    dy = abs(ty - ay)
    sx = 1 if ax < tx else -1
    sy = 1 if ay < ty else -1
    err = dx - dy

    curr_x, curr_y = ax, ay
    all_pokes = game.party + game.spawned_pokemon

    seen = set()
    unique_pokes = []
    for p in all_pokes:
        if p not in seen:
            seen.add(p)
            unique_pokes.append(p)

    def get_poke_at(cx, cy):
        for p in unique_pokes:
            if p is not attacker and int(p.current_hp) > 0:
                px, py = get_pokemon_position(game, p)
                if px == cx and py == cy:
                    return p
        return None

    while True:
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

        if curr_x == tx and curr_y == ty:
            return target

        obstacle_poke = get_poke_at(curr_x, curr_y)
        if obstacle_poke:
            return obstacle_poke


def has_clear_path(floor, x1: int, y1: int, x2: int, y2: int, cuts_corners: bool) -> bool:
    """Checks if there is line-of-sight from (x1, y1) to (x2, y2).

    If cuts_corners is False, blocks diagonal steps that, well, cut corners
    """
    from dungeon import WALL_CHAR
    if x1 == x2 and y1 == y2:
        return True

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    curr_x, curr_y = x1, y1
    while True:
        prev_x, prev_y = curr_x, curr_y

        e2 = 2 * err
        step_x, step_y = 0, 0
        if e2 > -dy:
            err -= dy
            curr_x += sx
            step_x = sx
        if e2 < dx:
            err += dx
            curr_y += sy
            step_y = sy

        if curr_x == x2 and curr_y == y2:
            #Check final step corner cut
            if not cuts_corners and step_x != 0 and step_y != 0:
                c1 = floor.grid[prev_y][prev_x + step_x]
                c2 = floor.grid[prev_y + step_y][prev_x]
                if c1 == WALL_CHAR or c2 == WALL_CHAR:
                    return False
            break

        #Check if intermediate block is a wall
        if floor.grid[curr_y][curr_x] == WALL_CHAR:
            return False

        #Check corner cut for intermediate step
        if not cuts_corners and step_x != 0 and step_y != 0:
            c1 = floor.grid[prev_y][prev_x + step_x]
            c2 = floor.grid[prev_y + step_y][prev_x]
            if c1 == WALL_CHAR or c2 == WALL_CHAR:
                return False

    return True


def get_room_tiles_at(floor, x: int, y: int) -> set[tuple[int, int]]:
    """Returns the set of all coordinates inside the room containing (x, y)"""
    room_tiles: set[tuple[int, int]] = set()
    current_rooms = []
    for cell, room in floor.rooms.items():
        if room.x1 <= x <= room.x2 and room.y1 <= y <= room.y2:
            current_rooms.append((cell, room))

    if not current_rooms:
        #Check carved merged connections if (x, y) is in a connection tile between merged rooms
        for cell1, room1 in floor.rooms.items():
            for cell2 in room1.merged_with:
                if cell1 >= cell2:
                    continue
                room2 = floor.rooms[cell2]
                cx1, cy1 = cell1
                cx2, cy2 = cell2
                if cy1 == cy2:  #Horizontal neighbors
                    x_start = min(room1.x2, room2.x2)
                    x_end = max(room1.x1, room2.x1)
                    y_start = max(min(room1.y1, room2.y1), 0)
                    y_end = max(room1.y2, room2.y2)
                    if room1.x2 < room2.x1:
                        x_start, x_end = room1.x2, room2.x1
                    elif room2.x2 < room1.x1:
                        x_start, x_end = room2.x2, room1.x1
                    y_start = max(room1.y1, room2.y1)
                    y_end = min(room1.y2, room2.y2)
                    if x_start <= x <= x_end and y_start <= y <= y_end:
                        current_rooms.append((cell1, room1))
                elif cx1 == cx2:  #Vertical neighbors
                    if room1.y2 < room2.y1:
                        y_start, y_end = room1.y2, room2.y1
                    elif room2.y2 < room1.y1:
                        y_start, y_end = room2.y2, room1.y1
                    else:
                        y_start, y_end = min(room1.y2, room2.y2), max(room1.y1, room2.y1)
                    x_start = max(room1.x1, room2.x1)
                    x_end = min(room1.x2, room2.x2)
                    if x_start <= x <= x_end and y_start <= y <= y_end:
                        current_rooms.append((cell1, room1))

    if not current_rooms:
        return room_tiles

    all_merged = set()
    for cell, room in current_rooms:
        all_merged.add(cell)
        all_merged.update(room.merged_with)

    for cell in all_merged:
        r = floor.rooms[cell]
        for ry in range(r.y1, r.y2 + 1):
            for rx in range(r.x1, r.x2 + 1):
                room_tiles.add((rx, ry))

    #Also include carved connections between any merged pairs in all_merged
    for cell1 in all_merged:
        room1 = floor.rooms[cell1]
        for cell2 in room1.merged_with:
            if cell1 >= cell2 or cell2 not in all_merged:
                continue
            room2 = floor.rooms[cell2]
            cx1, cy1 = cell1
            cx2, cy2 = cell2
            if cy1 == cy2:  #Horizontal neighbors
                x_start = min(room1.x2, room2.x2)
                x_end = max(room1.x1, room2.x1)
                y_start = max(room1.y1, room2.y1)
                y_end = min(room1.y2, room2.y2)
                for ry in range(y_start, y_end + 1):
                    for rx in range(x_start, x_end + 1):
                        room_tiles.add((rx, ry))
            elif cx1 == cx2:  #Vertical neighbors
                y_start = min(room1.y2, room2.y2)
                y_end = max(room1.y1, room2.y1)
                x_start = max(room1.x1, room2.x1)
                x_end = min(room1.x2, room2.x2)
                for ry in range(y_start, y_end + 1):
                    for rx in range(x_start, x_end + 1):
                        room_tiles.add((rx, ry))

    return room_tiles


def is_ally_in_way_of_attack(game, attacker: Pokemon, target: Pokemon, move: dict) -> bool:
    """Returns True if another ally Pokémon is blocking the line of attack from attacker to target"""
    if attacker not in game.party:
        return False

    range_str = move.get("range", "Adjacent enemy")
    if range_str == "Enemy in front":
        range_str = "Adjacent enemy"

    #Room-wide/floor-wide, self or ally moves do not travel along a line to a target
    if range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower() or range_str == "User":
        return False

    #Piercing moves pass through allies
    if range_str == "Straight line piercing":
        return False

    ax, ay = get_pokemon_position(game, attacker)
    tx, ty = get_pokemon_position(game, target)

    dist = max(abs(tx - ax), abs(ty - ay))
    if dist <= 1:
        return False

    #Check straight line moves
    if range_str.startswith("Straight line"):
        dx = 1 if tx > ax else (-1 if tx < ax else 0)
        dy = 1 if ty > ay else (-1 if ty < ay else 0)

        curr_x, curr_y = ax + dx, ay + dy
        while (curr_x, curr_y) != (tx, ty):
            if hasattr(game, "floor") and game.floor:
                from dungeon import WALL_CHAR
                if not (0 <= curr_x < game.floor.width and 0 <= curr_y < game.floor.height):
                    break
                if game.floor.grid[curr_y][curr_x] == WALL_CHAR:
                    break
            for p in game.party:
                if p is not attacker and int(p.current_hp) > 0:
                    px, py = get_pokemon_position(game, p)
                    if px == curr_x and py == curr_y:
                        return True
            curr_x += dx
            curr_y += dy
        return False

    #Check ranged moves using get_actual_target
    actual = get_actual_target(game, attacker, target, move)
    if actual is not target and actual in game.party:
        return True

    return False


def is_ally_in_way_from_pos(game, attacker: Pokemon, ax: int, ay: int, target: Pokemon) -> bool:
    """Checks if any ally Pokémon (other than attacker) is on the line between (ax, ay) and target position"""
    tx, ty = get_pokemon_position(game, target)
    dist = max(abs(tx - ax), abs(ty - ay))
    if dist <= 1:
        return False

    dx = abs(tx - ax)
    dy = abs(ty - ay)
    sx = 1 if ax < tx else -1
    sy = 1 if ay < ty else -1
    err = dx - dy

    curr_x, curr_y = ax, ay
    while True:
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

        if curr_x == tx and curr_y == ty:
            break

        for p in game.party:
            if p is not attacker and int(p.current_hp) > 0:
                px, py = get_pokemon_position(game, p)
                if px == curr_x and py == curr_y:
                    return True

    return False


def get_valid_targets(game, attacker: Pokemon, move: dict) -> list[Pokemon]:
    """Returns a list of Pokémon instances on the floor that are valid targets for a move"""
    if move.get("name") == "Copycat":
        last_success = getattr(game, "last_move_used_successfully", None)
        if not last_success:
            return []
        last_move, last_attacker = last_success
        BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
        if last_attacker == attacker or last_move.get("name") in BLACKLIST_COPIABLE:
            return []
        return get_valid_targets(game, attacker, last_move)

    range_str = move.get("range", "Adjacent enemy")
    if move.get("name") == "Curse": #because curse is annoying and dumb and basically 2 moves in one it has to get special logic lmao
        user_types = getattr(attacker, "temp_types", None) or getattr(attacker, "types", attacker.species_data.get("types", []))
        if "Ghost" in user_types:
            range_str = "Adjacent enemy"
        else:
            range_str = "User"

    ax, ay = get_pokemon_position(game, attacker)

    #Determine relationships
    attacker_is_ally = attacker in game.party
    all_pokes = game.party + game.spawned_pokemon

    #Remove duplicate player reference if player is in party
    seen = set()
    unique_pokes = []
    for p in all_pokes:
        if p not in seen:
            seen.add(p)
            unique_pokes.append(p)

    valid = []
    cuts_corners = (
        move.get("cuts_corners", False)
        or "room" in range_str.lower()
        or "floor" in range_str.lower()
        or range_str == "User"
    )

    #Cache room tiles for room checks
    attacker_room_tiles = get_room_tiles_at(game.floor, ax, ay)

    for target in unique_pokes:
        tx, ty = get_pokemon_position(game, target)

        #Check self-targeting rules
        is_self = target is attacker
        if range_str == "User":
            if is_self:
                valid.append(target)
            continue
        elif is_self and "including user" not in range_str.lower():
            #Other moves cannot target self unless explicitly included
            continue

        #Determine target alignment relative to attacker
        target_is_ally = target in game.party
        is_enemy = attacker_is_ally != target_is_ally

        #Filter by relationship (skipped if attacker is confused or target is a decoy)
        if attacker.status_effects.get("Puppet", 0) > 0:
            if range_str in ("Adjacent enemy", "Adjacent enemy or ally", "All adjacent enemies", "Enemy up to 2 tiles away", "Enemy up to 3 tiles away", "All enemies in room", "All enemies on floor", "Straight line", "Straight line up to 4 tiles", "Straight line piercing"):
                if not target_is_ally or target is attacker:
                    continue
            elif range_str in ("All allies in room", "All allies on floor", "All allies in room, including user", "All allies on floor, including user"):
                if not target_is_ally:
                    continue
        elif attacker.status_effects.get("Confusion", 0) <= 0 and target.status_effects.get("Decoy", 0) <= 0:
            if range_str in ("Adjacent enemy", "All adjacent enemies", "Enemy up to 2 tiles away", "Enemy up to 3 tiles away", "All enemies in room", "All enemies on floor"):
                if not is_enemy:
                    continue
            elif range_str in ("All allies in room", "All allies on floor", "All allies in room, including user", "All allies on floor, including user"):
                if is_enemy:
                    continue

        #Distance & line-of-sight checks
        dist = max(abs(tx - ax), abs(ty - ay))

        if range_str in ("Adjacent enemy", "Adjacent enemy or ally", "All adjacent enemies", "All adjacent enemies and allies", "Adjacent tile"):
            if dist != 1:
                continue
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                continue

        elif range_str == "Enemy up to 2 tiles away":
            if dist > 2:
                continue
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                continue
                
        elif range_str == "Enemy up to 3 tiles away":
            if dist > 3:
                continue
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                continue

        elif range_str.startswith("Straight line"):
            max_d = 4 if "4" in range_str else 10
            if dist > max_d:
                continue
            dx = tx - ax
            dy = ty - ay
            #Must be cardinal or 45-degree diagonal
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                continue
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                continue

        elif "room" in range_str.lower():
            if attacker_room_tiles:
                #Inside room: must be inside the same room (including merged rooms)
                if (tx, ty) not in attacker_room_tiles:
                    continue
            else:
                #Outside room: treat range as visibility radius (5 normally, 100 (basically infinite when floor_luminous)
                v_radius = 100 if getattr(game, "floor_luminous", False) else 5
                if dist > v_radius:
                    continue
                if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                    continue

        #Floor-wide moves do not require distance or line-of-sight checks

        valid.append(target)

    return valid


def get_confusion_targets(game, attacker: Pokemon, move: dict) -> list[Pokemon]:
    """Selects targets for a confused attacker, which chooses attack directions at random"""
    import random
    from targeting import get_pokemon_position, has_clear_path, get_room_tiles_at
    range_str = move.get("range", "Adjacent enemy")
    if move.get("name") == "Curse": #ditto (not the pokémon)
        user_types = getattr(attacker, "temp_types", None) or getattr(attacker, "types", attacker.species_data.get("types", []))
        if "Ghost" in user_types:
            range_str = "Adjacent enemy"
        else:
            range_str = "User"
    if range_str == "Enemy in front":
        range_str = "Adjacent enemy"

    ax, ay = get_pokemon_position(game, attacker)
    directions = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]

    def get_poke_at(cx, cy):
        for p in game.party + game.spawned_pokemon:
            px, py = get_pokemon_position(game, p)
            if px == cx and py == cy and int(p.current_hp) > 0:
                return p
        return None

    if range_str in ("Adjacent enemy", "Adjacent enemy or ally", "All adjacent enemies", "All adjacent enemies and allies", "Adjacent tile"):
        rdx, rdy = random.choice(directions)
        tx, ty = ax + rdx, ay + rdy
        p = get_poke_at(tx, ty)
        cuts_corners = move.get("cuts_corners", False)
        if p and has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
            return [p]
        return []

    elif range_str == "Enemy up to 2 tiles away":
        rdx, rdy = random.choice(directions)
        cuts_corners = move.get("cuts_corners", False)
        for i in range(1, 3):
            tx, ty = ax + i * rdx, ay + i * rdy
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                break
            p = get_poke_at(tx, ty)
            if p:
                return [p]
        return []
        
    elif range_str == "Enemy up to 3 tiles away":
        rdx, rdy = random.choice(directions)
        cuts_corners = move.get("cuts_corners", False)
        for i in range(1, 4):
            tx, ty = ax + i * rdx, ay + i * rdy
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                break
            p = get_poke_at(tx, ty)
            if p:
                return [p]
        return []

    elif range_str in ("Straight line", "Straight line up to 4 tiles", "Straight line piercing"):
        rdx, rdy = random.choice(directions)
        cuts_corners = move.get("cuts_corners", False)
        max_d = 4 if "4" in range_str else 10
        for i in range(1, max_d + 1):
            tx, ty = ax + i * rdx, ay + i * rdy
            if not has_clear_path(game.floor, ax, ay, tx, ty, cuts_corners):
                break
            p = get_poke_at(tx, ty)
            if p:
                return [p]
        return []

    elif "room" in range_str.lower() or "floor" in range_str.lower() or range_str == "User":
        return get_valid_targets(game, attacker, move)

    return []
