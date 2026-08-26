"""
dungeon.py

PMD-compliant dungeon generator, based off of generators 1, 8 and 12 (the most commonly used ones) from Red Rescue Team specifically. Generates procedural floors with rooms, merged adjacent rooms, corridors, and dead-ends.
This is my personal favorite code in the project. So awesome and efficient :)
Terrain generation will be implemented in the future.
Special shout-outs to TheZZAZZGlitch's video on the PMDRT dungeon generator and the pret Red Rescue Team decomp project, they were cruicial for writing this!
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import random

#Dungeon tile characters
WALL_CHAR = "█"
FLOOR_CHAR = "."


class Room:
    """Represents a rectangular room."""

    def __init__(self, x1: int, y1: int, x2: int, y2: int, cell_x: int, cell_y: int):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.cell_x = cell_x
        self.cell_y = cell_y
        self.merged_with: set[tuple[int, int]] = set()

    @property
    def width(self) -> int:
        return self.x2 - self.x1 + 1

    @property
    def height(self) -> int:
        return self.y2 - self.y1 + 1

    def intersects(self, other: "Room") -> bool:
        """Check if this room overlaps with another room."""
        return not (
            self.x2 < other.x1
            or self.x1 > other.x2
            or self.y2 < other.y1
            or self.y1 > other.y2
        )


class DungeonFloor:
    """Generates a single dungeon floor of size Width x Height"""

    def __init__(self, width: int | None = None, height: int = 32):
        if width is None:
            width = random.randint(32, 56)

        if not (32 <= width <= 56): #May raise this limit in the future. Big dungeon floors could be kinda cool? But need to implement map screen scrolling for that
            raise ValueError(f"Dungeon width must be between 32 and 56, got {width}")
        if height != 32: #Same as above
            raise ValueError(f"Dungeon height must be exactly 32, got {height}")

        self.width = width
        self.height = height

        #First we initialize the dungeon grid with wall tiles
        self.grid = [
            [WALL_CHAR for _ in range(self.width)] for _ in range(self.height)
        ]
        self.rooms: dict[tuple[int, int], Room] = {}
        self.cell_bounds: dict[tuple[int, int], dict[str, int]] = {}
        self.corridor_tiles: set[tuple[int, int]] = set()
        self.dead_end_tiles: set[tuple[int, int]] = set()

        self._generate()

    def _generate(self):
        """Main floor generation code"""
        num_cols = 3
        num_rows = 3

        #Divide the dungeon size into a grid of 3x3 cells
        col_widths = [self.width // num_cols] * num_cols
        for i in range(self.width % num_cols):
            col_widths[i] += 1

        row_heights = [self.height // num_rows] * num_rows
        for i in range(self.height % num_rows):
            row_heights[i] += 1

        #Compute cell bounding boxes
        x_offset = 0
        for cx in range(num_cols):
            y_offset = 0
            for cy in range(num_rows):
                self.cell_bounds[(cx, cy)] = {
                    "x_start": x_offset,
                    "x_end": x_offset + col_widths[cx] - 1,
                    "y_start": y_offset,
                    "y_end": y_offset + row_heights[cy] - 1,
                }
                y_offset += row_heights[cy]
            x_offset += col_widths[cx]

        #Select which cells will contain rooms (75% chance, 2 rooms min.)
        all_cells = [(cx, cy) for cx in range(num_cols) for cy in range(num_rows)]
        random.shuffle(all_cells)

        room_cells = []
        for cell in all_cells:
            if random.random() < 0.75:
                room_cells.append(cell)

        if len(room_cells) < 2:
            room_cells = all_cells[:2]

        #For merging two adjacent rooms together
        parent = {cell: cell for cell in room_cells}

        def find(c: tuple[int, int]) -> tuple[int, int]:
            if parent[c] == c:
                return c
            parent[c] = find(parent[c])
            return parent[c]

        def union(c1: tuple[int, int], c2: tuple[int, int]) -> bool:
            root1 = find(c1)
            root2 = find(c2)
            if root1 != root2:
                parent[root2] = root1
                return True
            return False

        #Identify adjacent cell pairs
        directions = [(1, 0), (0, 1)]
        adjacent_pairs = []
        for cx, cy in room_cells:
            for dx, dy in directions:
                neighbor = (cx + dx, cy + dy)
                if neighbor in room_cells:
                    adjacent_pairs.append(((cx, cy), neighbor))

        #Roll 5% chance to merge adjacent rooms
        for cell1, cell2 in adjacent_pairs:
            if random.random() < 0.05:
                union(cell1, cell2)

        #Group room cells by their merged component
        components: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for cell in room_cells:
            root = find(cell)
            if root not in components:
                components[root] = []
            components[root].append(cell)

        #Generate all rooms independently first (guaranteed to succeed and meet constraints)
        for cell in room_cells:
            cx, cy = cell
            self.rooms[cell] = self._generate_independent_room(cx, cy)

        #Adjust rooms in each merged component to overlap
        for root, cells in components.items():
            if len(cells) <= 1:
                continue

            visited = set()
            queue = [cells[0]]
            visited.add(cells[0])

            while queue:
                cell = queue.pop(0)
                cx, cy = cell
                room = self.rooms[cell]

                #Process adjacent neighbors in the same component that are already visited
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in cells and neighbor in visited:
                        room_n = self.rooms[neighbor]
                        bounds_cell = self.cell_bounds[cell]

                        if dx == 1 or dx == -1:  # Horizontal neighbors
                            #Align vertical bounds of room with room_n for overlap
                            y_start_pos = bounds_cell["y_start"] + 1
                            y_end_pos = bounds_cell["y_end"] - 1
                            y1_min = max(y_start_pos, room_n.y1 - room.height + 2)
                            y1_max = min(y_end_pos - room.height + 1, room_n.y2 - 1)
                            if y1_min <= y1_max:
                                new_y1 = (y1_min + y1_max) // 2
                                h_cached = room.height
                                room.y1 = new_y1
                                room.y2 = new_y1 + h_cached - 1

                        elif dy == 1 or dy == -1:  # Vertical neighbors
                            #Align horizontal bounds of room with room_n for overlap
                            x_start_pos = bounds_cell["x_start"] + 1
                            x_end_pos = bounds_cell["x_end"] - 1
                            x1_min = max(x_start_pos, room_n.x1 - room.width + 2)
                            x1_max = min(x_end_pos - room.width + 1, room_n.x2 - 1)
                            if x1_min <= x1_max:
                                new_x1 = (x1_min + x1_max) // 2
                                w_cached = room.width
                                room.x1 = new_x1
                                room.x2 = new_x1 + w_cached - 1

                #Queue unvisited neighbors
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    neighbor = (cx + dx, cy + dy)
                    if (
                        neighbor in cells
                        and neighbor not in visited
                        and neighbor not in queue
                    ):
                        queue.append(neighbor)
                        visited.add(neighbor)

        #Set parent pointer/merges in Room objects
        for cell in room_cells:
            root = find(cell)
            for other in room_cells:
                if other != cell and find(other) == root:
                    self.rooms[cell].merged_with.add(other)

        #Carve rooms into the grid
        for room in self.rooms.values():
            for x in range(room.x1, room.x2 + 1):
                for y in range(room.y1, room.y2 + 1):
                    self.grid[y][x] = FLOOR_CHAR

        #Carve merged room connections (remove separating walls)
        for cell1, room1 in self.rooms.items():
            for cell2 in room1.merged_with:
                #Don't carve rooms twice; only process if cell1 < cell2
                if cell1 >= cell2:
                    continue
                room2 = self.rooms[cell2]
                cx1, cy1 = cell1
                cx2, cy2 = cell2
                if cy1 == cy2:  #Horizontal neighbors
                    x_start = min(room1.x2, room2.x2)
                    x_end = max(room1.x1, room2.x1)
                    y_start = max(room1.y1, room2.y1)
                    y_end = min(room1.y2, room2.y2)
                    for x in range(x_start, x_end + 1):
                        for y in range(y_start, y_end + 1):
                            self.grid[y][x] = FLOOR_CHAR
                elif cx1 == cx2:  #Vertical neighbors
                    y_start = min(room1.y2, room2.y2)
                    y_end = max(room1.y1, room2.y1)
                    x_start = max(room1.x1, room2.x1)
                    x_end = min(room1.x2, room2.x2)
                    for y in range(y_start, y_end + 1):
                        for x in range(x_start, x_end + 1):
                            self.grid[y][x] = FLOOR_CHAR

        #Build connection tree for cells using Kruskal's algorithm
        edges = []
        for cx in range(3):
            for cy in range(3):
                if cx < 2:
                    edges.append(((cx, cy), (cx + 1, cy)))
                if cy < 2:
                    edges.append(((cx, cy), (cx, cy + 1)))

        random.shuffle(edges)

        parent_cell = {cell: cell for cell in all_cells}

        def find_cell(c: tuple[int, int]) -> tuple[int, int]:
            if parent_cell[c] == c:
                return c
            parent_cell[c] = find_cell(parent_cell[c])
            return parent_cell[c]

        def union_cell(c1: tuple[int, int], c2: tuple[int, int]) -> bool:
            root1 = find_cell(c1)
            root2 = find_cell(c2)
            if root1 != root2:
                parent_cell[root2] = root1
                return True
            return False

        mst_edges = []
        non_mst_edges = []
        for cell1, cell2 in edges:
            if union_cell(cell1, cell2):
                mst_edges.append((cell1, cell2))
            else:
                non_mst_edges.append((cell1, cell2))

        #Select corridors to generate (MST edges + 15% of non-MST edges for loops)
        selected_edges = list(mst_edges)
        for edge in non_mst_edges:
            if random.random() < 0.15:
                selected_edges.append(edge)

        #Carve corridors between connected cells
        for cell1, cell2 in selected_edges:
            #If both contain rooms and are merged in the same component, they are already connected
            if cell1 in self.rooms and cell2 in self.rooms:
                if find(cell1) == find(cell2):
                    continue
            self._carve_corridor(cell1, cell2)

        #Generate dead-end corridors starting from rooms
        self._generate_dead_ends()

    def _generate_independent_room(self, cx: int, cy: int) -> Room:
        """Generates a valid rectangular room inside a cell with 1-tile padding"""
        bounds = self.cell_bounds[(cx, cy)]
        x_start_pos = bounds["x_start"] + 1
        x_end_pos = bounds["x_end"] - 1
        y_start_pos = bounds["y_start"] + 1
        y_end_pos = bounds["y_end"] - 1

        max_w = x_end_pos - x_start_pos + 1
        max_h = y_end_pos - y_start_pos + 1

        choices = []
        for w in range(5, max_w + 1):
            for h in range(4, max_h + 1):
                if 2 * h <= 3 * w and 2 * w <= 3 * h:
                    choices.append((w, h))

        if not choices:
            w, h = 5, 4
        else:
            w, h = random.choice(choices)

        x1 = random.randint(x_start_pos, x_end_pos - w + 1)
        y1 = random.randint(y_start_pos, y_end_pos - h + 1)

        return Room(x1, y1, x1 + w - 1, y1 + h - 1, cx, cy)

    def _carve_corridor(self, cell1: tuple[int, int], cell2: tuple[int, int]):
        """Connects cell1 and cell2 with a 1-tile wide corridor"""
        cx1, cy1 = cell1
        cx2, cy2 = cell2

        #1. Determine start coordinate in cell1
        if cell1 in self.rooms:
            room1 = self.rooms[cell1]
            if cx1 < cx2:  #cell2 is east
                x_start = room1.x2
                y_start = random.randint(room1.y1, room1.y2)
            elif cx1 > cx2:  #cell2 is west
                x_start = room1.x1
                y_start = random.randint(room1.y1, room1.y2)
            elif cy1 < cy2:  #cell2 is south
                y_start = room1.y2
                x_start = random.randint(room1.x1, room1.x2)
            else:  #cell2 is north
                y_start = room1.y1
                x_start = random.randint(room1.x1, room1.x2)
        else:
            #No room: use cell center point
            bounds = self.cell_bounds[cell1]
            x_start = (bounds["x_start"] + bounds["x_end"]) // 2
            y_start = (bounds["y_start"] + bounds["y_end"]) // 2

        #2. Determine end coordinate in cell2
        if cell2 in self.rooms:
            room2 = self.rooms[cell2]
            if cx1 < cx2:  #cell1 is west
                x_end = room2.x1
                y_end = random.randint(room2.y1, room2.y2)
            elif cx1 > cx2:  #cell1 is east
                x_end = room2.x2
                y_end = random.randint(room2.y1, room2.y2)
            elif cy1 < cy2:  #cell1 is north
                y_end = room2.y1
                x_end = random.randint(room2.x1, room2.x2)
            else:  #cell1 is south
                y_end = room2.y2
                x_end = random.randint(room2.x1, room2.x2)
        else:
            #No room: use cell center point
            bounds = self.cell_bounds[cell2]
            x_end = (bounds["x_start"] + bounds["x_end"]) // 2
            y_end = (bounds["y_start"] + bounds["y_end"]) // 2

        #3. Carve the Z-shaped corridor
        self._carve_path(
            x_start, y_start, x_end, y_end, horizontal_first=(cx1 != cx2)
        )

    def _carve_path(
        self, x1: int, y1: int, x2: int, y2: int, horizontal_first: bool
    ):
        """Carve a 1-tile wide Z-shaped path between two points"""
        if horizontal_first:
            x_mid = (x1 + x2) // 2
            self._carve_line(x1, y1, x_mid, y1)
            self._carve_line(x_mid, y1, x_mid, y2)
            self._carve_line(x_mid, y2, x2, y2)
        else:
            y_mid = (y1 + y2) // 2
            self._carve_line(x1, y1, x1, y_mid)
            self._carve_line(x1, y_mid, x2, y_mid)
            self._carve_line(x2, y_mid, x2, y2)

    def _carve_line(self, x1: int, y1: int, x2: int, y2: int):
        """Carves a straight horizontal or vertical line of floor tiles"""
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        start_y = min(y1, y2)
        end_y = max(y1, y2)

        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                if self.grid[y][x] == WALL_CHAR:
                    self.grid[y][x] = FLOOR_CHAR
                    self.corridor_tiles.add((x, y))

    def _generate_dead_ends(self):
        """Attempts to generate one dead-end corridor starting from each room with a 30% chance"""
        for room in list(self.rooms.values()):
            if random.random() < 0.30:
                self._carve_dead_end_from_room(room)

    def _carve_dead_end_from_room(self, room: Room):
        """Carves a dead-end corridor starting from a random boundary of the room"""
        direction = random.choice(["n", "s", "e", "w"])
        if direction == "n": # north
            x_start = random.randint(room.x1, room.x2)
            y_start = room.y1 - 1
            dx, dy = 0, -1
        elif direction == "s": # south
            x_start = random.randint(room.x1, room.x2)
            y_start = room.y2 + 1
            dx, dy = 0, 1
        elif direction == "w": # west
            x_start = room.x1 - 1
            y_start = random.randint(room.y1, room.y2)
            dx, dy = -1, 0
        else:  # east
            x_start = room.x2 + 1
            y_start = random.randint(room.y1, room.y2)
            dx, dy = 1, 0

        length = random.randint(3, 6)
        curr_x, curr_y = x_start, y_start

        for _ in range(length):
            #Check map boundary (leave 1-tile solid border)
            if (
                not (1 <= curr_x < self.width - 1)
                or not (1 <= curr_y < self.height - 1)
            ):
                break

            #The target tile must be a wall
            if self.grid[curr_y][curr_x] != WALL_CHAR:
                break

            #Dead end corridors must not connect to another existing floor tile. That's why they're called dead ends!
            valid = True
            for ndx, ndy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = curr_x + ndx, curr_y + ndy
                if (nx, ny) == (curr_x - dx, curr_y - dy):
                    continue
                if self.grid[ny][nx] == FLOOR_CHAR:
                    valid = False
                    break

            if not valid:
                break

            #Let's carve!
            self.grid[curr_y][curr_x] = FLOOR_CHAR
            self.dead_end_tiles.add((curr_x, curr_y))

            curr_x += dx
            curr_y += dy

    def to_ascii(self) -> str:
        """Render the dungeon floor to an ASCII grid string"""
        return "\n".join("".join(row) for row in self.grid)
