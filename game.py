"""
game.py

Core game loop and logic runner. Everything that doesn't happen in the other modules, happens here, and all the modules rely on this one.
"""

#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import sys
import random
import os
import re
import atexit
from dungeon import DungeonFloor, WALL_CHAR, FLOOR_CHAR
import input as game_input
from pokemon import Pokemon  #type: ignore
from message_log import MessageLog  #type: ignore
from combat import calculate_damage
from targeting import get_valid_targets, get_pokemon_position, get_room_tiles_at, get_confusion_targets, get_actual_target, is_ally_in_way_of_attack, is_ally_in_way_from_pos, has_clear_path
import items
from end_screen import EndScreenController, generate_end_screen_report, dump_team_report_to_file

PLAYER_CHAR = "@" #Appearance of the currently-controlled character (the team leader)

#Each type has a color associated with it that is used to color some parts of the UI, since there are 16 colors in compatible terminals and 18 (well, technically 19) types some types have to share colors.
TYPE_COLORS = {
    "Normal": "\033[37m",
    "Fire": "\033[91m",
    "Water": "\033[94m",
    "Grass": "\033[92m",
    "Electric": "\033[93m",
    "Ice": "\033[96m",
    "Fighting": "\033[31m",
    "Poison": "\033[35m",
    "Ground": "\033[33m",
    "Flying": "\033[96m",
    "Psychic": "\033[95m",
    "Bug": "\033[32m",
    "Rock": "\033[90m",
    "Ghost": "\033[35m",
    "Dragon": "\033[34m",
    "Steel": "\033[90m",
    "Fairy": "\033[95m",
    "Typeless": "\033[37m"
}

#Colors used for the hallucination status
SCINTILLATING_COLORS = [
    "\033[91m",  #bright red
    "\033[92m",  #bright green
    "\033[93m",  #bright yellow
    "\033[94m",  #bright blue
    "\033[95m",  #bright magenta
    "\033[96m",  #bright cyan
    "\033[97m",  #bright white
    "\033[31m",  #red
    "\033[32m",  #green
    "\033[33m",  #yellow
    "\033[34m",  #blue
    "\033[35m",  #magenta
    "\033[36m",  #cyan
]

GAME_LOGO_LINES = [
    "                                      █                                 ",
    "       ███            ██            ███                                 ",
    "   ████  ███          ██         ███                                    ",
    "  █████    ██         ██       ██                                       ",
    "     ██     █         ███         ████                                  ",
    "     ██     █         ███   █   ██   ██  ██ ██          ██              ",
    "     ██    ██  ████   ██████   █     ██  █████████    ██████  ██        ",
    "     ██████   ███ ██  ████    ██   ███   ██  ██  ██  ███   ██ ████      ",
    "     ██      ███   █  ███     █████      ██  ██  ██  ███    █ ██ ██     ",
    "     ███     ███   ██ ███      █     █   ██  ██  ██ ███     █ █    █    ",
    "     ███     ███ ████ █████    ██████    ██  █   ██ ███   ██  █    █    ",
    "     ███     ███████  ███ ███            ██      █  ████████  █    █    ",
    "      ██       ███    ███   ██                   █  ███████   █    █    ",
    "                                                     █████    █    █    ",
    "                                                                        ",
    "    █  █  █                       ███                                   ",
    "    ████      ███  ██  █ ██ █  █  █  █ █  █ █ █   ███  ██   ██  █ █     ",
    "    ████  █  ███  █  █ ██   █  █  █  █ █  █ ██ █ █  █ █  █ █  █ ██ █    ",
    "    █  █  █     █ ███  █     ███  █  █ █ ██ █  █  ███ ███  █  █ █  █    ",
    "    █  █  █  ███   ███ █       █  ███   █ █ █  █    █  ███  ██  █  █    ",
    "                             ██                   ██                    ",
    "                                                                        ",
    "                       ☼ Explorers of the Console ☼                    "
]

TIPS_OF_THE_DAY = [
    "Items are plentiful give you a huge advantage - use them when you can!",
    "Variety is the spice of life. Keep your team and moves varied!",
    "You can switch leaders at almost any time. This can be a lifesaver!",
    "Hold down [5] or [.] to recover HP quickly; but beware of enemies!",
    "Don't stay too long on floors, or your food will run out eventually.",
    "All hail the Swampert loaf!",
    "Having trouble with stat lowering moves? Remember to use Wonder Tiles!",
    "Geo Pebbles & Gravelerocks deal fixed damage and are great for early game.",
    "You can still properly throw items even when Confused.",
    "Stat raising moves can be used even without enemies nearby.",
    "Stronger Pokémon only show up on higher floors of the dungeon.",
    "No numpad? Use SHIFT+↑/↓ to move diag-left, & CTRL+↑/↓ to move diag right.",
    "Join my Discord server! https://discord.gg/qr9V6FvMEz",
    "This is an early beta version, so expect lots of bugs!",
    "Better move cost more PP; Normal-type moves tend to cost less PP.",
    "Drink Elixirs BEFORE fighting; using items in fights wastes valuable time.",
    "A larger party means more mouths to feed.",
    "If you somehow get a score of 1,000,000 or higher, send it to C4 ;)",
    "Not all starter Pokémon are made equal. Each have strengths & weaknesses.",
    "Time only moves when you do, so always carefully consider your options.",
    "The level of wild Pokémon is equal to the current floor number.",
    "Proudly open-source! Check out the repo on GitHub.",
    "Move category matters! You should try to have 1 Physical & 1 Special move.",
    "You can disable allies from using certain moves from their summary screen.",
    "If your belly is over 100%, you won't be able to eat any more items.",
    "If you make it to the end of the 50th floor, you win!",
    "You can view a Pokémon's remaining HP in 'look around' mode (press [L])",
    "Moves deal less damage when they hit multiple targets."
]


COLOR_ESCAPE_REGEX = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi_color(text: str) -> str:
    """Strips all ANSI color and text formatting escape sequences from a string. (compatability mode)"""
    return COLOR_ESCAPE_REGEX.sub('', text)


def center_ansi(text: str, width: int = 76) -> str:
    """Used to center text on the screen for menus and the like."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    visible_length = len(ansi_escape.sub('', text))
    left_padding = max(0, (width - visible_length) // 2)
    right_padding = max(0, width - visible_length - left_padding)
    return " " * left_padding + text + " " * right_padding


class Game:
    """Manages the player state, map coordinates, collision rules and rendering"""

    def __init__(self, width: int | None = None, player_species: str | None = None, player_nickname: str | None = None, compatibility_mode: bool = False, **kwargs):
        self.compatibility_mode: bool = bool(
            compatibility_mode
            or kwargs.get("compatability_mode", False)
            or os.environ.get("NO_COLOR")
            or os.environ.get("GAME_COMPATIBILITY_MODE")
        )
        self.floor = DungeonFloor(width=width)
        #Spawn player in a random room
        self.player_x, self.player_y = self._get_starting_position()
        self.floor_number = 1
        self.build_string = "Beta 0.1.1"
        self.message = self.build_string
        self.stairs_position = (0, 0)
        self.spawn_stairs()
        self.wonder_tile_position = (0, 0) #One wonder tile per floor for now, hardcoded currently.
        self.spawn_wonder_tile()
        self.is_running = True
        self.explored_tiles: set[tuple[int, int]] = set() #For the memory system, which draws tiles seen previously in gray
        self.radar_active: bool = False #Radar Orb
        self.scanner_active: bool = False #Scanner Orb
        self.stairs_revealed: bool = False #Stairs Orb
        self.turn_number = 0
        self.player_action_number: int = 1
        self.turn_in_progress: bool = False
        self.message_log = MessageLog()
        self._message_log_current_turn: int = 1
        self._turn_messages_count: int = 0
        self.turn_count = 0
        self.game_ended = False
        self.game_won = False

        #Game menu states
        self.disclaimer_screen_state: dict | None = None
        self.title_screen_state: dict | None = None
        self.starter_select_state: dict | None = None
        self.high_scores_state: dict | None = None

        #Statistics used for the game end summary
        import time
        self.start_time = time.time()
        self.session_start_time = time.time()
        self.accumulated_play_time: float = 0.0
        self.total_enemy_exp = 0
        self.encountered_species: dict[str, dict[str, int]] = {}
        self.total_recruited_count = 0
        self.all_team_members: list[dict] = []

        if player_species is None:
            if sys.stdin.isatty():
                self.disclaimer_screen_state = {
                    "start_time": time.time(),
                    "duration": 5.0
                }
            else:
                player_species = "Bulbasaur"

        if player_species is not None:
            self.player_pokemon = Pokemon(player_species, level=2, nickname=player_nickname)
            self.player_pokemon.is_leader = True
            self.party = [self.player_pokemon]

            starter_sp = getattr(self.player_pokemon, "species_name", "") or self.player_pokemon.species_data.get("name", self.player_pokemon.name)
            self.register_encountered_species(starter_sp)
            self.add_to_team_history(self.player_pokemon, is_starter=True)
        else:
            self.player_pokemon = None
            self.party = []

        self.spawned_pokemon: list[Pokemon] = []
        self.targeting_mode = False #Game mode used when choosing a target for multitarget moves
        self.targeting_move: dict | None = None
        self.targeting_cursor = (0, 0) #Position of the cursor in targeting mode
        self.targeting_targets: list[Pokemon] = [] #List of valid targets for the targeting mode cursor
        self.waiting_for_direction = False
        self.direction_move: dict | None = None
        self.flash_damages: dict[tuple[int, int], tuple[int | str, float | str]] = {} #Pop-ups that appear when a Pokémon is damaged, healed or gains EXP
        self.moved_used_this_turn: set[Pokemon] = set()
        self.round_users_this_turn: set[Pokemon] = set()
        self.party_start_positions: dict[Pokemon, tuple[int, int]] = {}
        self.player_actions_left: int = 1
        self.leech_seed_sources: dict[Pokemon, Pokemon] = {} #Pokémon that used Leech Seed on the team member
        self.taunt_sources: dict[Pokemon, Pokemon] = {} #Pokémon that taunted the team member
        self.fire_spin_bindings: list[dict] = []
        self.wrap_bindings: list[dict] = []
        self.sand_tomb_bindings: list[dict] = []
        self.whirlpool_bindings: list[dict] = []
        self.move_replacement_queue: list[tuple[Pokemon, dict]] = [] #List of moves that the Pokémon has learned that are pending

        self.gravity = False
        self.weather = "Clear"
        self.weather_turns_left = 0
        self.wonder_room_turns = 0
        self.look_around_mode = False #Game mode used when pressing "l", displays descriptions of items
        self.look_around_cursor = (0, 0)
        self.look_around_cursor_visible = True #Used to flash the cursor in look around mode
        self.active_status_pokemon = None #Active Pokémon in the party
        self.summary_scroll_offset: int = 0
        self.future_sight_effects: list[dict] = []
        
        #Inventory and items system initialization
        self.inventory: list[dict] = []
        self.items_on_floor: dict[tuple[int, int], dict] = {}
        self.money: int = 0
        self.inventory_state: dict | None = None #Is the inventory menu open?
        self.message_history_state: dict | None = None #Is the message history menu open?
        self.pause_menu_state: dict | None = None #Is the pause menu open?
        self.nickname_prompt_state: dict | None = None #Is the nickname window open?
        self.replace_recruit_state: dict | None = None #Is the Pokémon replacement screen open?
        self.summary_context_menu_state: dict | None = None #Is the context window open on the Pokémon summary screen?
        self.waiting_for_throw_direction: int | None = None #When throwing an item, the game pauses and prompts the user for a direction
        self.waiting_for_orb_direction: int | None = None #When using a directional orb, the game pauses and prompts the user for a direction
        self.flying_item_animation: dict | None = None #Airborne items play an animation
        self.suppress_animation_delay: bool = False #TODO: Add a settings screen that allows this to be toggled at any time
        self.explosion_overlays: dict[tuple[int, int], str] = {}
        self.exp_batching_active: bool = False
        self.pending_team_exp: int = 0

        #Load all move names for color-coding in log messages
        from moves_db import load_moves_database
        from data_utils import get_data_file_path
        moves_db_path = get_data_file_path("moves.json")
        try:
            moves = load_moves_database(moves_db_path)
            self.moves_db = moves
            self.all_move_names = {m["name"] for m in moves}
        except Exception:
            self.moves_db = []
            self.all_move_names = set()
        self.last_move_used_successfully: tuple[dict, Pokemon] | None = None

        #Load all species names and database for randomized enemy spawning and for message color-coding
        from pokemon_db import load_pokemon_database
        pokemon_db_path = get_data_file_path("pokemon.json")
        try:
            self.pokemon_db = load_pokemon_database(pokemon_db_path)
            self.all_species_names = [entry["name"] for entry in self.pokemon_db]
        except Exception:
            self.pokemon_db = []
            self.all_species_names = ["Bulbasaur", "Charmander", "Squirtle"]

        self.floor_spawn_list: list[str] = []
        self.generate_floor_spawn_list()

        #Initial setup
        self.spawn_initial_items()
        self.spawn_initial_enemies()
        self.log_message("You enter the misery dungeon...")

    def register_encountered_species(self, species_name: str, was_defeated: bool = False, is_recruited: bool = False):
        """Tracks encountered species, defeated count, and recruitment count (used for the summary screen)"""
        if not species_name:
            return
        if species_name not in self.encountered_species:
            self.encountered_species[species_name] = {"seen": 1, "defeated": 0, "recruited": 0}
        else:
            self.encountered_species[species_name]["seen"] += 1
        if was_defeated:
            self.encountered_species[species_name]["defeated"] += 1
        if is_recruited:
            self.encountered_species[species_name]["recruited"] += 1

    def add_to_team_history(self, pokemon, is_starter: bool = False):
        """Records a Pokémon that became a member of the player's team (for use in the summary)"""
        sp_name = getattr(pokemon, "species_name", "") or (pokemon.species_data.get("name", pokemon.name) if getattr(pokemon, "species_data", None) else pokemon.name)
        nickname = getattr(pokemon, "nickname", None) or pokemon.name
        poke_id = getattr(pokemon, "id", None)
        if not poke_id:
            import uuid
            poke_id = str(uuid.uuid4())
            pokemon.id = poke_id

        for entry in self.all_team_members:
            if entry.get("pokemon") is pokemon or (entry.get("pokemon_id") and entry.get("pokemon_id") == poke_id):
                return
        self.all_team_members.append({
            "pokemon": pokemon,
            "pokemon_id": poke_id,
            "name": nickname,
            "species_name": sp_name,
            "is_starter": is_starter,
            "fate": None,
            "final_hp": None,
            "final_max_hp": None,
            "final_level": None,
            "final_moves": None,
            "final_stats": None
        })

    def record_team_member_departure(self, pokemon):
        """Records the fate and final stats of a team member when they leave the team (e.g. replaced by recruit)"""
        poke_id = getattr(pokemon, "id", None)
        for entry in self.all_team_members:
            if entry.get("pokemon") is pokemon or (poke_id and entry.get("pokemon_id") == poke_id):
                if entry.get("fate") is not None:
                    return
                floor_num = getattr(self, "floor_number", 1)
                turns = getattr(self, "turn_number", 0) or getattr(self, "turn_count", 0)
                entry["fate"] = f"Departed the team on {floor_num}F on turn {turns}"
                entry["final_hp"] = int(getattr(pokemon, "current_hp", 0))
                entry["final_max_hp"] = int(pokemon.stats.get("HP", 1)) if getattr(pokemon, "stats", None) else 1
                entry["final_level"] = getattr(pokemon, "level", 1)
                entry["final_moves"] = [m["name"] for m in pokemon.moves if isinstance(m, dict) and "name" in m] if getattr(pokemon, "moves", None) else []
                entry["final_stats"] = dict(pokemon.stats) if getattr(pokemon, "stats", None) else {}
                break

    def record_team_member_defeat(self, pokemon, damage_source: str | None = None):
        """Records the fate and final stats of a team member when they are defeated (also see record_team_member_defeat above)"""
        poke_id = getattr(pokemon, "id", None)
        for entry in self.all_team_members:
            if entry.get("pokemon") is pokemon or (poke_id and entry.get("pokemon_id") == poke_id):
                if entry.get("fate") is not None:
                    return
                src = damage_source or getattr(pokemon, "last_damage_source", None)
                floor_num = getattr(self, "floor_number", 1)
                turns = getattr(self, "turn_number", 0) or getattr(self, "turn_count", 0)

                if src == "poison":
                    fate_str = f"Succumbed to poison on {floor_num}F on turn {turns}"
                elif src == "burn":
                    fate_str = f"Succumbed to burn on {floor_num}F on turn {turns}"
                elif src == "hunger":
                    fate_str = f"Fainted from hunger on {floor_num}F on turn {turns}"
                elif src == "Give Up":
                    fate_str = f"Gave up on {floor_num}F on turn {turns}"
                elif src == "Chestnut":
                    fate_str = f"Pricked to death by a chestnut on {floor_num}F on turn {turns}"
                elif src == "Geo Pebble":
                    fate_str = f"Defeated by a Geo Pebble on {floor_num}F on turn {turns}"
                elif src == "Gravelerock":
                    fate_str = f"Defeated by a Gravelerock on {floor_num}F on turn {turns}"
                elif src == "Stick":
                    fate_str = f"Defeated by a Stick on {floor_num}F on turn {turns}"
                elif src == "Iron Thorn":
                    fate_str = f"Defeated by an Iron Thorn on {floor_num}F on turn {turns}"
                elif src == "Silver Spike":
                    fate_str = f"Defeated by a Silver Spike on {floor_num}F on turn {turns}"
                elif src == "Corsola Twig":
                    fate_str = f"Defeated by a Corsola Twig on {floor_num}F on turn {turns}"
                elif src == "Cacnea Spike":
                    fate_str = f"Defeated by a Cacnea Spike on {floor_num}F on turn {turns}"
                elif src == "Gold Fang":
                    fate_str = f"Defeated by a Gold Fang on {floor_num}F on turn {turns}"
                elif src == "Leech Seed":
                    fate_str = f"Drained to nothing by Leech Seed on {floor_num}F on turn {turns}"
                elif src == "Destiny Bond":
                    fate_str = f"Taken down by Destiny Bond on {floor_num}F on turn {turns}"
                elif src == "Leech Seed":
                    fate_str = f"Drained to nothing by Leech Seed on {floor_num}F on turn {turns}"
                elif src == "Hail":
                    fate_str = f"Battered by hail on {floor_num}F on turn {turns}"
                elif src == "Sandstorm":
                    fate_str = f"Blasted by blowing sand on {floor_num}F on turn {turns}"
                elif src == "Perish Song":
                    fate_str = f"Perished on {floor_num}F on turn {turns}"
                elif src in ("Mirror Coat", "Counter"):
                    fate_str = f"Defeated by a reflected attack on {floor_num}F on turn {turns}"
                elif src in ("Healing Wish", "Memento"):
                    fate_str = f"Sacrificed themselves on {floor_num}F on turn {turns}"
                elif src in ("Self-Destruct", "Explosion"):
                    fate_str = f"Exploded on {floor_num}F on turn {turns}"
                elif src == "recoil":
                    fate_str = f"Finished off by recoil damage on {floor_num}F on turn {turns}"
                elif src:
                    fate_str = f"Defeated by {src} on {floor_num}F on turn {turns}"
                else:
                    fate_str = f"Defeated on {floor_num}F on turn {turns}"
                    
                entry["fate"] = fate_str
                entry["final_hp"] = int(pokemon.current_hp)
                entry["final_max_hp"] = int(pokemon.stats.get("HP", 1)) if getattr(pokemon, "stats", None) else 1
                entry["final_level"] = getattr(pokemon, "level", 1)
                entry["final_moves"] = [m["name"] for m in pokemon.moves if isinstance(m, dict) and "name" in m] if getattr(pokemon, "moves", None) else []
                entry["final_stats"] = dict(pokemon.stats) if getattr(pokemon, "stats", None) else {}
                break

    def is_team_pokemon(self, pokemon) -> bool:
        """Returns True if the given pokemon instance was a member of the team"""
        if pokemon is None:
            return False
        if hasattr(self, "party") and any(p is pokemon for p in self.party):
            return True
        poke_id = getattr(pokemon, "id", None)
        if hasattr(self, "all_team_members"):
            return any(entry.get("pokemon") is pokemon or (poke_id and entry.get("pokemon_id") == poke_id) for entry in self.all_team_members)
        return False

    def get_elapsed_play_time(self) -> float:
        """Returns total active play time in seconds across all game sessions for that save file"""
        import time
        session_duration = max(0.0, time.time() - getattr(self, "session_start_time", time.time()))
        return getattr(self, "accumulated_play_time", 0.0) + session_duration

    def is_in_team_sight(self, pokemon) -> bool:
        """Returns True if the given Pokémon is in the player team's sight"""
        if pokemon is None:
            return False
        if self.is_team_pokemon(pokemon):
            return True
        from targeting import get_pokemon_position
        pos = get_pokemon_position(self, pokemon)
        return pos in self._compute_currently_visible()

    def log_pokemon_defeat(self, pokemon):
        """Logs the defeat of a Pokémon with team vs enemy distinction"""
        if pokemon is None:
            return
        if self.is_team_pokemon(pokemon):
            self.log_message(f"Oh, no! {pokemon.name} was defeated!", important=True)
        else:
            self.log_message(f"{pokemon.name} was defeated!")

    def handle_enemy_defeat(self, enemy: Pokemon, defeater: Pokemon | None = None):
        """Processes an enemy defeat, awarding EXP to the team (only if attacked by a team member)"""
        if enemy is None or self.is_team_pokemon(enemy):
            return
        if defeater is not None and self.is_team_pokemon(defeater):
            defeater.defeat_pokemon(enemy, game=self)
        elif getattr(enemy, "has_been_attacked_by_team", False):
            leader = getattr(self, "player_pokemon", None)
            if leader:
                leader.defeat_pokemon(enemy, game=self)

    def on_enemy_defeated(self, enemy, exp_gained: int):
        """Called when an enemy Pokémon is defeated by a team member"""
        self.total_enemy_exp += exp_gained
        sp = getattr(enemy, "species_name", "") or (enemy.species_data.get("name", enemy.name) if getattr(enemy, "species_data", None) else enemy.name)
        self.register_encountered_species(sp, was_defeated=True)

    def toggle_compatibility_mode(self) -> bool:
        """Toggles compatibility mode (no-color mode)."""
        self.compatibility_mode = not getattr(self, "compatibility_mode", False)
        return self.compatibility_mode

    def sanitize_rendered_row(self, row: str) -> str:
        """Strips ANSI color escape sequences from a row if compatibility mode is active"""
        if getattr(self, "compatibility_mode", False):
            return COLOR_ESCAPE_REGEX.sub('', row)
        return row

    def sanitize_rendered_rows(self, rows: list[str]) -> list[str]:
        """Strips ANSI color escape sequences from a list of rows if compatibility mode is active"""
        if getattr(self, "compatibility_mode", False):
            return [COLOR_ESCAPE_REGEX.sub('', r) for r in rows]
        return rows

    def show_end_screen(self):
        """Transitions to the run summary screen when game ends"""
        controller = EndScreenController(self, getattr(self, "game_won", False))

        #Flush the screen
        try:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
        except Exception:
            pass

        while controller.is_active:
            rows = controller.render()
            if getattr(self, "compatibility_mode", False):
                rows = self.sanitize_rendered_rows(rows)
            try:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.write("\n".join(rows) + "\n")
                sys.stdout.flush()
            except Exception:
                pass
            try:
                action = game_input.get_key(timeout=None)
            except (StopIteration, RuntimeError):
                controller.is_active = False
                break
            if action is not None:
                controller.handle_input(action)

        #When the run summary is closed, go to the high score screen
        last_entry = getattr(self, "last_run_score_entry", None)
        from high_scores import HighScoreController
        hs_controller = HighScoreController(self, highlight_entry=last_entry)
        self.high_scores_state = {"controller": hs_controller}

        while hs_controller.is_active:
            rows = hs_controller.render()
            if getattr(self, "compatibility_mode", False):
                rows = self.sanitize_rendered_rows(rows)
            try:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.write("\n".join(rows) + "\n")
                sys.stdout.flush()
            except Exception:
                pass
            try:
                action = game_input.get_key(timeout=None)
            except (StopIteration, RuntimeError):
                hs_controller.is_active = False
                break
            if action is not None:
                hs_controller.handle_input(action)

        #Return to the title screen when high score screen is closed
        self.high_scores_state = None
        import random
        self.title_screen_state = {
            "selected_index": 0,
            "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
        }
        self.game_ended = False
        self.game_won = False
        self.is_running = True

    def generate_floor_spawn_list(self):
        """
        Populates a floor's spawning list, generating a list of 5 species to spawn on the current floor.
        Excludes legendary species and prefers species with a BST close to the floor's target BST (1F = 200, +8 per floor, max 600 on 50F).
        Replaces evolved Pokémon that would not have evolved at their spawn level with their "correct" evolution, and ensures no duplicates.
        """
        from pokemon_db import get_valid_evolution_stage

        target_bst = min(600, 200 + (self.floor_number - 1) * 8)
        spawn_level = self.floor_number #Level of wild mons = floor number
        pokemon_db = getattr(self, "pokemon_db", [])

        candidates = [sp for sp in pokemon_db if not sp.get("legendary", False)]
        if not candidates:
            self.floor_spawn_list = list(self.all_species_names[:5])
            return

        weights = []
        for sp in candidates:
            bst = sum(sp.get("base_stats", {}).values())
            diff = abs(bst - target_bst)
            weights.append(1.0 / (1.0 + diff))

        pool = list(candidates)
        pool_weights = list(weights)
        chosen = []

        while len(chosen) < 5 and pool:
            picked = random.choices(pool, weights=pool_weights, k=1)[0]
            idx = pool.index(picked)

            stage_name = get_valid_evolution_stage(picked["name"], spawn_level, pokemon_db)
            if stage_name not in chosen:
                chosen.append(stage_name)

            pool.pop(idx)
            pool_weights.pop(idx)

        self.floor_spawn_list = chosen

    def set_weather(self, weather: str, duration: int = 0):
        """Sets the dungeon weather and prints the appropriate message"""
        msg_map = {
            "Sunny": "The sunlight turned harsh!",
            "Rain": "It began to rain!",
            "Hail": "It began to hail!",
            "Sandstorm": "A sandstorm kicked up!",
            "Clear": "The weather cleared up.",
            "Grassy Terrain": "Grass grew to cover the dungeon!",
            "Electric Terrain": "An electric current runs across the dungeon!"
        }
        self.weather = weather
        self.weather_turns_left = duration
        if weather in msg_map:
            self.log_message(msg_map[weather])

    def get_status_line(self, pokemon: Pokemon, max_len: int = 56) -> str:
        """Formats the status line of a Pokémon's party window, truncated to fit max_len"""
        items = []
        if pokemon.status_effects.get("Sleep", 0) > 0:
            items.append(("Sleep", "negative"))
        if pokemon.status_effects.get("Resting", 0) > 0:
            items.append(("Resting", "negative"))
        if pokemon.status_effects.get("Frozen", 0) > 0:
            items.append(("Frozen", "negative"))
        if pokemon.status_effects.get("Petrified", 0) > 0 or pokemon.status_effects.get("Petrified") == -1:
            items.append(("Petrified", "negative"))
        if pokemon.status_effects.get("Paralysis", 0) > 0:
            items.append(("Paralysis", "negative"))
        if pokemon.status_effects.get("Toxic"):
            items.append(("Toxic", "negative"))
        elif pokemon.status_effects.get("Poison"):
            items.append(("Poison", "negative"))
        if pokemon.status_effects.get("Burn"):
            items.append(("Burn", "negative"))
        if pokemon.status_effects.get("Flinch", 0) > 0:
            items.append(("Flinch", "negative"))
        if pokemon.status_effects.get("Confusion", 0) > 0:
            items.append(("Confusion", "negative"))
        if pokemon.status_effects.get("Puppet", 0) > 0:
            items.append(("Puppet", "negative"))
        if pokemon.status_effects.get("Terrified", 0) > 0:
            items.append(("Terrified", "negative"))
        if pokemon.status_effects.get("Hallucinating", 0) > 0:
            items.append(("Hallucinating", "negative"))
        if pokemon.status_effects.get("Leech Seed", 0) > 0:
            items.append(("Leech Seed", "negative"))
        if pokemon.status_effects.get("Stuck", 0) > 0:
            items.append(("Stuck", "negative"))
        if pokemon.status_effects.get("Wrap", 0) > 0:
            items.append(("Wrapped", "negative"))
        if pokemon.status_effects.get("Sand Tomb", 0) > 0:
            items.append(("Sand Tomb", "negative"))
        if pokemon.status_effects.get("Fire Spin", 0) > 0:
            items.append(("Fire Spin", "negative"))
        if pokemon.status_effects.get("Protect", 0) > 0:
            items.append(("Protect", "positive"))
        if pokemon.status_effects.get("Wide Guard", 0) > 0:
            items.append(("Wide Guard", "positive"))
        if pokemon.status_effects.get("Quick Guard", 0) > 0:
            items.append(("Quick Guard", "positive"))
        if pokemon.status_effects.get("Laser Focus"):
            items.append(("Laser Focus", "positive"))
        if pokemon.status_effects.get("Safeguard", 0) > 0:
            items.append(("Safeguard", "positive"))
        if pokemon.status_effects.get("Focus Energy", 0) > 0:
            items.append(("Focus Energy", "positive"))
        if pokemon.status_effects.get("Counter", 0) > 0:
            items.append(("Counter", "positive"))
        if pokemon.status_effects.get("Mirror Coat", 0) > 0:
            items.append(("Mirror Coat", "positive"))
        if pokemon.status_effects.get("Reflect", 0) > 0:
            items.append(("Reflect", "positive"))
        if pokemon.status_effects.get("Light Screen", 0) > 0:
            items.append(("Light Screen", "positive"))
        if pokemon.status_effects.get("Sleepless"):
            items.append(("Sleepless", "neutral"))
        if pokemon.status_effects.get("Digging", 0) > 0:
            items.append(("Dig", "neutral"))
        if pokemon.status_effects.get("Diving", 0) > 0:
            items.append(("Dive", "neutral"))
        if pokemon.status_effects.get("Encore", 0) > 0:
            items.append(("Encore", "negative"))
        if pokemon.status_effects.get("Magnet Rise", 0) > 0:
            items.append(("Magnet Rise", "positive"))
        if pokemon.status_effects.get("Telekinesis", 0) > 0:
            items.append(("Telekinesis", "positive"))
        if pokemon.status_effects.get("Resting", 0) > 0:
            items.append(("Resting", "neutral"))
        if pokemon.status_effects.get("Drowsy", 0) > 0:
            items.append(("Drowsy", "negative"))
        if pokemon.status_effects.get("Curse"):
            items.append(("Cursed", "negative"))
        if pokemon.status_effects.get("Lock-On"):
            items.append(("Locked On", "positive"))
        if pokemon.status_effects.get("Aqua Ring"):
            items.append(("Aqua Ring", "positive"))
        if pokemon.status_effects.get("Blind", 0) > 0:
            items.append(("Blind", "negative"))
        if pokemon.status_effects.get("Sluggish", 0) > 0:
            items.append(("Sluggish", "negative"))
        if pokemon.status_effects.get("Paused", 0) > 0:
            items.append(("Recharging", "negative"))
        if pokemon.status_effects.get("Ingrain", 0) > 0:
            items.append(("Ingrain", "neutral"))
        if pokemon.status_effects.get("Landed", 0) > 0:
            items.append(("Landed", "neutral"))
        if pokemon.status_effects.get("Friendly"):
            items.append(("Friendly", "positive"))
        if pokemon.status_effects.get("EXP Up"):
            items.append(("EXP Up", "positive"))
        if pokemon.status_effects.get("Snatch", 0) > 0:
            items.append(("Snatch", "positive"))
        if pokemon.status_effects.get("Rebound", 0) > 0:
            items.append(("Rebound", "positive"))
        if pokemon.status_effects.get("Invisible", 0) > 0:
            items.append(("Invisible", "positive"))
        if pokemon.status_effects.get("Cowering", 0) > 0:
            items.append(("Cowering", "negative"))
        if pokemon.status_effects.get("Silenced", 0) > 0:
            items.append(("Silenced", "negative"))
        for res_t in ("Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy", "Normal", "All"):
            if pokemon.status_effects.get(f"{res_t} Resist"):
                items.append((f"{res_t} Res", "positive"))

        spd_stage = pokemon.movement_speed_stage
        if spd_stage == -1:
            items.append(("Slow", "negative"))
        elif spd_stage == 1:
            items.append(("2x Speed", "positive"))
        elif spd_stage == 2:
            items.append(("3x Speed", "positive"))
        elif spd_stage == 3:
            items.append(("4x Speed", "positive"))

        if not items:
            return ""

        visible_len = 0
        parts = []
        for idx, (name, cat) in enumerate(items):
            if idx > 0:
                if visible_len + 2 > max_len:
                    break
                parts.append(", ")
                visible_len += 2

            rem = max_len - visible_len
            if rem <= 0:
                break

            visible_name = name[:rem]
            visible_len += len(visible_name)

            if cat == "positive":
                color_code = "\033[92m"  #Green
            elif cat == "negative":
                color_code = "\033[91m"  #Red
            else:
                color_code = "\033[97m"  #White

            if getattr(self, "compatibility_mode", False):
                parts.append(visible_name)
            else:
                parts.append(f"{color_code}{visible_name}\033[0m")

        return "".join(parts)

    def get_look_around_description(self) -> list[str]:
        """Returns the description of the tile under the look around cursor (max 56x5 lines)"""
        cx, cy = self.look_around_cursor
        currently_visible = self._compute_currently_visible()

        #1. Unseen tile (i.e., a tile that has not been discovered yet)
        if (cx, cy) not in currently_visible and (cx, cy) not in self.explored_tiles:
            return ["Unseen.", "", "", "", ""]

        #2. Pokémon (only if currently visible)
        found_pokemon = None
        if (cx, cy) in currently_visible:
            for p in self.party + self.spawned_pokemon:
                if get_pokemon_position(self, p) == (cx, cy):
                    found_pokemon = p
                    break

        if found_pokemon:
            is_ally = found_pokemon in self.party

            #1st line: Name, HP (allies only), Level (allies only) or HP % (foes only)
            if is_ally:
                line1 = f"{found_pokemon.name} Lv {found_pokemon.level} HP {int(found_pokemon.current_hp)}/{found_pokemon.stats['HP']}"
            else:
                import math
                pct = int(math.ceil((found_pokemon.current_hp / found_pokemon.stats["HP"]) * 100.0))
                pct = min(100, pct)
                line1 = f"{found_pokemon.name} HP {pct}%"

            #2nd line: Known moves (for allies) or seen moves (for foes)
            if is_ally:
                line2 = ", ".join(m["name"] for m in found_pokemon.moves)
            else:
                line2 = ", ".join(m["name"] if m["name"] in found_pokemon.seen_moves else "???" for m in found_pokemon.moves) #Foes' moves are hidden until they have been seen using them.

            #3rd line: List of status effects
            line3 = self.get_status_line(found_pokemon, max_len=56)

            #Last 2 lines: Pokémon description from pokemon.json
            desc = found_pokemon.species_data.get("description", "")
            import textwrap
            wrapped = textwrap.wrap(desc, width=56)
            line4 = wrapped[0] if len(wrapped) > 0 else ""
            line5 = wrapped[1] if len(wrapped) > 1 else ""

            return [line1, line2, line3, line4, line5]

        #3. Item
        if (cx, cy) in self.items_on_floor:
            item = self.items_on_floor[(cx, cy)]
            line1 = items.get_item_display_name(item)
            rarity = item.get("rarity", "Common")
            r_color = items.RARITY_COLORS.get(rarity, "\033[37m")
            line2 = f"{r_color}{rarity}\033[0m"
            desc = item.get("description", "")
            import textwrap
            wrapped = textwrap.wrap(desc, width=56)
            line3 = wrapped[0] if len(wrapped) > 0 else ""
            line4 = wrapped[1] if len(wrapped) > 1 else ""
            line5 = wrapped[2] if len(wrapped) > 2 else ""
            return [line1, line2, line3, line4, line5]

        #4. Stairs (special case)
        if (cx, cy) == getattr(self, "stairs_position", None):
            return ["Stairs to the next floor.", "Press [>] while on these to use.", "", "", ""]

        #5. Wonder Tile (to be used in the future for all trap/special tiles)
        if (cx, cy) == getattr(self, "wonder_tile_position", None):
            if (cx, cy) in currently_visible:
                return ["A Wonder Tile.", "Stepping on this resets a Pokémon's stats to their", "normal levels.", "", ""]
            elif (cx, cy) in self.explored_tiles:
                return ["There was a Wonder Tile here.", "Stepping on this resets a Pokémon's stats to their", "normal levels.", "", ""]
                

        #6. Explored or Visible wall or floor tile.
        from dungeon import WALL_CHAR
        char = self.floor.grid[cy][cx]
        if (cx, cy) not in currently_visible:
            if char == WALL_CHAR:
                return ["There was a wall here.", "", "", "", ""]
            else:
                return ["There was a floor here.", "", "", "", ""]

        if char == WALL_CHAR:
            return ["A wall.", "", "", "", ""]
        else:
            return ["The floor.", "", "", "", ""]

    def is_message_important(self, text: str) -> bool:
        """Determines if a message is important, which forces a [MORE] prompt"""
        if not text:
            return False
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        lower_text = clean_text.lower()

        important_keywords = [
            "oh, no!",
            "took over as team leader",
            "team was wiped out",
            "congratulations!",
        ]
        if any(kw in lower_text for kw in important_keywords):
            return True

        return False

    def colorize_log_message(self, text: str, important: bool = False) -> str:
        """Applies color coding to ally names (yellow), enemy names (blue), and moves (green) in the message log.
        Also, if important is True, surrounds the message in red ANSI escape codes
        """
        if getattr(self, "compatibility_mode", False):
            return text
        #Gather ally names
        ally_names = set()
        for p in self.party:
            ally_names.add(p.name)
            if "species" in p.species_data:
                ally_names.add(p.species_data["species"])

        #Gather enemy names
        enemy_names = set()
        for p in self.spawned_pokemon:
            enemy_names.add(p.name)
            if "species" in p.species_data:
                enemy_names.add(p.species_data["species"])

        #Exclude allies from enemies
        enemy_names = enemy_names - ally_names

        #Map target strings to color escape sequences
        replacements = []

        #1. Ally names (Yellow: \033[93m)
        for name in sorted(ally_names, key=len, reverse=True):
            if name:
                replacements.append((name, "\033[93m"))

        #2. Enemy names (Blue: \033[94m)
        for name in sorted(enemy_names, key=len, reverse=True):
            if name:
                replacements.append((name, "\033[94m"))

        #3. Move names (Green: \033[92m)
        for name in sorted(self.all_move_names, key=len, reverse=True):
            if name:
                replacements.append((name, "\033[92m"))

        reset_color = "\033[91m" if important else "\033[0m"

        for target, color in replacements:
            escaped_target = re.escape(target)
            pattern = re.compile(rf"\b{escaped_target}\b")
            text = pattern.sub(f"{color}{target}{reset_color}", text)
            
        #4. Important messages (overrides everything else)
        if important:
            text = f"\033[91m{text}\033[0m"

        return text

    def start_player_action(self):
        """Starts a new player action period between the player's current action and their next action"""
        if not getattr(self, "turn_in_progress", False):
            self.player_action_number = getattr(self, "player_action_number", 0) + 1
            self._message_log_current_turn = self.player_action_number
            self._turn_messages_count = 0
            self.turn_in_progress = True

    def log_message(self, text: str, important: bool = False):
        """Logs a message with the current turn number, and updates the message log.
        If >5 messages are added in a single turn, displays the [MORE] prompt and pauses the turn until dismissed."""
        import sys
        if getattr(self, "suppress_target_logs", False):
            return

        #Track messages in the current player action turn
        current_action = getattr(self, "player_action_number", 0)
        if getattr(self, "_message_log_current_turn", None) != current_action:
            self._message_log_current_turn = current_action
            self._turn_messages_count = 0

        is_imp = important or self.is_message_important(text)
        turn_active = getattr(self, "turn_in_progress", False)

        #When more than 5 messages have been added in a single turn, prompt [MORE]
        #For most cases, don't display the prompt unless a turn is ongoing.
        if turn_active and getattr(self, "_turn_messages_count", 0) >= 5:
            self.message_log.has_more_page = True
            self.render()
            if not getattr(self, "suppress_animation_delay", False):
                game_input.get_key()
            self.message_log.has_more_page = False
            self._turn_messages_count = 0

        colorized = self.colorize_log_message(text, important=is_imp)
        self.message_log.log(colorized, current_action, important=is_imp)
        self._turn_messages_count = getattr(self, "_turn_messages_count", 0) + 1

        if is_imp:
            self.message_log.has_more_page = True
            self.render()
            if not getattr(self, "suppress_animation_delay", False):
                game_input.get_key()
            self.message_log.has_more_page = False
            self._turn_messages_count = 0
        else:
            self.render()

    def is_valid_enemy_spawn_tile(self, x: int, y: int) -> bool:
        """Returns True if (x, y) is a valid tile for dynamic enemy spawning"""
        if not (0 <= x < self.floor.width and 0 <= y < self.floor.height):
            return False
        if self.floor.grid[y][x] != FLOOR_CHAR:
            return False
        if (x, y) == getattr(self, "stairs_position", None):
            return False

        #We don't want the player seeing enemies suddenly appear from nothing, so here's some checks to ensure that Pokémon spawn out of sight
        #Must not be occupied by any Pokémon currently on the map
        all_occupied = [get_pokemon_position(self, p) for p in self.party + self.spawned_pokemon]
        if (x, y) in all_occupied:
            return False

        #Must be at least 10 tiles away from any team Pokémon (Chebyshev distance).
        team_coords = [get_pokemon_position(self, p) for p in self.party]
        for tx, ty in team_coords:
            if max(abs(x - tx), abs(y - ty)) < 10:
                return False

        #Can never spawn inside rooms occupied by at least one team member (merged rooms count)
        room_tiles = get_room_tiles_at(self.floor, x, y)
        if room_tiles:
            for tx, ty in team_coords:
                if (tx, ty) in room_tiles:
                    return False

        return True

    def spawn_initial_items(self):
        """Handles the logic for initial item spawns on the floor.
        Each floor should contain around 10 items, with one Apple or Apricorn and one Elixir guaranteed to spawn per floor.
        """
        import random
        self.items_on_floor = {}
        
        rooms = list(self.floor.rooms.values())
        if not rooms:
            return

        #Gather valid unoccupied floor tiles per room
        valid_rooms_with_tiles = []
        for room in rooms:
            r_tiles = []
            for ry in range(room.y1, room.y2 + 1):
                for rx in range(room.x1, room.x2 + 1):
                    if self.floor.grid[ry][rx] == FLOOR_CHAR:
                        if (rx, ry) == getattr(self, "stairs_position", None):
                            continue
                        occupied = any(get_pokemon_position(self, p) == (rx, ry) for p in self.party)
                        if not occupied:
                            r_tiles.append((rx, ry))
            if r_tiles:
                valid_rooms_with_tiles.append((room, r_tiles))

        if not valid_rooms_with_tiles:
            return

        #Count 8-12 items
        num_items = random.randint(8, 12)
        r_count = len(valid_rooms_with_tiles)

        #Distribute items roughly equally across rooms
        base = num_items // r_count
        remainder = num_items % r_count
        room_counts = [base] * r_count
        if remainder > 0:
            for idx in random.sample(range(r_count), remainder):
                room_counts[idx] += 1

        selected_tiles = []
        for (_, r_tiles), count in zip(valid_rooms_with_tiles, room_counts):
            cnt = min(count, len(r_tiles))
            if cnt > 0:
                selected_tiles.extend(random.sample(r_tiles, cnt))

        if not selected_tiles:
            return

        #Guaranteed items: Apple or Apricorn, Elixir, and Money ("Poké")
        apple_item = random.choice(["Apple", "Big Apple", "Plain Apricorn", "Blue Apricorn", "Brown Apricorn", "White Apricorn", "Gold Apricorn", "Green Apricorn", "Bronze Apricorn", "Orange Apricorn", "Transparent Apricorn", "Purple Apricorn", "Pink Apricorn", "Red Apricorn", "Indigo Apricorn", "Violet Apricorn", "Yellow Apricorn", "Lime Apricorn"])
        elixir_item = random.choice(["Elixir", "Max Elixir"])
        item_names = [apple_item, elixir_item, "Poké"]

        #Fill remaining slots using weighted random choice based on item rarity
        item_keys = list(items.ITEMS_DB.keys()) + ["Poké"]
        item_weights = [items.RARITY_WEIGHTS.get(items.ITEMS_DB[k].get("rarity", "Common"), 50) if k != "Poké" else 50 for k in item_keys]

        needed = len(selected_tiles) - len(item_names)
        if needed > 0:
            rand_items = random.choices(item_keys, weights=item_weights, k=needed)
            item_names.extend(rand_items)

        item_names = item_names[:len(selected_tiles)]
        random.shuffle(item_names)

        for (tx, ty), item_name in zip(selected_tiles, item_names):
            if item_name == "Poké":
                min_amt = 2
                max_amt = 25 + (4 * self.floor_number)
                item_data = {
                    "name": "Poké",
                    "type": "Money",
                    "amount": random.randint(min_amt, max_amt),
                    "symbol": "P",
                    "appearance": "P",
                    "color": "\033[30;43m",
                    "rarity": "Common"
                }
            else:
                item_data = dict(items.ITEMS_DB[item_name])
                if item_data.get("stackable", False):
                    item_data["count"] = random.randint(3, 6)
            self.items_on_floor[(tx, ty)] = item_data

    def spawn_initial_enemies(self):
        """Spawns napping enemies in non-player rooms with 1% chance per tile on first generation, excluding tiles directly adjacent to corridor entrances"""
        player_room = None
        for room in self.floor.rooms.values():
            if room.x1 <= self.player_x <= room.x2 and room.y1 <= self.player_y <= room.y2:
                player_room = room
                break

        #Iterate over all rooms
        for room in self.floor.rooms.values():
            if room is player_room:
                continue

            #Iterate over every tile of a room. I wonder if this would cause performance issues with larger maps. (It seems fine with 56x32 so far)
            for ry in range(room.y1, room.y2 + 1):
                for rx in range(room.x1, room.x2 + 1):
                    if self.floor.grid[ry][rx] == FLOOR_CHAR:
                        if self.is_tile_adjacent_to_corridor(rx, ry, check_8way=True):
                            continue

                        #Ensure tile isn't occupied
                        occupied = False
                        for p in self.party + self.spawned_pokemon:
                            px, py = get_pokemon_position(self, p)
                            if px == rx and py == ry:
                                occupied = True
                                break
                        if not occupied and (rx, ry) != getattr(self, "stairs_position", None) and (rx, ry) != getattr(self, "wonder_tile_position", None):
                            #1% chance per tile
                            if random.random() < 0.01:
                                species_pool = self.floor_spawn_list if self.floor_spawn_list else self.all_species_names
                                species = random.choice(species_pool)
                                enemy = Pokemon(species, level=self.floor_number)
                                enemy.x = rx
                                enemy.y = ry
                                enemy.napping = True
                                enemy.moves = enemy.moves[-4:]
                                self.spawned_pokemon.append(enemy)
                                self.register_encountered_species(species)

    def spawn_random_enemy(self) -> bool:
        """Attempts to spawn a random active enemy Pokémon on a valid tile"""
        candidates = []
        for y in range(self.floor.height):
            for x in range(self.floor.width):
                if self.is_valid_enemy_spawn_tile(x, y):
                    candidates.append((x, y))

        if not candidates:
            return False

        rx, ry = random.choice(candidates)
        species_pool = self.floor_spawn_list if self.floor_spawn_list else self.all_species_names
        species = random.choice(species_pool)
        enemy = Pokemon(species, level=self.floor_number)
        enemy.x = rx
        enemy.y = ry
        enemy.napping = False #Only fixed spawns will be napping, as in PMD. Calling it "napping" is kind of a misnomer, really their AI is just disabled until woken up
        enemy.moves = enemy.moves[-4:] #Last 4 moves they would know by level up
        self.spawned_pokemon.append(enemy)
        self.register_encountered_species(species)
        return True

    def update_enemy_spawning(self):
        """Handles random Pokémon spawns."""
        if len(self.spawned_pokemon) >= 24: #Maximum spawn limit. Turn this up if you dare
            return

        #Per turn chance of a Pokémon spawning on the floor. Dungeons with no enemies are boring, so the rate is increased if there are no enemies at all on the floor.
        #TODO: Make this floor based, higher floors have higher spawn rates
        chance = 0.08 if not self.spawned_pokemon else 0.03
        if random.random() < chance:
            self.spawn_random_enemy()

    def check_napping_enemies_wakeup(self):
        """Wakes up napping enemies if a team member is on an adjacent square"""
        team_coords = [get_pokemon_position(self, p) for p in self.party]
        for enemy in self.spawned_pokemon:
            if enemy.napping:
                ex, ey = get_pokemon_position(self, enemy)
                for tx, ty in team_coords:
                    if max(abs(ex - tx), abs(ey - ty)) <= 1:
                        enemy.napping = False
                        enemy.just_woke_up = True
                        break

    def check_taunt_wearoff(self):
        """Taunting works differently in the game, so this cures taunted status if taunter is defeated, out of game, or no longer visible to the target"""
        if not hasattr(self, "taunt_sources"):
            return
        to_remove = []
        for target, taunter in list(self.taunt_sources.items()):
            if target not in self.spawned_pokemon and target not in self.party:
                to_remove.append(target)
                continue

            is_defeated = False
            if taunter is None or int(getattr(taunter, "current_hp", 0)) <= 0:
                is_defeated = True
            elif taunter not in self.spawned_pokemon and taunter not in self.party:
                is_defeated = True

            if is_defeated or not self.enemy_can_see(target, taunter):
                target.cure_status("Taunted", self)
                to_remove.append(target)

        for t in to_remove:
            if t in self.taunt_sources:
                del self.taunt_sources[t]

    def enemy_can_see(self, enemy: Pokemon, team_member: Pokemon) -> bool:
        """Returns True if the enemy can see the team member"""
        if team_member.status_effects.get("Invisible", 0) > 0:
            return False

        ex, ey = get_pokemon_position(self, enemy)
        tx, ty = get_pokemon_position(self, team_member)

        #Inside a room: Check if both are in the same room (taking merged rooms into account)
        enemy_room_tiles = get_room_tiles_at(self.floor, ex, ey)
        if enemy_room_tiles and (tx, ty) in enemy_room_tiles:
            return True

        #Outside a room: within visibility radius (5 normally, 100 (unlimited) when floor_luminous) and has line of sight
        dist = max(abs(ex - tx), abs(ey - ty))
        radius = 100 if getattr(self, "floor_luminous", False) else 5
        if dist <= radius:
            return self._has_line_of_sight(ex, ey, tx, ty)

        return False

    def can_enemy_step_to(self, enemy: Pokemon, x: int, y: int, dx: int, dy: int) -> bool:
        """Returns True if the enemy can move to the tile (x, y)"""
        #Status effects that prevent movement
        if enemy.status_effects.get("Fire Spin", 0) > 0:
            return False
        if enemy.status_effects.get("Wrap", 0) > 0:
            return False
        if enemy.status_effects.get("Sand Tomb", 0) > 0:
            return False
        if enemy.status_effects.get("Stuck", 0) > 0 or enemy.status_effects.get("Ingrain", 0) > 0:
            return False
        if not (0 <= x < self.floor.width and 0 <= y < self.floor.height):
            return False

        has_mobile = (enemy.status_effects.get("Mobile", 0) > 0)
        is_wall = (self.floor.grid[y][x] == WALL_CHAR)

        if is_wall and not has_mobile:
            return False

        #Check target tile occupancy
        for p in self.party + self.spawned_pokemon:
            if p is enemy:
                continue
            px, py = get_pokemon_position(self, p)
            if px == x and py == y:
                return False

        #Pokémon movement can't cut corners unless Mobile
        if not has_mobile and dx != 0 and dy != 0:
            c1 = self.floor.grid[enemy.y][x]
            c2 = self.floor.grid[y][enemy.x]
            if c1 == WALL_CHAR or c2 == WALL_CHAR:
                return False

        return True

    def get_target_directed_candidate_dirs(self, primary_dir: tuple[int, int]) -> list[tuple[int, int]]:
        """Returns the 8 directions starting with primary_dir, prioritizing CCW over CW (used for AI obstacle avoidance)."""
        DIRECTIONS_CW = [
            (0, -1),   # Up
            (1, -1),   # Up-Right
            (1, 0),    # Right
            (1, 1),    # Down-Right
            (0, 1),    # Down
            (-1, 1),   # Down-Left
            (-1, 0),   # Left
            (-1, -1)   # Up-Left
        ]
        if primary_dir not in DIRECTIONS_CW:
            return list(DIRECTIONS_CW)
        idx = DIRECTIONS_CW.index(primary_dir)
        offsets = [0, -1, 1, -2, 2, -3, 3, 4]
        return [DIRECTIONS_CW[(idx + off) % 8] for off in offsets]

    def find_path_to_target(self, enemy: Pokemon, tx: int, ty: int) -> tuple[int, int] | None:
        """Finds the first step (dx, dy) on the shortest path from enemy to (tx, ty) using BFS, with obstacle avoidance"""
        ex, ey = get_pokemon_position(self, enemy)
        if (ex, ey) == (tx, ty):
            return None

        from collections import deque
        from dungeon import WALL_CHAR
        queue: deque[tuple[int, int, int, int]] = deque()
        visited = {(ex, ey)}

        #Initial steps from enemy position, prioritizing CCW over CW
        p_dx = 1 if tx > ex else (-1 if tx < ex else 0)
        p_dy = 1 if ty > ey else (-1 if ty < ey else 0)
        init_dirs = self.get_target_directed_candidate_dirs((p_dx, p_dy))

        for dx, dy in init_dirs:
            nx, ny = ex + dx, ey + dy
            if self.can_enemy_step_to(enemy, nx, ny, dx, dy):
                if (nx, ny) == (tx, ty):
                    return (dx, dy)
                visited.add((nx, ny))
                queue.append((nx, ny, dx, dy))

        if enemy in self.party:
            occupied = {get_pokemon_position(self, p) for p in self.spawned_pokemon if int(getattr(p, "current_hp", 0)) > 0}
        else:
            occupied = {get_pokemon_position(self, p) for p in self.party + self.spawned_pokemon if p is not enemy and int(getattr(p, "current_hp", 0)) > 0}

        while queue:
            cx, cy, fdx, fdy = queue.popleft()
            if (cx, cy) == (tx, ty):
                return (fdx, fdy)

            p_cx = 1 if tx > cx else (-1 if tx < cx else 0)
            p_cy = 1 if ty > cy else (-1 if ty < cy else 0)
            step_dirs = self.get_target_directed_candidate_dirs((p_cx, p_cy))

            for dx, dy in step_dirs:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height):
                    continue
                if self.floor.grid[ny][nx] != FLOOR_CHAR:
                    continue
                if (nx, ny) in occupied and (nx, ny) != (tx, ty):
                    continue
                #Check if cutting corners
                if dx != 0 and dy != 0:
                    c1 = self.floor.grid[cy][nx]
                    c2 = self.floor.grid[ny][cx]
                    if c1 == WALL_CHAR or c2 == WALL_CHAR:
                        continue
                visited.add((nx, ny))
                queue.append((nx, ny, fdx, fdy))

        return None

    def get_ai_step_towards(self, mon: Pokemon, tx: int, ty: int) -> tuple[int, int] | None:
        """Determines the next step (dx, dy) for an AI-controlled Pokémon moving towards its target (tx, ty).
        If an obstacle is encountered, attempts to step around the obstacle, prioritizing counterclockwise directions over clockwise directions"""
        mx, my = get_pokemon_position(self, mon)
        if (mx, my) == (tx, ty):
            return None

        #1. Try finding a full path using BFS
        path_dir = self.find_path_to_target(mon, tx, ty)
        if path_dir:
            pdx, pdy = path_dir
            if self.can_enemy_step_to(mon, mx + pdx, my + pdy, pdx, pdy):
                return path_dir

        #2. If BFS found no path, test candidate directions around the obstacle
        p_dx = 1 if tx > mx else (-1 if tx < mx else 0)
        p_dy = 1 if ty > my else (-1 if ty < my else 0)
        candidate_dirs = self.get_target_directed_candidate_dirs((p_dx, p_dy))

        for cdx, cdy in candidate_dirs:
            nx, ny = mx + cdx, my + cdy
            if self.can_enemy_step_to(mon, nx, ny, cdx, cdy):
                return (cdx, cdy)

        return None

    def get_valid_path_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Returns a list of (dx, dy) representing valid adjacent floor tiles that do not cut corners."""
        valid = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                    if self.floor.grid[ny][nx] == FLOOR_CHAR:
                        #Check if cutting corners
                        if dx != 0 and dy != 0:
                            c1 = self.floor.grid[y][nx]
                            c2 = self.floor.grid[ny][x]
                            if c1 == WALL_CHAR or c2 == WALL_CHAR:
                                continue
                        valid.append((dx, dy))
        return valid

    def is_move_effective_for_ai(self, move: dict, attacker, target) -> bool:
        """
        This script determines whether a move is appropriate for the AI to use given its current situation.
        By default, the AI won't use status moves that apply a status if the target already has that status, or moves that lower/raise stats if they're already at max/min.
        The exception to both cases is if the move in question also deals damage.
        This will be improved in the future.
        """
        if move.get("name") == "Copycat" or any(e.get("effect_type") == "copycat" for e in move.get("effects", [])):
            if not getattr(self, "last_move_used_successfully", None):
                return False
            last_move, last_attacker = self.last_move_used_successfully
            BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
            if last_attacker == attacker or last_move.get("name") in BLACKLIST_COPIABLE:
                return False
            valid_targets = get_valid_targets(self, attacker, last_move)
            if not valid_targets:
                return False
            if target in valid_targets:
                return self.is_move_effective_for_ai(last_move, attacker, target)
            if target == attacker and attacker in valid_targets:
                return self.is_move_effective_for_ai(last_move, attacker, attacker)
            rel_pokes = self.party if attacker not in self.party else self.spawned_pokemon
            eff_target = next((t for t in valid_targets if t in rel_pokes), None)
            if eff_target:
                return self.is_move_effective_for_ai(last_move, attacker, eff_target)
            return False

        #Damaging moves are always considered effective
        if move.get("category") in ("Physical", "Special") or move.get("power") is not None:
            return True

        effects = move.get("effects", [])
        if not effects:
            return True

        has_useful_effect = False
        for effect in effects:
            eff_type = effect.get("effect_type")
            target_name = effect.get("target", "defender")
            eff_target = attacker if target_name == "attacker" else target

            if eff_type == "status_apply":
                status_name = effect.get("status")
                if status_name:
                    if status_name == "Slow":
                        is_slowed = getattr(eff_target, "movement_speed_stage", 0) < 0 or eff_target.status_effects.get("Slow", 0) > 0
                        if not is_slowed:
                            has_useful_effect = True
                    elif status_name == "2x Speed" or status_name == "3x Speed" or status_name == "4x Speed":
                        if getattr(eff_target, "movement_speed_stage", 0) < 3:
                            has_useful_effect = True
                    else:
                        val = eff_target.status_effects.get(status_name, 0)
                        if not val:
                            has_useful_effect = True
                        elif status_name == "Sleep" and move.get("name") == "Hypnosis":
                            attacker_is_team = attacker in self.party
                            target_is_team = eff_target in self.party
                            if attacker_is_team != target_is_team:
                                has_useful_effect = True
                        
            elif eff_type == "stat_change":
                stat = effect.get("stat")
                stages = effect.get("stages", 0)
                if stat:
                    if stat == "Movement_Speed":
                        curr_stage = getattr(eff_target, "movement_speed_stage", 0)
                        if stages > 0 and curr_stage < 3:
                            has_useful_effect = True
                        elif stages < 0 and curr_stage > -1:
                            has_useful_effect = True
                    else:
                        curr_stage = eff_target.stat_modifiers.get(stat, 0)
                        if stages > 0 and curr_stage < 6:
                            has_useful_effect = True
                        elif stages < 0 and curr_stage > -6:
                            has_useful_effect = True
                        
            elif eff_type == "healing":
                max_hp = eff_target.stats.get("HP", 100)
                if int(eff_target.current_hp) < max_hp:
                    has_useful_effect = True
            else:
                has_useful_effect = True

        return has_useful_effect

    def handle_sleep_turn(self, pokemon: Pokemon) -> bool:
        """Handles automatic execution of Snore or Sleep Talk if the Pokémon is asleep. Returns True if a move was executed"""
        if not (pokemon.status_effects.get("Sleep", 0) > 0 or pokemon.status_effects.get("Resting", 0) > 0):
            return False

        knows_snore = any(m.get("name") == "Snore" for m in pokemon.moves)
        knows_sleep_talk = any(m.get("name") == "Sleep Talk" for m in pokemon.moves)

        if not (knows_snore or knows_sleep_talk):
            return False

        #Check for adjacent enemies. Prioritize Snore if there are adjacent enemies, since it is more consistent
        px, py = get_pokemon_position(self, pokemon)
        adj_enemies = []
        possible_enemies = self.spawned_pokemon if pokemon in self.party else self.party
        for enemy in possible_enemies:
            if int(enemy.current_hp) > 0:
                ex, ey = get_pokemon_position(self, enemy)
                if max(abs(px - ex), abs(py - ey)) <= 1:
                    adj_enemies.append(enemy)

        from pokemon import _get_move_data
        snore_move = _get_move_data("Snore") if knows_snore else None
        sleep_talk_move = _get_move_data("Sleep Talk") if knows_sleep_talk else None

        if knows_snore and adj_enemies and snore_move:
            self.execute_multi_move(pokemon, adj_enemies, snore_move, free=True)
            return True
        elif knows_sleep_talk and sleep_talk_move:
            self.execute_single_move(pokemon, pokemon, sleep_talk_move, free=True)
            return True

        return False

    def check_ally_auto_pickup(self, ally: Pokemon, x: int, y: int):
        """Checks if an ally stepped onto an item tile and picks it up if inventory space is available"""
        if (x, y) not in self.items_on_floor:
            return
        item = self.items_on_floor[(x, y)]
        if item.get("dropped_by_player", False):
            return
        if item.get("type") == "Money" or item.get("name") == "Poké":
            amount = item.get("amount", 0)
            self.money += amount
            del self.items_on_floor[(x, y)]
            self.log_message(f"{ally.name} picked up {amount} \033[30;43mP\033[0m.")
            return
        item_disp = items.get_item_display_name(item)
        success = self.add_item_to_inventory(item)
        if success:
            if item.get("stackable", False) and item.get("count", 0) > 0:
                self.log_message(f"{ally.name} picked up some of the {item['name']}s.")
            else:
                del self.items_on_floor[(x, y)]
                self.log_message(f"{ally.name} picked up the {item_disp}.")
        else:
            self.log_message(f"{ally.name} passed over the {item_disp}.")

    def process_roaming_ai(self, mon: Pokemon):
        """Processes standard wandering/roaming AI for a Pokémon (inside room or corridor)"""
        ex, ey = get_pokemon_position(self, mon)
        room_tiles = get_room_tiles_at(self.floor, ex, ey)

        if room_tiles:
            exits = set()
            for rx, ry in room_tiles:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = rx + dx, ry + dy
                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                        if self.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) not in room_tiles:
                            exits.add((nx, ny))

            if not getattr(mon, "target_exit", None) or mon.target_exit not in exits or (ex, ey) == mon.target_exit:
                if exits:
                    mon.target_exit = random.choice(list(exits))
                else:
                    mon.target_exit = None

            if mon.target_exit:
                tx, ty = mon.target_exit
                step = self.get_ai_step_towards(mon, tx, ty)
                if step:
                    best_dx, best_dy = step
                    nx, ny = ex + best_dx, ey + best_dy
                    self.set_poke_pos(mon, nx, ny)
                    mon.last_dx, mon.last_dy = best_dx, best_dy
                    if mon in self.party:
                        self.check_ally_auto_pickup(mon, nx, ny)
                else:
                    mon.target_exit = None
            else:
                neighbors = self.get_valid_path_neighbors(ex, ey)
                if neighbors:
                    dx, dy = random.choice(neighbors)
                    nx, ny = ex + dx, ey + dy
                    if self.can_enemy_step_to(mon, nx, ny, dx, dy):
                        self.set_poke_pos(mon, nx, ny)
                        mon.last_dx, mon.last_dy = dx, dy
                        if mon in self.party:
                            self.check_ally_auto_pickup(mon, nx, ny)
        else:
            neighbors = self.get_valid_path_neighbors(ex, ey)
            if not neighbors:
                return

            last_dx, last_dy = getattr(mon, "last_dx", 0), getattr(mon, "last_dy", 0)

            if len(neighbors) == 1:
                dx, dy = neighbors[0]
            elif len(neighbors) >= 3:
                opposite = (-last_dx, -last_dy)
                junction_choices = [n for n in neighbors if n != opposite]
                if junction_choices:
                    dx, dy = random.choice(junction_choices)
                else:
                    dx, dy = random.choice(neighbors)
            else:
                if (last_dx, last_dy) in neighbors:
                    dx, dy = last_dx, last_dy
                else:
                    opposite = (-last_dx, -last_dy)
                    choices = [n for n in neighbors if n != opposite]
                    if choices:
                        dx, dy = random.choice(choices)
                    else:
                        dx, dy = random.choice(neighbors)

            nx, ny = ex + dx, ey + dy
            if self.can_enemy_step_to(mon, nx, ny, dx, dy):
                self.set_poke_pos(mon, nx, ny)
                mon.last_dx, mon.last_dy = dx, dy
                if mon in self.party:
                    self.check_ally_auto_pickup(mon, nx, ny)
            else:
                #Forward path in corridor is blocked (e.g. met another wandering Pokémon coming in opposite direction)
                alt_choices = [n for n in neighbors if n != (dx, dy)]
                if alt_choices:
                    opposite = (-dx, -dy)
                    if opposite in alt_choices:
                        alt_dx, alt_dy = opposite
                    else:
                        alt_dx, alt_dy = random.choice(alt_choices)

                    alt_nx, alt_ny = ex + alt_dx, ey + alt_dy
                    if self.can_enemy_step_to(mon, alt_nx, alt_ny, alt_dx, alt_dy):
                        self.set_poke_pos(mon, alt_nx, alt_ny)
                        mon.last_dx, mon.last_dy = alt_dx, alt_dy
                        if mon in self.party:
                            self.check_ally_auto_pickup(mon, alt_nx, alt_ny)
                    else:
                        mon.last_dx, mon.last_dy = alt_dx, alt_dy
                else:
                    mon.last_dx, mon.last_dy = dx, dy

    def process_terrified_ai(self, mon: Pokemon):
        """Processes AI turn for a Terrified Pokémon (ally or enemy).
        Terrified Pokémon move away from any Pokémon they see and will not attack.
        If in a room with an enemy, they move toward the nearest exit away from enemies"""
        px, py = get_pokemon_position(self, mon)

        if mon in self.party:
            enemies = [e for e in self.spawned_pokemon if e not in self.party and int(e.current_hp) > 0]
        else:
            enemies = [p for p in self.party if int(p.current_hp) > 0]

        visible_enemies = [e for e in enemies if self.enemy_can_see(mon, e)]

        #If enemies are seen in a room, consider what exits are there and which are safe
        if visible_enemies:
            room_tiles = get_room_tiles_at(self.floor, px, py)
            if room_tiles:
                exits = set()
                for rx, ry in room_tiles:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = rx + dx, ry + dy
                        if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                            if self.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) not in room_tiles:
                                exits.add((nx, ny))

                safe_exits = []
                for ex_x, ex_y in exits:
                    in_enemy_direction = False
                    for e in visible_enemies:
                        ex_dist = max(abs(ex_x - e.x), abs(ex_y - e.y))
                        mon_dist = max(abs(px - e.x), abs(py - e.y))
                        dot = (ex_x - px) * (e.x - px) + (ex_y - py) * (e.y - py)
                        if ex_dist < mon_dist or dot > 0:
                            in_enemy_direction = True
                            break
                    if not in_enemy_direction:
                        safe_exits.append((ex_x, ex_y))

                #Target a safe exit if there is one
                if safe_exits:
                    safe_exits.sort(key=lambda exit_pos: max(abs(exit_pos[0] - px), abs(exit_pos[1] - py)))
                    tx, ty = safe_exits[0]
                    step = self.get_ai_step_towards(mon, tx, ty)
                    if step:
                        pdx, pdy = step
                        nx, ny = px + pdx, py + pdy
                        self.set_poke_pos(mon, nx, ny)
                        mon.last_dx, mon.last_dy = pdx, pdy
                        if mon in self.party:
                            self.check_ally_auto_pickup(mon, nx, ny)
                        return

            candidates = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = px + dx, py + dy
                    #Consider which direction maximizes distance from the enemy and target that tile
                    if self.can_enemy_step_to(mon, nx, ny, dx, dy):
                        min_enemy_dist = min(max(abs(nx - e.x), abs(ny - e.y)) for e in visible_enemies)
                        sum_enemy_dist = sum(max(abs(nx - e.x), abs(ny - e.y)) for e in visible_enemies)
                        candidates.append((min_enemy_dist, sum_enemy_dist, dx, dy))

            if candidates:
                candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
                best_min_dist = candidates[0][0]
                best_candidates = [c for c in candidates if c[0] == best_min_dist]
                _, _, bdx, bdy = random.choice(best_candidates)
                nx, ny = px + bdx, py + bdy
                self.set_poke_pos(mon, nx, ny)
                mon.last_dx, mon.last_dy = bdx, bdy
                if mon in self.party:
                    self.check_ally_auto_pickup(mon, nx, ny)
                return
        else:
            #No enemies in sight, default to roaming
            self.process_roaming_ai(mon)

    def process_hallucinating_ai(self, mon: Pokemon):
        """Processes AI turn for a Hallucinating Pokémon
        Hallucinating Pokémon move in random directions each turn without attacking"""
        if int(mon.current_hp) <= 0 or not self.is_running:
            return

        px, py = get_pokemon_position(self, mon)
        dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
        random.shuffle(dirs)

        for rdx, rdy in dirs:
            nx, ny = px + rdx, py + rdy
            if self.can_enemy_step_to(mon, nx, ny, rdx, rdy):
                self.set_poke_pos(mon, nx, ny)
                mon.last_dx, mon.last_dy = rdx, rdy
                if mon in self.party:
                    self.check_ally_auto_pickup(mon, nx, ny)
                return

        #If no step could be made, just set direction
        rdx, rdy = random.choice(dirs)
        mon.last_dx, mon.last_dy = rdx, rdy

    def process_puppet_ai(self, mon: Pokemon):
        """Processes AI for Pokémon under the Puppet status effect,
        which causes the Pokémon to attack other teammates at random, ignoring enemies.
        """
        if int(mon.current_hp) <= 0 or not self.is_running:
            return

        if self.process_charging_move(mon):
            return

        other_teammates = [m for m in self.party if m is not mon and int(m.current_hp) > 0]
        if not other_teammates:
            return

        ax, ay = get_pokemon_position(self, mon)

        #1. Check for usable moves that can hit other teammates
        ready_moves = []
        if mon.status_effects.get("Flinch", 0) <= 0 and mon.status_effects.get("Paused", 0) <= 0:
            enabled_moves = [m for m in mon.moves if m.get("enabled", True)]
            has_usable_enabled = any(mon.can_use_move(m, game=self) for m in enabled_moves)
            if mon.can_struggle(game=self) or not has_usable_enabled:
                from pokemon import _get_move_data
                struggle_move = _get_move_data("Struggle")
                valid_targets = get_valid_targets(self, mon, struggle_move)
                rel_targets = [t for t in valid_targets if t in other_teammates]
                if rel_targets:
                    ready_moves.append((struggle_move, rel_targets))
            else:
                for move in enabled_moves:
                    if mon.can_use_move(move, game=self):
                        valid_targets = get_valid_targets(self, mon, move)
                        rel_targets = [t for t in valid_targets if t in other_teammates]
                        if rel_targets:
                            ready_moves.append((move, rel_targets))

        if ready_moves:
            chosen_move, mate_targets = random.choice(ready_moves)
            range_str = chosen_move.get("range", "Adjacent enemy")
            if range_str == "Enemy in front":
                range_str = "Adjacent enemy"

            is_multi = range_str.startswith("All ")
            if is_multi:
                self.execute_multi_move(mon, mate_targets, chosen_move)
            elif range_str == "Straight line piercing":
                chosen_target = random.choice(mate_targets)
                tx, ty = get_pokemon_position(self, chosen_target)
                dx = 1 if tx > ax else (-1 if tx < ax else 0)
                dy = 1 if ty > ay else (-1 if ty < ay else 0)
                line_targets = self.get_line_piercing_targets(mon, chosen_move, dx, dy)
                if not line_targets:
                    line_targets = [chosen_target]
                self.execute_multi_move(mon, line_targets, chosen_move)
            else:
                chosen_target = random.choice(mate_targets)
                self.execute_single_move(mon, chosen_target, chosen_move)
            return

        #2. Movement towards other teammates if not in attack range
        target_mate = random.choice(other_teammates)
        tx, ty = get_pokemon_position(self, target_mate)
        step = self.get_ai_step_towards(mon, tx, ty)
        if step:
            dx, dy = step
            nx, ny = ax + dx, ay + dy
            self.set_poke_pos(mon, nx, ny)
            mon.last_dx, mon.last_dy = dx, dy
            if mon in self.party and mon is not self.player_pokemon:
                self.check_ally_auto_pickup(mon, nx, ny)

    def process_ally_turns(self):
        """Default AI for non-leader teammates (allies) in self.party."""
        for ally in list(self.party):
            if ally is self.player_pokemon or int(ally.current_hp) <= 0:
                continue

            #If ally swapped this turn, don't run the AI
            if getattr(ally, "swapped_this_turn", False):
                ally.swapped_this_turn = False
                continue

            #Don't move if asleep
            if ally.status_effects.get("Sleep", 0) > 0 or ally.status_effects.get("Resting", 0) > 0:
                self.handle_sleep_turn(ally)
                continue

            #Don't move on the first turn after waking up
            if ally.just_woke_up:
                ally.just_woke_up = False
                continue

            #Don't move if wrapped
            is_wrapped_target = False
            for binding in self.wrap_bindings:
                if ally == binding["defender"]:
                    is_wrapped_target = True
                    break
            if is_wrapped_target:
                continue

            actions = self.get_pokemon_actions_this_turn(ally)
            for _ in range(actions):
                if int(ally.current_hp) <= 0 or not self.is_running:
                    break

                #Don't move if charging a move
                if self.process_charging_move(ally):
                    continue

                if ally.status_effects.get("Puppet", 0) > 0:
                    self.process_puppet_ai(ally)
                    continue

                if ally.status_effects.get("Terrified", 0) > 0:
                    self.process_terrified_ai(ally)
                    continue

                if ally.status_effects.get("Hallucinating", 0) > 0:
                    self.process_hallucinating_ai(ally)
                    continue

                #Confusion handling
                if ally.status_effects.get("Confusion", 0) > 0:
                    enabled_moves = [m for m in ally.moves if m.get("enabled", True)]
                    usable_moves = [m for m in enabled_moves if ally.can_use_move(m, game=self)]
                    if not usable_moves and (ally.can_struggle(game=self) or not any(ally.can_use_move(m, game=self) for m in enabled_moves)):
                        from pokemon import _get_move_data
                        usable_moves = [_get_move_data("Struggle")]

                    moves_with_enemy = []
                    for m in usable_moves:
                        v_targets = get_valid_targets(self, ally, m)
                        if any(t in self.spawned_pokemon and t not in self.party and int(t.current_hp) > 0 for t in v_targets):
                            moves_with_enemy.append(m)

                    if moves_with_enemy and random.randint(1, 100) <= 50:
                        chosen_move = random.choice(moves_with_enemy)
                        targets = get_confusion_targets(self, ally, chosen_move)
                        if not targets:
                            try:
                                ally.use_move(chosen_move, game=self)
                                self.moved_used_this_turn.add(ally)
                            except ValueError as e:
                                self.log_message(f"Error! {str(e)} Please report this to C4!")
                                continue
                            self.log_message(f"{ally.name} used {chosen_move['name']}!")
                            self.log_message("The move failed!")
                        else:
                            range_str = chosen_move.get("range", "Adjacent enemy")
                            if range_str == "Enemy in front":
                                range_str = "Adjacent enemy"
                            is_multi = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower()
                            if is_multi:
                                self.execute_multi_move(ally, targets, chosen_move)
                            else:
                                self.execute_single_move(ally, targets[0], chosen_move)
                        continue

                    ax, ay = get_pokemon_position(self, ally)
                    dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                    rdx, rdy = random.choice(dirs)
                    nx, ny = ax + rdx, ay + rdy
                    if self.can_enemy_step_to(ally, nx, ny, rdx, rdy):
                        ally.x = nx
                        ally.y = ny
                        ally.last_dx, ally.last_dy = rdx, rdy
                    else:
                        ally.last_dx, ally.last_dy = rdx, rdy
                    continue

                #Blindness for NPC allies: move in a straight line until bumping into something, then 50% chance to attack or move in a different direction
                if ally.status_effects.get("Blind", 0) > 0:
                    ax, ay = get_pokemon_position(self, ally)
                    last_dx = getattr(ally, "last_dx", 0)
                    last_dy = getattr(ally, "last_dy", 0)
                    if last_dx == 0 and last_dy == 0:
                        dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                        last_dx, last_dy = random.choice(dirs)
                    nx, ny = ax + last_dx, ay + last_dy
                    if self.can_enemy_step_to(ally, nx, ny, last_dx, last_dy):
                        self.set_poke_pos(ally, nx, ny)
                        ally.last_dx, ally.last_dy = last_dx, last_dy
                    else:
                        if random.randint(1, 100) <= 50:
                            ready_moves = [m for m in ally.moves if m.get("enabled", True) and ally.can_use_move(m, game=self)]
                            if ready_moves:
                                m = random.choice(ready_moves)
                                targets = get_valid_targets(self, ally, m)
                                front_targets = [t for t in targets if get_pokemon_position(self, t) == (nx, ny)]
                                if front_targets:
                                    self.execute_single_move(ally, front_targets[0], m)
                        else:
                            other_dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0) and (dx, dy) != (last_dx, last_dy)]
                            rdx, rdy = random.choice(other_dirs)
                            r_nx, r_ny = ax + rdx, ay + rdy
                            if self.can_enemy_step_to(ally, r_nx, r_ny, rdx, rdy):
                                self.set_poke_pos(ally, r_nx, r_ny)
                            ally.last_dx, ally.last_dy = rdx, rdy
                    continue

                #Normal AI
                ax, ay = get_pokemon_position(self, ally)
                leader_pos = get_pokemon_position(self, self.player_pokemon)
                ally_room = get_room_tiles_at(self.floor, ax, ay)
                leader_room = get_room_tiles_at(self.floor, leader_pos[0], leader_pos[1])
                is_leader_in_same_room = bool(ally_room and leader_room and ally_room == leader_room)

                #1. Check if any enemy is in attack range
                ready_moves = []
                if ally.status_effects.get("Flinch", 0) <= 0 and ally.status_effects.get("Paused", 0) <= 0:
                    enabled_moves = [m for m in ally.moves if m.get("enabled", True)]
                    has_usable_enabled = any(ally.can_use_move(m, game=self) for m in enabled_moves)
                    if ally.can_struggle(game=self) or not has_usable_enabled:
                        from pokemon import _get_move_data
                        struggle_move = _get_move_data("Struggle")
                        valid_targets = get_valid_targets(self, ally, struggle_move)
                        rel_targets = [
                            t for t in valid_targets 
                            if (t in self.spawned_pokemon and t not in self.party)
                            and not is_ally_in_way_of_attack(self, ally, t, struggle_move)
                        ]
                        if rel_targets:
                            ready_moves.append((struggle_move, rel_targets))
                    else:
                        for move in enabled_moves:
                            if ally.can_use_move(move, game=self):
                                valid_targets = get_valid_targets(self, ally, move)
                                rel_targets = [
                                    t for t in valid_targets 
                                    if (t in self.spawned_pokemon and t not in self.party)
                                    and not is_ally_in_way_of_attack(self, ally, t, move)
                                ]
                                if rel_targets:
                                    best_target = rel_targets[0]
                                    if self.is_move_effective_for_ai(move, ally, best_target):
                                        ready_moves.append((move, rel_targets))

                if ready_moves:
                    chosen_move, enemy_targets = random.choice(ready_moves)
                    range_str = chosen_move.get("range", "Adjacent enemy")
                    if range_str == "Enemy in front":
                        range_str = "Adjacent enemy"

                    is_multi = range_str.startswith("All ")
                    if is_multi:
                        self.execute_multi_move(ally, enemy_targets, chosen_move)
                    elif range_str == "Straight line piercing":
                        chosen_target = random.choice(enemy_targets)
                        tx, ty = get_pokemon_position(self, chosen_target)
                        dx = 1 if tx > ax else (-1 if tx < ax else 0)
                        dy = 1 if ty > ay else (-1 if ty < ay else 0)
                        line_targets = self.get_line_piercing_targets(ally, chosen_move, dx, dy)
                        if not line_targets:
                            line_targets = [chosen_target]
                        self.execute_multi_move(ally, line_targets, chosen_move)
                    else:
                        chosen_target = random.choice(enemy_targets)
                        self.execute_single_move(ally, chosen_target, chosen_move)
                    continue

                #2. Movement Priority
                moved = False

                #Target A: Enemy in sight (prioritized even over following leader, if leader is in the same room)
                visible_enemies = [
                    e for e in self.spawned_pokemon
                    if int(e.current_hp) > 0 and e not in self.party and self.enemy_can_see(ally, e)
                ]
                if visible_enemies and (is_leader_in_same_room or self.enemy_can_see(ally, self.player_pokemon)):
                    visible_enemies.sort(key=lambda e: max(abs(e.x - ax), abs(e.y - ay)))
                    target_enemy = visible_enemies[0]
                    p_dx = 1 if target_enemy.x > ax else (-1 if target_enemy.x < ax else 0)
                    p_dy = 1 if target_enemy.y > ay else (-1 if target_enemy.y < ay else 0)
                    path_dir = self.find_path_to_target(ally, target_enemy.x, target_enemy.y)

                    best_step = None
                    best_score = None

                    candidate_dirs = self.get_target_directed_candidate_dirs((p_dx, p_dy))
                    for pdx, pdy in candidate_dirs:
                        nx, ny = ax + pdx, ay + pdy
                        if self.can_enemy_step_to(ally, nx, ny, pdx, pdy):
                            is_blocked = is_ally_in_way_from_pos(self, ally, nx, ny, target_enemy)
                            has_path = has_clear_path(self.floor, nx, ny, target_enemy.x, target_enemy.y, False)
                            dist = max(abs(target_enemy.x - nx), abs(target_enemy.y - ny))
                            path_penalty = 0 if path_dir == (pdx, pdy) else 1

                            score = (is_blocked or not has_path, dist, path_penalty)
                            if best_score is None or score < best_score:
                                best_score = score
                                best_step = (pdx, pdy)

                    if best_step:
                        pdx, pdy = best_step
                        nx, ny = ax + pdx, ay + pdy
                        self.set_poke_pos(ally, nx, ny)
                        ally.last_dx, ally.last_dy = pdx, pdy
                        moved = True
                    elif not moved:
                        step = self.get_ai_step_towards(ally, target_enemy.x, target_enemy.y)
                        if step:
                            pdx, pdy = step
                            self.set_poke_pos(ally, ax + pdx, ay + pdy)
                            ally.last_dx, ally.last_dy = pdx, pdy
                            moved = True

                #Target B: Items on floor (if inventory space available or item is money)
                if not moved and self.items_on_floor:
                    has_inv_space = len(self.inventory) < self.max_inventory_capacity
                    visible_tiles = self._compute_currently_visible()
                    visible_items = []
                    for (ix, iy), item in self.items_on_floor.items():
                        if item.get("dropped_by_player", False):
                            continue
                        is_money = item.get("type") == "Money" or item.get("name") in ("Poké", "Poke")
                        if not has_inv_space and not is_money:
                            continue
                        if (ix, iy) in visible_tiles:
                            dist = max(abs(ix - ax), abs(iy - ay))
                            visible_items.append((dist, ix, iy))

                    if visible_items:
                        visible_items.sort(key=lambda item_info: item_info[0])
                        _, ix, iy = visible_items[0]
                        step = self.get_ai_step_towards(ally, ix, iy)
                        if step:
                            pdx, pdy = step
                            nx, ny = ax + pdx, ay + pdy
                            self.set_poke_pos(ally, nx, ny)
                            ally.last_dx, ally.last_dy = pdx, pdy
                            moved = True
                            self.check_ally_auto_pickup(ally, nx, ny)

                #Target C: Wonder Tile (if in same room and has at least one lowered stat)
                has_lowered_stat = any(stage < 0 for stage in ally.stat_modifiers.values()) or getattr(ally, "movement_speed_stage", 0) < 0
                wonder_pos = getattr(self, "wonder_tile_position", None)
                if not moved and has_lowered_stat and wonder_pos is not None:
                    wx, wy = wonder_pos
                    ally_room = get_room_tiles_at(self.floor, ax, ay)
                    if ally_room and (wx, wy) in ally_room:
                        dist = max(abs(ax - wx), abs(ay - wy))
                        if dist > 0:
                            step = self.get_ai_step_towards(ally, wx, wy)
                            if step:
                                pdx, pdy = step
                                nx, ny = ax + pdx, ay + pdy
                                self.set_poke_pos(ally, nx, ny)
                                ally.last_dx, ally.last_dy = pdx, pdy
                                moved = True

                #Target D: Follow Leader
                if not moved:
                    follow_target = self.player_pokemon
                    tx, ty = get_pokemon_position(self, follow_target)
                    dist = max(abs(ax - tx), abs(ay - ty))
                    if dist > 1:
                        step = self.get_ai_step_towards(ally, tx, ty)
                        if step:
                            pdx, pdy = step
                            nx, ny = ax + pdx, ay + pdy
                            self.set_poke_pos(ally, nx, ny)
                            ally.last_dx, ally.last_dy = pdx, pdy
                            moved = True
                    else:
                        pdx = 1 if tx > ax else (-1 if tx < ax else 0)
                        pdy = 1 if ty > ay else (-1 if ty < ay else 0)
                        if pdx != 0 or pdy != 0:
                            ally.last_dx, ally.last_dy = pdx, pdy

    def process_enemy_turns(self):
        """Processes AI turns for all active (non-napping) enemy Pokémon on the floor"""
        #Process a copy of spawned_pokemon in case the list gets modified (e.g. defeat)
        for enemy in list(self.spawned_pokemon):
            if enemy.status_effects.get("Sleep", 0) > 0 or enemy.status_effects.get("Resting", 0) > 0:
                self.handle_sleep_turn(enemy)
                continue
            if enemy.napping or int(enemy.current_hp) <= 0:
                continue
            if enemy.just_woke_up:
                enemy.just_woke_up = False #Enemies that have just been activated miss a turn, as in PMD
                continue

            #Check if wrapped (wrapped targets cannot attack or move)
            is_wrapped_target = False
            for binding in self.wrap_bindings:
                if enemy == binding["defender"]:
                    is_wrapped_target = True
                    break
            if is_wrapped_target:
                continue

            #Determine allowed actions this turn
            actions = self.get_pokemon_actions_this_turn(enemy)
            for _ in range(actions):
                if enemy.napping or int(enemy.current_hp) <= 0 or not self.is_running:
                    break

                if self.process_charging_move(enemy):
                    continue

                if enemy.status_effects.get("Terrified", 0) > 0:
                    self.process_terrified_ai(enemy)
                    continue

                if enemy.status_effects.get("Hallucinating", 0) > 0:
                    self.process_hallucinating_ai(enemy)
                    continue

                if enemy.status_effects.get("Confusion", 0) > 0: #Confusion has a 50% chance to override movement/attacks to randomize their direction
                    usable_moves = [m for m in enemy.moves if enemy.can_use_move(m, game=self)]
                    if not usable_moves and enemy.can_struggle(game=self):
                        from pokemon import _get_move_data
                        usable_moves = [_get_move_data("Struggle")]

                    moves_with_enemy = []
                    for m in usable_moves:
                        v_targets = get_valid_targets(self, enemy, m)
                        if any((t in self.party or t.status_effects.get("Decoy", 0) > 0) and int(t.current_hp) > 0 for t in v_targets):
                            moves_with_enemy.append(m)

                    if moves_with_enemy and random.randint(1, 100) <= 50:
                        chosen_move = random.choice(moves_with_enemy)
                        targets = get_confusion_targets(self, enemy, chosen_move)
                        if not targets:
                            try:
                                enemy.use_move(chosen_move, game=self)
                                self.moved_used_this_turn.add(enemy)
                            except ValueError as e:
                                self.log_message(f"Error! {str(e)} Please report this to C4!")
                                continue
                            self.log_message(f"{enemy.name} used {chosen_move['name']}!")
                            self.log_message("The move failed!")
                        else:
                            range_str = chosen_move.get("range", "Adjacent enemy")
                            if range_str == "Enemy in front":
                                range_str = "Adjacent enemy"
                            is_multi = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower()
                            if is_multi:
                                self.execute_multi_move(enemy, targets, chosen_move)
                            else:
                                self.execute_single_move(enemy, targets[0], chosen_move)
                        continue

                    #If not attacking, walk in a random direction
                    ex, ey = get_pokemon_position(self, enemy)
                    dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                    rdx, rdy = random.choice(dirs)
                    nx, ny = ex + rdx, ey + rdy
                    if self.can_enemy_step_to(enemy, nx, ny, rdx, rdy):
                        enemy.x = nx
                        enemy.y = ny
                        enemy.last_dx, enemy.last_dy = rdx, rdy
                    else:
                        enemy.last_dx, enemy.last_dy = rdx, rdy
                    continue

                if enemy.status_effects.get("Blind", 0) > 0:
                    ex, ey = get_pokemon_position(self, enemy)
                    last_dx = getattr(enemy, "last_dx", 0)
                    last_dy = getattr(enemy, "last_dy", 0)
                    if last_dx == 0 and last_dy == 0:
                        dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                        last_dx, last_dy = random.choice(dirs)
                    nx, ny = ex + last_dx, ey + last_dy
                    if self.can_enemy_step_to(enemy, nx, ny, last_dx, last_dy):
                        self.set_poke_pos(enemy, nx, ny)
                        enemy.last_dx, enemy.last_dy = last_dx, last_dy
                    else:
                        if random.randint(1, 100) <= 50:
                            ready_moves = [m for m in enemy.moves if enemy.can_use_move(m, game=self)]
                            if ready_moves:
                                m = random.choice(ready_moves)
                                targets = get_valid_targets(self, enemy, m)
                                front_targets = [t for t in targets if get_pokemon_position(self, t) == (nx, ny)]
                                if front_targets:
                                    self.execute_single_move(enemy, front_targets[0], m)
                        else:
                            other_dirs = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0) and (dx, dy) != (last_dx, last_dy)]
                            rdx, rdy = random.choice(other_dirs)
                            r_nx, r_ny = ex + rdx, ey + rdy
                            if self.can_enemy_step_to(enemy, r_nx, r_ny, rdx, rdy):
                                self.set_poke_pos(enemy, r_nx, r_ny)
                            enemy.last_dx, enemy.last_dy = rdx, rdy
                    continue

                #1. Targeting Check: Prioritize visible Decoys first, then visible team members
                visible_decoys = []
                all_candidates = [p for p in self.party + self.spawned_pokemon if p is not enemy and int(p.current_hp) > 0]
                for p in all_candidates:
                    if p.status_effects.get("Decoy", 0) > 0:
                        if self.enemy_can_see(enemy, p):
                            visible_decoys.append(p)

                visible_team_members = []
                target = None
                if visible_decoys:
                    ex, ey = get_pokemon_position(self, enemy)
                    visible_decoys.sort(key=lambda m: max(abs(get_pokemon_position(self, m)[0] - ex), abs(get_pokemon_position(self, m)[1] - ey)))
                    target = visible_decoys[0]
                else:
                    for member in self.party:
                        if int(member.current_hp) > 0:
                            if self.enemy_can_see(enemy, member):
                                visible_team_members.append(member)

                    if visible_team_members:
                        ex, ey = get_pokemon_position(self, enemy)
                        visible_team_members.sort(key=lambda m: max(abs(get_pokemon_position(self, m)[0] - ex), abs(get_pokemon_position(self, m)[1] - ey)))
                        target = visible_team_members[0]

                if target is not None:
                    #2. Combat check: Is the target in range of any move?
                    ready_moves = []
                    if enemy.status_effects.get("Flinch", 0) <= 0 and enemy.status_effects.get("Paused", 0) <= 0:
                        if enemy.can_struggle(game=self):
                            from pokemon import _get_move_data
                            struggle_move = _get_move_data("Struggle")
                            valid_targets = get_valid_targets(self, enemy, struggle_move)
                            rel_targets = [t for t in valid_targets if (t in self.party or t.status_effects.get("Decoy", 0) > 0)]
                            if rel_targets:
                                ready_moves.append((struggle_move, rel_targets))
                        else:
                            for move in enemy.moves:
                                if enemy.can_use_move(move, game=self):
                                    valid_targets = get_valid_targets(self, enemy, move)
                                    if target in valid_targets:
                                        rel_targets = [t for t in valid_targets if (t in self.party or t.status_effects.get("Decoy", 0) > 0)]
                                        if rel_targets and self.is_move_effective_for_ai(move, enemy, target):
                                            ready_moves.append((move, rel_targets))

                    ex, ey = get_pokemon_position(self, enemy)
                    tx, ty = get_pokemon_position(self, target)
                    is_adjacent = max(abs(ex - tx), abs(ey - ty)) <= 1

                    should_attack = False
                    if ready_moves:
                        if is_adjacent or random.random() < 0.5:
                            should_attack = True

                    if should_attack:
                        #Choose a move at random from those with targets in range
                        chosen_move, team_targets = random.choice(ready_moves)
                        range_str = chosen_move.get("range", "Adjacent enemy")
                        if range_str == "Enemy in front":
                            range_str = "Adjacent enemy"

                        is_multi = range_str.startswith("All ")
                        if is_multi:
                            self.execute_multi_move(enemy, team_targets, chosen_move)
                        elif range_str == "Straight line piercing":
                            chosen_target = random.choice(team_targets)
                            ex, ey = get_pokemon_position(self, enemy)
                            tx, ty = get_pokemon_position(self, chosen_target)
                            dx = 1 if tx > ex else (-1 if tx < ex else 0)
                            dy = 1 if ty > ey else (-1 if ty < ey else 0)
                            line_targets = self.get_line_piercing_targets(enemy, chosen_move, dx, dy)
                            if not line_targets:
                                line_targets = [chosen_target]
                            self.execute_multi_move(enemy, line_targets, chosen_move)
                        else:
                            #Choose a target at random from those in range
                            chosen_target = random.choice(team_targets)
                            self.execute_single_move(enemy, chosen_target, chosen_move)
                    else:
                        #Target is visible but out of range of attack moves. Check for usable moves that target the user.
                        user_moves = []
                        if enemy.status_effects.get("Flinch", 0) <= 0 and enemy.status_effects.get("Paused", 0) <= 0:
                            for move in enemy.moves:
                                if move.get("range") == "User" and enemy.can_use_move(move, game=self):
                                    if self.is_move_effective_for_ai(move, enemy, enemy):
                                        user_moves.append(move)

                        if user_moves and random.random() < 0.5: #50% chance to use the move
                            chosen_user_move = random.choice(user_moves)
                            self.execute_single_move(enemy, enemy, chosen_user_move)
                        else:
                            #Target is visible but out of range, so pathfind towards it
                            tx, ty = get_pokemon_position(self, target)
                            ex, ey = get_pokemon_position(self, enemy)

                            is_adjacent = max(abs(ex - tx), abs(ey - ty)) == 1
                            moved = False

                            if is_adjacent:
                                #Prioritize moving orthogonally adjacent to the target if across a corner wall or in corridor
                                p_dx = 1 if tx > ex else (-1 if tx < ex else 0)
                                p_dy = 1 if ty > ey else (-1 if ty < ey else 0)
                                candidate_dirs = self.get_target_directed_candidate_dirs((p_dx, p_dy))
                                for dx, dy in candidate_dirs:
                                    nx, ny = ex + dx, ey + dy
                                    if self.can_enemy_step_to(enemy, nx, ny, dx, dy):
                                        if abs(nx - tx) + abs(ny - ty) == 1:
                                            enemy.x += dx
                                            enemy.y += dy
                                            enemy.last_dx, enemy.last_dy = dx, dy
                                            moved = True
                                            break

                            if not moved:
                                step = self.get_ai_step_towards(enemy, tx, ty)
                                if step:
                                    best_dx, best_dy = step
                                    enemy.x += best_dx
                                    enemy.y += best_dy
                                    enemy.last_dx, enemy.last_dy = best_dx, best_dy

                else:
                    #3. Roaming behavior (no visible team members)
                    self.process_roaming_ai(enemy)

    def get_pokemon_actions_this_turn(self, pokemon: Pokemon) -> int:
        """Returns the number of actions the Pokémon can take this turn round based on speed and status effects"""
        #1. Status effects that prevent taking actions
        if (
            pokemon.status_effects.get("Sleep", 0) > 0 or
            pokemon.status_effects.get("Resting", 0) > 0 or
            pokemon.status_effects.get("Frozen", 0) > 0 or
            pokemon.status_effects.get("Petrified", 0) > 0 or
            pokemon.status_effects.get("Petrified") == -1
        ):
            return 0

        #2. Paralysis has 50% chance to skip turn
        if pokemon.status_effects.get("Paralysis", 0) > 0:
            import random
            if random.randint(1, 100) <= 50:
                self.log_message(f"{pokemon.name} is fully paralyzed!")
                return 0

        #3. Speed stage calculations
        stage = pokemon.movement_speed_stage
        if stage == 3: #4x speed
            return 4
        elif stage == 2: #3x speed
            return 3
        elif stage == 1: #2x speed
            return 2
        elif stage == 0: #Normal speed
            return 1
        elif stage == -1: #Slow (half speed)
            pokemon.slow_turn_toggle = not pokemon.slow_turn_toggle
            return 1 if pokemon.slow_turn_toggle else 0
        return 1

    def replenish_player_actions(self):
        """Replenishes player_actions_left for new turn according to current player movement speed stage"""
        self.player_actions_left = self.get_pokemon_actions_this_turn(self.player_pokemon)

    def on_turn_completed(self):
        """Resolves some stuff when a turn ends"""
        if getattr(self, "mimic_selection_state", None) is not None:
            return
        if not getattr(self, "turn_in_progress", False):
            self.turn_in_progress = True
        self.player_actions_left -= 1
        if self.player_actions_left > 0 and self.is_running and int(self.player_pokemon.current_hp) > 0:
            self.turn_in_progress = False
            return

        if not self.is_running or int(self.player_pokemon.current_hp) <= 0:
            self.player_actions_left = 0

        self.turn_number += 1
        self.message_log.has_more_page = False
        
        #1. Deduct belly points and print warnings if needed, then apply hunger effects or natural recovery
        import math
        fainted_members = []
        for member in self.party:
            #Action belly cost: wait = 1, move = 2, attack = 3
            if member in self.moved_used_this_turn:
                cost = 3
            else:
                curr_pos = get_pokemon_position(self, member)
                start_pos = self.party_start_positions.get(member, curr_pos)
                if curr_pos != start_pos:
                    cost = 2
                else:
                    cost = 1
            
            member.current_belly = max(0.0, member.current_belly - cost)
            
            #Warning calculation (rounded up)
            pct = math.ceil((member.current_belly / member.max_belly) * 100.0)
            pct = max(0, min(100, pct))
            
            #Reset warnings if belly rises above thresholds
            if pct > 20:
                member.warned_20 = False
            if pct > 10:
                member.warned_10 = False
            if pct > 0:
                member.warned_0 = False
                
            #Print the warnings to the message log
            if pct <= 0:
                if not member.warned_0:
                    self.log_message(f"Oh no! {member.name}'s belly is empty! Hurry, they must eat something!")
                    member.warned_0 = True
                    member.warned_10 = True
                    member.warned_20 = True
            elif pct <= 10:
                if not member.warned_10:
                    self.log_message(f"{member.name} is getting weak from hunger...")
                    member.warned_10 = True
                    member.warned_20 = True
            elif pct <= 20:
                if not member.warned_20:
                    self.log_message(f"{member.name} is getting hungry...")
                    member.warned_20 = True
                    
            #Apply HP recovery or hunger damage
            if int(member.current_hp) > 0:
                if member.current_belly <= 0.0:
                    member.last_damage_source = "hunger"
                    member.current_hp -= 1.0
                    
                    if member.status_effects.get("Confusion", 0) > 0:
                        if random.randint(1, 100) <= 50:
                            member.cure_status("Confusion", self)

                    if int(member.current_hp) <= 0:
                        self.log_pokemon_defeat(member)
                        fainted_members.append(member)
                else:
                    #Natural recovery: base 1% of max HP per turn
                    #Blocked by DoT status effects (Poison, Toxic, or Burn)
                    if not (member.status_effects.get("Poison") or member.status_effects.get("Toxic") or member.status_effects.get("Burn")):
                        max_hp = member.stats["HP"]
                        types = member.species_data.get("types", [])
                        if self.weather == "Grassy Terrain":
                            if "Flying" in types:
                                recovery_pct = 0.01
                            elif "Grass" in types:
                                recovery_pct = 0.03
                            else:
                                recovery_pct = 0.02
                        else:
                            recovery_pct = 0.01
                            if self.weather == "Sunny" and "Grass" in types:
                                recovery_pct = 0.02
                        if member.status_effects.get("Aqua Ring"):
                            recovery_pct *= 2.0
                        if member.status_effects.get("Ingrain", 0) > 0:
                            recovery_pct *= 4.0
                        member.current_hp = min(float(max_hp), member.current_hp + recovery_pct * max_hp)

        #Apply Ingrain healing to enemies (4 HP/turn)
        for enemy in list(self.spawned_pokemon):
            if int(enemy.current_hp) > 0 and enemy.status_effects.get("Ingrain", 0) > 0:
                max_hp = enemy.stats["HP"]
                enemy.current_hp = min(float(max_hp), enemy.current_hp + 4.0)

        for fainted in fainted_members:
            if fainted in self.party:
                self.remove_party_member(fainted)

        #Update Protect consecutive counters
        for p in list(self.party + self.spawned_pokemon):
            if p not in self.moved_used_this_turn or getattr(p, "last_used_move", None) not in ("Protect", "Quick Guard", "Wide Guard", "Endure"):
                p.protect_consecutive = 0

        #Clear turn-tracking states
        self.moved_used_this_turn.clear()
        self.party_start_positions.clear()

        self.check_napping_enemies_wakeup()
        self.check_taunt_wearoff()
        if getattr(self, "wonder_room_turns", 0) > 0:
            self.wonder_room_turns -= 1
            if self.wonder_room_turns <= 0:
                self.log_message("Wonder Room wore off!")

        #Process Future Sight delayed attacks
        remaining_fs = []
        for fs in getattr(self, "future_sight_effects", []):
            fs["turns_left"] -= 1
            if fs["turns_left"] <= 0:
                tx, ty = fs["tile"]
                attacker = fs["attacker"]
                move = fs["move"]

                target_poke = self.get_poke_at(tx, ty)
                if target_poke and int(target_poke.current_hp) > 0:
                    self.log_message(f"{target_poke.name} took the Future Sight attack!")
                    damage, is_critical, type_mult = calculate_damage(attacker, target_poke, move, self)
                    self.apply_direct_damage(target_poke, damage, attacker=attacker) #We need to damage this way because we're handling damage outside of the normal function
                    if is_critical:
                        self.log_message("A critical hit!")
                    if type_mult >= 1.25:
                        self.log_message("It's super effective!")
                    elif 0.25 < type_mult <= 0.75:
                        self.log_message("It's not very effective...")
                    elif type_mult == 0.25:
                        self.log_message("It had little effect...")
                else:
                    self.log_message("Future Sight failed!")
            else:
                remaining_fs.append(fs)
        self.future_sight_effects = remaining_fs
        #Handle sleep/rest turns for party members
        for p in list(self.party):
            if p.status_effects.get("Sleep", 0) > 0 or p.status_effects.get("Resting", 0) > 0:
                self.handle_sleep_turn(p)

        self.round_users_this_turn.clear()

        #Reset Echoed Voice count if Pokémon moved
        for p in list(self.party + self.spawned_pokemon):
            curr_pos = get_pokemon_position(self, p)
            last_pos = getattr(p, "last_turn_pos", None)
            if last_pos is not None and last_pos != curr_pos:
                p.echoed_voice_count = 0
            p.last_turn_pos = curr_pos

        self.process_ally_turns()
        self.process_enemy_turns()
        self.update_enemy_spawning()

        #Process movement speed durations for all Pokémon on the floor
        for p in list(self.party + self.spawned_pokemon):
            if p.movement_speed_duration > 0:
                p.movement_speed_duration -= 1
                if p.movement_speed_duration <= 0:
                    curr_stage = p.movement_speed_stage
                    if curr_stage > 0:
                        p.change_movement_speed(curr_stage - 1, self)
                    elif curr_stage < 0:
                        p.change_movement_speed(curr_stage + 1, self)

        #Rain cures Burn
        if self.weather == "Rain":
            for p in list(self.party + self.spawned_pokemon):
                if p.status_effects.get("Burn"):
                    p.cure_status("Burn", self)

        #Process status damage and decrement status durations for all Pokémon on the floor
        for p in list(self.party + self.spawned_pokemon):
            if int(p.current_hp) <= 0:
                continue

            #Enemy Aqua Ring recovery (2 HP/turn)
            if p in self.spawned_pokemon and p not in self.party and p.status_effects.get("Aqua Ring") and int(p.current_hp) > 0:
                p.current_hp = min(float(p.stats["HP"]), p.current_hp + 2.0)

            #1. Periodic status damage (Poison, Burn)
            damage_to_apply = 0
            if p.status_effects.get("Toxic"):
                damage_to_apply += 1
                p.last_damage_source = "poison"
            else:
                if p.status_effects.get("Poison") and self.turn_number % 2 == 0:
                    damage_to_apply += 1
                    p.last_damage_source = "poison"

            if p.status_effects.get("Burn") and self.turn_number % 2 == 0:
                damage_to_apply += 1
                p.last_damage_source = "burn"

            if damage_to_apply > 0:
                p.current_hp -= damage_to_apply
                if p.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        p.cure_status("Confusion", self)
                if int(p.current_hp) <= 0:
                    self.log_pokemon_defeat(p)
                    self.handle_enemy_defeat(p)
                    if p in self.party:
                        self.remove_party_member(p)
                    if p in self.spawned_pokemon:
                        self.spawned_pokemon.remove(p)
                    continue  #Pokémon fainted, skip duration decrement

            #2. Periodic weather damage (Hail, Sandstorm)
            if self.weather in ("Hail", "Sandstorm") and (p.status_effects.get("Digging", 0) > 0 or p.status_effects.get("Diving", 0) > 0):
                pass
            elif self.weather == "Hail":
                p_types = p.species_data.get("types", [])
                if not any(t in p_types for t in ["Ice", "Fire", "Rock"]):
                    p.last_damage_source = "Hail"
                    p.current_hp -= 1.0
                    if self.is_in_team_sight(p):
                        self.log_message(f"{p.name} was pelted by hail!")
                    if p.status_effects.get("Confusion", 0) > 0:
                        if random.randint(1, 100) <= 50:
                            p.cure_status("Confusion", self)
                    if int(p.current_hp) <= 0:
                        if self.is_in_team_sight(p):
                            self.log_pokemon_defeat(p)
                        self.handle_enemy_defeat(p)
                        if p in self.party:
                            self.remove_party_member(p)
                        if p in self.spawned_pokemon:
                            self.spawned_pokemon.remove(p)
                        self.leech_seed_sources.pop(p, None)
                        continue

            elif self.weather == "Sandstorm":
                p_types = p.species_data.get("types", [])
                if not any(t in p_types for t in ["Steel", "Ground", "Rock"]):
                    p.last_damage_source = "Sandstorm"
                    p.current_hp -= 1.0
                    if self.is_in_team_sight(p):
                        self.log_message(f"{p.name} was buffeted by the sandstorm!")
                    if p.status_effects.get("Confusion", 0) > 0:
                        if random.randint(1, 100) <= 50:
                            p.cure_status("Confusion", self)
                    if int(p.current_hp) <= 0:
                        if self.is_in_team_sight(p):
                            self.log_pokemon_defeat(p)
                        self.handle_enemy_defeat(p)
                        if p in self.party:
                            self.remove_party_member(p)
                        if p in self.spawned_pokemon:
                            self.spawned_pokemon.remove(p)
                        self.leech_seed_sources.pop(p, None)
                        continue

            #3. Leech Seed periodic damage
            if p.status_effects.get("Leech Seed", 0) > 0 and int(p.current_hp) > 0:
                leech_dmg = min(3, int(p.current_hp))
                if leech_dmg > 0:
                    src = self.leech_seed_sources.get(p)
                    p.last_damage_source = f"{src.name}'s Leech Seed" if src else "Leech Seed"
                    p.current_hp -= leech_dmg
                    
                    src = self.leech_seed_sources.get(p)
                    if src and int(src.current_hp) > 0:
                        src.current_hp = min(float(src.stats["HP"]), src.current_hp + leech_dmg)
                        self.log_message(f"{src.name} absorbed HP from {p.name}!")
                        
                    if p.status_effects.get("Confusion", 0) > 0:
                        if random.randint(1, 100) <= 50:
                            p.cure_status("Confusion", self)
                            
                    if int(p.current_hp) <= 0:
                        self.log_pokemon_defeat(p)
                        self.handle_enemy_defeat(p, src)
                        if p in self.party:
                            self.remove_party_member(p)
                        if p in self.spawned_pokemon:
                            self.spawned_pokemon.remove(p)
                        self.leech_seed_sources.pop(p, None)
                        continue

        #4. Update bindings for binding moves
        self.update_fire_spin_bindings()
        self.update_wrap_bindings()
        self.update_sand_tomb_bindings()
        self.update_whirlpool_bindings()

        #5. Decrement status durations
        for p in list(self.party + self.spawned_pokemon):
            if int(p.current_hp) <= 0:
                continue
            #All statuses that last a certain number of turns (and not semi-permanent statuses) go here
            for status in ["Sleep", "Paralysis", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Protect", "Safeguard", "Focus Energy", "Light Screen", "Reflect", "Sand Tomb", "Whirlpool", "Perishing", "Counter", "Mirror Coat", "Endure", "Paused", "Ingrain", "Destiny Bond", "Encore", "Magnet Rise", "Telekinesis", "Resting", "Stuck", "Quick Guard", "Wide Guard", "Vital Throw", "Drowsy", "Decoy", "Landed", "Terrified", "Blind", "Mobile", "Puppet", "Hallucinating", "Snatch", "Cowering", "Rebound", "Silenced", "Invisible"]:
                val = p.status_effects.get(status, 0)
                if status == "Petrified" and p in self.spawned_pokemon:
                    #Enemy petrification only wears off when attacked
                    continue

                if isinstance(val, int) and 0 < val < 90000:
                    dec = 1
                    if status == "Frozen" and self.weather == "Sunny":
                        dec = 2
                    new_val = max(0, val - dec)
                    if new_val == 0:
                        p.cure_status(status, self)
                        if status == "Perishing":
                            p.last_damage_source = "Perish Song"
                            p.current_hp = 0.0
                            self.log_message(f"{p.name} perished!")
                            self.handle_enemy_defeat(p)
                            if p in self.party:
                                self.remove_party_member(p)
                            elif p in self.spawned_pokemon:
                                self.spawned_pokemon.remove(p)
                    else:
                        p.status_effects[status] = new_val

        #Decrement weather turns if active
        if getattr(self, "weather_turns_left", 0) > 0:
            self.weather_turns_left -= 1
            if self.weather_turns_left <= 0:
                self.set_weather("Clear")

        #Replenish player actions for the next round
        self.replenish_player_actions()
        self.turn_in_progress = False

    def _prompt_nickname(self, species_name: str) -> str | None:
        """Prompts the user to enter their name."""
        try:
            nick = input(f"What's your name? (max 12 chars, Return to skip) ").strip()
            if nick:
                return nick[:12]
            return None
        except (KeyboardInterrupt, EOFError):
            return None

    def _get_starting_position(self) -> tuple[int, int]:
        """Finds a valid floor tile in a room to spawn the team at the start of each floor"""
        if not self.floor.rooms:
            #Fallback: search grid for a floor tile
            for y in range(self.floor.height):
                for x in range(self.floor.width):
                    if self.floor.grid[y][x] == FLOOR_CHAR:
                        return x, y
            raise RuntimeError("No valid floor tiles to spawn player!")

        #Pick a random room and place player in its center or inside bounds
        room_cell = random.choice(list(self.floor.rooms.keys()))
        room = self.floor.rooms[room_cell]
        mid_x = (room.x1 + room.x2) // 2
        mid_y = (room.y1 + room.y2) // 2
        return mid_x, mid_y

    def is_tile_adjacent_to_corridor(self, x: int, y: int, check_8way: bool = True) -> bool:
        """Returns True if (x, y) is a corridor/dead-end tile or a tile directly adjacent to one."""
        if not hasattr(self, "floor") or not self.floor:
            return False
        corridor_set = getattr(self.floor, "corridor_tiles", set()) | getattr(self.floor, "dead_end_tiles", set())
        if (x, y) in corridor_set:
            return True
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)] if check_8way else [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) in corridor_set:
                return True
        return False

    def spawn_stairs(self):
        """Pick a room tile to spawn the stairs that is not adjacent to a corridor."""
        candidates = []
        for room in self.floor.rooms.values():
            for y in range(room.y1, room.y2 + 1):
                for x in range(room.x1, room.x2 + 1):
                    if self.floor.grid[y][x] != FLOOR_CHAR:
                        continue
                    if self.is_tile_adjacent_to_corridor(x, y, check_8way=True):
                        continue
                    candidates.append((x, y))
        
        #Fallback 1: 4-way adjacent check
        if not candidates:
            for room in self.floor.rooms.values():
                for y in range(room.y1, room.y2 + 1):
                    for x in range(room.x1, room.x2 + 1):
                        if self.floor.grid[y][x] != FLOOR_CHAR:
                            continue
                        if self.is_tile_adjacent_to_corridor(x, y, check_8way=False):
                            continue
                        candidates.append((x, y))

        #Fallback 2: Any room tile that is not directly a corridor/dead-end tile
        if not candidates:
            for room in self.floor.rooms.values():
                for y in range(room.y1, room.y2 + 1):
                    for x in range(room.x1, room.x2 + 1):
                        if self.floor.grid[y][x] == FLOOR_CHAR and (x, y) not in self.floor.corridor_tiles and (x, y) not in self.floor.dead_end_tiles:
                            candidates.append((x, y))
        
        if not candidates:
            self.stairs_position = (self.player_x, self.player_y)
        else:
            self.stairs_position = random.choice(candidates)

    def spawn_wonder_tile(self):
        """Pick a room floor tile for the Wonder Tile (currently always 1 per floor) that is not adjacent to a corridor."""
        candidates = []
        for room in self.floor.rooms.values():
            for y in range(room.y1, room.y2 + 1):
                for x in range(room.x1, room.x2 + 1):
                    if self.floor.grid[y][x] != FLOOR_CHAR:
                        continue
                    if (x, y) == getattr(self, "stairs_position", None):
                        continue
                    if (x, y) == (self.player_x, self.player_y):
                        continue
                    if self.is_tile_adjacent_to_corridor(x, y, check_8way=True):
                        continue
                    candidates.append((x, y))

        #Fallback 1: 4-way adjacent check
        if not candidates:
            for room in self.floor.rooms.values():
                for y in range(room.y1, room.y2 + 1):
                    for x in range(room.x1, room.x2 + 1):
                        if self.floor.grid[y][x] != FLOOR_CHAR:
                            continue
                        if (x, y) == getattr(self, "stairs_position", None):
                            continue
                        if (x, y) == (self.player_x, self.player_y):
                            continue
                        if self.is_tile_adjacent_to_corridor(x, y, check_8way=False):
                            continue
                        candidates.append((x, y))

        #Fallback 2: Any room tile that is not a corridor/dead-end tile and not stairs/player
        if not candidates:
            for room in self.floor.rooms.values():
                for y in range(room.y1, room.y2 + 1):
                    for x in range(room.x1, room.x2 + 1):
                        if self.floor.grid[y][x] == FLOOR_CHAR:
                            if (x, y) != getattr(self, "stairs_position", None) and (x, y) != (self.player_x, self.player_y):
                                if (x, y) not in self.floor.corridor_tiles and (x, y) not in self.floor.dead_end_tiles:
                                    candidates.append((x, y))

        if candidates:
            import random
            self.wonder_tile_position = random.choice(candidates)
        else:
            self.wonder_tile_position = (self.player_x, self.player_y)

    def trigger_wonder_tile(self, pokemon: Pokemon):
        """Resets a Pokémon's stat changes to their normal levels when stepping on a Wonder Tile."""
        has_stat_changes = any(mod != 0 for mod in pokemon.stat_modifiers.values()) or pokemon.movement_speed_stage != 0

        wt_pos = getattr(self, "wonder_tile_position", None)
        if wt_pos is None:
            wt_pos = get_pokemon_position(self, pokemon)

        visible_tiles = self._compute_currently_visible()
        is_visible = wt_pos in visible_tiles

        if not has_stat_changes:
            if is_visible:
                self.log_message(f"{pokemon.name}'s stats didn't change.")
            return

        for stat in pokemon.stat_modifiers:
            pokemon.stat_modifiers[stat] = 0

        pokemon.movement_speed_stage = 0
        pokemon.movement_speed_duration = 0
        pokemon.slow_turn_toggle = False

        if is_visible:
            self.log_message(f"{pokemon.name}'s stat changes were reset to normal!")

    def trigger_crash_damage(self, attacker: Pokemon):
        """Applies crash damage equal to half max HP (rounded down) for moves that cause it."""
        crash = max(1, int(attacker.stats.get("HP", 1.0)) // 2)
        attacker.current_hp = float(int(attacker.current_hp) - crash)
        self.log_message(f"{attacker.name} kept going and crashed!")
        ax, ay = get_pokemon_position(self, attacker)
        self.flash_damages[(ax, ay)] = (crash, 1.0)
        self.trigger_damage_flash()
        if int(attacker.current_hp) <= 0:
            self.log_pokemon_defeat(attacker)
            if attacker in self.spawned_pokemon:
                self.spawned_pokemon.remove(attacker)
            elif attacker in self.party:
                self.remove_party_member(attacker)

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Returns True if there is a clear line-of-sight from (x1, y1) to (x2, y2) using Bresenham's algorithm. Used for the lighting engine"""
        if x1 == x2 and y1 == y2:
            return True

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        curr_x, curr_y = x1, y1
        while True:
            if curr_x == x2 and curr_y == y2:
                break

            if not (0 <= curr_x < self.floor.width and 0 <= curr_y < self.floor.height):
                return False
            #Block sight if any intermediate tile (excluding the start and end) is a wall
            if (curr_x != x1 or curr_y != y1) and self.floor.grid[curr_y][curr_x] == WALL_CHAR:
                return False

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy

        return True

    def _get_player_room_tiles(self) -> set[tuple[int, int]]:
        """Returns all coordinates belonging to the room a Pokémon is currently inside."""
        return get_room_tiles_at(self.floor, self.player_x, self.player_y)

    def _compute_currently_visible(self) -> set[tuple[int, int]]:
        """The backbone of the lighting engine, computes the set of currently visible tile coordinates across all team members."""
        if self.player_pokemon and self.player_pokemon.status_effects.get("Blind", 0) > 0:
            return {(self.player_x, self.player_y)}

        radius = 100 if getattr(self, "floor_luminous", False) else 5

        visible = set()
        for member in self.party:
            if int(getattr(member, "current_hp", 0)) <= 0:
                continue

            mx, my = get_pokemon_position(self, member)
            visible.add((mx, my))

            if member.status_effects.get("Blind", 0) > 0:
                continue

            #1. Rooms visibility (entire room/merged room is lit when inside)
            m_room_tiles = get_room_tiles_at(self.floor, mx, my)
            if m_room_tiles:
                visible.update(m_room_tiles)

            #2. General visibility (radius of 5 normally, 10 when luminous, subject to line-of-sight)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    tx = mx + dx
                    ty = my + dy
                    if 0 <= tx < self.floor.width and 0 <= ty < self.floor.height:
                        if self._has_line_of_sight(mx, my, tx, ty):
                            visible.add((tx, ty))

        return visible

    def ensure_valid_position(self, entity: object | str | list[int] | dict[str, int]) -> tuple[int, int]:
        """Failsafe check for entity position.
        If the entity is on an invalid tile (inside a wall while not allowed, out of bounds, or not a floor tile),
        teleports it to a random valid floor tile.

        Returns the final (x, y) coordinates of the entity.
        """
        #Determine current x, y and resolve pokemon object
        poke_obj = None
        if entity == "player" or entity is self:
            x, y = self.player_x, self.player_y
            poke_obj = getattr(self, "player_pokemon", None)
        elif hasattr(entity, "x") and hasattr(entity, "y"):
            x, y = getattr(entity, "x"), getattr(entity, "y")
            poke_obj = entity
        elif isinstance(entity, dict) and "x" in entity and "y" in entity:
            x, y = entity["x"], entity["y"]
            poke_obj = entity.get("pokemon")
        elif isinstance(entity, list) and len(entity) >= 2:
            x, y = entity[0], entity[1]
        else:
            raise ValueError("Unsupported entity representation for position validation")

        #Check if entity has Mobile status effect
        has_mobile = False
        if poke_obj is not None:
            status_map = getattr(poke_obj, "status_effects", {})
            if isinstance(status_map, dict) and status_map.get("Mobile", 0) > 0:
                has_mobile = True

        #Check validity
        in_bounds = (0 <= x < self.floor.width and 0 <= y < self.floor.height)
        if has_mobile:
            is_valid = in_bounds
        else:
            is_valid = in_bounds and self.floor.grid[y][x] == FLOOR_CHAR

        if not is_valid:
            #Resolve the entity name
            if entity == "player" or entity is self:
                name = self.player_pokemon.name
            elif hasattr(entity, "name"):
                name = str(getattr(entity, "name"))
            elif isinstance(entity, dict) and "name" in entity:
                name = str(entity["name"])
            else:
                name = "Pokémon"

            #Teleport to a random valid floor tile
            valid_tiles = []
            for ty in range(self.floor.height):
                for tx in range(self.floor.width):
                    if self.floor.grid[ty][tx] == FLOOR_CHAR:
                        valid_tiles.append((tx, ty))

            if not valid_tiles: #Last resort if there's nowhere to warp to
                self.log_message(f"{name} warped! But they dropped back to the same spot.")
                return x, y

            new_x, new_y = random.choice(valid_tiles)

            #Update entity position in place
            if entity == "player" or entity is self:
                self.player_x, self.player_y = new_x, new_y
                if hasattr(self.player_pokemon, "x") and hasattr(self.player_pokemon, "y"):
                    self.player_pokemon.x = new_x
                    self.player_pokemon.y = new_y
            elif hasattr(entity, "x") and hasattr(entity, "y"):
                setattr(entity, "x", new_x)
                setattr(entity, "y", new_y)
                if entity is getattr(self, "player_pokemon", None):
                    self.player_x, self.player_y = new_x, new_y
            elif isinstance(entity, dict) and "x" in entity and "y" in entity:
                entity["x"], entity["y"] = new_x, new_y
            elif isinstance(entity, list) and len(entity) >= 2:
                entity[0], entity[1] = new_x, new_y

            self.log_message(f"{name} warped!")
            return new_x, new_y

        return x, y

    def select_move(self, slot: int):
        """Selects a move from the player's moves list and initiates move execution"""
        if self.player_pokemon.status_effects.get("Flinch", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is flinching!")
            return

        if self.player_pokemon.status_effects.get("Paused", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is paused!")
            return

        if self.player_pokemon.status_effects.get("Puppet", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is a puppet and cannot be controlled!")
            return

        if self.player_pokemon.status_effects.get("Terrified", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is terrified and cannot attack!")
            return

        #Check if wrapped (wrapped targets cannot attack)
        is_wrapped = False
        for binding in self.wrap_bindings:
            if self.player_pokemon == binding["defender"]:
                is_wrapped = True
                break
        if is_wrapped:
            self.log_message(f"{self.player_pokemon.name} is wrapped and cannot attack!")
            return

        if self.player_pokemon.can_struggle(game=self):
            from pokemon import _get_move_data
            move = _get_move_data("Struggle")
        else:
            if slot >= len(self.player_pokemon.moves):
                return

            move = self.player_pokemon.moves[slot]

            if move["name"] in ("Snore", "Sleep Talk"):
                if not (self.player_pokemon.status_effects.get("Sleep", 0) > 0 or self.player_pokemon.status_effects.get("Resting", 0) > 0):
                    self.log_message("The move failed!")
                else:
                    self.log_message(f"{move['name']} can only be used while sleeping.")
                return

            #Check PP and move-specific requirements
            if not self.player_pokemon.can_use_move(move, game=self):
                if move["name"] == "Fake Out" and getattr(self.player_pokemon, "fake_out_used_this_floor", False):
                    self.log_message(f"{self.player_pokemon.name} can't use Fake Out again this floor!")
                elif move["name"] == "Stockpile" and self.player_pokemon.status_effects.get("Stockpile", 0) >= 3:
                    self.log_message(f"{self.player_pokemon.name} can't Stockpile any more!")
                elif move["name"] in ("Swallow", "Spit Up") and self.player_pokemon.status_effects.get("Stockpile", 0) <= 0:
                    self.log_message(f"No Stockpile charges to use {move['name']}!")
                elif move["name"] == "Belch" and self.player_pokemon.current_belly < 0.1 * self.player_pokemon.max_belly:
                    self.log_message(f"{self.player_pokemon.name} is too hungry to use {move['name']}!")
                elif move["name"] == "Belly Drum" and self.player_pokemon.current_belly < 0.5 * self.player_pokemon.max_belly:
                    self.log_message(f"{self.player_pokemon.name} is too hungry to use {move['name']}!")
                elif move["name"] == "Belly Drum" and self.player_pokemon.stat_modifiers.get("Attack", 0) >= 6:
                    self.log_message(f"{self.player_pokemon.name}'s Attack is already maxed!")
                elif move["name"] == "Recycle" and not any(item.get("name") == "Plain Seed" for item in getattr(self, "inventory", [])):
                    self.log_message(f"There are no Plain Seeds to recycle!")
                elif move["name"] == getattr(self.player_pokemon, "disable_move_effect", None):
                    self.log_message(f"{self.player_pokemon.name}'s {move['name']} is disabled!")
                elif self.player_pokemon.status_effects.get("Taunted") and move.get("category") == "Status":
                    self.log_message(f"{self.player_pokemon.name} can't use status moves while taunted!")
                elif self.player_pokemon.current_pp < move["pp_cost"]:
                    self.log_message(f"Not enough PP to use {move['name']}!")
                else:
                    self.log_message(f"This message should never appear. If it does, send a bug report to C4.")
                return

        #Player is confused
        if self.player_pokemon.status_effects.get("Confusion", 0) > 0:
            targets = get_confusion_targets(self, self.player_pokemon, move)
            if not targets:
                try:
                    self.player_pokemon.use_move(move, game=self)
                    self.moved_used_this_turn.add(self.player_pokemon)
                except ValueError as e:
                    self.log_message(f"Error! {str(e)} Please report this to C4!")
                    return
                self.log_message(f"{self.player_pokemon.name} used {move['name']}!")
                self.log_message("The move failed!")
            else:
                range_str = move.get("range", "Adjacent enemy")
                if range_str == "Enemy in front":
                    range_str = "Adjacent enemy"
                is_multi = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower()
                if is_multi:
                    self.execute_multi_move(self.player_pokemon, targets, move)
                elif range_str == "Straight line piercing":
                    ax, ay = get_pokemon_position(self, self.player_pokemon)
                    tx, ty = get_pokemon_position(self, targets[0])
                    dx = 1 if tx > ax else (-1 if tx < ax else 0)
                    dy = 1 if ty > ay else (-1 if ty < ay else 0)
                    line_targets = self.get_line_piercing_targets(self.player_pokemon, move, dx, dy)
                    if not line_targets:
                        line_targets = targets
                    self.execute_multi_move(self.player_pokemon, line_targets, move)
                else:
                    self.execute_single_move(self.player_pokemon, targets[0], move)
            self.on_turn_completed()
            return

        #Get valid targets
        targets = get_valid_targets(self, self.player_pokemon, move)

        if not targets and move.get("name") not in ("Future Sight",):
            self.log_message(f"There are no valid targets for {move['name']} right now.")
            return

        #Check range type
        range_str = move.get("range", "Adjacent enemy")
        if range_str == "Enemy in front":
            range_str = "Adjacent enemy"

        if move.get("name") == "Future Sight":
            self.waiting_for_direction = True
            self.direction_move = move
            self.log_message(f"Which direction to use {move['name']}? ([Esc] to cancel)")
            return

        is_multi = range_str.startswith("All ")

        if is_multi:
            #Multi-target move hits all targets automatically
            self.execute_multi_move(self.player_pokemon, targets, move)
            self.on_turn_completed()
        elif range_str == "Straight line piercing":
            if len(targets) == 1:
                ax, ay = get_pokemon_position(self, self.player_pokemon)
                tx, ty = get_pokemon_position(self, targets[0])
                dx = 1 if tx > ax else (-1 if tx < ax else 0)
                dy = 1 if ty > ay else (-1 if ty < ay else 0)
                line_targets = self.get_line_piercing_targets(self.player_pokemon, move, dx, dy)
                if not line_targets:
                    line_targets = targets
                self.execute_multi_move(self.player_pokemon, line_targets, move)
                self.on_turn_completed()
            else:
                ax, ay = get_pokemon_position(self, self.player_pokemon)
                dirs = set()
                for t in targets:
                    tx, ty = get_pokemon_position(self, t)
                    dx = 1 if tx > ax else (-1 if tx < ax else 0)
                    dy = 1 if ty > ay else (-1 if ty < ay else 0)
                    dirs.add((dx, dy))
                if len(dirs) == 1:
                    dx, dy = list(dirs)[0]
                    line_targets = self.get_line_piercing_targets(self.player_pokemon, move, dx, dy)
                    self.execute_multi_move(self.player_pokemon, line_targets, move)
                    self.on_turn_completed()
                else:
                    self.targeting_mode = True
                    self.targeting_move = move
                    self.targeting_targets = targets
                    tx, ty = get_pokemon_position(self, targets[0])
                    self.targeting_cursor = (tx, ty)
                    self.log_message(f"Who to target for {move['name']}? ([Return] to confirm, [Esc] to cancel)")
        else:
            #Single-target move
            if len(targets) == 1:
                #Auto-use on the single target
                self.execute_single_move(self.player_pokemon, targets[0], move)
                self.on_turn_completed()
            else:
                #Multiple targets
                if range_str in ("Adjacent enemy", "Adjacent enemy or ally"):
                    #Directional targeting
                    self.waiting_for_direction = True
                    self.direction_move = move
                    self.log_message(f"Which direction to use {move['name']}? ([Esc] to cancel)")
                else:
                    #Cursor targeting
                    self.targeting_mode = True
                    self.targeting_move = move
                    self.targeting_targets = targets
                    #Start cursor at first target position
                    tx, ty = get_pokemon_position(self, targets[0])
                    self.targeting_cursor = (tx, ty)
                    self.log_message(f"Who to target for {move['name']}? ([Return] to confirm, [Esc] to cancel)")

    def process_charging_move(self, p: Pokemon) -> bool:
        """Processes Pokémon's charging moves. Returns True if turn was automated."""
        if not p.charging_move:
            return False
        
        move = p.charging_move["move"]
        
        #Determine if prevented from moving
        prevented = (
            p.status_effects.get("Sleep", 0) > 0 or
            p.status_effects.get("Resting", 0) > 0 or
            p.status_effects.get("Frozen", 0) > 0 or
            p.status_effects.get("Petrified", 0) > 0 or
            p.status_effects.get("Petrified") == -1 or
            p.status_effects.get("Flinch", 0) > 0
        )
        if not prevented and p.status_effects.get("Paralysis", 0) > 0:
            import random
            if random.randint(1, 100) <= 50:
                self.log_message(f"{p.name} is fully paralyzed!")
                prevented = True
                
        if prevented:
            self.log_message(f"{p.name}'s {move['name']} was interrupted!")
            p.charging_move = None
            if p.status_effects.get("Digging", 0) > 0:
                p.cure_status("Digging", self)
            if p.status_effects.get("Diving", 0) > 0:
                p.cure_status("Diving", self)
            if p.status_effects.get("Focusing"):
                p.cure_status("Focusing", self)
            return True
            
        #Unleash!
        self.log_message(f"{p.name} unleashed {move['name']}!")
        if p.status_effects.get("Digging", 0) > 0:
            p.cure_status("Digging", self)
        if p.status_effects.get("Diving", 0) > 0:
            p.cure_status("Diving", self)
        if p.status_effects.get("Focusing"):
            p.cure_status("Focusing", self)
        
        #Get targets using the stored direction or target
        targets = []
        from targeting import get_valid_targets, has_clear_path
        range_str = move.get("range", "Adjacent enemy")

        if range_str.startswith("Straight line piercing"):
            dx, dy = p.charging_move.get("direction", (0, 0))
            line_targets = self.get_line_piercing_targets(p, move, dx, dy)
            if line_targets:
                for target in line_targets:
                    if int(target.current_hp) > 0 and int(p.current_hp) > 0:
                        self.execute_single_move(p, target, move, free=True)
            else:
                self.log_message("The move failed!")
            p.charging_move = None
            return True
        elif range_str.startswith("Straight line"):
            ax, ay = get_pokemon_position(self, p)
            dx, dy = p.charging_move.get("direction", (0, 0))
            if dx != 0 or dy != 0:
                cuts_corners = move.get("cuts_corners", False)
                max_d = 4 if "4" in range_str else 10
                valid_pokes = get_valid_targets(self, p, move)
                for i in range(1, max_d + 1):
                    tx, ty = ax + i * dx, ay + i * dy
                    if not has_clear_path(self.floor, ax, ay, tx, ty, cuts_corners):
                        break
                    found = self.get_poke_at(tx, ty)
                    if found and found != p and int(found.current_hp) > 0 and found in valid_pokes:
                        targets = [found]
                        break
        elif move["name"] == "Focus Punch":
            target_tile = p.charging_move.get("target_tile")
            dx, dy = p.charging_move.get("direction", (0, 0))
            ax, ay = get_pokemon_position(self, p)
            cuts_corners = move.get("cuts_corners", False)
            valid_pokes = get_valid_targets(self, p, move)
            tx, ty = target_tile if target_tile else (ax + dx, ay + dy)
            dist = max(abs(tx - ax), abs(ty - ay))
            if dist == 1 and has_clear_path(self.floor, ax, ay, tx, ty, cuts_corners):
                found = self.get_poke_at(tx, ty)
                if found and found != p and int(found.current_hp) > 0 and found in valid_pokes:
                    targets = [found]
        else:
            target_p = p.charging_move.get("target")
            valid_pokes = get_valid_targets(self, p, move)
            if target_p and int(target_p.current_hp) > 0:
                if target_p in valid_pokes:
                    targets = [target_p]
            else:
                target_tile = p.charging_move.get("target_tile")
                dx, dy = p.charging_move.get("direction", (0, 0))
                ax, ay = get_pokemon_position(self, p)
                tx, ty = target_tile if target_tile else (ax + dx, ay + dy)
                found = self.get_poke_at(tx, ty)
                if found and found != p and int(found.current_hp) > 0 and found in valid_pokes:
                    targets = [found]
        
        if targets:
            self.execute_single_move(p, targets[0], move, free=True)
        else:
            self.log_message("The move failed!")
            
        p.charging_move = None
        return True

    def trigger_damage_flash(self):
        """Displays a brief pop-up over a Pokémon."""
        import time
        if not self.flash_damages:
            return
        all_flashes = list(self.flash_damages.items())
        self.flash_damages.clear()
        for pos, flash in all_flashes:
            self.flash_damages[pos] = flash
            self.render()
            sys.stdout.flush()
            if not getattr(self, "suppress_animation_delay", False):
                time.sleep(0.25)
            self.flash_damages.clear()
            self.render()
            sys.stdout.flush()
            if not getattr(self, "suppress_animation_delay", False):
                time.sleep(0.1)

    def trigger_explosion(
        self,
        center_x: int,
        center_y: int,
        size: int = 3,
        base_power: int = 100,
        attacker: Pokemon | None = None,
        cause_name: str = "Explosion",
        fixed_center_damage: int | None = None,
        fixed_adjacent_damage: int | None = None
    ):
        """Triggers a multi-tile explosion with animation, damage falloff, wall destruction, and item destruction."""
        is_outer_attack = not getattr(self, "exp_batching_active", False)
        if is_outer_attack:
            self.exp_batching_active = True
            self.pending_team_exp = 0

        try:
            self._trigger_explosion_at_internal(center_x, center_y, size=size, base_power=base_power, attacker=attacker, cause_name=cause_name, fixed_center_damage=fixed_center_damage, fixed_adjacent_damage=fixed_adjacent_damage)
        finally:
            if is_outer_attack:
                self.exp_batching_active = False
                self.flush_pending_exp()

    def _trigger_explosion_at_internal(
        self,
        center_x: int,
        center_y: int,
        size: int = 3,
        base_power: int = 100,
        attacker: Pokemon | None = None,
        cause_name: str = "Explosion",
        fixed_center_damage: int | None = None,
        fixed_adjacent_damage: int | None = None
    ):
        import sys
        import time
        from dungeon import WALL_CHAR, FLOOR_CHAR
        from targeting import get_pokemon_position
        from combat import calculate_damage

        radius = (size - 1) // 2

        #1. Determine affected tiles within floor boundaries
        affected_tiles: list[tuple[int, int]] = []
        for y in range(max(0, center_y - radius), min(self.floor.height, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(self.floor.width, center_x + radius + 1)):
                affected_tiles.append((x, y))

        #2. Play radial expansion ANSI animation (expanding rings outwards & fading)
        shade_chars = ["█", "▓", "▒", "░"]
        color_cycles = ["\033[91m", "\033[93m", "\033[38;5;208m"] #Red, yellow, white

        if not getattr(self, "suppress_animation_delay", False):
            for step in range(radius + 4):
                self.explosion_overlays = {}
                for x, y in affected_tiles:
                    d = max(abs(x - center_x), abs(y - center_y))
                    if d <= step:
                        fade_stage = step - d
                        if fade_stage < len(shade_chars):
                            char = shade_chars[fade_stage]
                            color = color_cycles[(d + fade_stage) % len(color_cycles)]
                            self.explosion_overlays[(x, y)] = f"{color}{char}\033[0m"
                if self.explosion_overlays:
                    self.render()
                    sys.stdout.flush()
                    time.sleep(0.10)
            self.explosion_overlays = {}

        #3. Wall destruction (excluding floor outer boundaries)
        for x, y in affected_tiles:
            if 0 < x < self.floor.width - 1 and 0 < y < self.floor.height - 1:
                if self.floor.grid[y][x] == WALL_CHAR:
                    self.floor.grid[y][x] = FLOOR_CHAR

        #4. Item destruction
        for x, y in list(affected_tiles):
            if (x, y) in self.items_on_floor:
                del self.items_on_floor[(x, y)]

        #5. Damage & falloff application to all Pokémon in blast radius. Explosions are considered to be Fire type moves using the stats and level of the Pokémon that caused it
        all_pokes = [self.player_pokemon] + [p for p in self.party if p != self.player_pokemon] + list(self.spawned_pokemon)
        target_pokes: list[tuple[Pokemon, int]] = []
        seen = set()
        for p in all_pokes:
            if p in seen or int(p.current_hp) <= 0:
                continue
            seen.add(p)
            px, py = get_pokemon_position(self, p)
            if max(abs(px - center_x), abs(py - center_y)) <= radius:
                d = max(abs(px - center_x), abs(py - center_y))
                target_pokes.append((p, d))

        explosion_move = {
            "name": cause_name,
            "type": "Fire",
            "category": "Physical",
            "power": base_power,
            "accuracy": 100
        }

        dummy_attacker = attacker if attacker is not None else (self.player_pokemon if self.player_pokemon in all_pokes else all_pokes[0])

        for target, d in target_pokes:
            if int(target.current_hp) <= 0:
                continue

            if fixed_center_damage is not None and fixed_adjacent_damage is not None:
                damage = fixed_center_damage if d == 0 else fixed_adjacent_damage
                type_mult = 1.0
            else:
                falloff = max(0.2, 1.0 - (0.2 * d)) #20% damage reduction per tile
                raw_dmg, is_crit, type_mult = calculate_damage(dummy_attacker, target, explosion_move, self)
                damage = max(1, int(raw_dmg * falloff))

            #Damage Pokémon
            target.last_damage_source = f"{attacker.name}'s {cause_name}" if attacker else cause_name
            target.current_hp = float(int(target.current_hp) - damage)
            self.log_message(f"{target.name} was caught in the explosion!")

            tx, ty = get_pokemon_position(self, target)
            self.flash_damages[(tx, ty)] = (damage, type_mult)
            self.trigger_damage_flash()

            #Explosions wake-up sleeping Pokémon
            if target.napping:
                target.napping = False
                target.just_woke_up = True
            if target.status_effects.get("Sleep", 0) > 0:
                target.cure_status("Sleep", self)

            if int(target.current_hp) <= 0:
                self.log_pokemon_defeat(target)
                if dummy_attacker != target and dummy_attacker in self.party and int(dummy_attacker.current_hp) > 0:
                    dummy_attacker.defeat_pokemon(target, game=self)
                if target in self.spawned_pokemon:
                    self.spawned_pokemon.remove(target)
                elif target in self.party:
                    self.remove_party_member(target)
                    
    def find_nearest_empty_tile(self, start_x: int, start_y: int, exclude_pokemon: Pokemon | None = None) -> tuple[int, int]:
        """Finds the nearest walkable tile that is not occupied by another Pokémon using BFS."""
        from collections import deque
        from dungeon import WALL_CHAR
        from targeting import get_pokemon_position

        queue = deque([(start_x, start_y)])
        visited = {(start_x, start_y)}

        while queue:
            cx, cy = queue.popleft()
            if 0 <= cx < self.floor.width and 0 <= cy < self.floor.height:
                if self.floor.grid[cy][cx] != WALL_CHAR:
                    #Check if occupied by any other Pokémon
                    occupied = False
                    for p in self.party + self.spawned_pokemon:
                        if p is not exclude_pokemon and int(p.current_hp) > 0:
                            px, py = get_pokemon_position(self, p)
                            if px == cx and py == cy:
                                occupied = True
                                break
                    if not occupied:
                        return cx, cy

            #Add neighbors (8 directions)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return start_x, start_y

    def apply_generic_move_effects(self, attacker: Pokemon, defender: Pokemon, move: dict):
        """Applies generic effects (stat_change, status_apply, healing) for a move, defined in moves.json"""
        import random
        from dungeon import WALL_CHAR
        from targeting import get_pokemon_position
        
        BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
        if move.get("name") not in BLACKLIST_COPIABLE:
            self.last_move_used_successfully = (move, attacker)
        if move.get("name") == "Charge":
            attacker.apply_status("Charging", self, duration=1)
        for effect in move.get("effects", []):
            eff_type = effect.get("effect_type")
            if eff_type in ("multi_hit", "recoil"):
                continue
                
            chance = effect.get("chance", 1.0)
            import random as rand
            if rand.random() > chance:
                continue
                
            #Determine target
            target_default = "attacker" if eff_type == "healing" else "defender"
            target_name = effect.get("target", target_default)
            eff_target = attacker if target_name == "attacker" else defender
            
            if target_name == "defender" and int(defender.current_hp) <= 0:
                continue
                
            if eff_target != attacker and getattr(eff_target, "napping", False):
                eff_target.napping = False
                eff_target.just_woke_up = True
                
            if eff_type == "stat_change":
                stat = effect.get("stat")
                stages = effect.get("stages", 0)
                if stat:
                    eff_target.apply_stat_modifier(stat, stages, self)
                    
            elif eff_type == "status_apply":
                status_name = effect.get("status")
                duration = effect.get("duration")
                
                #Check custom failure logic
                #Ghost-types are unaffected by Mean Look (you can't scare a ghost!)
                if status_name == "Stuck" and move.get("name") == "Mean Look":
                    if "Ghost" in eff_target.species_data.get("types", []):
                        self.log_message(f"{eff_target.name} is unaffected!")
                        continue
                elif status_name == "Leech Seed":
                    if eff_target.status_effects.get("Leech Seed", 0) > 0:
                        self.log_message(f"{eff_target.name} is already seeded.")
                        continue
                elif status_name == "Poison":
                    if eff_target.status_effects.get("Poison") or eff_target.status_effects.get("Toxic"):
                        self.log_message(f"{eff_target.name} is already poisoned.")
                        continue
                elif status_name == "Sleep":
                    if eff_target.status_effects.get("Sleep", 0) > 0 or eff_target.status_effects.get("Resting", 0) > 0:
                        if move.get("name") == "Hypnosis":
                            rem_sleep = eff_target.status_effects.get("Sleep", 0) or eff_target.status_effects.get("Resting", 0)
                            attacker_is_team = attacker in self.party
                            target_is_team = eff_target in self.party
                            if attacker_is_team and not target_is_team:
                                if eff_target.status_effects.get("Sleep", 0) > 0:
                                    eff_target.cure_status("Sleep", self)
                                elif eff_target.status_effects.get("Resting", 0) > 0:
                                    eff_target.cure_status("Resting", self)
                                eff_target.apply_status("Terrified", self, duration=rem_sleep)
                                continue
                            elif not attacker_is_team and target_is_team:
                                if eff_target.status_effects.get("Sleep", 0) > 0:
                                    eff_target.cure_status("Sleep", self)
                                elif eff_target.status_effects.get("Resting", 0) > 0:
                                    eff_target.cure_status("Resting", self)
                                eff_target.apply_status("Puppet", self, duration=rem_sleep)
                                continue
                        self.log_message(f"{eff_target.name} is already asleep.")
                        continue
                elif status_name == "Sleepless":
                    if eff_target.status_effects.get("Sleepless"):
                        self.log_message(f"{eff_target.name} is already sleepless.")
                        continue
                        
                eff_target.apply_status(status_name, self, duration=duration)
                if status_name == "Leech Seed":
                    self.leech_seed_sources[eff_target] = attacker
                elif status_name == "Taunted":
                    self.taunt_sources[eff_target] = attacker

            elif eff_type == "soak":
                if eff_target.types == ["Water"]:
                    self.log_message(f"{eff_target.name} is already Water-type!")
                else:
                    eff_target.temp_types = ["Water"]
                    self.log_message(f"{eff_target.name}'s type changed to Water!")
            elif eff_type == "reflect_type":
                if attacker.types == eff_target.types:
                    self.log_message("The move failed!") #Fails if user's types would be unchanged
                else:
                    attacker.temp_types = list(eff_target.types)
                    type_str = "/".join(eff_target.types)
                    self.log_message(f"{attacker.name}'s type changed to {type_str}!")

            elif eff_type == "psych_up":
                if attacker.stat_modifiers == eff_target.stat_modifiers:
                    self.log_message("The move failed!") #Fails if user's stat changes would be unchanged
                else:
                    attacker.stat_modifiers = dict(eff_target.stat_modifiers)
                    self.log_message(f"{attacker.name} copied {eff_target.name}'s stat changes!")

            elif eff_type == "wonder_room":
                if getattr(self, "wonder_room_turns", 0) > 0:
                    self.wonder_room_turns = 0
                    self.log_message("Wonder Room wore off!") #If Wonder Room is already active then cancel it
                else:
                    self.wonder_room_turns = 20
                    self.log_message("Defense and Sp. Def stats were swapped on the floor!")
                    
            elif eff_type == "healing":
                heal_percent = effect.get("heal_percent", 0.0)
                if heal_percent > 0.0:
                    heal_amt = int(float(eff_target.stats["HP"]) * heal_percent)
                    eff_target.current_hp = min(float(eff_target.stats["HP"]), eff_target.current_hp + heal_amt)
                    self.log_message(f"{eff_target.name}'s HP was restored.")
                    tx, ty = get_pokemon_position(self, eff_target)
                    self.flash_damages[(tx, ty)] = (f"{heal_amt}", "HEAL")
                    self.trigger_damage_flash()
            elif eff_type == "weather_change":
                weather_name = effect.get("weather", "Clear")
                duration = 0
                if weather_name == "Grassy Terrain":
                    duration = random.randint(10, 20)
                self.set_weather(weather_name, duration)
            elif eff_type == "rapid_spin_clear":
                eff_target.cure_status("Leech Seed", self)
            elif eff_type == "cure_all_statuses":
                #All negative statuses go here
                for neg_status in ["Sleep", "Paralysis", "Poison", "Toxic", "Burn", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Slow", "Encore", "Stuck", "Terrified", "Blind", "Puppet", "Hallucinating"]:
                    eff_target.cure_status(neg_status, self)
            elif eff_type == "tri_attack_effects":
                import random
                if random.randint(1, 100) <= 20:
                    eff_target.apply_status("Paralysis", self)
                if random.randint(1, 100) <= 20:
                    eff_target.apply_status("Frozen", self)
                if random.randint(1, 100) <= 20:
                    eff_target.apply_status("Burn", self)
            elif eff_type == "fire_spin":
                already_bound = False
                for binding in self.fire_spin_bindings:
                    if binding["defender"] == defender or binding["attacker"] == attacker or binding["defender"] == attacker or binding["attacker"] == defender:
                        already_bound = True
                        break
                if already_bound:
                    self.log_message("The move failed!")
                    continue
                
                #Fire Spin lasts 2-5 turns at random
                duration = random.randint(2, 5)
                self.fire_spin_bindings.append({
                    "attacker": attacker,
                    "defender": defender,
                    "turns_left": duration,
                    "move": move
                })
                defender.apply_status("Fire Spin", self, duration=duration)
                attacker.apply_status("Fire Spin", self, duration=duration)
            elif eff_type == "wrap":
                already_bound = False
                for binding in self.fire_spin_bindings + self.wrap_bindings:
                    if binding["defender"] == defender or binding["attacker"] == attacker or binding["defender"] == attacker or binding["attacker"] == defender:
                        already_bound = True
                        break
                if already_bound:
                    self.log_message(f"{eff_target.name} is already bound.")
                    continue
                
                duration = random.randint(2, 5)
                self.wrap_bindings.append({
                    "attacker": attacker,
                    "defender": defender,
                    "turns_left": duration,
                    "move": move
                })
                defender.apply_status("Wrap", self, duration=duration)
                attacker.apply_status("Wrap", self, duration=duration)
            elif eff_type == "sand_tomb":
                already_bound = False
                for binding in self.fire_spin_bindings + self.wrap_bindings + self.sand_tomb_bindings + self.whirlpool_bindings:
                    if binding["defender"] == defender or binding["attacker"] == attacker or binding["defender"] == attacker or binding["attacker"] == defender:
                        already_bound = True
                        break
                if already_bound:
                    self.log_message(f"{eff_target.name} is already bound.")
                    continue
                
                duration = random.randint(2, 5)
                self.sand_tomb_bindings.append({
                    "attacker": attacker,
                    "defender": defender,
                    "turns_left": duration,
                    "move": move
                })
                defender.apply_status("Sand Tomb", self, duration=duration)
                attacker.apply_status("Sand Tomb", self, duration=duration)
            elif eff_type == "whirlpool":
                already_bound = False
                for binding in self.fire_spin_bindings + self.wrap_bindings + self.sand_tomb_bindings + self.whirlpool_bindings:
                    if binding["defender"] == defender or binding["attacker"] == attacker or binding["defender"] == attacker or binding["attacker"] == defender:
                        already_bound = True
                        break
                if already_bound:
                    self.log_message(f"{eff_target.name} is already bound.")
                    continue
                
                duration = random.randint(2, 5)
                self.whirlpool_bindings.append({
                    "attacker": attacker,
                    "defender": defender,
                    "turns_left": duration,
                    "move": move
                })
                defender.apply_status("Whirlpool", self, duration=duration)
                attacker.apply_status("Whirlpool", self, duration=duration)
            elif eff_type == "splash":
                import random
                ux, uy = get_pokemon_position(self, attacker)
                adjacent = [(ux + dx, uy + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                tx, ty = random.choice(adjacent)
                is_wall = not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height) or self.floor.grid[ty][tx] == WALL_CHAR
                if is_wall:
                    attacker.current_hp -= 1.0
                    self.log_message(f"{attacker.name} collided with a wall!")
                    if int(attacker.current_hp) <= 0:
                        self.log_pokemon_defeat(attacker)
                        if attacker in self.party:
                            self.remove_party_member(attacker)
                        elif attacker in self.spawned_pokemon:
                            self.spawned_pokemon.remove(attacker)
                else:
                    collided_poke = None
                    for p in self.party + self.spawned_pokemon:
                        if p != attacker and int(p.current_hp) > 0 and get_pokemon_position(self, p) == (tx, ty):
                            collided_poke = p
                            break
                    if collided_poke is not None:
                        attacker.current_hp -= 1.0
                        collided_poke.current_hp -= 1.0
                        self.log_message(f"{attacker.name} collided with {collided_poke.name}!")
                        for p in (attacker, collided_poke):
                            if int(p.current_hp) <= 0:
                                self.log_pokemon_defeat(p)
                                if p in self.party:
                                    self.remove_party_member(p)
                                elif p in self.spawned_pokemon:
                                    self.spawned_pokemon.remove(p)
                                elif p in self.spawned_pokemon:
                                    self.spawned_pokemon.remove(p)
                    else:
                        if attacker == self.player_pokemon:
                            self.player_x, self.player_y = tx, ty
                        attacker.x, attacker.y = tx, ty
                        self.log_message(f"{attacker.name} flopped about!")
            elif eff_type == "encore":
                import random
                last = getattr(defender, "last_used_move", None)
                if not last:
                    self.log_message("The move failed!")
                else:
                    duration = random.randint(5, 8)
                    defender.apply_status("Encore", self, duration=duration)
            elif eff_type == "after_you":
                import random
                if attacker in self.party:
                    teammates = [p for p in self.party if p != attacker]
                else:
                    teammates = [p for p in self.spawned_pokemon if p != attacker]
                if not teammates:
                    self.log_message("The move failed!")
                else:
                    target_tm = random.choice(teammates)
                    ux, uy = get_pokemon_position(self, attacker)
                    tx, ty = get_pokemon_position(self, target_tm)
                    if attacker == self.player_pokemon:
                        self.player_x, self.player_y = tx, ty
                    elif target_tm == self.player_pokemon:
                        self.player_x, self.player_y = ux, uy
                    attacker.x, attacker.y = tx, ty
                    target_tm.x, target_tm.y = ux, uy
                    self.log_message(f"{attacker.name} switched places with {target_tm.name}.")
            elif eff_type == "gravity":
                self.gravity = True
                self.log_message("Gravity intensified!")
                for p in list(self.party + self.spawned_pokemon):
                    if p.status_effects.get("Magnet Rise", 0) > 0:
                        p.cure_status("Magnet Rise", self)
                    if p.status_effects.get("Telekinesis", 0) > 0:
                        p.cure_status("Telekinesis", self)
                    if p.charging_move:
                        c_move = p.charging_move.get("move", {})
                        if c_move.get("name") in ("Fly", "Bounce"):
                            self.log_message(f"{p.name}'s {c_move['name']} was interrupted!")
                            p.charging_move = None
            elif eff_type == "follow_me":
                import random
                ux, uy = get_pokemon_position(self, attacker)
                from targeting import get_room_tiles_at
                room_tiles = get_room_tiles_at(self.floor, ux, uy)
                allies_in_room = []
                enemies_in_room = []
                for p in list(self.party + self.spawned_pokemon):
                    if p == attacker or int(p.current_hp) <= 0:
                        continue
                    px, py = get_pokemon_position(self, p)
                    in_room = False
                    if room_tiles:
                        in_room = (px, py) in room_tiles
                    else:
                        in_room = max(abs(px - ux), abs(py - uy)) <= 5
                    if in_room:
                        is_ally = (attacker in self.party) == (p in self.party)
                        if is_ally:
                            allies_in_room.append(p)
                        else:
                            enemies_in_room.append(p)
                to_teleport = allies_in_room + enemies_in_room
                adjacent = [(ux + dx, uy + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
                valid_adj = [] #Invalid adjacent tiles are wall tiles
                for tx, ty in adjacent:
                    if 0 <= tx < self.floor.width and 0 <= ty < self.floor.height and self.floor.grid[ty][tx] == FLOOR_CHAR:
                        valid_adj.append((tx, ty))
                for p in to_teleport:
                    occupied_coords = {get_pokemon_position(self, other) for other in self.party + self.spawned_pokemon if other != p and int(other.current_hp) > 0}
                    free_adj = [c for c in valid_adj if c not in occupied_coords]
                    if not free_adj:
                        break
                    tx, ty = random.choice(free_adj)
                    if p == self.player_pokemon:
                        self.player_x, self.player_y = tx, ty
                    p.x, p.y = tx, ty
                    self.log_message(f"{p.name} was pulled toward {attacker.name}!")
            elif eff_type == "healing_wish":
                attacker.current_hp = 0.0
                self.log_message(f"{attacker.name} sacrificed itself!")
                if attacker in self.party:
                    teammates = [p for p in self.party if p != attacker]
                else:
                    teammates = [p for p in self.spawned_pokemon if p != attacker]
                for p in teammates:
                    if int(p.current_hp) > 0:
                        p.current_hp = float(p.stats["HP"])
                        p.current_pp = p.max_pp
                        p.current_belly = float(p.max_belly)
                        #Once again, all negative statuses go here
                        for status in ["Sleep", "Paralysis", "Poison", "Toxic", "Burn", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Slow", "Encore", "Stuck"]:
                            p.cure_status(status, self)
                if attacker in self.party:
                    self.remove_party_member(attacker)
                elif attacker in self.spawned_pokemon:
                    self.spawned_pokemon.remove(attacker)
            elif eff_type == "copycat":
                if not self.last_move_used_successfully:
                    self.log_message("The move failed!")
                else:
                    last_move, last_attacker = self.last_move_used_successfully
                    BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
                    if last_attacker == attacker or last_move.get("name") in BLACKLIST_COPIABLE:
                        self.log_message("The target's move isn't copyable.")
                    else:
                        self.execute_free_move(attacker, last_move)
            elif eff_type == "metronome":
                import random
                known_move_names = {m["name"] for m in attacker.moves}
                BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
                metronome_pool = [
                    m for m in self.moves_db
                    if m["name"] not in known_move_names and m["name"] not in BLACKLIST_COPIABLE
                ]
                if not metronome_pool:
                    self.log_message("Error handling message??? Send a bug report to C4 plz :)")
                else:
                    chosen_move = random.choice(metronome_pool)
                    self.execute_free_move(attacker, chosen_move)
            elif eff_type == "disable":
                last_move_name = getattr(defender, "last_used_move", None)
                disabled_name = getattr(defender, "disable_move_effect", None)
                imprisoned_set = set(getattr(defender, "imprisoned_moves", []))
                if not last_move_name or last_move_name == disabled_name or last_move_name in imprisoned_set:
                    self.log_message("The move failed!")
                else:
                    defender.disable_move_effect = last_move_name
                    self.log_message(f"{defender.name}'s {last_move_name} was disabled!")
            elif eff_type == "imprison":
                user_move_names = {m["name"] for m in attacker.moves}
                shared_disabled = []
                for m_obj in defender.moves:
                    m_name = m_obj["name"]
                    if m_name in user_move_names:
                        shared_disabled.append(m_name)
                        if m_name not in defender.imprisoned_moves:
                            defender.imprisoned_moves.append(m_name)
                if shared_disabled:
                    self.log_message(f"{defender.name}'s moves were disabled!")
                else:
                    self.log_message(f"{defender.name} was unaffected!")
            elif eff_type == "rest":
                if eff_target.status_effects.get("Sleepless"):
                    self.log_message("They were unable to fall asleep!")
                else:
                    eff_target.apply_status("Resting", self)
            elif eff_type == "mimic":
                mimic_slot = None
                for idx, m in enumerate(attacker.moves):
                    if m["name"] == move["name"]:
                        mimic_slot = idx
                        break

                BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
                known_names = {m["name"] for m in attacker.moves}
                eligible_moves = [m for m in defender.moves if m["name"] not in BLACKLIST_COPIABLE and m["name"] not in known_names]

                if attacker == self.player_pokemon:
                    self.mimic_selection_state = {
                        "user": attacker,
                        "target": defender,
                        "mimic_move": move,
                        "slot": mimic_slot
                    }
                else:
                    if not eligible_moves:
                        self.log_message("The target's move is not copyable.")
                    else:
                        last_used_name = getattr(defender, "last_used_move_on_floor", None)
                        chosen_move = None
                        if last_used_name and last_used_name not in BLACKLIST_COPIABLE and last_used_name not in known_names:
                            for m in defender.moves:
                                if m["name"] == last_used_name:
                                    chosen_move = m
                                    break
                        if chosen_move is None:
                            chosen_move = random.choice(eligible_moves)

                        copied_move = dict(chosen_move)
                        if mimic_slot is not None:
                            attacker.moves[mimic_slot] = copied_move
                            attacker.mimic_original_state = {
                                "slot": mimic_slot,
                                "original_move": move,
                                "copied_move": copied_move
                            }
                            self.log_message(f"{attacker.name} copied {chosen_move['name']}!")
            elif eff_type == "stockpile":
                current = attacker.status_effects.get("Stockpile", 0)
                attacker.status_effects["Stockpile"] = min(3, current + 1)
                self.log_message(f"{attacker.name} stockpiled {attacker.status_effects['Stockpile']}!")
            elif eff_type == "haze":
                for stat in eff_target.stat_modifiers:
                    eff_target.stat_modifiers[stat] = 0
                eff_target.change_movement_speed(0, self)
                self.log_message(f"{eff_target.name}'s stat changes were neutralized!")
            elif eff_type == "whirlwind":
                from combat import calculate_damage

                ax, ay = get_pokemon_position(self, attacker)
                tx, ty = get_pokemon_position(self, defender)

                dx = tx - ax
                dy = ty - ay
                #Normalize dx, dy to [-1, 0, 1]
                dx = max(-1, min(1, dx))
                dy = max(-1, min(1, dy))

                final_x, final_y = tx, ty
                collision = False
                collided_with_wall = False
                collided_pokemon = None

                for step in range(1, 11):
                    nx = tx + step * dx
                    ny = ty + step * dy

                    #Wall or out of bounds check
                    if nx < 0 or nx >= self.floor.width or ny < 0 or ny >= self.floor.height or self.floor.grid[ny][nx] == WALL_CHAR:
                        collision = True
                        collided_with_wall = True
                        break

                    #Pokémon collision check
                    other = None
                    for p in self.party + self.spawned_pokemon:
                        if p is not defender and int(p.current_hp) > 0:
                            px, py = get_pokemon_position(self, p)
                            if px == nx and py == ny:
                                other = p
                                break
                    if other is not None:
                        collision = True
                        collided_pokemon = other
                        break

                    final_x, final_y = nx, ny

                self.log_message(f"{defender.name} was blown away!")

                if collision:
                    #Lands on nearest empty tile starting from the last valid tile
                    lx, ly = self.find_nearest_empty_tile(final_x, final_y, exclude_pokemon=defender)
                    if defender is self.player_pokemon:
                        self.player_x, self.player_y = lx, ly
                    else:
                        defender.x, defender.y = lx, ly

                    collision_move = {
                        "name": "Collision Damage",
                        "type": "Normal",
                        "category": "Physical",
                        "power": 40,
                        "accuracy": None,
                        "effects": []
                    }

                    if collided_with_wall:
                        self.log_message(f"{defender.name} collided with a wall!")
                        dmg, crit, mult = calculate_damage(attacker, defender, collision_move, self)
                        defender.current_hp -= dmg
                        
                        self.flash_damages[(lx, ly)] = (dmg, mult)
                        self.trigger_damage_flash()

                        if int(defender.current_hp) <= 0:
                            self.log_pokemon_defeat(defender)
                            attacker.defeat_pokemon(defender, game=self)
                            if defender in self.spawned_pokemon:
                                self.spawned_pokemon.remove(defender)
                            elif defender in self.party:
                                self.remove_party_member(defender)

                    elif collided_pokemon is not None:
                        self.log_message(f"{defender.name} collided with {collided_pokemon.name}!")
                        dmg_def, crit_def, mult_def = calculate_damage(attacker, defender, collision_move, self)
                        dmg_col, crit_col, mult_col = calculate_damage(attacker, collided_pokemon, collision_move, self)

                        defender.current_hp -= dmg_def
                        collided_pokemon.current_hp -= dmg_col

                        self.flash_damages[(lx, ly)] = (dmg_def, mult_def)
                        cx, cy = get_pokemon_position(self, collided_pokemon)
                        self.flash_damages[(cx, cy)] = (dmg_col, mult_col)
                        self.trigger_damage_flash()

                        if int(defender.current_hp) <= 0:
                            self.log_pokemon_defeat(defender)
                            attacker.defeat_pokemon(defender, game=self)
                            if defender in self.spawned_pokemon:
                                self.spawned_pokemon.remove(defender)
                            elif defender in self.party:
                                self.remove_party_member(defender)

                        if int(collided_pokemon.current_hp) <= 0:
                            self.log_pokemon_defeat(collided_pokemon)
                            attacker.defeat_pokemon(collided_pokemon, game=self)
                            if collided_pokemon in self.spawned_pokemon:
                                self.spawned_pokemon.remove(collided_pokemon)
                            elif collided_pokemon in self.party:
                                self.remove_party_member(collided_pokemon)
                else:
                    if defender is self.player_pokemon:
                        self.player_x, self.player_y = final_x, final_y
                    else:
                        defender.x, defender.y = final_x, final_y

        #Sweet Scent belly reduction
        if move["name"] == "Sweet Scent" and defender in self.party:
            defender.current_belly = max(0.0, defender.current_belly - 0.05 * defender.max_belly)
            self.log_message(f"{defender.name} feels hungrier...")

    def update_fire_spin_bindings(self):
        """Updates all active Fire Spin bindings, dealing damage and decrementing the turn counter"""
        from combat import calculate_damage
        active_bindings = []
        for binding in self.fire_spin_bindings:
            attacker = binding["attacker"]
            defender = binding["defender"]
            
            #Check if either is defeated
            if int(attacker.current_hp) <= 0 or int(defender.current_hp) <= 0:
                if int(attacker.current_hp) > 0:
                    attacker.cure_status("Fire Spin", self)
                if int(defender.current_hp) > 0:
                    defender.cure_status("Fire Spin", self)
                continue
                
            #Both are alive, decrement turns_left
            binding["turns_left"] -= 1
            
            #Accuracy check for this turn's hit
            move = binding["move"]
            acc = move.get("accuracy", 85)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            if acc_stage >= 0:
                acc_mult = (3.0 + acc_stage) / 3.0
            else:
                acc_mult = 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            if ev_stage >= 0:
                ev_mult = (3.0 + ev_stage) / 3.0
            else:
                ev_mult = 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            
            import random
            if random.randint(1, 100) <= modified_acc:
                damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)
                self.log_message(f"{defender.name} was hurt by Fire Spin!")
                
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()
                
                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    
                    if int(attacker.current_hp) > 0:
                        attacker.cure_status("Fire Spin", self)
                    continue
            else:
                self.log_message(f"Fire Spin missed {defender.name}!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                
            #Check if expired
            if binding["turns_left"] <= 0:
                attacker.cure_status("Fire Spin", self)
                defender.cure_status("Fire Spin", self)
            else:
                attacker.status_effects["Fire Spin"] = binding["turns_left"]
                defender.status_effects["Fire Spin"] = binding["turns_left"]
                active_bindings.append(binding)
                
        self.fire_spin_bindings = active_bindings

    def update_wrap_bindings(self):
        """Updates all active Wrap bindings, dealing damage and decrementing the turn counter"""
        from combat import calculate_damage
        active_bindings = []
        for binding in self.wrap_bindings:
            attacker = binding["attacker"]
            defender = binding["defender"]
            
            #Check if either is defeated
            if int(attacker.current_hp) <= 0 or int(defender.current_hp) <= 0:
                if int(attacker.current_hp) > 0:
                    attacker.cure_status("Wrap", self)
                if int(defender.current_hp) > 0:
                    defender.cure_status("Wrap", self)
                continue
                
            #Both are alive, decrement turns_left
            binding["turns_left"] -= 1
            
            #Wrap subsequent hits always hit (no accuracy check)
            move = binding["move"]
            damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self)
            defender.current_hp = float(int(defender.current_hp) - damage)
            self.log_message(f"{defender.name} was hurt by Wrap!")
            
            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = (damage, type_mult)
            self.trigger_damage_flash()
            
            if int(defender.current_hp) <= 0:
                self.log_pokemon_defeat(defender)
                attacker.defeat_pokemon(defender, game=self)
                if defender in self.spawned_pokemon:
                    self.spawned_pokemon.remove(defender)
                elif defender in self.party:
                    self.remove_party_member(defender)
                
                if int(attacker.current_hp) > 0:
                    attacker.cure_status("Wrap", self)
                continue
                
            #Check if expired
            if binding["turns_left"] <= 0:
                attacker.cure_status("Wrap", self)
                defender.cure_status("Wrap", self)
            else:
                attacker.status_effects["Wrap"] = binding["turns_left"]
                defender.status_effects["Wrap"] = binding["turns_left"]
                active_bindings.append(binding)
                
        self.wrap_bindings = active_bindings

    def update_sand_tomb_bindings(self):
        """Updates all active Sand Tomb bindings, dealing damage and decrementing the turn counter."""
        from combat import calculate_damage
        active_bindings = []
        for binding in self.sand_tomb_bindings:
            attacker = binding["attacker"]
            defender = binding["defender"]
            
            #Check if either is defeated
            if int(attacker.current_hp) <= 0 or int(defender.current_hp) <= 0:
                if int(attacker.current_hp) > 0:
                    attacker.cure_status("Sand Tomb", self)
                if int(defender.current_hp) > 0:
                    defender.cure_status("Sand Tomb", self)
                continue
                
            #Both are alive, decrement turns_left
            binding["turns_left"] -= 1
            
            #Accuracy check for this turn's hit
            move = binding["move"]
            acc = move.get("accuracy", 85)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            
            import random
            if random.randint(1, 100) <= modified_acc:
                damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)
                self.log_message(f"{defender.name} was hurt by Sand Tomb!")
                
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()
                
                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    
                    if int(attacker.current_hp) > 0:
                        attacker.cure_status("Sand Tomb", self)
                    continue
                    
            #Check if expired
            if binding["turns_left"] <= 0:
                attacker.cure_status("Sand Tomb", self)
                defender.cure_status("Sand Tomb", self)
            else:
                attacker.status_effects["Sand Tomb"] = binding["turns_left"]
                defender.status_effects["Sand Tomb"] = binding["turns_left"]
                active_bindings.append(binding)
                
        self.sand_tomb_bindings = active_bindings

    def update_whirlpool_bindings(self):
        """Updates all active Whirlpool bindings, dealing damage and decrementing the turn counter"""
        from combat import calculate_damage
        active_bindings = []
        for binding in self.whirlpool_bindings:
            attacker = binding["attacker"]
            defender = binding["defender"]
            
            #Check if either is defeated
            if int(attacker.current_hp) <= 0 or int(defender.current_hp) <= 0:
                if int(attacker.current_hp) > 0:
                    attacker.cure_status("Whirlpool", self)
                if int(defender.current_hp) > 0:
                    defender.cure_status("Whirlpool", self)
                continue
                
            #Both are alive, decrement turns_left
            binding["turns_left"] -= 1
            
            #Accuracy check for this turn's hit
            move = binding["move"]
            acc = move.get("accuracy", 85)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            
            if random.randint(1, 100) <= modified_acc:
                damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)
                self.log_message(f"{defender.name} was hurt by Whirlpool!")
                
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()
                
                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    
                    if int(attacker.current_hp) > 0:
                        attacker.cure_status("Whirlpool", self)
                    continue
            else:
                self.log_message(f"Whirlpool missed {defender.name}!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                
            #Check if expired
            if binding["turns_left"] <= 0:
                attacker.cure_status("Whirlpool", self)
                defender.cure_status("Whirlpool", self)
            else:
                attacker.status_effects["Whirlpool"] = binding["turns_left"]
                defender.status_effects["Whirlpool"] = binding["turns_left"]
                active_bindings.append(binding)
                
        self.whirlpool_bindings = active_bindings

    def clear_pokemon_bindings(self, pokemon: Pokemon):
        """Immediately ends all binding move effects (Wrap, Fire Spin, Sand Tomb, Whirlpool, etc.) where pokemon is the attacker or defender."""
        binding_lists = [
            ("Fire Spin", self.fire_spin_bindings),
            ("Wrap", self.wrap_bindings),
            ("Sand Tomb", self.sand_tomb_bindings),
            ("Whirlpool", self.whirlpool_bindings),
        ]
        binding_statuses = ["Wrap", "Fire Spin", "Sand Tomb", "Whirlpool", "Bind", "Clamp"]

        for status_name, b_list in binding_lists:
            remaining = []
            for binding in b_list:
                att = binding.get("attacker")
                defend = binding.get("defender")
                if att == pokemon or defend == pokemon:
                    if att and int(att.current_hp) > 0:
                        for s in binding_statuses:
                            att.cure_status(s, self)
                    if defend and int(defend.current_hp) > 0:
                        for s in binding_statuses:
                            defend.cure_status(s, self)
                else:
                    remaining.append(binding)

            if status_name == "Fire Spin":
                self.fire_spin_bindings = remaining
            elif status_name == "Wrap":
                self.wrap_bindings = remaining
            elif status_name == "Sand Tomb":
                self.sand_tomb_bindings = remaining
            elif status_name == "Whirlpool":
                self.whirlpool_bindings = remaining

        for s in binding_statuses:
            if pokemon.status_effects.get(s, 0) > 0:
                pokemon.cure_status(s, self)

    def execute_free_move(self, attacker: Pokemon, move: dict) -> bool:
        """Executes a move for free, selecting valid targets on the floor. Used for moves that call other moves (Copycat, Metronome etc.)"""
        from targeting import get_valid_targets
        targets = get_valid_targets(self, attacker, move)
        if not targets:
            self.log_message("The move failed!") #No valid targets
            return False

        range_str = move.get("range", "Adjacent enemy")
        if range_str == "Enemy in front":
            range_str = "Adjacent enemy"
        is_multi = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower()

        if is_multi:
            self.execute_multi_move(attacker, targets, move, free=True)
        else:
            import random
            target = random.choice(targets)
            self.execute_single_move(attacker, target, move, free=True)
        return True

    def get_poke_at(self, x: int, y: int) -> Pokemon | None:
        """Returns the Pokemon at (x, y) if any"""
        for p in self.party + self.spawned_pokemon:
            px, py = get_pokemon_position(self, p)
            if px == x and py == y and int(p.current_hp) > 0:
                return p
        return None

    def set_poke_pos(self, p: Pokemon, x: int, y: int):
        """Sets the position of a Pokemon in the game"""
        old_pos = get_pokemon_position(self, p)
        if old_pos != (x, y):
            p.echoed_voice_count = 0
        if p == self.player_pokemon or getattr(p, "is_leader", False):
            self.player_x = x
            self.player_y = y
        p.x = x
        p.y = y
        if (x, y) == getattr(self, "wonder_tile_position", None) and (x, y) != old_pos:
            self.trigger_wonder_tile(p)
        #Moving through walls while Mobile costs additional belly
        if hasattr(self, "floor") and getattr(self.floor, "grid", None) and 0 <= y < self.floor.height and 0 <= x < self.floor.width:
            if self.floor.grid[y][x] == WALL_CHAR and getattr(p, "status_effects", {}).get("Mobile", 0) > 0:
                if hasattr(p, "current_belly"):
                    p.current_belly = max(0.0, getattr(p, "current_belly", 0.0) - 10.0)

    def get_line_piercing_targets(self, attacker: Pokemon, move: dict, dx: int, dy: int) -> list[Pokemon]:
        """Returns all enemy (or confused-target) Pokémon along a line direction (dx, dy) up to 10 tiles. Used for piercing moves"""
        ax, ay = get_pokemon_position(self, attacker)
        cuts_corners = move.get("cuts_corners", False)
        attacker_is_ally = attacker in self.party

        hit_targets: list[Pokemon] = []
        curr_x, curr_y = ax, ay

        for step in range(1, 11):
            nx = ax + step * dx
            ny = ay + step * dy

            if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height):
                break
            if self.floor.grid[ny][nx] == WALL_CHAR:
                break
            if not cuts_corners and dx != 0 and dy != 0:
                c1 = self.floor.grid[curr_y][curr_x + dx]
                c2 = self.floor.grid[curr_y + dy][curr_x]
                if c1 == WALL_CHAR or c2 == WALL_CHAR:
                    break

            curr_x, curr_y = nx, ny

            for p in self.party + self.spawned_pokemon:
                px, py = get_pokemon_position(self, p)
                if px == nx and py == ny and p is not attacker and int(p.current_hp) > 0:
                    if p not in hit_targets:
                        is_enemy = attacker_is_ally != (p in self.party)
                        if is_enemy or attacker.status_effects.get("Confusion", 0) > 0:
                            hit_targets.append(p)

        return hit_targets

    def trigger_vital_throw_counter(self, attacker: Pokemon, defender: Pokemon, damage_taken: int):
        """Logic for Vital Throw: Throw attacker away when defender takes damage with Vital Throw active"""
        ax, ay = get_pokemon_position(self, attacker)
        dx, dy = get_pokemon_position(self, defender)

        rx, ry = ax - dx, ay - dy
        all_dirs = [(x, y) for x in [-1, 0, 1] for y in [-1, 0, 1] if not (x == 0 and y == 0)]
        away_dirs = [d for d in all_dirs if d[0] * rx + d[1] * ry > 0]
        if not away_dirs:
            away_dirs = all_dirs

        import random
        tdx, tdy = random.choice(away_dirs)

        collision_obj: str | Pokemon | None = None
        collision_step = 0

        for s in range(1, 11):
            nx = ax + s * tdx
            ny = ay + s * tdy
            if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height) or self.floor.grid[ny][nx] == WALL_CHAR:
                collision_obj = "wall"
                collision_step = s
                break
            p2 = self.get_poke_at(nx, ny)
            if p2 and p2 is not attacker and int(p2.current_hp) > 0:
                collision_obj = p2
                collision_step = s
                break

        if collision_obj is not None:
            landing_x = ax + (collision_step - 1) * tdx
            landing_y = ay + (collision_step - 1) * tdy
            self.set_poke_pos(attacker, landing_x, landing_y)

            if collision_obj == "wall":
                dmg = max(1, int(0.5 * damage_taken)) #Deal 50% of the damage the defender took
                self.log_message(f"{attacker.name} was thrown into a wall!")
                self.apply_direct_damage(attacker, dmg, attacker=defender)
            elif isinstance(collision_obj, Pokemon):
                dmg = max(1, int(0.25 * damage_taken)) #Deal 25% of the damage to both mons that the defender took
                self.log_message(f"{attacker.name} was thrown into {collision_obj.name}!")
                self.apply_direct_damage(attacker, dmg, attacker=defender)
                self.apply_direct_damage(collision_obj, dmg, attacker=defender)
        else:
            landing_x = ax + 10 * tdx
            landing_y = ay + 10 * tdy
            self.set_poke_pos(attacker, landing_x, landing_y)
            self.log_message(f"{attacker.name} was thrown away by {defender.name}'s Vital Throw!")
            
    def _process_single_target_hit(self, attacker: Pokemon, defender: Pokemon, move: dict, is_multi_target: bool = False, free: bool = False):
        """Processes damaging moves that hit a single target."""

        #Check Rebound status immunity & damage reflection
        if attacker != defender and defender.status_effects.get("Rebound", 0) > 0 and move.get("category") in ("Physical", "Special"):
            ax, ay = get_pokemon_position(self, attacker)
            dx, dy = get_pokemon_position(self, defender)
            if max(abs(ax - dx), abs(ay - dy)) <= 1:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message(f"{defender.name}'s Rebound status reflected the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                raw_dmg, _, _ = calculate_damage(attacker, defender, move, self)
                reflected_dmg = max(1, int(raw_dmg * 0.25))
                self.apply_direct_damage(attacker, reflected_dmg, attacker=defender)
                self.log_message(f"{attacker.name} took {reflected_dmg} damage from the reflection!")
                return

        #Check Protect immunity
        if attacker != defender and defender.status_effects.get("Protect", 0) > 0 and move.get("name") != "Feint":
            attacker.last_move_failed_turn = self.turn_number
            self.log_message(f"{defender.name} protected itself!")
            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = ("/", "MISS")
            self.trigger_damage_flash()
            if move.get("name") in ("High Jump Kick", "Axe Kick"):
                self.trigger_crash_damage(attacker)
            if move.get("name") in ("Giga Impact", "Hyper Beam"):
                attacker.apply_status("Paused", self, duration=1)
            return

        #Check Quick Guard immunity (blocks attacks from attackers not directly adjacent)
        if attacker != defender and defender.status_effects.get("Quick Guard", 0) > 0 and move.get("name") != "Feint":
            ax, ay = get_pokemon_position(self, attacker)
            dx, dy = get_pokemon_position(self, defender)
            if max(abs(ax - dx), abs(ay - dy)) > 1:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message(f"{defender.name}'s Quick Guard blocked the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("0", "MISS")
                self.trigger_damage_flash()
                if move.get("name") in ("High Jump Kick", "Axe Kick"):
                    self.trigger_crash_damage(attacker)
                if move.get("name") in ("Giga Impact", "Hyper Beam"):
                    attacker.apply_status("Paused", self, duration=1)
                return

        #Check Wide Guard immunity (blocks attacks that hit more than one teammate)
        if attacker != defender and defender.status_effects.get("Wide Guard", 0) > 0 and move.get("name") != "Feint":
            range_str = move.get("range", "")
            is_multi_move = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower() or range_str == "Straight line piercing"
            if is_multi_move:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message(f"{defender.name}'s Wide Guard blocked the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("0", "MISS")
                self.trigger_damage_flash()
                if move.get("name") in ("High Jump Kick", "Axe Kick"):
                    self.trigger_crash_damage(attacker)
                if move.get("name") in ("Giga Impact", "Hyper Beam"):
                    attacker.apply_status("Paused", self, duration=1)
                return

        #Check Digging immunity
        has_lock_on = bool(attacker.status_effects.get("Lock-On"))
        atk_types = getattr(attacker, "temp_types", None) or attacker.types
        is_toxic_poison = bool(move.get("name") == "Toxic" and "Poison" in atk_types)
        if attacker != defender and defender.status_effects.get("Digging", 0) > 0 and move.get("name") not in ("Earthquake", "Bulldoze", "Helping Hand", "Lock-On", "Mind Reader") and not has_lock_on and not is_toxic_poison:
            attacker.last_move_failed_turn = self.turn_number
            self.log_message(f"{defender.name} avoided the attack!")
            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = ("/", "MISS")
            self.trigger_damage_flash()
            if move.get("name") in ("High Jump Kick", "Axe Kick"):
                self.trigger_crash_damage(attacker)
            if move.get("name") in ("Giga Impact", "Hyper Beam"):
                attacker.apply_status("Paused", self, duration=1)
            return

        #Check Diving immunity
        if attacker != defender and defender.status_effects.get("Diving", 0) > 0 and move.get("name") not in ("Surf", "Whirlpool", "Helping Hand", "Lock-On", "Mind Reader") and not has_lock_on and not is_toxic_poison:
            attacker.last_move_failed_turn = self.turn_number
            self.log_message(f"{defender.name} avoided the attack!")
            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = ("/", "MISS")
            self.trigger_damage_flash()
            if move.get("name") in ("High Jump Kick", "Axe Kick"):
                self.trigger_crash_damage(attacker)
            if move.get("name") in ("Giga Impact", "Hyper Beam"):
                attacker.apply_status("Paused", self, duration=1)
            return



        #Check type immunities for specific status moves
        if attacker != defender:
            def_types = defender.types
            is_powder = "powder" in move["name"].lower() or "spore" in move["name"].lower()
            if is_powder and "Grass" in def_types:
                self.log_message(f"{defender.name} is unaffected!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                return

            if move.get("category") == "Status" and move.get("type") == "Grass":
                if "Grass" in def_types:
                    self.log_message(f"{defender.name} is unaffected!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    return

            if move.get("category") == "Status":
                status_applied = None
                for eff in move.get("effects", []):
                    if eff.get("effect_type") == "status_apply":
                        status_applied = eff.get("status")
                        break

                if status_applied in ("Poison", "Toxic") and any(t in def_types for t in ["Poison", "Steel"]):
                    self.log_message(f"{defender.name}'s type cannot be poisoned!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    return

                if status_applied == "Burn" and "Fire" in def_types:
                    self.log_message(f"{defender.name}'s type cannot be burned!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    return

                if status_applied == "Paralysis" and "Electric" in def_types:
                    self.log_message(f"{defender.name}'s type cannot be paralyzed!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    return

                if status_applied == "Frozen" and any(t in def_types for t in ["Fire", "Ice"]):
                    self.log_message(f"{defender.name}'s type cannot be frozen!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    return

        #Handle charging move initialization
        if (move.get("charge_turns") or move["name"] in ("Solar Beam", "Dig", "Dive", "Focus Punch", "Sky Attack")) and not free:
            if move["name"] == "Solar Beam":
                self.log_message(f"{attacker.name} took in sunlight!")
                if self.weather in ("Sunny", "Harsh Sunlight"):
                    pass  #Solar Beam charges instantly in sunny weather!
                else:
                    ax, ay = get_pokemon_position(self, attacker)
                    tx, ty = get_pokemon_position(self, defender)
                    dx = max(-1, min(1, tx - ax))
                    dy = max(-1, min(1, ty - ay))
                    attacker.charging_move = {
                        "move": move,
                        "target": defender,
                        "target_tile": (tx, ty),
                        "direction": (dx, dy)
                    }
                    return
            else:
                if move["name"] == "Dig":
                    attacker.apply_status("Digging", self)
                elif move["name"] == "Dive":
                    attacker.apply_status("Diving", self)
                elif move["name"] == "Focus Punch":
                    attacker.apply_status("Focusing", self)
                elif move["name"] == "Sky Attack":
                    self.log_message(f"{attacker.name} became cloaked in a harsh light!")

                ax, ay = get_pokemon_position(self, attacker)
                tx, ty = get_pokemon_position(self, defender)
                dx = max(-1, min(1, tx - ax))
                dy = max(-1, min(1, ty - ay))
                attacker.charging_move = {
                    "move": move,
                    "target": defender,
                    "target_tile": (tx, ty),
                    "direction": (dx, dy)
                }
                return

        #Now for a bunch of moves that have custom effects. There are a lot of these and implementing these was a pain lol
        #Mist custom handling
        if move.get("name") == "Mist":
            self.weather = "Mist"
            self.weather_duration = random.randint(15, 20)
            self.log_message(f"{attacker.name} surrounded the area with Mist!")
            return

        #Fling custom handling
        if move.get("name") == "Fling":
            ax, ay = get_pokemon_position(self, attacker)
            tx, ty = get_pokemon_position(self, defender)
            dx = 1 if tx > ax else (-1 if tx < ax else 0)
            dy = 1 if ty > ay else (-1 if ty < ay else 0)
            if dx == 0 and dy == 0:
                dx = 1

            collision_obj: str | Pokemon | None = None
            collision_step = 0
            for s in range(1, 11):
                nx = tx + s * dx
                ny = ty + s * dy
                if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height) or self.floor.grid[ny][nx] == WALL_CHAR:
                    collision_obj = "wall"
                    collision_step = s
                    break
                p2 = self.get_poke_at(nx, ny)
                if p2 and p2 is not defender and int(p2.current_hp) > 0:
                    collision_obj = p2
                    collision_step = s
                    break

            if collision_obj is not None:
                calc_power = min(100, max(10, 10 * collision_step))
                landing_x = tx + (collision_step - 1) * dx
                landing_y = ty + (collision_step - 1) * dy
                self.set_poke_pos(defender, landing_x, landing_y)

                temp_move = move.copy()
                temp_move["power"] = calc_power

                damage, is_critical, type_mult = calculate_damage(attacker, defender, temp_move, self)
                self.apply_direct_damage(defender, damage, attacker=attacker)
                target_coll_name = "wall" if collision_obj == "wall" else (collision_obj.name if isinstance(collision_obj, Pokemon) else "")
                self.log_message(f"{defender.name} was flung into {target_coll_name}!")

                if isinstance(collision_obj, Pokemon):
                    p2_damage, _, _ = calculate_damage(attacker, collision_obj, temp_move, self)
                    self.apply_direct_damage(collision_obj, p2_damage, attacker=attacker)
            else:
                landing_x = tx + 10 * dx
                landing_y = ty + 10 * dy
                self.set_poke_pos(defender, landing_x, landing_y)
                self.log_message(f"{defender.name} was flung away!")
            return

        #Seismic Toss custom handling
        if move.get("name") == "Seismic Toss":
            ax, ay = get_pokemon_position(self, attacker)
            tx, ty = get_pokemon_position(self, defender)

            enemies = []
            if attacker in self.party:
                enemies = [p for p in self.spawned_pokemon if p is not defender and int(p.current_hp) > 0]
            else:
                enemies = [p for p in self.party if p is not defender and int(p.current_hp) > 0]

            visible_enemies = [p for p in enemies if (get_pokemon_position(self, p)) in self._compute_currently_visible()]

            if visible_enemies:
                target_enemy = min(visible_enemies, key=lambda e: max(abs(get_pokemon_position(self, e)[0] - tx), abs(get_pokemon_position(self, e)[1] - ty)))
                ex, ey = get_pokemon_position(self, target_enemy)
                dx = 1 if ex > tx else (-1 if ex < tx else 0)
                dy = 1 if ey > ty else (-1 if ey < ty else 0)
                if dx == 0 and dy == 0:
                    dx, dy = random.choice([(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)])
            else:
                dx, dy = random.choice([(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)])

            collision_toss: str | Pokemon | None = None
            collision_step = 0
            for s in range(1, 21):
                nx = tx + s * dx
                ny = ty + s * dy
                if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height) or self.floor.grid[ny][nx] == WALL_CHAR:
                    collision_toss = "wall"
                    collision_step = s
                    break
                p2 = self.get_poke_at(nx, ny)
                if p2 and p2 is not defender and int(p2.current_hp) > 0:
                    collision_toss = p2
                    collision_step = s
                    break

            if collision_toss is not None:
                landing_x = tx + (collision_step - 1) * dx
                landing_y = ty + (collision_step - 1) * dy
                self.set_poke_pos(defender, landing_x, landing_y)

                damage = attacker.level
                self.apply_direct_damage(defender, damage, attacker=attacker)
                toss_coll_name = "wall" if collision_toss == "wall" else (collision_toss.name if isinstance(collision_toss, Pokemon) else "")
                self.log_message(f"{defender.name} was thrown into {toss_coll_name}!")

                if isinstance(collision_toss, Pokemon):
                    self.apply_direct_damage(collision_toss, damage, attacker=attacker)
            else:
                landing_x = tx + 20 * dx
                landing_y = ty + 20 * dy
                self.set_poke_pos(defender, landing_x, landing_y)
                self.log_message(f"{defender.name} was thrown away!")
            return

        #Thrash custom handling
        if move.get("name") == "Thrash":
            ax, ay = get_pokemon_position(self, attacker)
            directions = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]

            with_poke = []
            empty = []
            for dx, dy in directions:
                nx, ny = ax + dx, ay + dy
                if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height and self.floor.grid[ny][nx] != WALL_CHAR:
                    p = self.get_poke_at(nx, ny)
                    if p and p is not attacker and int(p.current_hp) > 0:
                        with_poke.append((nx, ny, p))
                    else:
                        empty.append((nx, ny, None))

            random.shuffle(with_poke)
            random.shuffle(empty)

            targets_chosen = (with_poke + empty)[:3]
            valid_thrash = [p for _, _, p in targets_chosen if p and int(getattr(p, "current_hp", 0)) > 0]
            is_multi_thrash = len(valid_thrash) > 1

            for tx, ty, target_poke in targets_chosen:
                if target_poke and int(target_poke.current_hp) > 0:
                    damage, is_critical, type_mult = calculate_damage(attacker, target_poke, move, self, is_multi_target=is_multi_thrash)
                    self.apply_direct_damage(target_poke, damage, attacker=attacker)
                    if is_critical:
                        self.log_message("A critical hit!")
                    if type_mult >= 1.25:
                        self.log_message("It's super effective!")
                    elif 0.25 < type_mult <= 0.75:
                        self.log_message("It's not very effective...")
                    elif type_mult == 0.25:
                        self.log_message("It had little effect...")
                else:
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()

            attacker.apply_status("Confusion", game=self)
            return

        #Final Gambit custom handling
        if move.get("name") == "Final Gambit":
            if int(attacker.current_hp) <= 1:
                self.log_message(f"{attacker.name} doesn't have enough HP to use Final Gambit!")
                return
            damage = max(1, int(attacker.current_hp) - 1)
            self.apply_direct_damage(defender, damage, attacker=attacker)
            attacker.current_hp = 1.0
            return

        #Circle Throw & Dragon Tail custom handling - they do damage twice, once before throwing, then again after throwing if the thrown guy hits something
        if move.get("name") == "Circle Throw" or move.get("name") == "Dragon Tail":
            damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self)
            self.apply_direct_damage(defender, damage, attacker=attacker)
            if is_critical:
                self.log_message("A critical hit!")
            if type_mult >= 1.25:
                self.log_message("It's super effective!")
            elif 0.25 < type_mult <= 0.75:
                self.log_message("It's not very effective...")
            elif type_mult == 0.25:
                self.log_message("It had little effect...")

            if int(defender.current_hp) <= 0:
                return

            ax, ay = get_pokemon_position(self, attacker)
            tx, ty = get_pokemon_position(self, defender)
            dx = 1 if tx > ax else (-1 if tx < ax else 0)
            dy = 1 if ty > ay else (-1 if ty < ay else 0)
            if dx == 0 and dy == 0:
                dx = 1

            collision_ct: str | Pokemon | None = None
            collision_step = 0
            for s in range(1, 6):
                nx = tx + s * dx
                ny = ty + s * dy
                if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height) or self.floor.grid[ny][nx] == WALL_CHAR:
                    collision_ct = "wall"
                    collision_step = s
                    break
                p2 = self.get_poke_at(nx, ny)
                if p2 and p2 is not defender and int(p2.current_hp) > 0:
                    collision_ct = p2
                    collision_step = s
                    break

            if collision_ct is not None:
                landing_x = tx + (collision_step - 1) * dx
                landing_y = ty + (collision_step - 1) * dy
                self.set_poke_pos(defender, landing_x, landing_y)

                d2, _, _ = calculate_damage(attacker, defender, move, self)
                self.apply_direct_damage(defender, d2, attacker=attacker)

                target_coll_name = "wall" if collision_ct == "wall" else (collision_ct.name if isinstance(collision_ct, Pokemon) else "")
                self.log_message(f"{defender.name} was thrown into {target_coll_name}!")

                if isinstance(collision_ct, Pokemon):
                    p2_damage, _, _ = calculate_damage(attacker, collision_ct, move, self)
                    self.apply_direct_damage(collision_ct, p2_damage, attacker=attacker)
            else:
                landing_x = tx + 5 * dx
                landing_y = ty + 5 * dy
                self.set_poke_pos(defender, landing_x, landing_y)
                self.log_message(f"{defender.name} was thrown away!")
            return

        #Power Swap custom handling
        if move.get("name") == "Power Swap":
            u_atk = attacker.stat_modifiers.get("Attack", 0)
            u_spatk = attacker.stat_modifiers.get("Special_Attack", 0)
            t_atk = defender.stat_modifiers.get("Attack", 0)
            t_spatk = defender.stat_modifiers.get("Special_Attack", 0)

            if u_atk == t_atk and u_spatk == t_spatk:
                self.log_message("The move failed!")
                return

            attacker.stat_modifiers["Attack"] = t_atk
            attacker.stat_modifiers["Special_Attack"] = t_spatk
            defender.stat_modifiers["Attack"] = u_atk
            defender.stat_modifiers["Special_Attack"] = u_spatk

            self.log_message(f"{attacker.name} swapped their Attack and Sp. Atk stat changes with {defender.name}!")
            return

        #Guard Swap custom handling (it's just Power Swap but with defense instead)
        if move.get("name") == "Guard Swap":
            u_def = attacker.stat_modifiers.get("Defense", 0)
            u_spdef = attacker.stat_modifiers.get("Special_Defense", 0)
            t_def = defender.stat_modifiers.get("Defense", 0)
            t_spdef = defender.stat_modifiers.get("Special_Defense", 0)

            if u_def == t_def and u_spdef == t_spdef:
                self.log_message("The move failed!")
                return

            attacker.stat_modifiers["Defense"] = t_def
            attacker.stat_modifiers["Special_Defense"] = t_spdef
            defender.stat_modifiers["Defense"] = u_def
            defender.stat_modifiers["Special_Defense"] = u_spdef

            self.log_message(f"{attacker.name} swapped their Defense and Sp. Def stat changes with {defender.name}!")
            return

        #Baton Pass custom handling
        if move.get("name") == "Baton Pass":
            from targeting import get_room_tiles_at
            ax, ay = get_pokemon_position(self, attacker)
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            allies = self.party if attacker in self.party else self.spawned_pokemon
            excluded_statuses = {"Poison", "Bad Poison", "Burn", "Sleep", "Paralysis", "Frozen", "Leech Seed", "Minimized", "Fire Spin", "Sand Tomb", "Whirlpool", "Wrap", "Clamp", "Bind"}

            self.log_message(f"{attacker.name} used Baton Pass!")
            for ally in list(allies):
                if ally == attacker or int(ally.current_hp) <= 0:
                    continue
                px, py = get_pokemon_position(self, ally)
                in_room = (px, py) in room_tiles if room_tiles else (max(abs(px - ax), abs(py - ay)) <= 1)
                if in_room:
                    for stat in attacker.stat_modifiers:
                        ally.stat_modifiers[stat] = attacker.stat_modifiers[stat]
                    ally.movement_speed_stage = attacker.movement_speed_stage

                    for status_name, duration in attacker.status_effects.items():
                        if status_name not in excluded_statuses and (isinstance(duration, bool) and duration or isinstance(duration, (int, float)) and duration > 0):
                            ally.status_effects[status_name] = duration
                    self.log_message(f"{ally.name} received stat changes and status effects!")


        #Transform custom handling (ew)
        if move.get("name") == "Transform":
            orig_name = attacker.name
            if getattr(attacker, "transform_original_state", None) is None:
                attacker.transform_original_state = {
                    "species_data": attacker.species_data,
                    "nickname": attacker.nickname,
                    "temp_types": list(attacker.temp_types) if attacker.temp_types is not None else None,
                    "moves": [dict(m) for m in attacker.moves],
                    "stat_modifiers": dict(attacker.stat_modifiers),
                    "stats": dict(attacker.stats),
                }

            #Copy the defender's species and metadata to the user
            attacker.species_data = defender.species_data
            attacker.nickname = defender.nickname
            attacker.temp_types = list(defender.temp_types) if defender.temp_types is not None else None
            attacker.stat_modifiers = dict(defender.stat_modifiers)
            attacker.moves = [dict(m) for m in defender.moves]

            #User stat's will have changed, so we need to recalculate them
            attacker.recalculate_stats()

            max_hp = float(attacker.stats["HP"])
            if attacker.current_hp > max_hp:
                attacker.current_hp = max_hp

            self.log_message(f"{orig_name} transformed into {defender.name}!")
            return

        #Conversion custom handling (it's actually Conversion 2, but Conversion 1 was merged into Reflect Type since they both do the same thing)
        if move.get("name") == "Conversion":
            last_move = getattr(attacker, "last_hit_by_move", None)
            if not last_move:
                self.log_message("The move failed!")
                return

            cat = last_move.get("category")
            pwr = last_move.get("power")
            if cat == "Status" or pwr is None or pwr <= 0:
                self.log_message("The move failed!")
                return

            m_type = str(last_move.get("type", "typeless"))
            if m_type == "typeless":
                self.log_message("The move failed!")
                return

            move_type_key = str(last_move.get("name")) if last_move.get("name") in ("Muddy Water", "Freeze-Dry") else m_type

            from pokemon_db import VALID_TYPES
            from type_chart import get_effectiveness_multiplier

            #Basically we need to choose types that resist the last damaging move, in the following priority; little effect > 2 not very effective > not very effective > normal > super effective > 2 super effective
            #Multiple type combos with same score? Choose one at random
            standard_types = sorted([t for t in VALID_TYPES if t != "typeless"])
            single_candidates = [[t] for t in standard_types]
            dual_candidates = [[t1, t2] for i, t1 in enumerate(standard_types) for t2 in standard_types[i + 1:]]
            all_candidates = single_candidates + dual_candidates

            current_types = set(attacker.types)

            tier1_different = []
            tier2_different = []

            for combo in all_candidates:
                mult = get_effectiveness_multiplier(move_type_key, combo)
                combo_set = set(combo)
                if mult <= 0.5:
                    if combo_set != current_types:
                        tier1_different.append(combo)
                elif mult < 1.0:
                    if combo_set != current_types:
                        tier2_different.append(combo)

            chosen_combo = None
            if tier1_different:
                chosen_combo = random.choice(tier1_different)
            elif tier2_different:
                chosen_combo = random.choice(tier2_different)

            if chosen_combo is None:
                self.log_message("The move failed!")
                return

            attacker.temp_types = chosen_combo
            type_str = "/".join(chosen_combo)
            self.log_message(f"{attacker.name}'s type changed to {type_str}!")
            return

        #Recycle custom handling
        if move.get("name") == "Recycle":
            if attacker not in self.party:
                self.log_message("The move failed!")
                return
            plain_seed_idx = next((i for i, item in enumerate(self.inventory) if item.get("name") == "Plain Seed"), None)
            if plain_seed_idx is None:
                self.log_message("The move failed!")
                return

            from items import ITEMS_DB
            seed_berry_pool = [
                dict(data) for name, data in ITEMS_DB.items()
                if (name.endswith(" Seed") or name.endswith(" Berry") or name.endswith("Seed") or name.endswith("Berry"))
                and name != "Plain Seed"
            ]
            if not seed_berry_pool:
                seed_berry_pool = [
                    dict(data) for name, data in ITEMS_DB.items()
                    if (name.endswith(" Seed") or name.endswith(" Berry") or name.endswith("Seed") or name.endswith("Berry"))
                ]

            new_item = random.choice(seed_berry_pool).copy()
            target_item = self.inventory[plain_seed_idx]
            if target_item.get("stackable", False) and target_item.get("count", 1) > 1:
                target_item["count"] -= 1
                self.inventory.append(new_item)
            else:
                self.inventory[plain_seed_idx] = new_item

            article = "an" if new_item["name"][0].lower() in "aeiou" else "a"
            self.log_message(f"The Plain Seed was recycled into {article} {new_item['name']}!")
            return

        #Explosion & Self-Destruct custom handling
        if move.get("name") in ("Explosion", "Self-Destruct"):
            ax, ay = get_pokemon_position(self, attacker)
            size = 7 if move["name"] == "Explosion" else 5
            power = move.get("power", 250 if move["name"] == "Explosion" else 200)

            self.log_message(f"{attacker.name} exploded!")
            self.trigger_explosion(ax, ay, size=size, base_power=power, attacker=attacker, cause_name=move["name"])
            return
         
        #Sleep Talk custom handling
        if move.get("name") == "Sleep Talk":
            if not (attacker.status_effects.get("Sleep", 0) > 0 or attacker.status_effects.get("Resting", 0) > 0):
                self.log_message("The move failed!")
                return

            blacklist = {
                "Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore",
                "Fly", "Dive", "Dig", "Bounce", "Uproar",
                "Focus Punch", "Solar Beam", "Razor Wind", "Sky Attack", "Skull Bash", "Geomancy", "Freeze Shock", "Ice Burn", "Bide", "Beak Blast"
            }
            eligible_moves = []
            for m in attacker.moves:
                m_name = m.get("name", "")
                if m_name in blacklist:
                    continue
                if m.get("charge_turns") or m.get("is_charging"):
                    continue
                eligible_moves.append(m)

            if not eligible_moves:
                self.log_message("The move failed!")
                return

            chosen = random.choice(eligible_moves)
            self.log_message(f"{attacker.name}'s Sleep Talk called {chosen['name']}!")
            from targeting import get_valid_targets
            targets = get_valid_targets(self, attacker, chosen)
            range_str = chosen.get("range", "Adjacent enemy")
            if range_str == "Enemy in front":
                range_str = "Adjacent enemy"
            is_multi = range_str.startswith("All ") or "room" in range_str.lower() or "floor" in range_str.lower()
            if is_multi or range_str == "User":
                self.execute_multi_move(attacker, targets if targets else [attacker], chosen, free=True)
            elif targets:
                self.execute_single_move(attacker, targets[0], chosen, free=True)
            else:
                self.execute_single_move(attacker, attacker, chosen, free=True)
            return

        #Belly Drum custom handling
        if move.get("name") == "Belly Drum":
            current_atk = attacker.stat_modifiers.get("Attack", 0)
            if current_atk < 6:
                attacker.apply_stat_modifier("Attack", 6 - current_atk, self)
            else:
                self.log_message(f"{attacker.name}'s stat cannot go any higher.")
            return
        #Dream Eater custom handling
        if move.get("name") == "Dream Eater":
            if not (defender.status_effects.get("Sleep", 0) > 0 or defender.status_effects.get("Resting", 0) > 0):
                self.log_message("That can only be used on a sleeping target!")
                return

        #Perish Song custom handling
        if move.get("name") == "Perish Song":
            enemies = [p for p in self.spawned_pokemon if p not in self.party and int(p.current_hp) > 0] if attacker in self.party else [p for p in self.party if int(p.current_hp) > 0]
            self.log_message(f"{attacker.name} used Perish Song!")
            for enemy in enemies:
                acc = 20.0
                acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
                acc_stage = max(-6, min(6, acc_stage))
                acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))
                ev_stage = enemy.stat_modifiers.get("Evasion", 0)
                ev_stage = max(-6, min(6, ev_stage))
                ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))
                modified_acc = acc * acc_mult / ev_mult
                if random.randint(1, 100) <= modified_acc:
                    if enemy.status_effects.get("Perishing", 0) > 0:
                        self.log_message(f"{enemy.name} is already perishing!")
                    else:
                        enemy.apply_status("Perishing", self, duration=5)
                else:
                    self.log_message(f"{enemy.name} is unaffected!")
            return

        #Counter custom handling
        if move.get("name") == "Counter":
            attacker.apply_status("Counter", self)
            return

        #Mirror Coat custom handling
        if move.get("name") == "Mirror Coat":
            attacker.apply_status("Mirror Coat", self)
            return

        #Endure custom handling
        if move.get("name") == "Endure":
            attacker.apply_status("Endure", self)
            return

        #Growth custom handling
        if move.get("name") == "Growth":
            stages = 2 if self.weather in ("Sunny", "Harsh Sunlight") else 1
            attacker.apply_stat_modifier("Attack", stages, self)
            attacker.apply_stat_modifier("Special_Attack", stages, self)
            return

        #Synthesis custom handling
        if move.get("name") == "Synthesis":
            max_hp = float(attacker.stats["HP"])
            if self.weather in ("Sunny", "Harsh Sunlight"):
                heal_amount = max(1, int(max_hp * (2.0 / 3.0)))
            elif self.weather in ("Clear", "Normal", None) or not self.weather:
                heal_amount = max(1, int(max_hp * 0.5))
            else:
                heal_amount = max(1, int(max_hp * 0.25))
            attacker.current_hp = min(max_hp, attacker.current_hp + heal_amount)
            self.log_message(f"{attacker.name}'s HP was restored.")
            return

        #Roost custom handling
        if move.get("name") == "Roost":
            max_hp = float(attacker.stats["HP"])
            heal_amount = max(1, int(max_hp * 0.5))
            attacker.current_hp = min(max_hp, attacker.current_hp + heal_amount)
            self.log_message(f"{attacker.name}'s HP was restored.")

            user_types = getattr(attacker, "temp_types", None) or getattr(attacker, "types", attacker.species_data.get("types", []))
            is_flying_or_levitating = (
                "Flying" in user_types
                or attacker.status_effects.get("Magnet Rise", 0) > 0
                or attacker.status_effects.get("Telekinesis", 0) > 0
                or attacker.species_data.get("ability") == "Levitate"
                or getattr(attacker, "is_floating", False)
            )
            if is_flying_or_levitating:
                attacker.apply_status("Landed", self, duration=1)
            return

        #Magnetic Flux custom handling
        if move.get("name") == "Magnetic Flux":
            from targeting import get_room_tiles_at
            ax, ay = get_pokemon_position(self, attacker)
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            self.log_message(f"{attacker.name} used Magnetic Flux!")
            for p in list(self.party + self.spawned_pokemon):
                if int(p.current_hp) <= 0:
                    continue
                px, py = get_pokemon_position(self, p)
                in_room = (px, py) in room_tiles if room_tiles else (max(abs(px - ax), abs(py - ay)) <= 1)
                if in_room:
                    p_types = getattr(p, "temp_types", None) or getattr(p, "types", p.species_data.get("types", []))
                    if "Electric" in p_types:
                        p.apply_stat_modifier("Defense", 1, self)
                        p.apply_stat_modifier("Special_Defense", 1, self)
            return

        #Teleport custom handling
        if move.get("name") == "Teleport":
            empty_tiles = []
            for y in range(self.floor.height):
                for x in range(self.floor.width):
                    if self.floor.grid[y][x] == FLOOR_CHAR and self.get_poke_at(x, y) is None:
                        empty_tiles.append((x, y))
            if empty_tiles:
                nx, ny = random.choice(empty_tiles)
                self.set_poke_pos(attacker, nx, ny)
                self.log_message(f"{attacker.name} teleported away!")
            else:
                self.log_message("There's nowhere to Teleport to!")
            return

        #Curse custom handling (ew)
        if move.get("name") == "Curse":
            user_types = getattr(attacker, "temp_types", None) or getattr(attacker, "types", attacker.species_data.get("types", []))
            if "Ghost" in user_types:
                if defender != attacker and defender.status_effects.get("Safeguard", 0) > 0:
                    self.log_message(f"{defender.name} is protected by Safeguard!")
                else:
                    defender.apply_status("Curse", self)

                max_hp = float(attacker.stats["HP"])
                hp_loss = float(int(0.5 * max_hp))
                attacker.current_hp -= hp_loss
                self.log_message(f"{attacker.name} cut its own HP!")
                tx, ty = get_pokemon_position(self, attacker)
                self.flash_damages[(tx, ty)] = (f"{int(hp_loss)}", "\033[91m")
                self.trigger_damage_flash()

                if int(attacker.current_hp) <= 0:
                    self.log_pokemon_defeat(attacker)
                    if attacker in self.party:
                        self.remove_party_member(attacker)
                    elif attacker in self.spawned_pokemon:
                        self.spawned_pokemon.remove(attacker)
            else:
                attacker.change_movement_speed(attacker.movement_speed_stage - 1, self)
                attacker.apply_stat_modifier("Attack", 1, self)
                attacker.apply_stat_modifier("Defense", 1, self)
            return

        #Aqua Ring custom handling
        if move.get("name") == "Aqua Ring":
            attacker.apply_status("Aqua Ring", self)
            return

        #Minimize custom handling
        if move.get("name") == "Minimize":
            attacker.apply_stat_modifier("Evasion", 2, self)
            attacker.apply_status("Minimized", self)
            return

        #Memento custom handling
        if move.get("name") == "Memento":
            from targeting import get_room_tiles_at
            ax, ay = get_pokemon_position(self, attacker)
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            enemies = [p for p in self.spawned_pokemon if p not in self.party] if attacker in self.party else list(self.party)
            
            target_enemies = []
            for p in enemies:
                if int(p.current_hp) <= 0:
                    continue
                px, py = get_pokemon_position(self, p)
                if room_tiles:
                    if (px, py) in room_tiles:
                        target_enemies.append(p)
                else:
                    if max(abs(px - ax), abs(py - ay)) <= 1:
                        target_enemies.append(p)

            attacker.current_hp = 0.0
            self.log_pokemon_defeat(attacker)

            for enemy in target_enemies:
                for stat in ["Attack", "Defense", "Special_Attack", "Special_Defense", "Speed", "Accuracy", "Evasion"]:
                    enemy.stat_modifiers[stat] = -6
                self.log_message(f"{enemy.name}'s stats fell severely!")

            if attacker in self.party:
                self.remove_party_member(attacker)
            elif attacker in self.spawned_pokemon:
                self.spawned_pokemon.remove(attacker)
            return

        #Yawn custom handling
        if move.get("name") == "Yawn":
            if defender.status_effects.get("Sleepless") or defender.status_effects.get("Sleep", 0) > 0 or defender.status_effects.get("Drowsy", 0) > 0:
                self.log_message("The move failed!")
                return
            if defender.status_effects.get("Safeguard", 0) > 0:
                self.log_message(f"{defender.name} is protected by Safeguard!")
                return
            defender.apply_status("Drowsy", self, duration=3)
            return

        #Electric Terrain custom handling
        if move.get("name") == "Electric Terrain":
            self.set_weather("Electric Terrain", duration=random.randint(10, 20))
            for p in list(self.party + self.spawned_pokemon):
                p_types = getattr(p, "temp_types", None) or p.species_data.get("types", [])
                if "Flying" not in p_types:
                    if p.status_effects.get("Sleep", 0) > 0:
                        p.cure_status("Sleep", self)
                    if p.status_effects.get("Resting", 0) > 0:
                        p.cure_status("Resting", self)
                    if p.status_effects.get("Drowsy", 0) > 0:
                        p.cure_status("Drowsy", self)
            return

        #Magnet Rise custom handling
        if move.get("name") == "Magnet Rise":
            if getattr(self, "gravity", False):
                self.log_message("Gravity prevents Magnet Rise!")
                return
            attacker.apply_status("Magnet Rise", self, duration=5)
            return

        #Lock-On custom handling
        if move.get("name") == "Lock-On":
            if defender != attacker and defender.status_effects.get("Safeguard", 0) > 0:
                self.log_message(f"{defender.name} is protected by Safeguard!")
            else:
                attacker.apply_status("Lock-On", self)
            return

        #Acupressure custom handling
        if move.get("name") == "Acupressure":
            from targeting import get_room_tiles_at
            ax, ay = get_pokemon_position(self, attacker)
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            allies = self.party if attacker in self.party else self.spawned_pokemon
            room_allies = []
            for p in list(allies):
                px, py = get_pokemon_position(self, p)
                if room_tiles and (px, py) in room_tiles:
                    room_allies.append(p)
                elif not room_tiles and max(abs(px - ax), abs(py - ay)) <= 1:
                    room_allies.append(p)

            for target in room_allies:
                if target.status_effects.get("Safeguard", 0) > 0 and target != attacker:
                    self.log_message(f"{target.name} is protected by Safeguard!")
                    continue

                candidates = []
                stat_names = ["Attack", "Defense", "Special_Attack", "Special_Defense", "Accuracy", "Evasion"]
                for st in stat_names:
                    if target.stat_modifiers.get(st, 0) < 6:
                        candidates.append(st)
                if target.movement_speed_stage < 3:
                    candidates.append("Movement_Speed")

                if not candidates:
                    self.log_message(f"{target.name}'s stats cannot go any higher!")
                    continue

                chosen_stat = random.choice(candidates)
                boost = random.choice([1, 2])

                if chosen_stat == "Movement_Speed":
                    actual_boost = min(boost, 3 - target.movement_speed_stage)
                    target.change_movement_speed(target.movement_speed_stage + actual_boost, self)
                else:
                    actual_boost = min(boost, 6 - target.stat_modifiers.get(chosen_stat, 0))
                    target.apply_stat_modifier(chosen_stat, actual_boost, self)
            return

        #Future Sight custom handling
        if move.get("name") == "Future Sight":
            ax, ay = get_pokemon_position(self, attacker)
            #Find an adjacent non-wall tile that does NOT have Future Sight already active
            dirs = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,-1), (-1,1), (1,1)]
            random.shuffle(dirs)
            chosen_tile = None
            for dx, dy in dirs:
                tx, ty = ax + dx, ay + dy
                if 0 <= tx < self.floor.width and 0 <= ty < self.floor.height and self.floor.grid[ty][tx] != WALL_CHAR:
                    if not any(fs["tile"] == (tx, ty) for fs in getattr(self, "future_sight_effects", [])):
                        chosen_tile = (tx, ty)
                        break
            if chosen_tile:
                if not hasattr(self, "future_sight_effects"):
                    self.future_sight_effects = []
                self.future_sight_effects.append({
                    "attacker": attacker,
                    "tile": chosen_tile,
                    "turns_left": 2,
                    "move": move
                })
                self.log_message(f"{attacker.name} foresaw an attack!")
            else:
                self.log_message("The move failed!")
            return

        #Swallow custom handling
        if move.get("name") == "Swallow":
            stacks = attacker.status_effects.get("Stockpile", 0)
            if stacks <= 0:
                self.log_message("There's nothing to Swallow!")
                return

            heal_percent = 1.0 / 3.0 if stacks == 1 else (2.0 / 3.0 if stacks == 2 else 1.0)
            heal_amt = int(float(attacker.stats["HP"]) * heal_percent)
            attacker.current_hp = min(float(attacker.stats["HP"]), attacker.current_hp + heal_amt)
            self.log_message(f"{attacker.name}'s HP was restored.")
            tx, ty = get_pokemon_position(self, attacker)
            self.flash_damages[(tx, ty)] = (f"{heal_amt}", "HEAL")
            self.trigger_damage_flash()

            attacker.status_effects["Stockpile"] = 0
            attacker.apply_stat_modifier("Defense", -stacks, self)
            attacker.apply_stat_modifier("Special_Defense", -stacks, self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Spit Up custom handling
        #TODO: Make this use the same damage formula as everything else
        if move.get("name") == "Spit Up":
            stacks = attacker.status_effects.get("Stockpile", 0)
            if stacks <= 0:
                self.log_message("There's nothing to Spit Up!")
                return

            spit_up_move = move.copy()
            spit_up_move["power"] = 100 * stacks

            #Accuracy check
            acc = move.get("accuracy", 100)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            if random.randint(1, 100) > modified_acc:
                self.log_message(f"{defender.name} avoided the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
            else:
                damage, is_critical, type_mult = calculate_damage(attacker, defender, spit_up_move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)
                if defender.napping:
                    defender.napping = False
                    defender.just_woke_up = True

                if defender.status_effects.get("Sleep", 0) > 0 and damage > 0:
                    defender.cure_status("Sleep", self)

                val_petr = defender.status_effects.get("Petrified", 0)
                if val_petr > 0 or val_petr == -1:
                    defender.cure_status("Petrified", self)

                if damage > 0 and defender.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        defender.cure_status("Confusion", self)

                if is_critical:
                    self.log_message("A critical hit!")

                if type_mult >= 1.25:
                    self.log_message("It's super effective!")
                elif 0.25 < type_mult <= 0.75:
                    self.log_message("It's not very effective...")
                elif type_mult == 0.25:
                    self.log_message("It had little effect...")

                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()

                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)

            #Reset stockpile charges and stats (always happens, even on a miss!)
            attacker.status_effects["Stockpile"] = 0
            attacker.apply_stat_modifier("Defense", -stacks, self)
            attacker.apply_stat_modifier("Special_Defense", -stacks, self)

            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #OHKO move custom handling
        if move.get("name") in ("Fissure", "Sheer Cold", "Guillotine"):
            #Guillotine always fails against Ghost Pokémon
            if move.get("name") == "Guillotine":
                def_types = getattr(defender, "temp_types", None) or getattr(defender, "types", defender.species_data.get("types", []))
                if "Ghost" in def_types:
                    self.log_message(f"It had no effect on {defender.name}!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("0", "MISS")
                    self.trigger_damage_flash()
                    if attacker.status_effects.get("Laser Focus"):
                        attacker.cure_status("Laser Focus", self)
                    return
            elif move.get("name") == "Fissure":
                #Check if frozen
                if defender.status_effects.get("Frozen", 0) > 0:
                    self.log_message(f"{defender.name} is frozen solid!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("0", "MISS")
                    self.trigger_damage_flash()
                    if attacker.status_effects.get("Laser Focus"):
                        attacker.cure_status("Laser Focus", self)
                    return

                #Fissure always fails against Flying Pokémon
                if move.get("name") == "Fissure":
                    if "Flying" in defender.species_data.get("types", []):
                        self.log_message(f"It had no effect on {defender.name}!")
                        tx, ty = get_pokemon_position(self, defender)
                        self.flash_damages[(tx, ty)] = ("0", "MISS")
                        self.trigger_damage_flash()
                        if attacker.status_effects.get("Laser Focus"):
                            attacker.cure_status("Laser Focus", self)
                        return

            #Accuracy check: dependent on user's Speed and target's Speed (bypassed if Lock-On active)
            has_lock_on = bool(attacker.status_effects.get("Lock-On"))
            if not has_lock_on:
                u_speed = attacker.get_modified_stat("Speed", self)
                t_speed = defender.get_modified_stat("Speed", self)
                
                u_stage = attacker.movement_speed_stage
                u_mult = 0.5 if u_stage == -1 else float(1 + u_stage)
                t_stage = defender.movement_speed_stage
                t_mult = 0.5 if t_stage == -1 else float(1 + t_stage)
                
                u_speed_eff = u_speed * u_mult
                t_speed_eff = t_speed * t_mult

                if u_speed_eff < t_speed_eff:
                    #If user's Speed is lower, than always misses
                    self.log_message(f"{defender.name} was unaffected!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    if attacker.status_effects.get("Laser Focus"):
                        attacker.cure_status("Laser Focus", self)
                    return

                #Otherwise accuracy is 20% * (user_speed / target_speed), capped at 60%
                ratio = u_speed_eff / max(1.0, float(t_speed_eff))
                acc = min(60.0, 20.0 * ratio)
                
                if random.random() * 100.0 > acc:
                    self.log_message(f"{defender.name} avoided the attack!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    if attacker.status_effects.get("Laser Focus"):
                        attacker.cure_status("Laser Focus", self)
                    return

            #Defeats defender instantly
            damage = int(defender.current_hp)
            defender.current_hp = 0.0
            
            #Standard cures on hit
            if defender.napping:
                defender.napping = False
                defender.just_woke_up = True
            if defender.status_effects.get("Sleep", 0) > 0:
                defender.cure_status("Sleep", self)
            val_petr = defender.status_effects.get("Petrified", 0)
            if val_petr > 0 or val_petr == -1:
                defender.cure_status("Petrified", self)
            if defender.status_effects.get("Confusion", 0) > 0:
                if random.randint(1, 100) <= 50:
                    defender.cure_status("Confusion", self)

            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = (damage, 1.0)
            self.trigger_damage_flash()

            self.log_message(f"It's a one-hit KO!")
            attacker.defeat_pokemon(defender, game=self)
            if defender in self.spawned_pokemon:
                self.spawned_pokemon.remove(defender)
            elif defender in self.party:
                self.remove_party_member(defender)

            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Super Fang custom handling
        if move.get("name") == "Super Fang":
            #Check if frozen
            if defender.status_effects.get("Frozen", 0) > 0:
                self.log_message(f"{defender.name} is frozen solid!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("0", "MISS")
                self.trigger_damage_flash()
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            #Accuracy check (Super Fang has 90% accuracy)
            acc = move.get("accuracy", 90)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            if random.randint(1, 100) > modified_acc:
                self.log_message(f"{defender.name} avoided the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            if int(defender.current_hp) <= 1:
                damage = 0
            else:
                damage = int(defender.current_hp) // 2
                m_type = move.get("type", "Normal")
                if defender.status_effects.get("All Resist") or defender.status_effects.get(f"{m_type} Resist"):
                    damage = max(1, int(damage * 0.5))

            if damage > 0:
                defender.current_hp = float(int(defender.current_hp) - damage)

                #Standard cures on hit
                if defender.napping:
                    defender.napping = False
                    defender.just_woke_up = True
                if defender.status_effects.get("Sleep", 0) > 0:
                    defender.cure_status("Sleep", self)

                if move.get("name") == "Freeze-Dry":
                    def_types = getattr(defender, "temp_types", None) or getattr(defender, "types", defender.species_data.get("types", []))
                    if "Water" in def_types:
                        defender.apply_status("Frozen", self)
                val_petr = defender.status_effects.get("Petrified", 0)
                if val_petr > 0 or val_petr == -1:
                    defender.cure_status("Petrified", self)
                if defender.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        defender.cure_status("Confusion", self)

            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = (damage, 1.0)
            self.trigger_damage_flash()

            #Defeat check
            if int(defender.current_hp) <= 0:
                self.log_pokemon_defeat(defender)
                attacker.defeat_pokemon(defender, game=self)
                if defender in self.spawned_pokemon:
                    self.spawned_pokemon.remove(defender)
                elif defender in self.party:
                    self.remove_party_member(defender)

            #Remove laser focus
            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Endeavor custom handling (runs before status/power checks)
        if move.get("name") == "Endeavor":
            #Check if frozen
            if defender.status_effects.get("Frozen", 0) > 0:
                self.log_message(f"{defender.name} is frozen solid!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("0", "MISS")
                self.trigger_damage_flash()
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            #Accuracy check
            acc = move.get("accuracy", 100)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5
            if random.randint(1, 100) > modified_acc:
                self.log_message(f"{defender.name} avoided the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            if int(attacker.current_hp) >= int(defender.current_hp):
                self.log_message("But it failed!")
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return
            damage = int(defender.current_hp) - int(attacker.current_hp)
            defender.current_hp = float(int(defender.current_hp) - damage)

            #Standard cures on hit
            if defender.napping:
                defender.napping = False
                defender.just_woke_up = True
            if defender.status_effects.get("Sleep", 0) > 0 and damage > 0:
                defender.cure_status("Sleep", self)
            val_petr = defender.status_effects.get("Petrified", 0)
            if val_petr > 0 or val_petr == -1:
                defender.cure_status("Petrified", self)
            if damage > 0 and defender.status_effects.get("Confusion", 0) > 0:
                if random.randint(1, 100) <= 50:
                    defender.cure_status("Confusion", self)

            tx, ty = get_pokemon_position(self, defender)
            self.flash_damages[(tx, ty)] = (damage, 1.0)
            self.trigger_damage_flash()

            #Defeat check
            if int(defender.current_hp) <= 0:
                self.log_pokemon_defeat(defender)
                attacker.defeat_pokemon(defender, game=self)
                if defender in self.spawned_pokemon:
                    self.spawned_pokemon.remove(defender)
                elif defender in self.party:
                    self.remove_party_member(defender)

            #Laser Focus wears off
            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Rollout / Ice Ball custom handling
        if move.get("name") == "Rollout":
            #Check if frozen
            if defender.status_effects.get("Frozen", 0) > 0:
                self.log_message(f"{defender.name} avoided the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            hits = 5
            base_power = 10
            #2x power if Defense Curl was used previously
            if getattr(attacker, "last_used_move", None) == "Defense Curl":
                base_power = 20

            curr_power = base_power
            acc = 90
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5

            hit_count = 0
            for hit_idx in range(hits):
                if int(defender.current_hp) <= 0:
                    break

                if random.randint(1, 100) > modified_acc:
                    self.log_message(f"{defender.name} avoided the attack!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    break

                hit_count += 1
                temp_move = move.copy()
                temp_move["power"] = curr_power

                damage, is_critical, type_mult = calculate_damage(attacker, defender, temp_move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)

                if defender.napping:
                    defender.napping = False
                    defender.just_woke_up = True
                if defender.status_effects.get("Sleep", 0) > 0 and damage > 0:
                    defender.cure_status("Sleep", self)
                val_petr = defender.status_effects.get("Petrified", 0)
                if val_petr > 0 or val_petr == -1:
                    defender.cure_status("Petrified", self)
                if damage > 0 and defender.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        defender.cure_status("Confusion", self)

                if is_critical:
                    self.log_message("A critical hit!")
                if type_mult >= 1.25:
                    self.log_message("It's super effective!")
                elif 0.25 < type_mult <= 0.75:
                    self.log_message("It's not very effective...")
                elif type_mult == 0.25:
                    self.log_message("It had little effect...")

                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()

                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    break

                curr_power *= 2

            if hit_count > 0:
                self.log_message(f"Hit {hit_count} time(s)!")

            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Fury Cutter custom handling (it works the same as Rollout/Ice Ball but without the 2x Defense Curl increase)
        if move.get("name") == "Fury Cutter":
            #Check if frozen
            if defender.status_effects.get("Frozen", 0) > 0:
                self.log_message(f"{defender.name} is frozen solid!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("0", "MISS")
                self.trigger_damage_flash()
                #Laser Focus wears off
                if attacker.status_effects.get("Laser Focus"):
                    attacker.cure_status("Laser Focus", self)
                return

            hits = 5
            curr_power = 15
            acc = 90
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5

            hit_count = 0
            for hit_idx in range(hits):
                if int(defender.current_hp) <= 0:
                    break

                if random.randint(1, 100) > modified_acc:
                    self.log_message(f"{defender.name} avoided the attack!")
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = ("/", "MISS")
                    self.trigger_damage_flash()
                    break

                hit_count += 1
                temp_move = move.copy()
                temp_move["power"] = curr_power

                damage, is_critical, type_mult = calculate_damage(attacker, defender, temp_move, self)
                defender.current_hp = float(int(defender.current_hp) - damage)

                if defender.napping:
                    defender.napping = False
                    defender.just_woke_up = True
                if defender.status_effects.get("Sleep", 0) > 0 and damage > 0:
                    defender.cure_status("Sleep", self)
                val_petr = defender.status_effects.get("Petrified", 0)
                if val_petr > 0 or val_petr == -1:
                    defender.cure_status("Petrified", self)
                if damage > 0 and defender.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        defender.cure_status("Confusion", self)

                if is_critical:
                    self.log_message("A critical hit!")
                if type_mult >= 1.25:
                    self.log_message("It's super effective!")
                elif 0.25 < type_mult <= 0.75:
                    self.log_message("It's not very effective...")
                elif type_mult == 0.25:
                    self.log_message("It had little effect...")

                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = (damage, type_mult)
                self.trigger_damage_flash()

                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    break

                curr_power *= 2

            if hit_count > 0:
                self.log_message(f"Hit {hit_count} time(s)!")
            #Laser Focus wears off
            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)

            self.apply_generic_move_effects(attacker, defender, move)
            return

        #If it's a non-damaging status move, execute effects directly and return
        category = move.get("category", "Status")
        power = move.get("power")
        if category == "Status" or power is None or power <= 0:
            if attacker.status_effects.get("Taunted"):
                self.log_message(f"{attacker.name} cannot use status moves while Taunted!")
                return
            if attacker != defender:
                defender.last_hit_by_move = dict(move)
            if attacker != defender and getattr(defender, "napping", False):
                defender.napping = False
                defender.just_woke_up = True
            self.apply_generic_move_effects(attacker, defender, move)
            return

        #Check if frozen
        if defender.status_effects.get("Frozen", 0) > 0:
            if move.get("type") == "Fire":
                defender.cure_status("Frozen", self)
            else:
                self.log_message(f"{defender.name} is frozen solid!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                return

        #Check if out of sight hit
        dx, dy = get_pokemon_position(self, defender)
        currently_visible = self._compute_currently_visible()
        defender_visible = (dx, dy) in currently_visible
        is_out_of_sight_hit = (attacker in self.party and not defender_visible)

        #Accuracy check
        raw_acc = move.get("accuracy")
        move_name = move.get("name")
        if move_name == "Hurricane":
            if self.weather in ("Rain", "Heavy Rain"):
                raw_acc = None
            elif self.weather in ("Sunny", "Harsh Sunlight"):
                raw_acc = 50
        elif move_name == "Thunder":
            if self.weather in ("Rain", "Heavy Rain", "Hail", "Snow"):
                raw_acc = None
            elif self.weather in ("Sunny", "Harsh Sunlight"):
                raw_acc = 50
        elif move_name == "Toxic":
            atk_types = getattr(attacker, "temp_types", None) or attacker.types
            if "Poison" in atk_types:
                raw_acc = None

        #When Minimized, some moves deal 2x damage and bypass accuracy checks
        minimized_double_moves = ("Body Slam", "Stomp", "Astonish", "Extrasensory", "Dragon Rush", "Heavy Slam")
        is_minimized_bypass = bool(defender.status_effects.get("Minimized") and move.get("name") in minimized_double_moves)
        if raw_acc is not None and not attacker.status_effects.get("Lock-On") and not is_minimized_bypass:
            acc = float(raw_acc)
            acc_stage = attacker.stat_modifiers.get("Accuracy", 0)
            acc_stage = max(-6, min(6, acc_stage))
            if acc_stage >= 0:
                acc_mult = (3.0 + acc_stage) / 3.0
            else:
                acc_mult = 3.0 / (3.0 + abs(acc_stage))

            ev_stage = defender.stat_modifiers.get("Evasion", 0)
            ev_stage = max(-6, min(6, ev_stage))
            if ev_stage >= 0:
                ev_mult = (3.0 + ev_stage) / 3.0
            else:
                ev_mult = 3.0 / (3.0 + abs(ev_stage))

            modified_acc = acc * acc_mult / ev_mult
            if self.gravity:
                modified_acc *= 1.5

            if random.randint(1, 100) > modified_acc:
                attacker.last_move_failed_turn = self.turn_number
                if defender_visible:
                    self.log_message(f"{defender.name} avoided the attack!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                if move.get("name") in ("High Jump Kick", "Axe Kick"):
                    self.trigger_crash_damage(attacker)
                if move.get("name") in ("Giga Impact", "Hyper Beam"):
                    attacker.apply_status("Paused", self, duration=1)
                return

        #Ghost type immunity crash check for High Jump Kick / Axe Kick
        if move.get("name") in ("High Jump Kick", "Axe Kick"):
            def_types = getattr(defender, "temp_types", None) or getattr(defender, "types", defender.species_data.get("types", []))
            if "Ghost" in def_types:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message(f"It had no effect on {defender.name}!")
                tx, ty = get_pokemon_position(self, defender)
                self.flash_damages[(tx, ty)] = ("/", "MISS")
                self.trigger_damage_flash()
                self.trigger_crash_damage(attacker)
                return

        if is_out_of_sight_hit:
            self.log_message("You hit something in the distance!")
            self.suppress_target_logs = True

        if attacker != defender:
            defender.last_hit_by_move = dict(move)

        if self.is_team_pokemon(attacker) and not self.is_team_pokemon(defender):
            defender.has_been_attacked_by_team = True

        if move.get("name") in ("Raging Bull", "Brick Break"):
            for status in ("Light Screen", "Reflect"):
                if defender.status_effects.get(status, 0) > 0:
                    defender.cure_status(status, self)
            if move.get("name") == "Raging Bull":
                for status in ("Counter", "Mirror Coat"):
                    if defender.status_effects.get(status, 0) > 0:
                        defender.cure_status(status, self)

        try:
            #Determine hit amount from multi-hit effect if defined
            hits = 1
            multi_hit_effect = None
            for effect in move.get("effects", []):
                if effect.get("effect_type") == "multi_hit":
                    multi_hit_effect = effect
                    break
            if multi_hit_effect:
                min_hits = multi_hit_effect.get("min_hits", 1)
                max_hits = multi_hit_effect.get("max_hits", 1)
                hits = random.randint(min_hits, max_hits)

            actual_hits = 0
            for hit_idx in range(hits):
                if int(attacker.current_hp) <= 0 or int(defender.current_hp) <= 0:
                    break

                actual_hits += 1
                damage, is_critical, type_mult = calculate_damage(attacker, defender, move, self, is_multi_target=is_multi_target)
                h_before = int(defender.current_hp)
                if move.get("name") == "Spite":
                    defender.current_pp = max(0, defender.current_pp - damage)
                    self.log_message(f"Spite reduced {defender.name}'s PP by {damage}!")
                else:
                    if defender.status_effects.get("Endure", 0) > 0 and damage >= defender.current_hp:
                        defender.current_hp = 1.0
                        self.log_message(f"{defender.name} endured the hit!")
                    else:
                        defender.last_damage_source = f"{attacker.name}'s {move.get('name', 'move')}"
                        defender.current_hp = float(int(defender.current_hp) - damage)
                hp_lost = h_before - int(defender.current_hp)

                if move.get("category") in ("Physical", "Special") and damage > 0:
                    defender.damage_hit_turns.append(self.turn_number)
                    defender.damaged_by_pokemons[attacker] = self.turn_number

                if defender.napping:
                    defender.napping = False
                    defender.just_woke_up = True

                #Cure sleep if damaging attack hit
                if defender.status_effects.get("Sleep", 0) > 0:
                    if move.get("category") in ("Physical", "Special") and damage > 0:
                        defender.cure_status("Sleep", self)

                if move.get("name") == "Freeze-Dry":
                    def_types = getattr(defender, "temp_types", None) or getattr(defender, "types", defender.species_data.get("types", []))
                    if "Water" in def_types:
                        defender.apply_status("Frozen", self)

                #Check Vital Throw counter-throw effect
                if damage > 0 and defender.status_effects.get("Vital Throw", 0) > 0 and int(attacker.current_hp) > 0 and attacker != defender:
                    ax, ay = get_pokemon_position(self, attacker)
                    dx, dy = get_pokemon_position(self, defender)
                    range_str = move.get("range", "")
                    is_room_floor = "room" in range_str.lower() or "floor" in range_str.lower()
                    if max(abs(ax - dx), abs(ay - dy)) <= 1 and not is_room_floor:
                        self.trigger_vital_throw_counter(attacker, defender, damage)

                #Force target out of Dive if hit by Surf or Whirlpool
                if defender.status_effects.get("Diving", 0) > 0 and move.get("name") in ("Surf", "Whirlpool"):
                    defender.cure_status("Diving", self)
                    defender.charging_move = None
                    self.log_message(f"{defender.name} was forced out of the dive!")

                #Focus Punch interruption check
                if damage > 0 and defender.charging_move and defender.charging_move.get("move", {}).get("name") == "Focus Punch":
                    defender.charging_move = None
                    defender.cure_status("Focusing", self)
                    defender.last_move_failed_turn = self.turn_number
                    self.log_message(f"{defender.name} lost its focus and couldn't move!")

                #Remove petrification if attacked
                val_petr = defender.status_effects.get("Petrified", 0)
                if val_petr > 0 or val_petr == -1:
                    defender.cure_status("Petrified", self)

                #50% chance to cure confusion when damaged
                if damage > 0 and defender.status_effects.get("Confusion", 0) > 0:
                    if random.randint(1, 100) <= 50:
                        defender.cure_status("Confusion", self)

                if is_critical:
                    self.log_message("A critical hit!")

                if type_mult >= 1.25:
                    self.log_message("It's super effective!")
                elif 0.25 < type_mult <= 0.75:
                    self.log_message("It's not very effective...")
                elif type_mult == 0.25:
                    self.log_message("It had little effect...")

                #HP-draining moves
                heal_amount = 0
                is_drain_move = False
                for effect in move.get("effects", []):
                    if effect.get("effect_type") == "drain" and hp_lost > 0:
                        is_drain_move = True
                        heal_amount = max(1, hp_lost // 2) #Always restore at least 1 HP!
                        attacker.current_hp = min(float(attacker.stats["HP"]), attacker.current_hp + heal_amount)
                        self.log_message(f"{attacker.name}'s HP was restored.")
                        tx, ty = get_pokemon_position(self, defender)
                        self.flash_damages[(tx, ty)] = (damage, type_mult)
                        ax, ay = get_pokemon_position(self, attacker)
                        self.flash_damages[(ax, ay)] = (f"{heal_amount}", "HEAL")
                        self.trigger_damage_flash()

                if not is_drain_move and (move.get("category") in ("Physical", "Special") or damage > 0):
                    tx, ty = get_pokemon_position(self, defender)
                    self.flash_damages[(tx, ty)] = (damage, type_mult)
                    self.trigger_damage_flash()

                #Handle recoil
                for effect in move.get("effects", []):
                    if effect.get("effect_type") == "recoil" and damage > 0:
                        chance = effect.get("chance", 1.0)
                        if random.random() <= chance:
                            recoil_pct = effect.get("recoil_percent", 0.0)
                            recoil = int(damage * recoil_pct)
                            if recoil > 0:
                                attacker.last_damage_source = "recoil"
                                attacker.current_hp -= recoil
                                self.log_message(f"{attacker.name} was damaged by the recoil!")
                                if int(attacker.current_hp) <= 0:
                                    self.log_pokemon_defeat(attacker)
                                    if attacker in self.party:
                                        self.remove_party_member(attacker)
                                    elif attacker in self.spawned_pokemon:
                                        self.spawned_pokemon.remove(attacker)

                #Handle Counter physical damage reflection
                if move.get("category") == "Physical" and damage > 0 and defender.status_effects.get("Counter", 0) > 0 and attacker != defender and int(attacker.current_hp) > 0:
                    refl = max(1, damage // 2)
                    attacker.last_damage_source = f"{defender.name}'s Counter"
                    attacker.current_hp = float(int(attacker.current_hp) - refl)
                    self.log_message(f"{defender.name}'s Counter reflected {refl} damage back to {attacker.name}!")
                    ax, ay = get_pokemon_position(self, attacker)
                    self.flash_damages[(ax, ay)] = (refl, 1.0)
                    self.trigger_damage_flash()
                    if int(attacker.current_hp) <= 0:
                        self.log_pokemon_defeat(attacker)
                        if attacker in self.spawned_pokemon:
                            self.spawned_pokemon.remove(attacker)
                        elif attacker in self.party:
                            self.remove_party_member(attacker)

                #Handle Mirror Coat special damage reflection
                if move.get("category") == "Special" and damage > 0 and defender.status_effects.get("Mirror Coat", 0) > 0 and attacker != defender and int(attacker.current_hp) > 0:
                    refl = max(1, damage // 2)
                    attacker.last_damage_source = f"{defender.name}'s Mirror Coat"
                    attacker.current_hp = float(int(attacker.current_hp) - refl)
                    self.log_message(f"{defender.name}'s Mirror Coat reflected {refl} damage back to {attacker.name}!")
                    ax, ay = get_pokemon_position(self, attacker)
                    self.flash_damages[(ax, ay)] = (refl, 1.0)
                    self.trigger_damage_flash()
                    if int(attacker.current_hp) <= 0:
                        self.log_pokemon_defeat(attacker)
                        if attacker in self.spawned_pokemon:
                            self.spawned_pokemon.remove(attacker)
                        elif attacker in self.party:
                            self.remove_party_member(attacker)

                if int(defender.current_hp) <= 0:
                    self.log_pokemon_defeat(defender)
                    attacker.defeat_pokemon(defender, game=self)
                    if defender.status_effects.get("Destiny Bond", 0) > 0 and attacker != defender and int(attacker.current_hp) > 0:
                        self.log_message(f"{defender.name} took {attacker.name} down with it!")
                        attacker.last_damage_source = f"{defender.name}'s Destiny Bond"
                        attacker.current_hp = 0.0
                        if attacker in self.spawned_pokemon:
                            self.spawned_pokemon.remove(attacker)
                        elif attacker in self.party:
                            self.remove_party_member(attacker)
                    if move.get("name") == "Fell Stinger":
                        attacker.apply_stat_modifier("Attack", 2, self)
                    if move.get("name") == "Smack Down":
                        if defender.status_effects.get("Magnet Rise", 0) > 0:
                            defender.cure_status("Magnet Rise", self)
                    if move.get("name") == "Pay Day":
                        tx, ty = get_pokemon_position(self, defender)
                        money_item = {
                            "name": "Poké",
                            "type": "Money",
                            "amount": max(1, int(attacker.level)),
                            "symbol": "P",
                            "appearance": "P",
                            "color": "\033[30;43m",
                            "rarity": "Common",
                            "description": "The currency of the Pokémon world. Spend it wisely!",
                            "stackable": False,
                            "drop_percentage": 0
                        }
                        self.place_item_on_floor(tx, ty, money_item)
                    if defender in self.spawned_pokemon:
                        self.spawned_pokemon.remove(defender)
                    elif defender in self.party:
                        self.remove_party_member(defender)
                    break

            if multi_hit_effect and actual_hits > 0:
                self.log_message(f"Hit {actual_hits} time(s)!")

            if move.get("name") == "Smack Down":
                def_types = getattr(defender, "temp_types", None) or getattr(defender, "types", defender.species_data.get("types", []))
                is_airborne_charging = bool(
                    defender.charging_move
                    and defender.charging_move.get("move", {}).get("name") in ("Fly", "Bounce")
                )
                is_flying = bool(
                    "Flying" in def_types
                    or defender.status_effects.get("Magnet Rise", 0) > 0
                    or is_airborne_charging
                )
                if defender.status_effects.get("Magnet Rise", 0) > 0:
                    defender.cure_status("Magnet Rise", self)
                if is_airborne_charging and defender.charging_move:
                    c_move_name = defender.charging_move.get("move", {}).get("name", "move")
                    self.log_message(f"{defender.name}'s {c_move_name} was interrupted!")
                    defender.charging_move = None
                    defender.last_move_failed_turn = self.turn_number
                if is_flying:
                    defender.apply_status("Landed", self, duration=9999)

            #Apply generic effects (stat_change, status_apply, healing)
            self.apply_generic_move_effects(attacker, defender, move)
        finally:
            if is_out_of_sight_hit:
                self.suppress_target_logs = False

        #Laser Focus / Lock-On wear off after user's next attack
        if move.get("category") in ("Physical", "Special"):
            if attacker.status_effects.get("Laser Focus"):
                attacker.cure_status("Laser Focus", self)
            if attacker.status_effects.get("Lock-On"):
                attacker.cure_status("Lock-On", self)

        if move.get("name") in ("Giga Impact", "Hyper Beam"):
            attacker.apply_status("Paused", self, duration=1)

    def flush_pending_exp(self):
        """Hands out the combined amount of experience points gained from all defeated Pokémon during a turn"""
        combined_exp = getattr(self, "pending_team_exp", 0)
        self.pending_team_exp = 0
        if combined_exp <= 0:
            return

        import math
        import random

        team_members = [p for p in self.party if int(getattr(p, "current_hp", 0)) > 0]
        if not team_members:
            return

        weights = [1.0 / float(p.level) for p in team_members]
        total_weight = sum(weights)

        shares: dict = {}
        sum_allocated = 0
        for p, w in zip(team_members, weights):
            fraction = w / total_weight
            allocated = math.floor(combined_exp * fraction)
            shares[p] = allocated
            sum_allocated += allocated

        remainder = combined_exp - sum_allocated
        if remainder > 0:
            min_lvl = min(p.level for p in team_members)
            lowest_pokes = [p for p in team_members if p.level == min_lvl]

            leader_in_lowest = [p for p in lowest_pokes if p is getattr(self, "player_pokemon", None) or getattr(p, "is_leader", False)]
            if leader_in_lowest:
                chosen_recipient = leader_in_lowest[0]
            else:
                chosen_recipient = random.choice(lowest_pokes)

            shares[chosen_recipient] += remainder

        for p, share in shares.items():
            if share > 0:
                p.gain_experience(share, game=self)

    def execute_move(self, attacker: Pokemon, targets: Pokemon | list[Pokemon], move: dict, free: bool = False):
        """Executes a move, either single- or multi-target"""
        is_outer_attack = not getattr(self, "exp_batching_active", False)
        if is_outer_attack:
            self.exp_batching_active = True
            self.pending_team_exp = 0

        try:
            self._execute_move_internal(attacker, targets, move, free=free)
        finally:
            if is_outer_attack:
                self.exp_batching_active = False
                self.flush_pending_exp()

    def is_snatchable_move(self, move: dict) -> bool:
        """Determines if a Status move can be redirected by Snatch.
        A move can be snatched if it does not lower stats or cause one of the main negative status effects listed in the function."""
        if move.get("category") != "Status":
            return False

        EXCLUDED_STATUSES = {"Poison", "Toxic", "Burn", "Paralysis", "Sleep", "Frozen", "Confusion"}

        #1. Validate status effects
        for eff in move.get("effects", []):
            eff_type = eff.get("effect_type")
            if eff_type == "stat_change":
                if eff.get("stages", 0) < 0:
                    return False
            elif eff_type == "status_apply":
                if eff.get("status") in EXCLUDED_STATUSES:
                    return False

        #2. Validate stat changes
        if move.get("stat_changes"):
            for stat, change in move["stat_changes"].items():
                if change < 0:
                    return False

        #3. Validate status_effect field (internal use only)
        if move.get("status_effect") in EXCLUDED_STATUSES:
            return False

        return True

    def apply_snatched_move_effects(self, snatcher: Pokemon, attacker: Pokemon, move: dict):
        """Applies the effects of a snatched move to the snatcher."""
        import random
        from targeting import get_pokemon_position

        move_name = move.get("name")

        NEGATIVE_STATUSES = {"Poison", "Toxic", "Burn", "Paralysis", "Sleep", "Frozen", "Confusion"}

        if move_name == "Belly Drum":
            current_atk = snatcher.stat_modifiers.get("Attack", 0)
            if current_atk < 6:
                snatcher.apply_stat_modifier("Attack", 6 - current_atk, self)
            else:
                self.log_message(f"{snatcher.name}'s Attack can't go any higher.")
            return

        if move_name == "Growth":
            stages = 2 if self.weather in ("Sunny", "Harsh Sunlight") else 1
            snatcher.apply_stat_modifier("Attack", stages, self)
            snatcher.apply_stat_modifier("Special_Attack", stages, self)
            return

        if move_name in ("Synthesis", "Roost", "Recover", "Moonlight", "Life Dew", "Morning Sun", "Soft-Boiled", "Milk Drink", "Heal Pulse"):
            max_hp = float(snatcher.stats["HP"])
            if move_name == "Synthesis":
                if self.weather in ("Sunny", "Harsh Sunlight"):
                    heal_amount = max(1, int(max_hp * (2.0 / 3.0)))
                elif self.weather in ("Clear", "Normal", None) or not self.weather:
                    heal_amount = max(1, int(max_hp * 0.5))
                else:
                    heal_amount = max(1, int(max_hp * 0.25))
            else:
                heal_amount = max(1, int(max_hp * 0.5))
            snatcher.current_hp = min(max_hp, snatcher.current_hp + heal_amount)
            self.log_message(f"{snatcher.name}'s HP was restored.")
            tx, ty = get_pokemon_position(self, snatcher)
            self.flash_damages[(tx, ty)] = (f"{heal_amount}", "HEAL")
            self.trigger_damage_flash()
            return

        if move_name == "Magnetic Flux":
            snatcher_types = getattr(snatcher, "temp_types", None) or getattr(snatcher, "types", snatcher.species_data.get("types", []))
            if "Electric" in snatcher_types:
                snatcher.apply_stat_modifier("Defense", 1, self)
                snatcher.apply_stat_modifier("Special_Defense", 1, self)
            return

        if move_name == "Minimize":
            snatcher.apply_stat_modifier("Evasion", 2, self)
            snatcher.apply_status("Minimized", self)
            return

        if move_name == "Aqua Ring":
            snatcher.apply_status("Aqua Ring", self)
            return

        if move_name == "Magnet Rise":
            snatcher.apply_status("Magnet Rise", self, duration=5)
            return

        if move_name == "Charge":
            snatcher.apply_stat_modifier("Special_Defense", 1, self)
            snatcher.apply_status("Charging", self, duration=1)
            return

        if move_name == "Acupressure":
            stat_names = ["Attack", "Defense", "Special_Attack", "Special_Defense", "Accuracy", "Evasion"]
            candidates = [st for st in stat_names if snatcher.stat_modifiers.get(st, 0) < 6]
            if snatcher.movement_speed_stage < 3:
                candidates.append("Movement_Speed")
            if candidates:
                chosen_stat = random.choice(candidates)
                boost = random.choice([1, 2])
                if chosen_stat == "Movement_Speed":
                    actual_boost = min(boost, 3 - snatcher.movement_speed_stage)
                    snatcher.change_movement_speed(snatcher.movement_speed_stage + actual_boost, self)
                else:
                    actual_boost = min(boost, 6 - snatcher.stat_modifiers.get(chosen_stat, 0))
                    snatcher.apply_stat_modifier(chosen_stat, actual_boost, self)
            return

        if move_name in ("Counter", "Mirror Coat", "Endure", "Safeguard", "Protect", "Quick Guard", "Wide Guard", "Vital Throw", "Ingrain", "Laser Focus", "Focus Energy", "Light Screen", "Reflect"):
            snatcher.apply_status(move_name, self)
            return

        #Generic effects
        for effect in move.get("effects", []):
            eff_type = effect.get("effect_type")
            if eff_type == "stat_change":
                stat = effect.get("stat")
                stages = effect.get("stages", 0)
                if stat and stages > 0:
                    snatcher.apply_stat_modifier(stat, stages, self)
            elif eff_type == "healing":
                max_hp = float(snatcher.stats["HP"])
                heal_amt = max(1, int(max_hp * 0.5))
                snatcher.current_hp = min(max_hp, snatcher.current_hp + heal_amt)
                self.log_message(f"{snatcher.name}'s HP was restored.")
                tx, ty = get_pokemon_position(self, snatcher)
                self.flash_damages[(tx, ty)] = (f"{heal_amt}", "HEAL")
                self.trigger_damage_flash()
            elif eff_type == "status_apply":
                status_name = effect.get("status")
                duration = effect.get("duration")
                if status_name == "2x Speed":
                    if snatcher.movement_speed_stage < 3:
                        snatcher.change_movement_speed(snatcher.movement_speed_stage + 1, self)
                elif status_name and status_name not in NEGATIVE_STATUSES:
                    snatcher.apply_status(status_name, self, duration=duration)
            elif eff_type == "cure_all_statuses":
                for st in ["Poison", "Toxic", "Burn", "Paralysis", "Sleep", "Frozen", "Confusion"]:
                    snatcher.cure_status(st, self)

        #Generic top-level fields (internal use only)
        if move.get("stat_changes"):
            for stat, change in move["stat_changes"].items():
                if change > 0:
                    snatcher.apply_stat_modifier(stat, change, self)
        status_app = move.get("status_effect")
        if status_app and status_app not in NEGATIVE_STATUSES:
            snatcher.apply_status(status_app, self)

    def _execute_move_internal(self, attacker: Pokemon, targets: Pokemon | list[Pokemon], move: dict, free: bool = False):
        """Executiton method for single-target and multi-target moves."""
        if attacker is self.player_pokemon:
            self.start_player_action()
        if isinstance(targets, Pokemon):
            is_single = True
            single_target: Pokemon = targets
            target_list: list[Pokemon] = [get_actual_target(self, attacker, single_target, move)]
        else:
            is_single = False
            target_list = list(targets)
        if attacker.status_effects.get("Cowering", 0) > 0 and is_single and single_target:
            ax, ay = get_pokemon_position(self, attacker)
            tx, ty = get_pokemon_position(self, single_target)
            dx = 1 if tx > ax else (-1 if tx < ax else 0)
            dy = 1 if ty > ay else (-1 if ty < ay else 0)
            if dx != 0 or dy != 0:
                opp_x = ax - dx
                opp_y = ay - dy
                opp_target = self.get_poke_at(opp_x, opp_y)
                if opp_target and opp_target is not attacker:
                    target_list = [opp_target]
                    self.log_message(f"{attacker.name}'s attack went the wrong way!")

        if move.get("category") == "Status" and self.is_snatchable_move(move):
            ax, ay = get_pokemon_position(self, attacker)
            from targeting import get_room_tiles_at
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            snatchers = []
            for p in self.party + self.spawned_pokemon:
                if p is not attacker and int(getattr(p, "current_hp", 0)) > 0 and p.status_effects.get("Snatch", 0) > 0:
                    px, py = get_pokemon_position(self, p)
                    if room_tiles and (px, py) in room_tiles:
                        snatchers.append(p)
                    elif not room_tiles and max(abs(px - ax), abs(py - ay)) <= 5:
                        snatchers.append(p)
            if snatchers:
                for snatcher in snatchers:
                    self.log_message(f"{snatcher.name} snatched {attacker.name}'s {move['name']}!")
                    self.apply_snatched_move_effects(snatcher, attacker, move)
                return

        if not free:
            try:
                attacker.use_move(move, game=self)
                self.moved_used_this_turn.add(attacker)
            except ValueError as e:
                #Error handling message
                self.log_message(f"Error! {str(e)} Please report this to C4!")
                return
            self.log_message(f"{attacker.name} used {move['name']}!")
        else:
            self.moved_used_this_turn.add(attacker)

        attacker.last_used_move = move["name"]
        attacker.last_used_move_on_floor = move["name"]

        if move.get("name") != "Echoed Voice":
            #Reset Echoed Voice chain counter
            attacker.echoed_voice_count = 0

        #Power scaling for Stored Power, Moonblast, Echoed Voice, and Round
        if move.get("name") == "Stored Power":
            pos_stages = sum(max(0, stage) for stage in attacker.stat_modifiers.values())
            move = move.copy()
            move["power"] = min(240, 20 + 20 * pos_stages)
        elif move.get("name") == "Moonblast":
            move = move.copy()
            if self.weather in ("Sunny", "Harsh Sunlight"):
                move["power"] = 120
            elif self.weather in ("Rain", "Heavy Rain", "Hail", "Sandstorm", "Snow"):
                move["power"] = 60
            else:
                move["power"] = 95
        elif move.get("name") == "Echoed Voice":
            count = getattr(attacker, "echoed_voice_count", 0)
            move = move.copy()
            move["power"] = min(200, 40 + 40 * count)
            attacker.echoed_voice_count = count + 1
        elif move.get("name") == "Round":
            self.round_users_this_turn.add(attacker)
            num_users = len(self.round_users_this_turn)
            move = move.copy()
            move["power"] = min(150, 50 + 25 * (num_users - 1))

        if move.get("name") == "Fake Out":
            if getattr(attacker, "fake_out_used_this_floor", False):
                self.log_message(f"{attacker.name} can't use Fake Out again on this floor!")
                return
            attacker.fake_out_used_this_floor = True

        #Handle Protect / Quick Guard / Wide Guard / Endure consecutive success chance
        if move["name"] in ("Protect", "Quick Guard", "Wide Guard", "Endure"):
            success_chance = (1.0 / 2.0) ** getattr(attacker, "protect_consecutive", 0)
            attacker.protect_consecutive = getattr(attacker, "protect_consecutive", 0) + 1
            if random.random() > success_chance:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message("The move failed!")
                return

        if attacker not in self.party:
            attacker.seen_moves.add(move["name"])

        #Decoy multi-target rule: If at least one target is a Decoy, only hit decoys
        if not is_single:
            decoy_targets = [t for t in target_list if t.status_effects.get("Decoy", 0) > 0]
            if decoy_targets:
                target_list = decoy_targets

        #Snore custom handling
        if move.get("name") == "Snore":
            if not (attacker.status_effects.get("Sleep", 0) > 0 or attacker.status_effects.get("Resting", 0) > 0):
                attacker.last_move_failed_turn = self.turn_number
                self.log_message("Snore can only be used while sleeping.")
                return
            from targeting import get_valid_targets
            adj_enemies = get_valid_targets(self, attacker, move)
            valid_snore = [d for d in adj_enemies if int(getattr(d, "current_hp", 0)) > 0]
            is_multi_snore = len(valid_snore) > 1
            if valid_snore:
                for defender in valid_snore:
                    self._process_single_target_hit(attacker, defender, move, is_multi_target=is_multi_snore, free=True)
            else:
                attacker.last_move_failed_turn = self.turn_number
                self.log_message("The move failed!")
            return

        valid_targets = [d for d in target_list if int(getattr(d, "current_hp", 0)) > 0]
        is_multi = len(valid_targets) > 1

        for defender in list(target_list):
            if int(defender.current_hp) > 0:
                self._process_single_target_hit(attacker, defender, move, is_multi_target=is_multi, free=free)

        if move.get("name") == "Charge":
            attacker.apply_status("Charging", self, duration=1)

        if move.get("type") == "Electric" and move.get("category") in ("Physical", "Special"):
            if attacker.status_effects.get("Charging", 0) > 0:
                attacker.cure_status("Charging", self)

        #Uproar status application to all Pokemon in the room
        if move.get("name") == "Uproar":
            from targeting import get_room_tiles_at
            ax, ay = get_pokemon_position(self, attacker)
            room_tiles = get_room_tiles_at(self.floor, ax, ay)
            room_pokes = []
            for p in list(self.party + self.spawned_pokemon):
                px, py = get_pokemon_position(self, p)
                if room_tiles and (px, py) in room_tiles:
                    room_pokes.append(p)
                elif not room_tiles and max(abs(px - ax), abs(py - ay)) <= 1:
                    room_pokes.append(p)
            for p in room_pokes:
                p.apply_status("Sleepless", self)

    def execute_single_move(self, attacker: Pokemon, defender: Pokemon, move: dict, free: bool = False):
        """Executes a single-target move, consuming PP and applying the move's effects to the target"""
        self.execute_move(attacker, defender, move, free=free)

    def execute_multi_move(self, attacker: Pokemon, targets: list[Pokemon], move: dict, free: bool = False):
        """Executes a multi-target move (all targets in range), consuming PP once and applying the move's effects to the targets"""
        self.execute_move(attacker, targets, move, free=free)

    def can_switch_places_with_ally(self, ally: Pokemon) -> bool:
        """Checks if the player can switch places with an ally.
        Returns False if the ally is under certain negative status effects that prevent movement."""
        if ally is None:
            return False

        status_effects = getattr(ally, "status_effects", {})

        #Sleeping (including Resting)
        if status_effects.get("Sleep", 0) > 0 or status_effects.get("Resting", 0) > 0 or getattr(ally, "napping", False):
            return False

        #Wrapped
        if status_effects.get("Wrap", 0) > 0 or any(ally == b.get("defender") for b in getattr(self, "wrap_bindings", [])):
            return False

        #Frozen
        if status_effects.get("Frozen", 0) > 0:
            return False

        #Petrified
        petrified_val = status_effects.get("Petrified", 0)
        if petrified_val > 0 or petrified_val == -1:
            return False

        #Sand Tomb
        if status_effects.get("Sand Tomb", 0) > 0 or any(ally == b.get("defender") for b in getattr(self, "sand_tomb_bindings", [])):
            return False

        #Fire Spin
        if status_effects.get("Fire Spin", 0) > 0 or any(ally == b.get("defender") for b in getattr(self, "fire_spin_bindings", [])):
            return False

        #Whirlpool
        if status_effects.get("Whirlpool", 0) > 0 or any(ally == b.get("defender") for b in getattr(self, "whirlpool_bindings", [])):
            return False

        #Charging a multi-turn move
        if getattr(ally, "charging_move", None) is not None:
            return False
        if (status_effects.get("Charging", 0) > 0 or
                status_effects.get("Digging", 0) > 0 or
                status_effects.get("Diving", 0) > 0 or
                bool(status_effects.get("Focusing", False))):
            return False

        return True

    def can_player_step_to(self, dx: int, dy: int) -> bool:
        """Checks if the player can move in direction (dx, dy), checking any obstacles on the target tile."""
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        #Clamp player to within map bounds
        if not (0 <= new_x < self.floor.width and 0 <= new_y < self.floor.height):
            return False

        has_mobile = (self.player_pokemon.status_effects.get("Mobile", 0) > 0)
        is_wall = (self.floor.grid[new_y][new_x] == WALL_CHAR)

        if is_wall and not has_mobile:
            return False

        #Check target tile occupancy
        target_poke = None
        for p in self.party + self.spawned_pokemon:
            if p is self.player_pokemon:
                continue
            px, py = get_pokemon_position(self, p)
            if px == new_x and py == new_y:
                target_poke = p
                break

        if target_poke is not None:
            if target_poke in self.party:
                if not self.can_switch_places_with_ally(target_poke):
                    return False
                if not has_mobile and dx != 0 and dy != 0:
                    corner_1 = self.floor.grid[self.player_y][new_x]
                    corner_2 = self.floor.grid[new_y][self.player_x]
                    if corner_1 == WALL_CHAR or corner_2 == WALL_CHAR:
                        return False
                return True
            else:
                #Can't step into a tile occupied by an enemy
                return False

        #Diagonal movement can't cut corners
        if not has_mobile and dx != 0 and dy != 0:
            corner_1 = self.floor.grid[self.player_y][new_x]
            corner_2 = self.floor.grid[new_y][self.player_x]
            if corner_1 == WALL_CHAR or corner_2 == WALL_CHAR:
                return False

        return True

    def try_move(self, dx: int, dy: int) -> bool:
        """Attempts to move the player by (dx, dy) checking collisions and corner-cutting."""
        if dx == 0 and dy == 0:
            #Stand still / wait a turn
            return True

        if self.player_pokemon.status_effects.get("Fire Spin", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is trapped by Fire Spin!")
            return False

        if self.player_pokemon.status_effects.get("Puppet", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is a puppet and can't be controlled!")
            return False

        if self.player_pokemon.status_effects.get("Wrap", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is wrapped and can't move!")
            return False

        if self.player_pokemon.status_effects.get("Sand Tomb", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} is trapped by Sand Tomb!")
            return False

        if self.player_pokemon.status_effects.get("Stuck", 0) > 0 or self.player_pokemon.status_effects.get("Ingrain", 0) > 0:
            self.log_message(f"{self.player_pokemon.name} can't move!")
            return False

        if self.player_pokemon.status_effects.get("Confusion", 0) > 0:
            directions = [(d_x, d_y) for d_x in [-1, 0, 1] for d_y in [-1, 0, 1] if not (d_x == 0 and d_y == 0)]
            valid_dirs = [d for d in directions if self.can_player_step_to(d[0], d[1])]
            if not valid_dirs:
                return False
            dx, dy = random.choice(valid_dirs)

        new_x = self.player_x + dx
        new_y = self.player_y + dy

        #Clamp player to within map bounds
        if not (0 <= new_x < self.floor.width and 0 <= new_y < self.floor.height):
            return False

        has_mobile = (self.player_pokemon.status_effects.get("Mobile", 0) > 0)
        is_wall = (self.floor.grid[new_y][new_x] == WALL_CHAR)

        if is_wall and not has_mobile:
            return False

        #Check target tile occupancy
        target_poke = None
        for p in self.party + self.spawned_pokemon:
            if p is self.player_pokemon:
                continue
            px, py = get_pokemon_position(self, p)
            if px == new_x and py == new_y:
                target_poke = p
                break

        if target_poke is not None:
            if target_poke in self.party:
                if not self.can_switch_places_with_ally(target_poke):
                    return False

                #Leader swaps places with non-leader teammate
                if not has_mobile and dx != 0 and dy != 0:
                    corner_1 = self.floor.grid[self.player_y][new_x]
                    corner_2 = self.floor.grid[new_y][self.player_x]
                    if corner_1 == WALL_CHAR or corner_2 == WALL_CHAR:
                        return False

                old_x, old_y = self.player_x, self.player_y
                self.start_player_action()
                self.set_poke_pos(self.player_pokemon, new_x, new_y)
                self.set_poke_pos(target_poke, old_x, old_y)
                target_poke.swapped_this_turn = True #Consumes teammate's turn!
                self.check_auto_pickup(new_x, new_y)
                return True
            else:
                #Can't step into a tile occupied by an enemy
                return False

        #Diagonal movement cannot cut corners, this reflects PMD behavior
        if not has_mobile and dx != 0 and dy != 0:
            #Check adjacent cardinal tiles: (new_x, player_y) and (player_x, new_y)
            corner_1 = self.floor.grid[self.player_y][new_x]
            corner_2 = self.floor.grid[new_y][self.player_x]
            if corner_1 == WALL_CHAR or corner_2 == WALL_CHAR:
                return False

        #Successful movement
        self.start_player_action()
        self.set_poke_pos(self.player_pokemon, new_x, new_y)
        self.check_auto_pickup(new_x, new_y)
        return True

    @property
    def max_inventory_capacity(self) -> int:
        """Returns the maximum inventory capacity based on party size: 20 for 1 member, +4 for each additional member (max 40)"""
        party_size = len(getattr(self, "party", []))
        if party_size <= 0:
            return 20
        return min(40, 20 + 4 * (party_size - 1))

    def check_over_capacity_inventory_drop(self, fainted_member: Pokemon):
        """If party size decreases and inventory is over capacity, drops excess items around the defeated party member."""
        max_cap = self.max_inventory_capacity
        if len(self.inventory) > max_cap:
            excess_count = len(self.inventory) - max_cap
            fx, fy = get_pokemon_position(self, fainted_member)
            self.log_message("The Toolbox is over capacity!")
            for _ in range(excess_count):
                dropped_item = self.inventory.pop()
                item_name = dropped_item.get("name", "Item")
                self.log_message(f"The {item_name} fell onto the floor!")
                self.place_item_on_floor(fx, fy, dropped_item)

    def attempt_revive_member(self, member: Pokemon) -> bool:
        """Checks if a revival item is in inventory to revive a defeated teammate. Priority: Reviver Seed > Tiny Reviver Seed > Posess Orb"""
        if member not in self.party or getattr(member, "cannot_be_revived", False):
            return False

        reviver_idx = None
        tiny_reviver_idx = None

        for idx, item in enumerate(self.inventory):
            name = item.get("name")
            if name == "Reviver Seed":
                reviver_idx = idx
                break
            elif name == "Tiny Reviver Seed" and tiny_reviver_idx is None:
                tiny_reviver_idx = idx

        chosen_idx = reviver_idx if reviver_idx is not None else tiny_reviver_idx
        if chosen_idx is None:
            if member is self.player_pokemon or getattr(member, "is_leader", False):
                possess_idx = None
                for idx, item in enumerate(self.inventory):
                    if item.get("name") == "Possess Orb":
                        possess_idx = idx
                        break
                living_teammates = [p for p in self.party if p is not member and int(getattr(p, "current_hp", 0)) > 0]
                if possess_idx is not None and living_teammates:
                    living_teammates.sort(key=lambda p: getattr(p, "level", 1))
                    sacrificed = living_teammates[0]
                    self.inventory.pop(possess_idx)
                    sacrificed.cannot_be_revived = True
                    sacrificed.current_hp = 0.0

                    member.current_hp = float(member.stats["HP"])
                    member.status_effects = {k: (0 if isinstance(v, int) else False) for k, v in member.status_effects.items()}
                    if hasattr(member, "moves"):
                        for m in member.moves:
                            m["current_pp"] = m.get("max_pp", 10)
                    if hasattr(member, "current_belly"):
                        member.current_belly = member.max_belly
                    for st in member.stat_modifiers:
                        if member.stat_modifiers[st] < 0:
                            member.stat_modifiers[st] = 0
                    self.log_message(f"{member.name} possessed {sacrificed.name}!", important=True)
                    self.remove_party_member(sacrificed)
                    return True
            return False

        inv_item = self.inventory[chosen_idx]
        if inv_item.get("stackable", False) and inv_item.get("count", 1) > 1:
            inv_item["count"] -= 1
            seed_name = inv_item["name"]
        else:
            consumed_item = self.inventory.pop(chosen_idx)
            seed_name = consumed_item["name"]

        member.current_hp = float(member.stats["HP"])
        member.status_effects = {k: (0 if isinstance(v, int) else False) for k, v in member.status_effects.items()}

        if seed_name == "Reviver Seed":
            if hasattr(member, "moves"):
                for m in member.moves:
                    m["current_pp"] = m.get("max_pp", 10)
            if hasattr(member, "current_belly"):
                member.current_belly = member.max_belly
            for st in member.stat_modifiers:
                if member.stat_modifiers[st] < 0:
                    member.stat_modifiers[st] = 0
            self.log_message(f"{member.name} was revived by the Reviver Seed!", important=True)
        else:
            self.log_message(f"{member.name} was revived by the Tiny Reviver Seed!", important=True)

        return True

    def remove_party_member(self, member: Pokemon):
        """Party member defeat handling. Removes a party member, promotes next active member if leader fainted, and drops excess items if over capacity."""
        if member in self.party:
            if member.current_hp <= 0 and self.attempt_revive_member(member):
                return
            if member.current_hp <= 0:
                self.record_team_member_defeat(member)
            else:
                self.record_team_member_departure(member)
            is_leader = (member == self.player_pokemon or getattr(member, "is_leader", False))
            member.is_leader = False
            self.party.remove(member)

            if is_leader:
                if len(self.party) > 0:
                    new_leader = self.party[0]
                    new_leader.is_leader = True
                    self.player_pokemon = new_leader
                    for m in new_leader.moves:
                        m["enabled"] = True
                    if hasattr(new_leader, "x") and hasattr(new_leader, "y"):
                        self.player_x = new_leader.x
                        self.player_y = new_leader.y
                    self.log_message(f"{new_leader.name} took over as team leader!", important=True)
                else:
                    #Game over man, game over!
                    self.log_message("The team was wiped out...", important=True)
                    self.game_ended = True
                    self.game_won = False
                    self.is_running = False

            self.check_over_capacity_inventory_drop(member)

    def add_item_to_inventory(self, item: dict) -> bool:
        """Attempts to add an item (or stack) to the inventory.
        Stackable items merge into existing stackable items up to 40 per stack.
        Returns True if item (or any portion) was added, False if inventory is full.
        """
        if item.get("type") == "Money" or item.get("name") == "Poké":
            amount = item.get("amount", 0)
            self.money += amount
            return True

        added = False
        if item.get("stackable", False):
            amount = item.get("count", 1)
            original_amount = amount
            
            #1. Merge into existing non-full stacks
            for inv_item in self.inventory:
                if inv_item["name"] == item["name"] and inv_item.get("stackable", False):
                    curr = inv_item.get("count", 1)
                    if curr < 40:
                        space = 40 - curr
                        to_add = min(amount, space)
                        inv_item["count"] = curr + to_add
                        amount -= to_add
                        if amount == 0:
                            break
                            
            #2. If leftover amount, put in new inventory slot if room available
            if amount > 0 and len(self.inventory) < self.max_inventory_capacity:
                new_slot = dict(item)
                new_slot["count"] = amount
                self.inventory.append(new_slot)
                amount = 0

            #Update item count and determine if any was added
            if amount < original_amount:
                item["count"] = amount
                added = True
        else:
            if len(self.inventory) < self.max_inventory_capacity:
                self.inventory.append(item)
                added = True

        if added:
            for member in getattr(self, "party", []):
                member.check_evolution_notifications(game=self)
        return added

    def check_auto_pickup(self, x: int, y: int):
        """Checks if there is an item at (x, y) and automatically picks it up if inventory space is available. Items that have been dropped are not automatically picked up."""
        if (x, y) not in self.items_on_floor:
            return
            
        item = self.items_on_floor[(x, y)]
        if item.get("type") == "Money" or item.get("name") == "Poké":
            amount = item.get("amount", 0)
            self.money += amount
            del self.items_on_floor[(x, y)]
            self.log_message(f"Picked up {amount} \033[30;43mP\033[0m.")
            return

        item_disp = items.get_item_display_name(item)
        
        success = self.add_item_to_inventory(item)
        if success:
            if item.get("stackable", False) and item.get("count", 0) > 0:
                self.log_message(f"Picked up some of the {item['name']}s.")
            else:
                del self.items_on_floor[(x, y)]
                self.log_message(f"Picked up the {item_disp}.")
        else:
            self.log_message(f"Passed over the {item_disp}.")

    def manual_pickup(self):
        """Attempts to pick up an item below the player manually."""
        pos = (self.player_x, self.player_y)
        if pos not in self.items_on_floor:
            self.log_message("There is nothing to pick up here.")
            return
            
        item = self.items_on_floor[pos]
        self.start_player_action()
        if item.get("type") == "Money" or item.get("name") == "Poké":
            amount = item.get("amount", 0)
            self.money += amount
            del self.items_on_floor[pos]
            self.log_message(f"Picked up {amount} \033[30;43mP\033[0m.")
            self.on_turn_completed()
            return

        item_disp = items.get_item_display_name(item)
        
        success = self.add_item_to_inventory(item)
        if success:
            if item.get("stackable", False) and item.get("count", 0) > 0:
                self.log_message(f"Picked up some of the {item['name']}s.")
            else:
                del self.items_on_floor[pos]
                self.log_message(f"Picked up the {item_disp}.")
            self.on_turn_completed()
        else:
            self.log_message(f"The Toolbox is too full to pick up the {item_disp}!")

    def place_item_on_floor(self, x: int, y: int, item: dict):
        """Places an item on the ground at (x, y). Merges matching stackable items up to 40 max stack."""
        from dungeon import FLOOR_CHAR
        if (x, y) != getattr(self, "stairs_position", None):
            if (x, y) not in self.items_on_floor:
                self.items_on_floor[(x, y)] = item
                return
            else:
                existing = self.items_on_floor[(x, y)]
                if existing["name"] == item["name"] and existing.get("stackable", False) and item.get("stackable", False):
                    curr = existing.get("count", 1)
                    if curr < 40:
                        space = 40 - curr
                        to_add = min(item.get("count", 1), space)
                        existing["count"] = curr + to_add
                        rem = item.get("count", 1) - to_add
                        if rem <= 0:
                            return
                        item = dict(item)
                        item["count"] = rem

        for r in range(1, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                        if self.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) != getattr(self, "stairs_position", None):
                            if (nx, ny) not in self.items_on_floor:
                                self.items_on_floor[(nx, ny)] = item
                                return
                            else:
                                existing = self.items_on_floor[(nx, ny)]
                                if existing["name"] == item["name"] and existing.get("stackable", False) and item.get("stackable", False):
                                    curr = existing.get("count", 1)
                                    if curr < 40:
                                        space = 40 - curr
                                        to_add = min(item.get("count", 1), space)
                                        existing["count"] = curr + to_add
                                        rem = item.get("count", 1) - to_add
                                        if rem <= 0:
                                            return
                                        item = dict(item)
                                        item["count"] = rem

        self.items_on_floor[(x, y)] = item

    def spawn_random_item_at(self, x: int, y: int) -> dict:
        """Spawns a random item on floor at (x, y) using standard weighted rarity sampling."""
        #Special handling for money (Poké), considered to be a Common-rarity item
        item_keys = list(items.ITEMS_DB.keys()) + ["Poké"]
        item_weights = [items.RARITY_WEIGHTS.get(items.ITEMS_DB[k].get("rarity", "Common"), 50) if k != "Poké" else 50 for k in item_keys]
        item_name = random.choices(item_keys, weights=item_weights, k=1)[0]

        if item_name == "Poké":
            min_amt = 2
            max_amt = 25 + (4 * getattr(self, "floor_number", 1))
            item_data = {
                "name": "Poké",
                "type": "Money",
                "amount": random.randint(min_amt, max_amt),
                "symbol": "P",
                "appearance": "P",
                "color": "\033[30;43m",
                "description": "The currency of the Pokémon world. Spend it wisely!",
                "rarity": "Common"
            }
        else:
            item_data = dict(items.ITEMS_DB[item_name])
            if item_data.get("stackable", False):
                item_data["count"] = random.randint(3, 6)

        self.place_item_on_floor(x, y, item_data)
        return item_data

    def execute_throw_pokemon(self, poke: Pokemon, dx: int, dy: int, max_dist: int = 20, wall_damage: int = 10, poke_damage: int = 10):
        """Throws a Pokémon in direction (dx, dy) up to max_dist tiles"""
        curr_x, curr_y = get_pokemon_position(self, poke)
        final_x, final_y = curr_x, curr_y
        hit_wall = False
        hit_poke = None

        for step in range(1, max_dist + 1):
            nx = curr_x + step * dx
            ny = curr_y + step * dy

            if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height) or self.floor.grid[ny][nx] == WALL_CHAR:
                hit_wall = True
                break

            obstacle = None
            for p in self.party + self.spawned_pokemon:
                if p is not poke and int(getattr(p, "current_hp", 0)) > 0:
                    px, py = get_pokemon_position(self, p)
                    if px == nx and py == ny:
                        obstacle = p
                        break

            if obstacle:
                hit_poke = obstacle
                break
            else:
                final_x, final_y = nx, ny

        self.set_poke_pos(poke, final_x, final_y)

        if hit_wall:
            self.apply_direct_damage(poke, wall_damage)
            self.log_message(f"{poke.name} slammed into a wall!")
        elif hit_poke:
            self.apply_direct_damage(poke, poke_damage)
            self.apply_direct_damage(hit_poke, poke_damage)
            self.log_message(f"{poke.name} collided with {hit_poke.name}!")

    def handle_orb_direction_input(self, action):
        """Processes direction input when using directional Orbs."""
        dx, dy = 0, 0
        if action == game_input.MOVE_UP:
            dy = -1
        elif action == game_input.MOVE_DOWN:
            dy = 1
        elif action == game_input.MOVE_LEFT:
            dx = -1
        elif action == game_input.MOVE_RIGHT:
            dx = 1
        elif action == game_input.MOVE_UP_LEFT:
            dx, dy = -1, -1
        elif action == game_input.MOVE_UP_RIGHT:
            dx, dy = 1, -1
        elif action == game_input.MOVE_DOWN_LEFT:
            dx, dy = -1, 1
        elif action == game_input.MOVE_DOWN_RIGHT:
            dx, dy = 1, 1
        elif action == game_input.QUIT:
            self.log_message("Canceled.")
            self.waiting_for_orb_direction = None
            self.render()
            return
        else:
            return

        if dx != 0 or dy != 0:
            target_idx = self.waiting_for_orb_direction
            if target_idx is None or target_idx < 0 or target_idx >= len(self.inventory):
                self.waiting_for_orb_direction = None
                return
            inv_item = self.inventory[target_idx]
            orb_name = inv_item.get("name")
            px, py = self.player_x, self.player_y

            if orb_name == "Beat Up Orb":
                target_poke = None
                for step in range(1, 11):
                    tx = px + step * dx
                    ty = py + step * dy
                    if not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height):
                        break
                    if self.floor.grid[ty][tx] == WALL_CHAR:
                        break
                    for p in self.party + self.spawned_pokemon:
                        if p is not self.player_pokemon and int(getattr(p, "current_hp", 0)) > 0:
                            ex, ey = get_pokemon_position(self, p)
                            if ex == tx and ey == ty:
                                target_poke = p
                                break
                    if target_poke:
                        break

                if target_poke:
                    item_to_use = self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the Beat Up Orb!")

                    tx, ty = get_pokemon_position(self, target_poke)
                    team_members = [p for p in self.party if int(getattr(p, "current_hp", 0)) > 0]

                    placed = {(tx, ty)}
                    for member in team_members:
                        found_spot = None
                        for r in range(1, 15):
                            cand_tiles = []
                            for c_dy in range(-r, r + 1):
                                for c_dx in range(-r, r + 1):
                                    if max(abs(c_dx), abs(c_dy)) == r:
                                        nx, ny = tx + c_dx, ty + c_dy
                                        if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                                            if self.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) not in placed:
                                                cand_tiles.append((nx, ny))
                                                self.log_message(f"{member.name} warped!")
                            if cand_tiles:
                                found_spot = cand_tiles[0]
                                break
                        if found_spot:
                            placed.add(found_spot)
                            self.set_poke_pos(member, found_spot[0], found_spot[1])

                    self.on_turn_completed()
                else:
                    self.log_message("There's no Pokémon in that direction!")
                    self.waiting_for_orb_direction = None

            if orb_name == "Freeze Orb":
                target_poke = None
                for step in range(1, 11):
                    tx = px + step * dx
                    ty = py + step * dy
                    if not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height):
                        break
                    if self.floor.grid[ty][tx] == WALL_CHAR:
                        break
                    for p in self.party + self.spawned_pokemon:
                        if p is not self.player_pokemon and int(getattr(p, "current_hp", 0)) > 0:
                            ex, ey = get_pokemon_position(self, p)
                            if ex == tx and ey == ty:
                                target_poke = p
                                break
                    if target_poke:
                        break
                if target_poke:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the Freeze Orb!")
                    target_poke.apply_status("Frozen", self)
                    self.on_turn_completed()
                else:
                    self.log_message("There's no Pokémon in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name == "One-Shot Orb":
                adj_x = px + dx
                adj_y = py + dy
                target_enemy = None
                for enemy in self.spawned_pokemon:
                    if int(getattr(enemy, "current_hp", 0)) > 0:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == adj_x and ey == adj_y:
                            target_enemy = enemy
                            break
                if target_enemy:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the One-Shot Orb!")
                    target_enemy.cannot_be_revived = True
                    self.apply_direct_damage(target_enemy, int(target_enemy.current_hp), attacker=self.player_pokemon)
                    self.on_turn_completed()
                else:
                    self.log_message("There's no enemy in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name == "Pounce Orb":
                self.inventory.pop(target_idx)
                self.waiting_for_orb_direction = None
                self.log_message(f"{self.player_pokemon.name} used the Pounce Orb!")
                curr_x, curr_y = px, py
                while True:
                    nx, ny = curr_x + dx, curr_y + dy
                    if not (0 <= nx < self.floor.width and 0 <= ny < self.floor.height):
                        break
                    if self.floor.grid[ny][nx] == WALL_CHAR:
                        break
                    if self.get_poke_at(nx, ny) is not None:
                        break
                    curr_x, curr_y = nx, ny
                    self.set_poke_pos(self.player_pokemon, curr_x, curr_y)
                self.on_turn_completed()

            elif orb_name == "Shocker Orb":
                adj_x = px + dx
                adj_y = py + dy
                target_enemy = None
                for enemy in self.spawned_pokemon:
                    if int(getattr(enemy, "current_hp", 0)) > 0:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == adj_x and ey == adj_y:
                            target_enemy = enemy
                            break
                if target_enemy:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the Shocker Orb!")
                    import random
                    target_enemy.apply_status("Cowering", self, duration=random.randint(4, 6))
                    self.on_turn_completed()
                else:
                    self.log_message("There's no enemy in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name == "Silence Orb":
                adj_x = px + dx
                adj_y = py + dy
                target_enemy = None
                for enemy in self.spawned_pokemon:
                    if int(getattr(enemy, "current_hp", 0)) > 0:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == adj_x and ey == adj_y:
                            target_enemy = enemy
                            break
                if target_enemy:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the Silence Orb!")
                    import random
                    target_enemy.apply_status("Silenced", self, duration=random.randint(5, 8))
                    self.on_turn_completed()
                else:
                    self.log_message("There's no enemy in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name == "Stayaway Orb":
                target_poke = None
                for step in range(1, 11):
                    tx = px + step * dx
                    ty = py + step * dy
                    if not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height):
                        break
                    if self.floor.grid[ty][tx] == WALL_CHAR:
                        break
                    for p in self.spawned_pokemon:
                        if int(getattr(p, "current_hp", 0)) > 0:
                            ex, ey = get_pokemon_position(self, p)
                            if ex == tx and ey == ty:
                                target_poke = p
                                break
                    if target_poke:
                        break
                if target_poke:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the Stayaway Orb!")
                    target_poke.apply_status("Petrified", self)

                    st_x, st_y = getattr(self, "stairs_position", (px, py))
                    near_tiles = []
                    for r in range(1, 4):
                        for c_dy in range(-r, r + 1):
                            for c_dx in range(-r, r + 1):
                                if max(abs(c_dx), abs(c_dy)) == r:
                                    nx, ny = st_x + c_dx, st_y + c_dy
                                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                                        if self.floor.grid[ny][nx] == FLOOR_CHAR and (nx, ny) != (st_x, st_y) and self.get_poke_at(nx, ny) is None:
                                            near_tiles.append((nx, ny))
                    if near_tiles:
                        warp_x, warp_y = near_tiles[0]
                        self.set_poke_pos(target_poke, warp_x, warp_y)
                    else:
                        self.ensure_valid_position(target_poke)
                    self.log_message(f"{target_poke.name} warped!")
                    self.on_turn_completed()
                else:
                    self.log_message("There's no enemy in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name == "Switcher Orb":
                target_poke = None
                for step in range(1, 11):
                    tx = px + step * dx
                    ty = py + step * dy
                    if not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height):
                        break
                    if self.floor.grid[ty][tx] == WALL_CHAR:
                        break
                    for p in self.party + self.spawned_pokemon:
                        if p is not self.player_pokemon and int(getattr(p, "current_hp", 0)) > 0:
                            ex, ey = get_pokemon_position(self, p)
                            if ex == tx and ey == ty:
                                target_poke = p
                                break
                    if target_poke:
                        break
                if target_poke:
                    self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    tx, ty = get_pokemon_position(self, target_poke)
                    self.set_poke_pos(self.player_pokemon, tx, ty)
                    self.set_poke_pos(target_poke, px, py)
                    self.log_message(f"{self.player_pokemon.name} switched places with {target_poke.name}!")
                    self.on_turn_completed()
                else:
                    self.log_message("There's no Pokémon in that direction!")
                    self.waiting_for_orb_direction = None

            elif orb_name in ("Blowback Orb", "Decoy Orb", "Hurl Orb", "Itemizer Orb"):
                adj_x = px + dx
                adj_y = py + dy
                target_enemy = None
                for enemy in self.spawned_pokemon:
                    if int(getattr(enemy, "current_hp", 0)) > 0:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == adj_x and ey == adj_y:
                            target_enemy = enemy
                            break

                if target_enemy:
                    item_to_use = self.inventory.pop(target_idx)
                    self.waiting_for_orb_direction = None
                    self.log_message(f"{self.player_pokemon.name} used the {orb_name}!")

                    if orb_name == "Blowback Orb":
                        self.execute_throw_pokemon(target_enemy, dx, dy, max_dist=20, wall_damage=10, poke_damage=10)

                    elif orb_name == "Decoy Orb":
                        target_enemy.apply_status("Decoy", self)

                    elif orb_name == "Hurl Orb":
                        other_enemies = [e for e in self.spawned_pokemon if e is not target_enemy and int(getattr(e, "current_hp", 0)) > 0]
                        if other_enemies:
                            ex, ey = get_pokemon_position(self, target_enemy)
                            other_enemies.sort(key=lambda o: max(abs(get_pokemon_position(self, o)[0] - ex), abs(get_pokemon_position(self, o)[1] - ey)))
                            closest = other_enemies[0]
                            cx, cy = get_pokemon_position(self, closest)
                            hdx = 1 if cx > ex else (-1 if cx < ex else 0)
                            hdy = 1 if cy > ey else (-1 if cy < ey else 0)
                        else:
                            dirs = [(d1, d2) for d1 in [-1, 0, 1] for d2 in [-1, 0, 1] if not (d1 == 0 and d2 == 0)]
                            hdx, hdy = random.choice(dirs)

                        self.execute_throw_pokemon(target_enemy, hdx, hdy, max_dist=20, wall_damage=15, poke_damage=15)

                    elif orb_name == "Itemizer Orb":
                        ex, ey = get_pokemon_position(self, target_enemy)
                        target_enemy.cannot_be_revived = True
                        target_enemy.current_hp = 0
                        if target_enemy in self.spawned_pokemon:
                            self.spawned_pokemon.remove(target_enemy)
                        self.spawn_random_item_at(ex, ey)
                        self.log_message(f"{target_enemy.name} was turned into an item!")

                    self.on_turn_completed()
                else:
                    self.log_message("There's no enemy in that direction!")
                    self.waiting_for_orb_direction = None

            if self.message_log.has_pending():
                self.process_messages()
            else:
                self.render()

    def apply_direct_damage(self, target, damage: int, attacker=None, damage_source: str | None = None):
        """Applies direct damage to a Pokémon, triggering damage flashes, logs, and checking defeat"""
        if damage_source:
            target.last_damage_source = damage_source
        elif attacker:
            target.last_damage_source = f"{attacker.name}"

        if getattr(target, "napping", False):
            target.napping = False
            target.just_woke_up = True

        tx, ty = get_pokemon_position(self, target)
        currently_visible = self._compute_currently_visible()
        target_visible = (tx, ty) in currently_visible

        suppressed_here = False
        if attacker and attacker in self.party and not target_visible and not getattr(self, "suppress_target_logs", False):
            self.log_message("You hit something in the distance!")
            suppressed_here = True
            self.suppress_target_logs = True

        try:
            actual_dmg = int(min(target.current_hp, damage))
            target.current_hp = float(int(target.current_hp) - actual_dmg)

            self.flash_damages[(tx, ty)] = (damage, 1.0)
            self.trigger_damage_flash()

            if int(target.current_hp) <= 0:
                if target in self.party and self.attempt_revive_member(target):
                    return
                self.log_pokemon_defeat(target)
                if attacker:
                    attacker.defeat_pokemon(target, game=self)
                else:
                    self.player_pokemon.defeat_pokemon(target, game=self)

                if target in self.spawned_pokemon:
                    self.spawned_pokemon.remove(target)
                elif target in self.party:
                    self.remove_party_member(target)
        finally:
            if suppressed_here:
                self.suppress_target_logs = False

    def handle_inventory_input(self, action):
        """Processes key inputs inside the inventory overlay screen"""
        state = self.inventory_state
        if state is None:
            return
            
        if action == game_input.QUIT:
            if state["context_menu"] is not None:
                state["context_menu"] = None
                state["context_index"] = 0
                state["mode"] = "options"
            else:
                self.inventory_state = None
            self.render()
            return
            
        if action == game_input.MOVE_UP:
            if state["context_menu"] is not None:
                menu_len = len(state["context_menu"])
                if menu_len > 0:
                    state["context_index"] = (state["context_index"] - 1) % menu_len
            else:
                item_len = len(self.inventory)
                if item_len > 0:
                    state["selected_index"] = (state["selected_index"] - 1) % item_len
            self.render()
            return
            
        if action == game_input.MOVE_DOWN:
            if state["context_menu"] is not None:
                menu_len = len(state["context_menu"])
                if menu_len > 0:
                    state["context_index"] = (state["context_index"] + 1) % menu_len
            else:
                item_len = len(self.inventory)
                if item_len > 0:
                    state["selected_index"] = (state["selected_index"] + 1) % item_len
            self.render()
            return
            
        if action == game_input.CONFIRM:
            if not self.inventory:
                return
                
            selected_item = self.inventory[state["selected_index"]]
            
            if state["context_menu"] is None:
                options = []
                if selected_item.get("edible", False):
                    options.append("Eat")
                elif selected_item.get("usable", False) or selected_item.get("evolution_item", False):
                    options.append("Use")
                options.append("Throw")
                pos = (self.player_x, self.player_y)
                if pos in self.items_on_floor:
                    options.append("Swap")
                else:
                    options.append("Drop")
                options.append("Trash")
                
                state["context_menu"] = options
                state["context_index"] = 0
                state["mode"] = "options"
                self.render()
            else:
                if state["mode"] == "options":
                    option = state["context_menu"][state["context_index"]]
                    if option in ("Use", "Eat", "Use/Eat"):
                        if self.player_pokemon.status_effects.get("Puppet", 0) > 0:
                            self.log_message(f"{self.player_pokemon.name} can't use items while a puppet!")
                            self.inventory_state = None
                            self.render()
                            return

                        if self.player_pokemon.status_effects.get("Terrified", 0) > 0:
                            self.log_message(f"{self.player_pokemon.name} can't use items while terrified!")
                            self.inventory_state = None
                            self.render()
                            return

                        if self.player_pokemon.status_effects.get("Taunted"):
                            self.log_message(f"{self.player_pokemon.name} can't use items while taunted!")
                            self.inventory_state = None
                            self.render()
                            return

                        is_usable_item = selected_item.get("edible", False) or selected_item.get("usable", False) or selected_item.get("evolution_item", False)
                        is_orb = selected_item.get("name", "").endswith("Orb") or selected_item.get("is_orb", False)
                        if is_usable_item and len(self.party) > 1 and not is_orb:
                            state["context_menu"] = [m.name for m in self.party]
                            state["context_index"] = 0
                            state["mode"] = "party_select"
                            self.render()
                        else:
                            if not is_usable_item:
                                self.log_message("This message should never appear. If it does, please send C4 a bug report :)")
                                self.inventory_state = None
                                self.render()
                                return
                                
                            target = self.player_pokemon
                            if selected_item.get("edible", False) and getattr(target, "current_belly", 0) > getattr(target, "max_belly", 100):
                                self.log_message(f"{target.name}'s can't eat anymore!")
                                self.inventory_state = None
                                self.render()
                                return

                            if items.is_evolution_item(selected_item) and not items.can_use_evolution_item(selected_item, target):
                                self.log_message(f"This item can't be used on {target.name}.")
                                self.inventory_state = None
                                self.render()
                                return

                            if is_orb and selected_item.get("name") in ("Beat Up Orb", "Blowback Orb", "Decoy Orb", "Hurl Orb", "Itemizer Orb", "Freeze Orb", "One-Shot Orb", "Pounce Orb", "Shocker Orb", "Silence Orb", "Stayaway Orb", "Switcher Orb"):
                                item_idx = state["selected_index"]
                                self.inventory_state = None
                                self.waiting_for_orb_direction = item_idx
                                self.log_message(f"Which direction to use the {selected_item['name']}? ([Esc] to cancel)")
                                if self.message_log.has_pending():
                                    self.process_messages()
                                else:
                                    self.render()
                                return

                            self.start_player_action()
                            item_to_use = self.inventory.pop(state["selected_index"])
                            self.inventory_state = None
                            
                            if item_to_use.get("edible", False):
                                self.log_message(f"{target.name} ate the {item_to_use['name']}.")
                            else:
                                self.log_message(f"{target.name} used the {item_to_use['name']}.")
                            
                            items.apply_item_effect(item_to_use, target, self)
                            for member in self.party:
                                member.check_evolution_notifications(game=self)
                            self.on_turn_completed()
                            if self.message_log.has_pending():
                                self.process_messages()
                            else:
                                self.render()
                                
                    elif option == "Throw":
                        if self.player_pokemon.status_effects.get("Puppet", 0) > 0:
                            self.log_message(f"{self.player_pokemon.name} can't use items while a puppet!")
                            self.inventory_state = None
                            self.render()
                            return
                        if self.player_pokemon.status_effects.get("Terrified", 0) > 0:
                            self.log_message(f"{self.player_pokemon.name} can't use items while terrified!")
                            self.inventory_state = None
                            self.render()
                            return
                        item_idx = state["selected_index"]
                        self.inventory_state = None
                        self.waiting_for_throw_direction = item_idx
                        self.log_message(f"Which direction to throw the {items.get_item_display_name(selected_item)}? ([Esc] to cancel)")
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                        
                    elif option == "Drop":
                        px, py = self.player_x, self.player_y
                        found_tile = None
                        from dungeon import FLOOR_CHAR
                        
                        #First check the player's current tile
                        if (px, py) not in self.items_on_floor and (px, py) != getattr(self, "stairs_position", None):
                            found_tile = (px, py)
                        else:
                            #Search the 8 adjacent tiles
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    if dx == 0 and dy == 0:
                                        continue
                                    nx, ny = px + dx, py + dy
                                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                                        if self.floor.grid[ny][nx] == FLOOR_CHAR:
                                            if (nx, ny) not in self.items_on_floor and (nx, ny) != getattr(self, "stairs_position", None):
                                                found_tile = (nx, ny)
                                                break
                                if found_tile:
                                    break
                                    
                        if found_tile is None:
                            self.log_message("There's no space to drop the item!")
                            state["context_menu"] = None
                            state["context_index"] = 0
                            self.render()
                        else:
                            self.start_player_action()
                            item_to_drop = self.inventory.pop(state["selected_index"])
                            item_to_drop["dropped_by_player"] = True
                            self.place_item_on_floor(found_tile[0], found_tile[1], item_to_drop)
                            self.inventory_state = None
                            self.log_message(f"{self.player_pokemon.name} dropped the {items.get_item_display_name(item_to_drop)}.")
                            self.on_turn_completed()
                            if self.message_log.has_pending():
                                self.process_messages()
                            else:
                                self.render()
                                
                    elif option == "Swap":
                        pos = (self.player_x, self.player_y)
                        if pos not in self.items_on_floor:
                            self.log_message("There's nothing on the ground to swap with!")
                            state["context_menu"] = None
                            state["context_index"] = 0
                            self.render()
                        else:
                            self.start_player_action()
                            ground_item = self.items_on_floor[pos]
                            selected_item_pop = self.inventory[state["selected_index"]]
                            selected_item_pop["dropped_by_player"] = True
                            ground_item.pop("dropped_by_player", None)
                            
                            self.inventory[state["selected_index"]] = ground_item
                            self.items_on_floor[pos] = selected_item_pop
                            self.inventory_state = None
                            
                            self.log_message(f"{self.player_pokemon.name} swapped the {items.get_item_display_name(selected_item_pop)} with the {items.get_item_display_name(ground_item)}.")
                            self.on_turn_completed()
                            if self.message_log.has_pending():
                                self.process_messages()
                            else:
                                self.render()
                                
                    elif option == "Trash":
                        self.start_player_action()
                        item_trashed = self.inventory.pop(state["selected_index"])
                        self.inventory_state = None
                        self.log_message(f"{self.player_pokemon.name} trashed the {items.get_item_display_name(item_trashed)}.")
                        self.on_turn_completed()
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                            
                elif state["mode"] == "party_select":
                    target_member = self.party[state["context_index"]]
                    selected_item = self.inventory[state["selected_index"]]
                    if selected_item.get("edible", False) and getattr(target_member, "current_belly", 0) > getattr(target_member, "max_belly", 100):
                        self.log_message(f"{target_member.name}'s belly is full!")
                        self.inventory_state = None
                        self.render()
                        return

                    if items.is_evolution_item(selected_item) and not items.can_use_evolution_item(selected_item, target_member):
                        self.log_message(f"This item can't be used on {target_member.name}.")
                        self.inventory_state = None
                        self.render()
                        return

                    self.start_player_action()
                    item_to_use = self.inventory.pop(state["selected_index"])
                    self.inventory_state = None
                    
                    if item_to_use.get("edible", False):
                        self.log_message(f"{target_member.name} ate the {items.get_item_display_name(item_to_use)}.")
                    else:
                        self.log_message(f"{target_member.name} used the {items.get_item_display_name(item_to_use)}.")
                    items.apply_item_effect(item_to_use, target_member, self)
                    for member in self.party:
                        member.check_evolution_notifications(game=self)
                    self.on_turn_completed()
                    if self.message_log.has_pending():
                        self.process_messages()
                    else:
                        self.render()

    def handle_message_history_input(self, action: str):
        """Processes key inputs inside the message history overlay screen"""
        state = self.message_history_state
        if state is None:
            return

        lines = self.message_log.get_history_lines(max_width=72)
        max_visible = 42
        max_scroll = max(0, len(lines) - max_visible)

        if action in (game_input.MOVE_UP, "k", "8"):
            state["scroll"] = max(0, state["scroll"] - 1)
            self.render()
        elif action in (game_input.MOVE_DOWN, "j", "2"):
            state["scroll"] = min(max_scroll, state["scroll"] + 1)
            self.render()
        elif action in (game_input.QUIT, game_input.MESSAGE_LOG, "q", "Q", "\x1b"):
            self.message_history_state = None
            self.render()

    def handle_throw_input(self, action):
        """Processes direction input when throwing an item"""
        dx, dy = 0, 0
        if action == game_input.MOVE_UP:
            dy = -1
        elif action == game_input.MOVE_DOWN:
            dy = 1
        elif action == game_input.MOVE_LEFT:
            dx = -1
        elif action == game_input.MOVE_RIGHT:
            dx = 1
        elif action == game_input.MOVE_UP_LEFT:
            dx, dy = -1, -1
        elif action == game_input.MOVE_UP_RIGHT:
            dx, dy = 1, -1
        elif action == game_input.MOVE_DOWN_LEFT:
            dx, dy = -1, 1
        elif action == game_input.MOVE_DOWN_RIGHT:
            dx, dy = 1, 1
        elif action == game_input.QUIT:
            self.log_message("Throw canceled.")
            self.waiting_for_throw_direction = None
            self.render()
            return
        else:
            return
            
        if dx != 0 or dy != 0:
            self.start_player_action()
            target_idx = self.waiting_for_throw_direction
            inv_item = self.inventory[target_idx]
            if inv_item.get("stackable", False) and inv_item.get("count", 1) > 1:
                thrown_item = dict(inv_item)
                thrown_item["count"] = 1
                inv_item["count"] -= 1
            else:
                thrown_item = self.inventory.pop(target_idx)
            thrown_item.pop("dropped_by_player", None)
            self.waiting_for_throw_direction = None

            flying_char = self.get_flying_item_char(thrown_item, dx, dy)
            color_raw = thrown_item.get("color", "green")
            if color_raw.startswith("\033["):
                color_code = color_raw
            else:
                color_map = {
                    "green": "\033[92m",
                    "red": "\033[91m",
                    "blue": "\033[94m",
                    "yellow": "\033[93m",
                    "cyan": "\033[96m",
                    "magenta": "\033[95m",
                    "purple": "\033[35m",
                    "brown": "\033[33m",
                    "white": "\033[37m",
                    "gray": "\033[90m",
                }
                color_code = color_map.get(color_raw.lower(), "\033[92m")

            trajectory = []
            target_enemy = None
            #Geo Pebbles & Gravelerocks can target any enemy in 10 tiles. Other thrown weapons can only target a straight line
            if thrown_item.get("name") in ("Geo Pebble", "Gravelerock"):
                from targeting import has_clear_path
                candidates = []
                for enemy in self.spawned_pokemon:
                    if int(enemy.current_hp) > 0:
                        ex, ey = get_pokemon_position(self, enemy)
                        dist = max(abs(ex - self.player_x), abs(ey - self.player_y))
                        if dist <= 10 and has_clear_path(self.floor, self.player_x, self.player_y, ex, ey, cuts_corners=True):
                            dot = (ex - self.player_x) * dx + (ey - self.player_y) * dy
                            candidates.append((dot > 0, -dist, enemy, ex, ey))
                if candidates:
                    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
                    target_enemy = candidates[0][2]

            if target_enemy:
                target_ex, target_ey = get_pokemon_position(self, target_enemy)
                curr_x, curr_y = self.player_x, self.player_y
                step_dx = abs(target_ex - curr_x)
                step_dy = abs(target_ey - curr_y)
                sx = 1 if curr_x < target_ex else -1
                sy = 1 if curr_y < target_ey else -1
                err = step_dx - step_dy
                
                while True:
                    e2 = 2 * err
                    if e2 > -step_dy:
                        err -= step_dy
                        curr_x += sx
                    if e2 < step_dx:
                        err += step_dx
                        curr_y += sy
                    
                    if curr_x == target_ex and curr_y == target_ey:
                        trajectory.append((curr_x, curr_y, target_enemy))
                        break
                    
                    if not (0 <= curr_x < self.floor.width and 0 <= curr_y < self.floor.height) or self.floor.grid[curr_y][curr_x] == WALL_CHAR:
                        trajectory.append((curr_x, curr_y, "wall"))
                        break
                        
                    inter_hit = None
                    for enemy in self.spawned_pokemon:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == curr_x and ey == curr_y:
                            inter_hit = enemy
                            break
                    if inter_hit:
                        trajectory.append((curr_x, curr_y, inter_hit))
                        break
                    else:
                        trajectory.append((curr_x, curr_y, None))
            else:
                is_pierce = bool(self.player_pokemon.status_effects.get("Pierce Throw"))
                for step in range(1, 11):
                    tx = self.player_x + step * dx
                    ty = self.player_y + step * dy

                    if not (0 <= tx < self.floor.width and 0 <= ty < self.floor.height) or self.floor.grid[ty][tx] == WALL_CHAR:
                        trajectory.append((tx, ty, "wall"))
                        break

                    enemy_hit = None
                    for enemy in self.spawned_pokemon:
                        ex, ey = get_pokemon_position(self, enemy)
                        if ex == tx and ey == ty:
                            enemy_hit = enemy
                            break

                    if enemy_hit:
                        trajectory.append((tx, ty, enemy_hit))
                        if not is_pierce:
                            break
                    else:
                        trajectory.append((tx, ty, None))

            import time
            currently_visible = self._compute_currently_visible()
            for anim_x, anim_y, hit_type in trajectory:
                if (anim_x, anim_y) not in currently_visible:
                    break
                self.flying_item_animation = {
                    "x": anim_x,
                    "y": anim_y,
                    "char": flying_char,
                    "color": color_code
                }
                self.render()
                if not getattr(self, "suppress_animation_delay", False):
                    time.sleep(0.03)

            self.flying_item_animation = None

            if trajectory:
                is_pierce = bool(self.player_pokemon.status_effects.get("Pierce Throw"))
                if is_pierce:
                    hit_enemies = [hit_type for _, _, hit_type in trajectory if isinstance(hit_type, Pokemon)]
                    for enemy_hit in hit_enemies:
                        ex, ey = get_pokemon_position(self, enemy_hit)
                        enemy_visible = (ex, ey) in currently_visible
                        if not enemy_visible:
                            self.log_message("You hit something in the distance!")
                            self.suppress_target_logs = True
                            try:
                                items.apply_item_effect(thrown_item, enemy_hit, self, is_thrown=True)
                            finally:
                                self.suppress_target_logs = False
                        else:
                            items.apply_item_effect(thrown_item, enemy_hit, self, is_thrown=True)

                    final_x, final_y, hit_type = trajectory[-1]
                    if hit_type == "wall":
                        fx = final_x - dx
                        fy = final_y - dy
                        self.place_item_on_floor(fx, fy, thrown_item)
                    else:
                        self.place_item_on_floor(final_x, final_y, thrown_item)
                else:
                    final_x, final_y, hit_type = trajectory[-1]
                    is_visible = (final_x, final_y) in currently_visible
                    if hit_type == "wall":
                        fx = final_x - dx
                        fy = final_y - dy
                        self.place_item_on_floor(fx, fy, thrown_item)
                        if (fx, fy) in currently_visible:
                            self.log_message(f"The thrown {thrown_item['name']} fell to the ground.")
                    elif isinstance(hit_type, Pokemon):
                        enemy_hit = hit_type
                        ex, ey = get_pokemon_position(self, enemy_hit)
                        enemy_visible = (ex, ey) in currently_visible

                        if thrown_item.get("apricorn", False):
                            consumed = self.attempt_apricorn_recruitment(thrown_item, enemy_hit)
                            if not consumed:
                                self.place_item_on_floor(final_x, final_y, thrown_item)
                                if (final_x, final_y) in currently_visible:
                                    self.log_message(f"The thrown {thrown_item['name']} fell to the ground.")
                        else:
                            acc_stage = max(-6, min(6, self.player_pokemon.stat_modifiers.get("Accuracy", 0)))
                            acc_mult = (3.0 + acc_stage) / 3.0 if acc_stage >= 0 else 3.0 / (3.0 + abs(acc_stage))

                            ev_stage = max(-6, min(6, enemy_hit.stat_modifiers.get("Evasion", 0)))
                            ev_mult = (3.0 + ev_stage) / 3.0 if ev_stage >= 0 else 3.0 / (3.0 + abs(ev_stage))

                            hit_chance = 90.0 * (acc_mult / ev_mult)

                            import random
                            if random.randint(1, 100) > hit_chance:
                                if enemy_visible:
                                    self.log_message(f"{enemy_hit.name} dodged the {thrown_item['name']}!")
                                self.place_item_on_floor(final_x, final_y, thrown_item)
                                if (final_x, final_y) in currently_visible:
                                    self.log_message(f"The thrown {thrown_item['name']} fell to the ground.")
                            else:
                                if not enemy_visible:
                                    self.log_message("You hit something in the distance!")
                                    self.suppress_target_logs = True
                                    try:
                                        items.apply_item_effect(thrown_item, enemy_hit, self, is_thrown=True)
                                    finally:
                                        self.suppress_target_logs = False
                                else:
                                    items.apply_item_effect(thrown_item, enemy_hit, self, is_thrown=True)
                    else:
                        self.place_item_on_floor(final_x, final_y, thrown_item)
                        if is_visible:
                            self.log_message(f"The thrown {thrown_item['name']} fell to the ground.")

            self.on_turn_completed()
            if self.message_log.has_pending():
                self.process_messages()
            else:
                self.render()

    def get_flying_item_char(self, item: dict, dx: int, dy: int) -> str:
        """Returns the directional or default character for a flying thrown item."""
        item_name = item.get("name", "")
        is_directional = (
            item.get("directional_graphic", False)
            or item.get("appearance") == "/"
            or any(k in item_name for k in ["Stick", "Thorn", "Spike", "Fang", "Twig", "Needle", "Arrow", "Dart"])
        )
        if is_directional:
            if dx == 0 and dy != 0:
                return "|"
            elif dx != 0 and dy == 0:
                return "-"
            elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                return "\\"
            elif (dx > 0 and dy < 0) or (dx < 0 and dy > 0):
                return "/"
        return item.get("appearance") or item.get("symbol") or item.get("char") or "?"

    def attempt_apricorn_recruitment(self, apricorn_item: dict, target: Pokemon) -> bool:
        """Attempts recruitment of an enemy using a thrown Apricorn.
        Returns True if target was adjacent to leader, consuming the Apricorn, or False otherwise.
        """
        tx, ty = target.x, target.y
        px, py = self.player_pokemon.x, self.player_pokemon.y
        is_adjacent = max(abs(tx - px), abs(ty - py)) == 1

        if not is_adjacent or target in self.party:
            self.log_message(f"{target.name} dodged the thrown {apricorn_item['name']}!")
            return False

        #Recruitment chance calculation
        import random
        from type_chart import get_type_effectiveness

        max_hp = float(target.stats["HP"])
        curr_hp = float(target.current_hp)
        hp_term = max(0.0, ((3.0 * max_hp) - (2.0 * curr_hp)) / (3.0 * max_hp))

        recruitment_rate = target.species_data.get("recruit_rate", 255)
        rate_term = recruitment_rate / 255.0

        if target.status_effects.get("Sleep", 0) > 0 or target.status_effects.get("Resting", 0) > 0 or target.status_effects.get("Frozen", 0) > 0:
            status_bonus = 1.5
        elif target.status_effects.get("Paralysis", 0) > 0 or target.status_effects.get("Petrified", 0) > 0:
            status_bonus = 1.3
        elif target.status_effects.get("Poison") or target.status_effects.get("Toxic") or target.status_effects.get("Burn"):
            status_bonus = 1.2
        else:
            status_bonus = 1.0

        ap_type = apricorn_item.get("type", "Normal")
        if apricorn_item.get("name") == "Rainbow Apricorn" or ap_type == "Rainbow":
            type_bonus = 4.0
        else:
            target_types = target.types
            if ap_type in target_types:
                type_bonus = 3.0
            else:
                eff = get_type_effectiveness(ap_type, target_types)
                if eff > 1.0:
                    type_bonus = 2.0
                elif eff == 1.0:
                    type_bonus = 1.5
                elif eff > 0.0:
                    type_bonus = 1.0
                else:
                    type_bonus = 0.5

        friendly_bonus = 1.5 if (self.player_pokemon and self.player_pokemon.status_effects.get("Friendly")) else 1.0
        chance = hp_term * rate_term * status_bonus * type_bonus * friendly_bonus
        roll = random.random()

        if chance >= 1.0 or roll < chance:
            self.clear_pokemon_bindings(target)
            target.current_hp = float(target.stats["HP"])
            target.current_pp = target.max_pp
            for m in target.moves:
                m["pp"] = m.get("max_pp", m.get("pp", 20))

            target.status_effects = {s: (False if isinstance(v, bool) else 0) for s, v in target.status_effects.items()}
            target.stat_modifiers = {s: 0 for s in target.stat_modifiers}
            target.last_damage_source = None

            if target in self.spawned_pokemon:
                self.spawned_pokemon.remove(target)

            self.total_recruited_count += 1
            sp_name = getattr(target, "species_name", "") or target.name
            self.register_encountered_species(sp_name, is_recruited=True)
            self.add_to_team_history(target, is_starter=False)

            self.award_recruitment_experience(target)

            if len(self.party) >= 6:
                self.log_message(f"Gotcha! {target.species_name} was recruited!")
                self.replace_recruit_state = {"recruit": target, "selected_index": 0}
            else:
                if target not in self.party:
                    self.party.append(target)
                self.log_message(f"Gotcha! {target.species_name} was recruited!")
                self.nickname_prompt_state = {"pokemon": target, "text": ""}
        else:
            self.log_message(f"{target.name} rejected the {apricorn_item['name']}. Give it another shot!")

        return True

    def award_recruitment_experience(self, recruited_pokemon: Pokemon):
        """Awards experience points to existing team members when a wild Pokémon is successfully recruited; it's the same as when defeating an enemy but with a 50% bonus
        The recruited Pokémon does not gain experience points.
        """
        if not recruited_pokemon or not hasattr(recruitment_pokemon if False else recruited_pokemon, "species_data"):
            return

        exp_yield = recruited_pokemon.species_data.get("exp_yield", 0)
        if exp_yield <= 0:
            return

        import math
        import random

        opponent_level = recruited_pokemon.level
        leader = getattr(self, "player_pokemon", None)
        post_evo_bonus = 1.2 if (leader and hasattr(leader, "can_evolve") and leader.can_evolve(game=self)) else 1.0

        base_exp = math.floor(((3 * exp_yield * opponent_level) / 14) * post_evo_bonus)
        boosted_exp = math.floor(base_exp * 1.5)

        if boosted_exp <= 0:
            return

        #Existing team members (excluding the recruited Pokémon, alive members only)
        existing_members = [p for p in self.party if p is not recruited_pokemon and int(getattr(p, "current_hp", 0)) > 0]
        if not existing_members:
            return

        weights = [1.0 / float(p.level) for p in existing_members]
        total_weight = sum(weights)

        shares: dict = {}
        sum_allocated = 0
        for p, w in zip(existing_members, weights):
            fraction = w / total_weight
            allocated = math.floor(boosted_exp * fraction)
            shares[p] = allocated
            sum_allocated += allocated

        remainder = boosted_exp - sum_allocated
        if remainder > 0:
            min_lvl = min(p.level for p in existing_members)
            lowest_pokes = [p for p in existing_members if p.level == min_lvl]

            leader_in_lowest = [p for p in lowest_pokes if p is leader or getattr(p, "is_leader", False)]
            if leader_in_lowest:
                chosen_recipient = leader_in_lowest[0]
            else:
                chosen_recipient = random.choice(lowest_pokes)

            shares[chosen_recipient] += remainder

        for p, share in shares.items():
            if share > 0:
                p.gain_experience(share, game=self)

    def handle_replace_recruit_input(self, action: str):
        """Handles key input for selecting a team member to replace when party is full (6 members)."""
        state = getattr(self, "replace_recruit_state", None)
        if state is None:
            return

        recruit = state["recruit"]
        sel_idx = state.get("selected_index", 0)

        slot_key_map = {
            "a": 0, "A": 0, "STATUS_1": 0, "1": 0,
            "s": 1, "S": 1, "STATUS_2": 1, "2": 1,
            "d": 2, "D": 2, "STATUS_3": 2, "3": 2,
            "f": 3, "F": 3, "STATUS_4": 3, "4": 3,
            "g": 4, "G": 4, "STATUS_5": 4, "5": 4,
            "h": 5, "H": 5, "STATUS_6": 5, "6": 5,
            "7": 6
        }

        chosen_slot: int | None = None

        if action in ("QUIT", "ESC", "Esc", "esc"):
            chosen_slot = 6
        elif action in slot_key_map:
            chosen_slot = slot_key_map[action]
        elif action == "UP":
            state["selected_index"] = (sel_idx - 1) % 7
            self.render()
            return
        elif action == "DOWN":
            state["selected_index"] = (sel_idx + 1) % 7
            self.render()
            return
        elif action in ("CONFIRM", "ENTER", "Enter", "\n", "\r"):
            chosen_slot = sel_idx

        if chosen_slot is not None:
            if chosen_slot == 6:
                #Reject recruit
                self.log_message(f"{recruit.species_name} went away...")
                #Recruit never joined the party, remove from all_team_members
                recruit_id = getattr(recruit, "id", None)
                self.all_team_members = [
                    entry for entry in self.all_team_members
                    if entry.get("pokemon") is not recruit and (not recruit_id or entry.get("pokemon_id") != recruit_id)
                ]
                self.replace_recruit_state = None
                self.render()
            elif 0 <= chosen_slot < len(self.party):
                replaced_mon = self.party[chosen_slot]
                rx, ry = get_pokemon_position(self, replaced_mon)

                is_replacing_leader = (replaced_mon == self.player_pokemon or getattr(replaced_mon, "is_leader", False) or chosen_slot == 0)
                replaced_mon.is_leader = False

                self.record_team_member_departure(replaced_mon)

                #Swap in party list
                self.party[chosen_slot] = recruit

                if is_replacing_leader:
                    recruit.is_leader = True
                    self.player_pokemon = recruit
                    for m in recruit.moves:
                        m["enabled"] = True
                    self.set_poke_pos(recruit, rx, ry)
                    self.log_message(f"{replaced_mon.name} went away. {recruit.name} is now the leader!")
                else:
                    self.set_poke_pos(recruit, rx, ry)
                    self.log_message(f"{replaced_mon.name} went away...")

                self.replace_recruit_state = None
                self.nickname_prompt_state = {"pokemon": recruit, "text": ""}
                self.render()

    def render_replace_recruit_prompt_screen(self) -> list[str]:
        """Prompts player to replace a team member to replace when recruiting with a full party."""
        state = getattr(self, "replace_recruit_state", None)
        if state is None:
            return []

        recruit = state["recruit"]
        sel_idx = state.get("selected_index", 0)

        width = 64
        top_border = "┌" + "─" * (width - 2) + "┐"
        bot_border = "└" + "─" * (width - 2) + "┘"
        empty_line = "│" + " " * (width - 2) + "│"

        def fmt_line(content: str) -> str:
            padded = content.ljust(width - 4)
            return f"│ {padded} │"

        hotkeys = ["[A]", "[S]", "[D]", "[F]", "[G]", "[H]"]
        rows = [
            top_border,
            fmt_line(f"Congrats! You recruited a {recruit.species_name} (Lv{recruit.level})"),
            fmt_line("The team is full! Choose a Pokémon to replace"),
            fmt_line("or press [Esc] to cancel:"),
        ]

        for idx, mon in enumerate(self.party[:6]):
            hk = hotkeys[idx] if idx < len(hotkeys) else f"[{idx+1}]"
            prefix = " ► " if sel_idx == idx else "   "
            leader_tag = " (Leader)" if (mon == self.player_pokemon or getattr(mon, "is_leader", False)) else ""
            types_str = "/".join(mon.types) if hasattr(mon, "types") else ""
            mon_info = f"{hk} {mon.name} (Lv{mon.level} {mon.species_name} {types_str}){leader_tag}"
            rows.append(fmt_line(f"{prefix}{mon_info}"))

        reject_prefix = " ► " if sel_idx == 6 else "   "
        rows.append(empty_line)
        rows.append(fmt_line("[Esc] Cancel  [Return] Confirm"))
        rows.append(bot_border)

        return self.sanitize_rendered_rows(rows)

    def handle_nickname_input(self, char_in: str):
        """Handles key input for nicknaming a newly recruited Pokémon."""
        state = getattr(self, "nickname_prompt_state", None)
        if state is None:
            return

        poke = state["pokemon"]
        curr_text = state["text"]

        if char_in == "ENTER":
            name_to_set = curr_text.strip()[:12]
            if name_to_set:
                poke.nickname = name_to_set
            else:
                poke.nickname = None
            self.nickname_prompt_state = None
            self.render()
        elif char_in == "ESC":
            poke.nickname = None
            self.nickname_prompt_state = None
            self.render()
        elif char_in == "BACKSPACE":
            if curr_text:
                state["text"] = curr_text[:-1]
                self.render()
        elif char_in and len(curr_text) < 12 and (char_in.isalnum() or char_in in " -_"):
            state["text"] = curr_text + char_in
            self.render()

    def render_nickname_prompt_screen(self) -> list[str]:
        """Renders the nicknaming overlay screen for a newly recruited Pokémon."""
        state = getattr(self, "nickname_prompt_state", None)
        if state is None:
            return []

        poke = state["pokemon"]
        text = state["text"]

        width = 60
        top_border = "┌" + "─" * (width - 2) + "┐"
        bot_border = "└" + "─" * (width - 2) + "┘"
        empty_line = "│" + " " * (width - 2) + "│"

        def fmt_line(content: str) -> str:
            padded = content.ljust(width - 4)
            return f"│ {padded} │"

        rows = [
            top_border,
            fmt_line(f"Congrats! You recruited a {poke.species_name} (Lv{poke.level})"),
            empty_line,
            fmt_line("Give them a nickname?"),
            fmt_line("(Max 12 characters or leave empty to skip)"),
            empty_line,
            fmt_line(f"► {text}_"),
            empty_line,
            fmt_line("[Return] Confirm   [Esc] Skip"),
            bot_border
        ]
        return self.sanitize_rendered_rows(rows)

    def handle_pause_menu_input(self, action: str):
        """Handles key input for the Pause Menu."""
        state = getattr(self, "pause_menu_state", None)
        if state is None:
            return

        sub_screen = state.get("sub_screen")
        confirm_give_up = state.get("confirm_give_up", False)

        if sub_screen == "pokemon_floor":
            if action in (game_input.QUIT, game_input.CONFIRM, "\x1b", "ESC", "Esc", "esc", "z", "Z", "x", "X", "\r", "\n"):
                state["sub_screen"] = None
                self.render()
            return

        if confirm_give_up:
            confirm_index = state.get("confirm_index", 0)
            if action in (game_input.MOVE_LEFT, game_input.MOVE_RIGHT, game_input.MOVE_UP, game_input.MOVE_DOWN, "w", "W", "s", "S", "a", "A", "d", "D", "left", "right", "up", "down"):
                state["confirm_index"] = 1 - confirm_index
                self.render()
                return

            if action in ("y", "Y"):
                self._execute_give_up()
                return

            if action in ("n", "N", game_input.QUIT, "\x1b", "ESC", "Esc", "esc"):
                state["confirm_give_up"] = False
                self.render()
                return

            if action in (game_input.CONFIRM, "\r", "\n", "z", "Z"):
                if confirm_index == 1:
                    self._execute_give_up()
                else:
                    state["confirm_give_up"] = False
                    self.render()
                return

            return

        sel = state.get("selected_index", 0)

        if action in (game_input.MOVE_UP, "w", "W", "up", "UP"):
            state["selected_index"] = (sel - 1) % 4
            self.render()
            return

        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN"):
            state["selected_index"] = (sel + 1) % 4
            self.render()
            return

        if action in ("1", game_input.USE_MOVE_1):
            state["selected_index"] = 0
            self._select_pause_menu_option(0)
            return

        if action in ("2", game_input.USE_MOVE_2):
            state["selected_index"] = 1
            self._select_pause_menu_option(1)
            return

        if action in ("3", game_input.USE_MOVE_3):
            state["selected_index"] = 2
            self._select_pause_menu_option(2)
            return

        if action in ("4", "4"):
            state["selected_index"] = 3
            self._select_pause_menu_option(3)
            return

        if action in (game_input.QUIT, "\x1b", "ESC", "Esc", "esc"):
            self.pause_menu_state = None
            self.render()
            return

        if action in (game_input.CONFIRM, "\r", "\n", "z", "Z"):
            self._select_pause_menu_option(sel)
            return

    def _select_pause_menu_option(self, option_index: int):
        state = getattr(self, "pause_menu_state", None)
        if state is None:
            return

        if option_index == 0:
            self.pause_menu_state = None
            self.render()
        elif option_index == 1:
            state["sub_screen"] = "pokemon_floor"
            self.render()
        elif option_index == 2:
            from save_game import save_game
            try:
                fpath = save_game(self)
                self.pause_menu_state = None
                self.is_running = False
                self.log_message(f"Game saved to {os.path.basename(fpath)}.", important=True)
            except Exception as e:
                self.log_message(f"Failed to save game: {str(e)}", important=True)
                self.render()
        elif option_index == 3:
            state["confirm_give_up"] = True
            state["confirm_index"] = 0
            self.render()

    def _execute_give_up(self):
        self.pause_menu_state = None
        self.game_ended = True
        self.game_won = False
        self.is_running = False
        if hasattr(self, "player_pokemon") and self.player_pokemon:
            self.player_pokemon.last_damage_source = "Give Up"
            if hasattr(self, "record_team_member_defeat"):
                self.record_team_member_defeat(self.player_pokemon, damage_source="Give Up")
        self.log_message(f"The team gave up...", important=True)
        self.render()

    def render_pause_menu_screen(self) -> list[str]:
        """Renders the pause menu overlay (or sub-screen)."""
        state = getattr(self, "pause_menu_state", None)
        if state is None:
            return []

        sub_screen = state.get("sub_screen")
        confirm_give_up = state.get("confirm_give_up", False)

        width = 54
        top_border = "┌" + "─" * (width - 2) + "┐"
        bot_border = "└" + "─" * (width - 2) + "┘"
        empty_line = "│" + " " * (width - 2) + "│"

        def fmt_line(content: str) -> str:
            padded = content.ljust(width - 4)
            return f"│ {padded} │"

        def center_line(content: str) -> str:
            padded = content.center(width - 4)
            return f"│ {padded} │"

        if sub_screen == "pokemon_floor":
            rows = [
                top_border,
                center_line("Pokémon on this Floor"),
                empty_line,
            ]
            spawns = getattr(self, "floor_spawn_list", [])
            if not spawns:
                spawns = getattr(self, "all_species_names", [])[:5]

            for idx, sp_name in enumerate(spawns, 1):
                rows.append(fmt_line(f"{sp_name}"))

            rows.append(empty_line)
            rows.append(center_line("[Esc] Return to Pause Menu"))
            rows.append(bot_border)
            return rows

        if confirm_give_up:
            confirm_index = state.get("confirm_index", 0)
            no_str = "► No ◄" if confirm_index == 0 else "  No  "
            yes_str = "► Yes ◄" if confirm_index == 1 else "  Yes  "
            opts_line = f"        {no_str}            {yes_str}"

            rows = [
                top_border,
                center_line("ARE YOU SURE YOU WANT TO GIVE UP?"),
                empty_line,
                center_line("This will end the game. Your progress will be lost."),
                empty_line,
                fmt_line(opts_line),
                empty_line,
                center_line("[←/→] Choose  [Return] Confirm  [Esc] Cancel"),
                bot_border,
            ]
            return rows

        sel_idx = state.get("selected_index", 0)
        options = [
            "Return to Game",
            "Pokémon on this Floor",
            "Save & Quit",
            "Give Up"
        ]

        rows = [
            top_border,
            center_line("MENU"),
            empty_line,
        ]

        for idx, opt in enumerate(options):
            prefix = " ► " if sel_idx == idx else "   "
            num_label = f"[{idx + 1}] "
            rows.append(fmt_line(f"{prefix}{num_label}{opt}"))

        rows.append(empty_line)
        rows.append(center_line("[↑/↓] Navigate  [Return] Select  [Esc] Close"))
        rows.append(bot_border)
        return self.sanitize_rendered_rows(rows)

    def handle_title_screen_input(self, action: str):
        """Handles key input for the main Title Screen."""
        state = getattr(self, "title_screen_state", None)
        if state is None:
            return

        sel = state.get("selected_index", 0)

        if action in (game_input.MOVE_UP, "w", "W", "up", "UP", "k", "K"): #Up arrow key
            state["selected_index"] = (sel - 1) % 4
            self.render()
            return

        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN", "j", "J"): #Down arrow key
            state["selected_index"] = (sel + 1) % 4
            self.render()
            return

        if action in ("1", game_input.USE_MOVE_1): #Z
            state["selected_index"] = 0
            self._select_title_screen_option(0)
            return

        if action in ("2", game_input.USE_MOVE_2): #X
            state["selected_index"] = 1
            self._select_title_screen_option(1)
            return

        if action in ("3", game_input.USE_MOVE_3): #C
            state["selected_index"] = 2
            self._select_title_screen_option(2)
            return

        if action in ("4", "4"): #V
            state["selected_index"] = 3
            self._select_title_screen_option(3)
            return

        if action in (game_input.QUIT, "q", "Q"): #Esc
            self.is_running = False
            return

        if action in (game_input.CONFIRM, "\r", "\n", "z", "Z"): #Return
            self._select_title_screen_option(sel)
            return

    def _select_title_screen_option(self, option_index: int):
        state = getattr(self, "title_screen_state", None)
        if state is None:
            return

        if option_index == 0: #New Game
            self.title_screen_state = None
            self.starter_select_state = {
                "selected_index": 0,
                "sub_mode": "select",
                "text": ""
            }
            self.render()
        elif option_index == 1: #Load Game
            self.title_screen_state = None
            self.load_game_state = {
                "selected_index": 0,
                "error_message": None
            }
            self.render()
        elif option_index == 2: #High Scores
            self.title_screen_state = None
            from high_scores import HighScoreController
            self.high_scores_state = {
                "controller": HighScoreController(self)
            }
            self.render()
        elif option_index == 3: #Exit
            self.title_screen_state = None
            self.is_running = False

    def handle_load_game_screen_input(self, action: str):
        """Handles key input for the Load Game selection screen"""
        state = getattr(self, "load_game_state", None)
        if state is None:
            return

        from save_game import list_save_files, load_game_from_file, validate_save_file
        save_files = list_save_files()
        sel = state.get("selected_index", 0)

        if not save_files:
            if action in (game_input.QUIT, game_input.CONFIRM, "\x1b", "ESC", "Esc", "esc", "q", "Q", "z", "Z", "\r", "\n"):
                self.load_game_state = None
                import random
                #Choose a random tip each time the title screen is displayed
                self.title_screen_state = {
                    "selected_index": 1,
                    "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
                }
                self.render()
            return

        if action in (game_input.MOVE_UP, "w", "W", "up", "UP", "k", "K"):
            state["error_message"] = None
            state["selected_index"] = (sel - 1) % len(save_files)
            self.render()
            return

        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN", "j", "J"):
            state["error_message"] = None
            state["selected_index"] = (sel + 1) % len(save_files)
            self.render()
            return

        if action in (game_input.QUIT, "\x1b", "ESC", "Esc", "esc"):
            self.load_game_state = None
            import random
            self.title_screen_state = {
                "selected_index": 1,
                "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
            }
            self.render()
            return

        if action in (game_input.CONFIRM, "\r", "\n", "z", "Z"):
            if 0 <= sel < len(save_files):
                sf = save_files[sel]
                fpath = sf["filepath"]
                valid, payload = validate_save_file(fpath)
                if not valid or payload is None:
                    state["error_message"] = "The save file appears to be corrupt!"
                    self.render()
                    return

                success, err, _ = load_game_from_file(fpath, game=self)
                if not success:
                    state["error_message"] = err or "Failed to load save file!"
                    self.render()
                    return

                #Successfully loaded!
                self.load_game_state = None
                self.title_screen_state = None
                self.render()

    def render_load_game_screen(self) -> list[str]:
        """Renders the Load Game selection screen surrounded by a 76x48 bordered frame."""
        state = getattr(self, "load_game_state", None)
        if state is None:
            return []

        sel_idx = state.get("selected_index", 0)
        error_msg = state.get("error_message", None)

        width = 76
        inner_w = width - 2
        top_border = "┌" + "─" * inner_w + "┐"
        bot_border = "└" + "─" * inner_w + "┘"
        divider = "├" + "─" * inner_w + "┤"
        empty_line = "│" + " " * inner_w + "│"

        def wrap_center(content: str) -> str:
            return "│" + center_ansi(content, inner_w) + "│"

        def wrap_left(content: str) -> str:
            import re
            ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
            vis_len = len(ansi_escape.sub('', content))
            right_pad = max(0, inner_w - 2 - vis_len)
            return "│ " + content + " " * right_pad + " │"

        rows = [
            top_border,
            wrap_center("\033[1;97mLoad Game\033[0m"),
            divider,
            empty_line,
        ]

        from save_game import list_save_files
        save_files = list_save_files()

        if not save_files:
            rows.append(wrap_center("\033[90mNo save files found.\033[0m"))
            while len(rows) < 45:
                rows.append(empty_line)
            rows.append(wrap_center("\033[90m[Esc] Return to Title Screen\033[0m"))
            rows.append(empty_line)
            rows.append(bot_border)
            return self.sanitize_rendered_rows(rows[:48])

        if sel_idx >= len(save_files):
            sel_idx = max(0, len(save_files) - 1)
            state["selected_index"] = sel_idx

        #Render list of save files
        for idx, sf in enumerate(save_files):
            prefix = "\033[1;93m ► " if sel_idx == idx else "   "
            suffix = "\033[0m" if sel_idx == idx else ""
            fname = sf["filename"]
            info = sf.get("info", "Save File")
            num = f"[{idx + 1:2d}] "
            if not sf.get("is_valid", True):
                line = f"{prefix}{num}{fname}  \033[91m(CORRUPT)\033[0m{suffix}"
            else:
                line = f"{prefix}{num}{fname}  \033[36m({info})\033[0m{suffix}"
            rows.append(wrap_left(line))

        while len(rows) < 43:
            rows.append(empty_line)

        if error_msg:
            rows.append(wrap_center(f"\033[1;91m{error_msg}\033[0m"))
        else:
            rows.append(empty_line)

        rows.append(empty_line)
        rows.append(wrap_center("\033[90m[↑/↓] Choose Save File   [Return] Load Game   [Esc] Back to Title\033[0m"))
        rows.append(empty_line)
        rows.append(bot_border)
        return self.sanitize_rendered_rows(rows[:48])

    def transition_disclaimer_to_title(self):
        """Transitions from the startup disclaimer screen to the title screen"""
        self.disclaimer_screen_state = None
        import random
        self.title_screen_state = {
            "selected_index": 0,
            "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
        }
        self.render()

    def render_disclaimer_screen(self) -> list[str]:
        """Renders the startup disclaimer screen"""
        state = getattr(self, "disclaimer_screen_state", None)
        if state is None:
            return []

        width = 76
        inner_w = width - 2
        top_border = "┌" + "─" * inner_w + "┐"
        bot_border = "└" + "─" * inner_w + "┘"
        empty_line = "│" + " " * inner_w + "│"

        def wrap(content: str) -> str:
            return "│" + center_ansi(content, inner_w) + "│"

        rows = [top_border]

        for _ in range(12):
            rows.append(empty_line)

        rows.append(wrap("\033[90m2026 C437RP13 (github.com/axolotl-and-fish)\033[0m"))

        for _ in range(4):
            rows.append(empty_line)

        p1 = "This is a non-profit FAN-GAME. It must not be sold or distributed for profit by any means. If you paid for this game, you have been scammed and should demand your money back."
        import textwrap
        wrapped_p1 = textwrap.wrap(p1, width=66)
        for line in wrapped_p1:
            rows.append(wrap(f"\033[97m{line}\033[0m"))

        for _ in range(4):
            rows.append(empty_line)

        p2_lines = [
            "This game is not associated with or endorsed by Nintendo, Game Freak,",
            "The Pokémon Company or Spike Chunsoft in any way.",
            "",
            "Licensed under the GNU General Public License V3, please see",
            "the LICENSE file for further details."
        ]
        for line in p2_lines:
            rows.append(wrap(f"\033[90m{line}\033[0m"))

        while len(rows) < 47:
            rows.append(empty_line)

        rows.append(bot_border)
        return self.sanitize_rendered_rows(rows[:48])

    def render_title_screen(self) -> list[str]:
        """Renders the main Title Screen surrounded by a 76x48 bordered frame."""
        state = getattr(self, "title_screen_state", None)
        if state is None:
            return []

        width = 76
        inner_w = width - 2
        top_border = "┌" + "─" * inner_w + "┐"
        bot_border = "└" + "─" * inner_w + "┘"
        empty_line = "│" + " " * inner_w + "│"

        def wrap(content: str) -> str:
            return "│" + center_ansi(content, inner_w) + "│"

        rows = [top_border, empty_line]

        #1. Logo in white
        for line in GAME_LOGO_LINES:
            rows.append(wrap(line))

        rows.append(empty_line)

        #2. Version in gray
        version_text = f"\033[90m{self.build_string}\033[0m"
        rows.append(wrap(version_text))

        for _ in range(4):
            rows.append(empty_line)

        #3. Menu options
        sel_idx = state.get("selected_index", 0)
        options = ["New Game", "Load Game", "High Scores", "Quit"]

        for idx, opt in enumerate(options):
            if sel_idx == idx:
                opt_str = f"\033[1;93m ► {opt} ◄ \033[0m"
            else:
                opt_str = f"   {opt}   "
            rows.append(wrap(opt_str))

        for _ in range(2):
            rows.append(empty_line)

        rows.append(wrap("\033[90m2026 C437RP13 (github.com/axolotl-and-fish)\033[0m"))

        for _ in range(6):
            rows.append(empty_line)

        #4. Tip of the Day
        tip = state.get("tip_of_the_day", TIPS_OF_THE_DAY[0])
        tip_text = f"\033[96mTip of the Day:\033[0m \033[37m{tip}\033[0m"
        rows.append(wrap(f"\033[96mTip of the Day:\033[0m"))
        rows.append(wrap(f"\033[96m{tip}\033[0m"))
        rows.append(empty_line)
        rows.append(bot_border)

        return self.sanitize_rendered_rows(rows[:48])

    def handle_starter_select_input(self, action: str):
        """Handles input for the New Game (starter selection) screen"""
        state = getattr(self, "starter_select_state", None)
        if state is None:
            return

        starters = [
            "Bulbasaur", "Charmander", "Squirtle", "Pikachu", "Vulpix",
            "Growlithe", "Meowth", "Psyduck", "Machop", "Cubone", "Eevee"
        ]
        sel = state.get("selected_index", 0)

        if action in (game_input.MOVE_UP, "w", "W", "up", "UP", "k", "K"):
            state["selected_index"] = (sel - 1) % len(starters)
            self.render()
            return

        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN", "j", "J"):
            state["selected_index"] = (sel + 1) % len(starters)
            self.render()
            return

        if action in (game_input.QUIT, "\x1b", "ESC", "Esc", "esc"):
            self.starter_select_state = None
            import random
            self.title_screen_state = {
                "selected_index": 0,
                "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
            }
            self.render()
            return

        if action in (game_input.CONFIRM, "\r", "\n", "z", "Z"):
            chosen_species = starters[sel]
            state["chosen_species"] = chosen_species
            state["sub_mode"] = "naming"
            state["text"] = chosen_species
            self.render()
            return

    def handle_starter_naming_input(self, char_in: str):
        """Handles character input for naming the starter Pokémon."""
        state = getattr(self, "starter_select_state", None)
        if state is None:
            return

        chosen_species = state.get("chosen_species", "Bulbasaur")
        curr_text = state.get("text", "")

        if char_in == "ENTER":
            nick = curr_text.strip()[:12]
            if not nick or nick == chosen_species:
                nick = None
            self.start_new_game(chosen_species, nick)
        elif char_in == "ESC":
            self.start_new_game(chosen_species, None)
        elif char_in == "BACKSPACE":
            if curr_text:
                state["text"] = curr_text[:-1]
                self.render()
        elif char_in and len(curr_text) < 12 and (char_in.isalnum() or char_in in " -_"):
            state["text"] = curr_text + char_in
            self.render()

    def handle_high_scores_screen_input(self, action: str):
        """Handles key input on the High Scores screen."""
        state = getattr(self, "high_scores_state", None)
        if state is None:
            return

        controller = state.get("controller")
        if controller:
            controller.handle_input(action)
            if not controller.is_active:
                self.high_scores_state = None
                import random
                self.title_screen_state = {
                    "selected_index": 1,
                    "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
                }
                self.render()
        else:
            if action in (game_input.QUIT, game_input.CONFIRM, "\x1b", "ESC", "Esc", "esc", "q", "Q", "z", "Z", "\r", "\n"):
                self.high_scores_state = None
                import random
                self.title_screen_state = {
                    "selected_index": 1,
                    "tip_of_the_day": random.choice(TIPS_OF_THE_DAY)
                }
                self.render()

    def start_new_game(self, species_name: str, nickname: str | None = None):
        """Initializes and starts a new game run with the chosen starter Pokémon."""
        self.title_screen_state = None
        self.starter_select_state = None
        self.high_scores_state = None

        self.player_pokemon = Pokemon(species_name, level=2, nickname=nickname)
        self.player_pokemon.is_leader = True
        self.party = [self.player_pokemon]

        starter_sp = getattr(self.player_pokemon, "species_name", "") or self.player_pokemon.species_data.get("name", self.player_pokemon.name)
        self.register_encountered_species(starter_sp)
        self.add_to_team_history(self.player_pokemon, is_starter=True)

        self.floor_number = 1
        self.floor = DungeonFloor(width=getattr(self, "floor_width_override", 56) or 56)
        self.explored_tiles.clear()
        self.player_x, self.player_y = self._get_starting_position()
        self.player_pokemon.x, self.player_pokemon.y = self.player_x, self.player_y

        self.spawn_stairs()
        self.spawn_wonder_tile()
        self.spawned_pokemon.clear()
        self.generate_floor_spawn_list()
        self.spawn_initial_items()
        self.spawn_initial_enemies()

        self.render()

    def render_starter_select_screen(self) -> list[str]:
        """Renders the full-screen (76x48) starter Pokémon selection and naming screen."""
        state = getattr(self, "starter_select_state", None)
        if state is None:
            return []

        sub_mode = state.get("sub_mode", "select")
        sel_idx = state.get("selected_index", 0)
        text = state.get("text", "")
        chosen_species = state.get("chosen_species", "Bulbasaur")

        width = 76
        inner_w = width - 2
        top_border = "┌" + "─" * inner_w + "┐"
        bot_border = "└" + "─" * inner_w + "┘"
        divider = "├" + "─" * inner_w + "┤"
        empty_line = "│" + " " * inner_w + "│"

        def wrap_center(content: str) -> str:
            return "│" + center_ansi(content, inner_w) + "│"

        def wrap_left(content: str) -> str:
            import re
            ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
            vis_len = len(ansi_escape.sub('', content))
            right_pad = max(0, inner_w - 2 - vis_len)
            return "│ " + content + " " * right_pad + " │"

        starters = [
            ("Bulbasaur", "Grass/Poison"),
            ("Charmander", "Fire"),
            ("Squirtle", "Water"),
            ("Pikachu", "Electric"),
            ("Vulpix", "Fire"),
            ("Growlithe", "Fire"),
            ("Meowth", "Normal"),
            ("Psyduck", "Water"),
            ("Machop", "Fighting"),
            ("Cubone", "Ground"),
            ("Eevee", "Normal"),
        ]

        rows = [
            top_border,
            wrap_center("\033[1;97mWho do you want to be?\033[0m"),
            divider,
        ]

        for idx, (sp, types_str) in enumerate(starters):
            if sub_mode == "naming" and sp == chosen_species:
                prefix = "\033[1;93m ► "
                suffix = f"  \033[1;92m[√]\033[0m"
            elif sub_mode == "select" and sel_idx == idx:
                prefix = "\033[1;93m ► "
                suffix = "\033[0m"
            else:
                prefix = "   "
                suffix = "\033[0m"
            info = f"{sp:<12} ({types_str:<12})"
            line = f"{prefix}{info}{suffix}"
            rows.append(wrap_left(line))

        rows.append(empty_line)

        if sub_mode == "naming":
            rows.append("├" + "─" * 74 + "┤")
            rows.append(empty_line)
            rows.append(empty_line)
            rows.append(wrap_center("What's your name?"))
            rows.append(wrap_center("\033[90m(Max 12 characters)\033[0m"))
            rows.append(empty_line)
            rows.append(f"                                \033[1;97m► {text}_\033[0m")
            rows.append(empty_line)
            rows.append(wrap_center("\033[90m[Return] Confirm   [Esc] Skip\033[0m"))
            while len(rows) < 47:
                rows.append(empty_line)
        else:
            while len(rows) < 45:
                rows.append(empty_line)
            rows.append(wrap_center("\033[90m[↑/↓] Choose   [Return] Select   [Esc] Back to Title\033[0m"))
            rows.append(empty_line)

        rows.append(bot_border)
        return self.sanitize_rendered_rows(rows)

    def render_high_scores_screen(self) -> list[str]:
        """Renders the High Scores screen overlay."""
        state = getattr(self, "high_scores_state", None)
        if state is None:
            return []

        controller = state.get("controller")
        if controller:
            return self.sanitize_rendered_rows(controller.render())
        from high_scores import load_high_scores, format_high_scores_table
        scores = load_high_scores()
        return self.sanitize_rendered_rows(format_high_scores_table(scores))

    def can_change_leader(self, target: Pokemon) -> bool:
        """Returns True if the leader can be changed to target.
        Leader cannot be changed if target is already the team leader, or if either the leader
        or target has active negative status conditions: Sleep, Resting, Petrified, Terrified, or Blind.
        """
        if target == self.player_pokemon or getattr(target, "is_leader", False):
            return False
        blocked_statuses = ("Sleep", "Resting", "Petrified", "Terrified", "Blind")
        for p in (self.player_pokemon, target):
            if p is None or not hasattr(p, "status_effects"):
                continue
            for st in blocked_statuses:
                val = p.status_effects.get(st, 0)
                if val > 0 or val == -1:
                    return False
        return True

    def get_summary_context_menu_options(self, pokemon: Pokemon) -> list[str]:
        """Returns valid context menu options for the given Pokémon summary screen."""
        options = []
        if pokemon.can_evolve(game=self):
            options.append("Evolve")
        if self.can_change_leader(pokemon):
            options.append("Make Leader")
        if len(self.party) > 1:
            options.append("Switch Places")
        is_leader = (pokemon == self.player_pokemon or getattr(pokemon, "is_leader", False))
        if not is_leader:
            options.append("Farewell")
        return options

    def render_summary_context_menu_overlay(self, rows: list[str]) -> list[str]:
        """Overlays the Pokémon summary screen context menu onto 48 screen rows."""
        state = getattr(self, "summary_context_menu_state", None)
        if not state:
            return rows

        mode = state.get("mode", "menu")
        poke = getattr(self, "active_status_pokemon", None)
        if not poke:
            return rows

        if mode == "menu" and not state.get("options", []):
            return rows

        box_width = 56
        box_rows = []
        top_border = "┌" + "─" * (box_width - 2) + "┐"
        bot_border = "└" + "─" * (box_width - 2) + "┘"
        sep_border = "├" + "─" * (box_width - 2) + "┤"
        empty_line = "│" + " " * (box_width - 2) + "│"

        def fmt_line(content: str) -> str:
            padded = self.pad_ansi_string(content, box_width - 4)
            return f"│ {padded} │"

        if mode == "menu":
            options = state.get("options", [])
            sel_idx = state.get("selected_index", 0)
            box_rows.append(top_border)
            box_rows.append(fmt_line(f"Options: {poke.name}"))
            box_rows.append(sep_border)
            for idx, opt in enumerate(options):
                prefix = "► " if idx == sel_idx else "  "
                box_rows.append(fmt_line(f"{prefix}{opt}"))
            box_rows.append(sep_border)
            box_rows.append(fmt_line("[↑/↓] Select  [Return] Confirm  [Esc] Cancel"))
            box_rows.append(bot_border)

        elif mode == "evolve_select":
            options = state.get("options", [])
            sel_idx = state.get("selected_index", 0)
            box_rows.append(top_border)
            box_rows.append(fmt_line(f"Evolve {poke.name}"))
            box_rows.append(sep_border)
            box_rows.append(fmt_line("What to evolve them into?"))
            for idx, opt in enumerate(options):
                prefix = "► " if idx == sel_idx else "  "
                box_rows.append(fmt_line(f"{prefix}{opt}"))
            box_rows.append(sep_border)
            box_rows.append(fmt_line("[↑/↓] Select  [Return] Confirm  [Esc] Cancel"))
            box_rows.append(bot_border)

        elif mode == "switch_places":
            box_rows.append(top_border)
            box_rows.append(fmt_line(f"Switch Places: {poke.name}"))
            box_rows.append(sep_border)
            box_rows.append(fmt_line("Swap with which team member?"))
            key_labels = ["[A]", "[S]", "[D]", "[F]", "[G]", "[H]"]
            for idx, member in enumerate(self.party[:6]):
                key_tag = key_labels[idx]
                leader_tag = " (Leader)" if (member == self.player_pokemon or getattr(member, "is_leader", False)) else ""
                current_tag = " (Current)" if member == poke else ""
                box_rows.append(fmt_line(f"{key_tag} {member.name} Lv{member.level}{leader_tag}{current_tag}"))
            box_rows.append(sep_border)
            box_rows.append(fmt_line("[Esc] Cancel"))
            box_rows.append(bot_border)

        elif mode == "farewell_confirm":
            box_rows.append(fmt_line(f"Are you SURE you want to say goodbye to"))
            box_rows.append(fmt_line(f"{poke.name}? They will leave the team forever."))
            box_rows.append(empty_line)
            box_rows.append(fmt_line("[Y] Proceed  [N] / [Esc] Cancel"))
            box_rows.append(bot_border)

        start_row = (48 - len(box_rows)) // 2
        new_rows = list(rows)
        left_pad = (76 - box_width) // 2
        for i, box_line in enumerate(box_rows):
            r_idx = start_row + i
            if 0 <= r_idx < 48:
                prefix = " " * left_pad
                suffix = " " * (76 - left_pad - box_width)
                new_rows[r_idx] = prefix + box_line + suffix
        return self.sanitize_rendered_rows(new_rows)

    def get_item_render_char(self, item: dict, is_visible: bool = True) -> str:
        """Returns the ANSI-colorized character for rendering an item on the floor."""
        if getattr(self, "compatibility_mode", False):
            if item.get("type") == "Money" or item.get("name") == "Poké":
                return "P"
            return item.get("appearance") or item.get("symbol") or item.get("char") or "?"

        if item.get("type") == "Money" or item.get("name") == "Poké":
            if is_visible:
                return "\033[30;43mP\033[0m"
            else:
                return "\033[90mP\033[0m"
        symbol = item.get("appearance") or item.get("symbol") or item.get("char") or "?"
        if not is_visible:
            return f"\033[90m{symbol}\033[0m"

        color_raw = item.get("color", "green")
        if color_raw.startswith("\033["):
            color_code = color_raw
        else:
            color_map = {
                "green": "\033[92m",
                "bright_green": "\033[92m",
                "red": "\033[91m",
                "bright_red": "\033[91m",
                "blue": "\033[94m",
                "bright_blue": "\033[94m",
                "yellow": "\033[93m",
                "bright_yellow": "\033[93m",
                "cyan": "\033[96m",
                "bright_cyan": "\033[96m",
                "magenta": "\033[95m",
                "bright_magenta": "\033[95m",
                "purple": "\033[35m",
                "brown": "\033[33m",
                "white": "\033[37m",
                "gray": "\033[90m",
            }
            color_code = color_map.get(color_raw.lower(), "\033[92m")
        return f"{color_code}{symbol}\033[0m"

    def render_map_to_rows(self) -> list[str]:
        """Compiles the raw dungeon map grid cells into row strings with overlaid entities"""
        currently_visible = self._compute_currently_visible()
        self.explored_tiles.update(currently_visible)

        #Create a mapping from position to pokemon on floor (for spawned pokemon)
        spawned_map = {}
        for p in self.spawned_pokemon:
            if hasattr(p, "x") and hasattr(p, "y") and int(getattr(p, "current_hp", 0)) > 0:
                spawned_map[(p.x, p.y)] = p

        #Create a mapping from position to (ally_pokemon, slot_str) for non-leader party members
        ally_map = {}
        non_leader_allies = [p for p in self.party if p is not self.player_pokemon and not getattr(p, "is_leader", False) and int(getattr(p, "current_hp", 0)) > 0]
        for idx, ally in enumerate(non_leader_allies):
            ax, ay = get_pokemon_position(self, ally)
            slot_num = idx + 1
            slot_str = str(slot_num + 1) if slot_num < 10 else str(slot_num % 10) #Because indices start at zero!
            ally_map[(ax, ay)] = (ally, slot_str)

        output_rows = []
        for y in range(self.floor.height):
            row_chars = []
            skip_x = 0
            for x in range(self.floor.width):
                if skip_x > 0:
                    skip_x -= 1
                    continue

                #Animation overlays
                anim = self.flying_item_animation
                if (x, y) in getattr(self, "explosion_overlays", {}):
                    row_chars.append(self.explosion_overlays[(x, y)])
                elif anim is not None and (x, y) == (anim["x"], anim["y"]) and (x, y) in currently_visible:
                    row_chars.append(f"{anim['color']}{anim['char']}\033[0m")
                elif getattr(self, "look_around_mode", False) and x == self.look_around_cursor[0] and y == self.look_around_cursor[1] and getattr(self, "look_around_cursor_visible", True):
                    row_chars.append("\033[93mX\033[0m")
                elif (x, y) in self.flash_damages:
                    dmg, mult = self.flash_damages[(x, y)]
                    if mult == "EXP":
                        color = "\033[94m"  #Blue
                    elif mult == "HEAL":
                        color = "\033[92m"  #Green
                    elif mult == "MISS":
                        color = "\033[90m"  #Gray
                    elif isinstance(mult, (int, float)) and mult >= 1.25:
                        color = "\033[91m"  #Red
                    elif isinstance(mult, (int, float)) and 0.25 < mult <= 0.75:
                        color = "\033[93m"  #Yellow
                    elif isinstance(mult, (int, float)) and mult == 0.25:
                        color = "\033[90m"  #Gray
                    else:
                        color = "\033[38;5;208m"  #Orange
                    
                    dmg_str = str(dmg)
                    row_chars.append(f"{color}{dmg_str}\033[0m")
                    skip_x = len(dmg_str) - 1
                elif self.targeting_mode and x == self.targeting_cursor[0] and y == self.targeting_cursor[1]:
                    row_chars.append("X")
                elif x == self.player_x and y == self.player_y:
                    is_hallucinating = bool(getattr(self.player_pokemon, "status_effects", {}).get("Hallucinating", 0) > 0)
                    if is_hallucinating: #Hallucinate Pokémon at random
                        fake_p = random.choice(self.pokemon_db) if self.pokemon_db else {"name": "Mew", "types": ["Psychic"]}
                        fake_type = fake_p.get("types", ["Normal"])[0] if fake_p.get("types") else "Normal"
                        color = TYPE_COLORS.get(fake_type, "\033[37m")
                        row_chars.append(f"{color}{fake_p['name'][0]}\033[0m")
                    elif self.player_pokemon.status_effects.get("Decoy", 0) > 0 and not getattr(self.player_pokemon, "is_leader", False):
                        row_chars.append("\033[92m?\033[0m")
                    else:
                        row_chars.append(PLAYER_CHAR)
                elif (x, y) in currently_visible and (x, y) in ally_map:
                    is_hallucinating = bool(getattr(self.player_pokemon, "status_effects", {}).get("Hallucinating", 0) > 0)
                    ally, slot_str = ally_map[(x, y)]
                    if is_hallucinating:
                        fake_p = random.choice(self.pokemon_db) if self.pokemon_db else {"name": "Ditto", "types": ["Normal"]}
                        fake_type = fake_p.get("types", ["Normal"])[0] if fake_p.get("types") else "Normal"
                        color = TYPE_COLORS.get(fake_type, "\033[37m")
                        row_chars.append(f"{color}{fake_p['name'][0]}\033[0m")
                    elif ally.status_effects.get("Decoy", 0) > 0 and not getattr(ally, "is_leader", False):
                        row_chars.append("\033[92m?\033[0m")
                    else:
                        primary_type = ally.types[0] if getattr(ally, "types", None) else (ally.species_data["types"][0] if "types" in ally.species_data and ally.species_data["types"] else "Typeless")
                        color = TYPE_COLORS.get(primary_type, "\033[37m")
                        row_chars.append(f"{color}{slot_str}\033[0m")
                elif ((x, y) in currently_visible or getattr(self, "radar_active", False)) and (x, y) in spawned_map:
                    is_hallucinating = bool(getattr(self.player_pokemon, "status_effects", {}).get("Hallucinating", 0) > 0)
                    poke = spawned_map[(x, y)]
                    if int(getattr(poke, "current_hp", 0)) > 0:
                        if is_hallucinating:
                            fake_p = random.choice(self.pokemon_db) if self.pokemon_db else {"name": "Eevee", "types": ["Normal"]}
                            fake_type = fake_p.get("types", ["Normal"])[0] if fake_p.get("types") else "Normal"
                            color = TYPE_COLORS.get(fake_type, "\033[37m")
                            if (x, y) in currently_visible:
                                row_chars.append(f"{color}{fake_p['name'][0]}\033[0m")
                            else:
                                row_chars.append(f"\033[91m{fake_p['name'][0]}\033[0m")
                        elif poke.status_effects.get("Decoy", 0) > 0 and not getattr(poke, "is_leader", False):
                            row_chars.append("\033[92m?\033[0m")
                        else:
                            primary_type = poke.species_data["types"][0] if "types" in poke.species_data and poke.species_data["types"] else "Typeless"
                            color = TYPE_COLORS.get(primary_type, "\033[37m")
                            if (x, y) in currently_visible:
                                row_chars.append(f"{color}{poke.name[0]}\033[0m")
                            else:
                                row_chars.append(f"\033[91m{poke.name[0]}\033[0m")
                elif (x, y) in currently_visible:
                    is_hallucinating = bool(getattr(self.player_pokemon, "status_effects", {}).get("Hallucinating", 0) > 0)
                    if (x, y) == getattr(self, "stairs_position", None):
                        if is_hallucinating: #Change tile colors randomly while hallucinating
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}>\033[0m")
                        else:
                            row_chars.append(">")
                    elif (x, y) == getattr(self, "wonder_tile_position", None):
                        if is_hallucinating: #Change tile colors randomly while hallucinating
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}↑\033[0m")
                        else:
                            row_chars.append("\033[32m↑\033[0m")
                    elif (x, y) in self.items_on_floor:
                        if is_hallucinating: #Randomize item appearances while hallucinating
                            fake_item = random.choice(list(items.ITEMS_DB.values()))
                            row_chars.append(self.get_item_render_char(fake_item, is_visible=True))
                        else:
                            item = self.items_on_floor[(x, y)]
                            row_chars.append(self.get_item_render_char(item, is_visible=True))
                    else:
                        grid_char = self.floor.grid[y][x]
                        if is_hallucinating:
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}{grid_char}\033[0m")
                        else:
                            row_chars.append(grid_char)
                elif (x, y) in self.explored_tiles or getattr(self, "scanner_active", False) or getattr(self, "stairs_revealed", False):
                    is_hallucinating = bool(getattr(self.player_pokemon, "status_effects", {}).get("Hallucinating", 0) > 0)
                    if (x, y) == getattr(self, "stairs_position", None) and ((x, y) in self.explored_tiles or getattr(self, "stairs_revealed", False)):
                        if is_hallucinating:
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}>\033[0m")
                        else:
                            row_chars.append("\033[93m>\033[0m" if getattr(self, "stairs_revealed", False) else "\033[90m>\033[0m")
                    elif (x, y) == getattr(self, "wonder_tile_position", None) and (x, y) in self.explored_tiles:
                        if is_hallucinating:
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}↑\033[0m")
                        else:
                            row_chars.append("\033[90m↑\033[0m")
                    elif (x, y) in self.items_on_floor and ((x, y) in self.explored_tiles or getattr(self, "scanner_active", False)):
                        if is_hallucinating:
                            fake_item = random.choice(list(items.ITEMS_DB.values()))
                            row_chars.append(self.get_item_render_char(fake_item, is_visible=False))
                        else:
                            item = self.items_on_floor[(x, y)]
                            row_chars.append(self.get_item_render_char(item, is_visible=False))
                    elif (x, y) in self.explored_tiles:
                        grid_char = self.floor.grid[y][x]
                        if is_hallucinating:
                            row_chars.append(f"{random.choice(SCINTILLATING_COLORS)}{grid_char}\033[0m")
                        else:
                            row_chars.append(f"\033[90m{grid_char}\033[0m")
                    else:
                        row_chars.append(" ")
                else:
                    row_chars.append(" ")
            output_rows.append("".join(row_chars))
        return self.sanitize_rendered_rows(output_rows)

    def render_main_interface_rows(self) -> list[str]:
        """Compiles and returns the combined main interface rows (48 rows)"""
        output_rows = self.render_map_to_rows()

        #Centering and padding calculations for map width (interior 56 cols). This lets us center the dungeon in the center of the map window
        W = self.floor.width
        if W < 56:
            pad_left = (56 - W) // 2
            pad_right = 56 - W - pad_left
        else:
            pad_left = 0
            pad_right = 0

        map_interior_rows = []
        for row in output_rows:
            padded_row = " " * pad_left + row + " " * pad_right
            map_interior_rows.append(f"│{padded_row}│")

        #Guarantee exactly 32 interior rows
        while len(map_interior_rows) < 32:
            map_interior_rows.append("│" + " " * 56 + "│")
        map_interior_rows = map_interior_rows[:32]

        #Build left side screen panel
        left_side_rows = []
        floor_str = f"{self.floor_number}F"
        left_part = f"─{floor_str}"
        money_amount = getattr(self, "money", 0)
        right_color = f"{money_amount:,} \033[30;43mP\033[0m─"
        right_plain = f"{money_amount:,} P─"
        dash_count = max(0, 56 - len(left_part) - len(right_plain))
        left_side_rows.append(f"┌{left_part}{'─' * dash_count}{right_color}┐")
        left_side_rows.extend(map_interior_rows)
        weather_str = getattr(self, "weather", "Clear") or "Clear"
        weather_color_map = {
            "Clear": "\033[90m",
            "Rain": "\033[94m",
            "Hail": "\033[97m",
            "Mist": "\033[97m",
            "Sandstorm": "\033[33m",
            "Sunny": "\033[93m",
            "Electric Terrain": "\033[93m",
            "Psychic Terrain": "\033[95m",
            "Grassy Terrain": "\033[92m",
            "Misty Terrain": "\033[97m",
            "Snow": "\033[97m",
            "Harsh Sunlight": "\033[93m",
            "Heavy Rain": "\033[94m",
        }
        w_color = weather_color_map.get(weather_str, "\033[90m")
        bot_left_plain = f"─{weather_str}"
        bot_left_color = f"─{w_color}{weather_str}\033[0m"

        turn_val = getattr(self, "turn_number", 1)
        bot_right_plain = f"Turn {turn_val:,}─"

        bot_dash_count = max(0, 56 - len(bot_left_plain) - len(bot_right_plain))
        left_side_rows.append(f"└{bot_left_color}{'─' * bot_dash_count}{bot_right_plain}┘")

        #Draw message log window (56 columns by 5 rows)
        left_side_rows.append("┌" + "─" * 56 + "┐")
        if getattr(self, "look_around_mode", False):
            desc_lines = self.get_look_around_description()
            for line in desc_lines:
                padded_line = self.pad_ansi_string(line, 56)
                left_side_rows.append(f"│{padded_line}│")
        else:
            log_lines_with_turns = self.message_log.get_visible_lines_with_turns()
            current_action = getattr(self, "player_action_number", 0)
            for item in log_lines_with_turns:
                line, logged_turn = item[0], item[1]
                if current_action - logged_turn >= 1:
                    stripped_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
                    padded_line = f"{stripped_line:<56}"[:56]
                    left_side_rows.append(f"│\033[90m{padded_line}\033[0m│")
                else:
                    padded_line = self.pad_ansi_string(line, 56)
                    left_side_rows.append(f"│{padded_line}│")
        if getattr(self.message_log, "has_more_page", False):
            left_side_rows.append("└" + "─" * 50 + "\033[94m[MORE]\033[0m" + "┘")
        else:
            left_side_rows.append("└" + "─" * 56 + "┘")

        #Move windows (aligned horizontally, taking 6 rows below log)
        move_rows = self.get_move_windows_rows()
        left_side_rows.extend(move_rows)

        #Pad left side rows to at least 48 rows to match party panel height
        while len(left_side_rows) < 48:
            left_side_rows.append("")

        #Pad each left-side row to exactly 58 printable characters
        padded_left_rows = [self.pad_ansi_string(row, 58) for row in left_side_rows]

        #Generate status panel rows (48 rows)
        panel_rows = self.get_party_panel_rows()

        #Combine side-by-side: column 59 is the left border of status windows
        combined_rows = []
        for y in range(48):
            combined_rows.append(f"{padded_left_rows[y]}{panel_rows[y]}")

        return self.sanitize_rendered_rows(combined_rows)

    def render(self):
        """Draws the dungeon map with the player overlaid and visibility/memory applied"""
        if getattr(self, "suppress_animation_delay", False) or getattr(self, "_is_rendering", False):
            return
        self._is_rendering = True
        try:
            if self.player_pokemon is not None:
                self.ensure_valid_position("player")
        finally:
            self._is_rendering = False

        rows = None

        #Game "states", so to speak
        screen_view = "gameplay"
        if getattr(self, "disclaimer_screen_state", None) is not None:
            screen_view = "disclaimer"
            rows = self.render_disclaimer_screen()
        elif getattr(self, "title_screen_state", None) is not None:
            screen_view = "title"
            rows = self.render_title_screen()
        elif getattr(self, "starter_select_state", None) is not None:
            screen_view = "starter_select"
            rows = self.render_starter_select_screen()
        elif getattr(self, "load_game_state", None) is not None:
            screen_view = "load_game"
            rows = self.render_load_game_screen()
        elif getattr(self, "high_scores_state", None) is not None:
            screen_view = "high_scores"
            rows = self.render_high_scores_screen()
        elif getattr(self, "pause_menu_state", None) is not None:
            screen_view = "pause_menu"
            pause_rows = self.render_pause_menu_screen()
            if pause_rows:
                base_rows = self.render_main_interface_rows()
                import re
                ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
                base_width = len(ansi_escape.sub('', base_rows[0])) if base_rows else 76
                overlay_width = 54
                overlay_height = len(pause_rows)
                start_x = max(0, (base_width - overlay_width) // 2)
                start_y = max(0, (len(base_rows) - overlay_height) // 2)
                rows = self.overlay_rows_on_base(base_rows, pause_rows, start_x, start_y)

        elif getattr(self, "replace_recruit_state", None) is not None:
            screen_view = "replace_recruit"
            replace_rows = self.render_replace_recruit_prompt_screen()
            if replace_rows:
                base_rows = self.render_main_interface_rows()
                import re
                ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
                base_width = len(ansi_escape.sub('', base_rows[0])) if base_rows else 76
                overlay_width = 64
                overlay_height = len(replace_rows)
                start_x = max(0, (base_width - overlay_width) // 2)
                start_y = max(0, (len(base_rows) - overlay_height) // 2)
                rows = self.overlay_rows_on_base(base_rows, replace_rows, start_x, start_y)

        elif getattr(self, "nickname_prompt_state", None) is not None:
            screen_view = "nickname_prompt"
            nickname_rows = self.render_nickname_prompt_screen()
            if nickname_rows:
                base_rows = self.render_main_interface_rows()
                import re
                ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
                base_width = len(ansi_escape.sub('', base_rows[0])) if base_rows else 76
                overlay_width = 60
                overlay_height = len(nickname_rows)
                start_x = max(0, (base_width - overlay_width) // 2)
                start_y = max(0, (len(base_rows) - overlay_height) // 2)
                rows = self.overlay_rows_on_base(base_rows, nickname_rows, start_x, start_y)

        elif getattr(self, "active_status_pokemon", None) is not None:
            screen_view = "full_status"
            rows = self.render_full_screen_status()

        elif getattr(self, "message_history_state", None) is not None:
            screen_view = "message_history"
            rows = self.render_message_history_screen()

        elif getattr(self, "inventory_state", None) is not None:
            screen_view = "inventory"
            rows = self.render_inventory_screen()

        elif getattr(self, "move_replacement_queue", None):
            screen_view = "move_replacement"
            pokemon, new_move = self.move_replacement_queue[0]
            rows = self.render_move_replacement_screen(pokemon, new_move)

        elif getattr(self, "mimic_selection_state", None) is not None:
            screen_view = "mimic_selection"
            state = self.mimic_selection_state
            rows = self.render_mimic_selection_screen(state["user"], state["target"])

        else:
            screen_view = "gameplay"
            rows = self.render_main_interface_rows()

        if rows:
            if getattr(self, "compatibility_mode", False):
                rows = self.sanitize_rendered_rows(rows)
            prev_screen = getattr(self, "_last_rendered_screen", None)
            screen_changed = (prev_screen != screen_view)
            self._last_rendered_screen = screen_view

            prefix = "\033[2J\033[H" if (screen_changed or screen_view in ("title", "starter_select", "high_scores", "load_game", "disclaimer")) else "\033[H"
            output_buffer = prefix + "\n".join(rows) + "\n\033[J"
            try:
                sys.stdout.write(output_buffer)
            except UnicodeEncodeError:
                clean_rows = [r.encode("ascii", "replace").decode("ascii") for r in rows]
                clean_buffer = prefix + "\n".join(clean_rows) + "\n\033[J"
                sys.stdout.write(clean_buffer)
            sys.stdout.flush()

    def overlay_rows_on_base(self, base_rows: list[str], overlay_rows: list[str], start_x: int, start_y: int) -> list[str]:
        """Overlays a list of box rows onto base_rows at (start_x, start_y) printable offsets."""
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

        result = list(base_rows)
        for i, ov_line in enumerate(overlay_rows):
            target_y = start_y + i
            if target_y >= len(result):
                break

            base_line = result[target_y]
            ov_len = len(ansi_escape.sub('', ov_line))

            #Tokenize base_line into (text_or_code, is_ansi)
            tokens = []
            j = 0
            n = len(base_line)
            while j < n:
                if base_line[j] in ('\x1b', '\033'):
                    start = j
                    j += 1
                    if j < n and base_line[j] == '[':
                        j += 1
                        while j < n and not base_line[j].isalpha():
                            j += 1
                        if j < n:
                            j += 1
                    tokens.append((base_line[start:j], True))
                else:
                    tokens.append((base_line[j], False))
                    j += 1

            left_part = []
            right_part = []
            vis_col = 0

            for tok, is_ansi in tokens:
                if is_ansi:
                    if vis_col <= start_x:
                        left_part.append(tok)
                    elif vis_col >= start_x + ov_len:
                        right_part.append(tok)
                else:
                    if vis_col < start_x:
                        left_part.append(tok)
                    elif vis_col >= start_x + ov_len:
                        right_part.append(tok)
                    vis_col += 1

            left_str = "".join(left_part)
            right_str = "".join(right_part)

            result[target_y] = f"{left_str}\033[0m{ov_line}\033[0m{right_str}"

        return result

    def pad_ansi_string(self, s: str, target_len: int) -> str:
        """Pads a string containing ANSI escape codes to target_len printable characters"""
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
        plain_len = len(ansi_escape.sub('', s))
        padding = target_len - plain_len
        if padding > 0:
            return s + " " * padding
        return s

    def get_party_panel_rows(self) -> list[str]:
        """Generates the 48 rows of stacked party status windows"""
        rows = []
        shortcuts = ["A", "S", "D", "F", "G", "H"]
        for i in range(6):
            pokemon = self.party[i] if i < len(self.party) else None
            shortcut = shortcuts[i]
            if pokemon is None:
                #Empty window: gray border, empty interior
                shortcut_str = f"\033[90m[{shortcut}]\033[0m"
                rows.append("\033[90m┌" + "─" * 13 + f"{shortcut_str}\033[90m┐\033[0m")
                for _ in range(6):
                    rows.append("\033[90m│\033[0m" + " " * 16 + "\033[90m│\033[0m")
                rows.append("\033[90m└" + "─" * 16 + "┘\033[0m")
            else:
                #Active team leader has a light blue status window. Others have white.
                is_leader = (pokemon is self.player_pokemon)
                base_color = "\033[96m" if is_leader else ""
                base_reset = "\033[0m" if is_leader else ""

                #Flashing warning logic: <=20% HP flashes red, empty belly flashes yellow every 0.5s.
                hp_pct = int(pokemon.current_hp) / pokemon.stats["HP"] if pokemon.stats["HP"] > 0 else 0.0
                is_low_hp = (hp_pct <= 0.20)
                is_belly_empty = (pokemon.current_belly <= 0.0)

                flash_color = None
                if is_low_hp:
                    flash_color = "\033[91m"  #Red
                elif is_belly_empty:
                    flash_color = "\033[93m"  #Yellow

                if flash_color is not None:
                    import time
                    show_flash = (int(time.time() * 2) % 2 == 1)
                    b_color = flash_color if show_flash else base_color
                    b_reset = "\033[0m" if (show_flash or is_leader) else ""
                else:
                    b_color = base_color
                    b_reset = base_reset

                #Occupied window: border (supports flashing), content lines
                shortcut_str = f"\033[92m[{shortcut}]\033[0m"
                rows.append(f"{b_color}┌" + "─" * 13 + f"{shortcut_str}{b_color}┐{b_reset}")

                #Line 1: Name (max 12) + Level (4). Name is in yellow when ready to evolve.
                name = pokemon.name[:12]
                level = pokemon.level
                level_str = f"Lv{level}" if level >= 10 else f"Lv {level}"
                if len(level_str) > 4:
                    level_str = "????"
                can_evolve = hasattr(pokemon, "can_evolve") and pokemon.can_evolve(game=self)
                if can_evolve:
                    name_str = f"\033[93m{name:<12}\033[0m"
                else:
                    name_str = f"{name:<12}"
                line1 = f"{name_str}{level_str:>4}"
                rows.append(f"{b_color}│{b_reset}{line1}{b_color}│{b_reset}")

                #Line 2: HP (9) + HP gauge (7)
                curr_hp = int(pokemon.current_hp)
                max_hp = pokemon.stats["HP"]
                curr_hp_str = f"{curr_hp:>3}" if curr_hp <= 999 else "???"
                max_hp_str = f"{max_hp:>3}" if max_hp <= 999 else "???"
                hp_text = f"HP{curr_hp_str}/{max_hp_str}"

                f_hp = curr_hp / max_hp if max_hp > 0 else 0.0
                if f_hp > 0.50:
                    hp_color = "\033[92m"  #Green
                elif f_hp >= 0.20:
                    hp_color = "\033[93m"  #Yellow
                else:
                    hp_color = "\033[91m"  #Red
                hp_gauge = self.make_gauge(f_hp, hp_color, length=7)
                rows.append(f"{b_color}│{b_reset}{hp_text}{hp_gauge}{b_color}│{b_reset}")

                #Line 3: PP (9) + PP gauge (7)
                curr_pp = pokemon.current_pp
                max_pp = pokemon.max_pp
                curr_pp_str = f"{curr_pp:>3}" if curr_pp <= 999 else "???"
                max_pp_str = f"{max_pp:>3}" if max_pp <= 999 else "???"
                pp_text = f"PP{curr_pp_str}/{max_pp_str}"

                f_pp = curr_pp / max_pp if max_pp > 0 else 0.0
                pp_gauge = self.make_gauge(f_pp, "\033[96m", length=7)  #Light blue
                rows.append(f"{b_color}│{b_reset}{pp_text}{pp_gauge}{b_color}│{b_reset}")

                #Line 4: EXP (9) + EXP gauge (7)
                if level >= 99:
                    rem_exp = 0
                    f_exp = 1.0
                else:
                    req_curr = pokemon.get_experience_required_for_level(level)
                    req_next = pokemon.get_experience_required_for_level(level + 1)
                    span = req_next - req_curr
                    progress = pokemon.experience - req_curr
                    f_exp = progress / span if span > 0 else 0.0
                    rem_exp = req_next - pokemon.experience

                rem_exp_str = f"{rem_exp:>6,}" if rem_exp <= 99999 else f"{'??,???':>6}"
                exp_text = f"EXP{rem_exp_str}"
                exp_gauge = self.make_gauge(f_exp, "\033[34m", length=7)  #Dark blue
                rows.append(f"{b_color}│{b_reset}{exp_text}{exp_gauge}{b_color}│{b_reset}")

                #Line 5: Hunger/Belly (9) + Belly gauge (7)
                import math
                pct = math.ceil((pokemon.current_belly / pokemon.max_belly) * 100.0) if pokemon.max_belly > 0 else 0
                pct = max(0, pct)
                belly_text = f"Belly{pct:>3}%"

                f_belly = pokemon.current_belly / pokemon.max_belly if pokemon.max_belly > 0 else 0.0
                if pokemon.current_belly > pokemon.max_belly:
                    belly_color = "\033[97m"  #White
                elif pct <= 10:
                    belly_color = "\033[91m"  #Red
                elif pct <= 20:
                    belly_color = "\033[93m"  #Yellow
                else:
                    belly_color = "\033[90m"  #Gray
                belly_gauge = self.make_gauge(f_belly, belly_color, length=7)
                rows.append(f"{b_color}│{b_reset}{belly_text}{belly_gauge}{b_color}│{b_reset}")

                #Line 6: Status effects
                status_items = []
                if pokemon.status_effects.get("Sleep", 0) > 0:
                    status_items.append(("Sleep", "negative"))
                if pokemon.status_effects.get("Resting", 0) > 0:
                    status_items.append(("Resting", "negative"))
                if pokemon.status_effects.get("Frozen", 0) > 0:
                    status_items.append(("Frozen", "negative"))
                if pokemon.status_effects.get("Petrified", 0) > 0 or pokemon.status_effects.get("Petrified") == -1:
                    status_items.append(("Petrified", "negative"))
                if pokemon.status_effects.get("Paralysis", 0) > 0:
                    status_items.append(("Paralysis", "negative"))
                if pokemon.status_effects.get("Toxic"):
                    status_items.append(("Toxic", "negative"))
                elif pokemon.status_effects.get("Poison"):
                    status_items.append(("Poison", "negative"))
                if pokemon.status_effects.get("Burn"):
                    status_items.append(("Burn", "negative"))
                if pokemon.status_effects.get("Flinch", 0) > 0:
                    status_items.append(("Flinch", "negative"))
                if pokemon.status_effects.get("Confusion", 0) > 0:
                    status_items.append(("Confusion", "negative"))
                if pokemon.status_effects.get("Puppet", 0) > 0:
                    status_items.append(("Puppet", "negative"))
                if pokemon.status_effects.get("Terrified", 0) > 0:
                    status_items.append(("Terrified", "negative"))
                if pokemon.status_effects.get("Leech Seed", 0) > 0:
                    status_items.append(("Leech Seed", "negative"))
                if pokemon.status_effects.get("Stuck", 0) > 0:
                    status_items.append(("Stuck", "negative"))
                if pokemon.status_effects.get("Wrap", 0) > 0:
                    status_items.append(("Wrapped", "negative"))
                if pokemon.status_effects.get("Sand Tomb", 0) > 0:
                    status_items.append(("Sand Tomb", "negative"))
                if pokemon.status_effects.get("Fire Spin", 0) > 0:
                    status_items.append(("Fire Spin", "negative"))
                if pokemon.status_effects.get("Protect", 0) > 0:
                    status_items.append(("Protect", "positive"))
                if pokemon.status_effects.get("Wide Guard", 0) > 0:
                    status_items.append(("Wide Guard", "positive"))
                if pokemon.status_effects.get("Quick Guard", 0) > 0:
                    status_items.append(("Quick Guard", "positive"))
                if pokemon.status_effects.get("Laser Focus"):
                    status_items.append(("Laser Focus", "positive"))
                if pokemon.status_effects.get("Safeguard", 0) > 0:
                    status_items.append(("Safeguard", "positive"))
                if pokemon.status_effects.get("Focus Energy", 0) > 0:
                    status_items.append(("Focus Energy", "positive"))
                if pokemon.status_effects.get("Counter", 0) > 0:
                    status_items.append(("Counter", "positive"))
                if pokemon.status_effects.get("Mirror Coat", 0) > 0:
                    status_items.append(("Mirror Coat", "positive"))
                if pokemon.status_effects.get("Reflect", 0) > 0:
                    status_items.append(("Reflect", "positive"))
                if pokemon.status_effects.get("Light Screen", 0) > 0:
                    status_items.append(("Light Screen", "positive"))
                if pokemon.status_effects.get("Sleepless"):
                    status_items.append(("Sleepless", "neutral"))
                if pokemon.status_effects.get("Digging", 0) > 0:
                    status_items.append(("Dig", "neutral"))
                if pokemon.status_effects.get("Diving", 0) > 0:
                    status_items.append(("Dive", "neutral"))
                if pokemon.status_effects.get("Encore", 0) > 0:
                    status_items.append(("Encore", "negative"))
                if pokemon.status_effects.get("Magnet Rise", 0) > 0:
                    status_items.append(("Magnet Rise", "positive"))
                if pokemon.status_effects.get("Telekinesis", 0) > 0:
                    status_items.append(("Telekinesis", "positive"))
                if pokemon.status_effects.get("Resting", 0) > 0:
                    status_items.append(("Resting", "neutral"))
                if pokemon.status_effects.get("Drowsy", 0) > 0:
                    status_items.append(("Drowsy", "negative"))
                if pokemon.status_effects.get("Curse"):
                    status_items.append(("Cursed", "negative"))
                if pokemon.status_effects.get("Lock-On"):
                    status_items.append(("Locked On", "positive"))
                if pokemon.status_effects.get("Aqua Ring"):
                    status_items.append(("Aqua Ring", "positive"))
                if pokemon.status_effects.get("Blind", 0) > 0:
                    status_items.append(("Blind", "negative"))
                if pokemon.status_effects.get("Sluggish", 0) > 0:
                    status_items.append(("Sluggish", "negative"))
                if pokemon.status_effects.get("Paused", 0) > 0:
                    status_items.append(("Recharging", "negative"))
                if pokemon.status_effects.get("Ingrain", 0) > 0:
                    status_items.append(("Ingrain", "neutral"))
                if pokemon.status_effects.get("Landed", 0) > 0:
                    status_items.append(("Landed", "neutral"))
                if pokemon.status_effects.get("Friendly"):
                    status_items.append(("Friendly", "positive"))
                if pokemon.status_effects.get("EXP Up"):
                    status_items.append(("EXP Up", "positive"))
                if pokemon.status_effects.get("Snatch", 0) > 0:
                    status_items.append(("Snatch", "positive"))
                if pokemon.status_effects.get("Rebound", 0) > 0:
                    status_items.append(("Rebound", "positive"))
                if pokemon.status_effects.get("Invisible", 0) > 0:
                    status_items.append(("Invisible", "positive"))
                if pokemon.status_effects.get("Cowering", 0) > 0:
                    status_items.append(("Cowering", "negative"))
                if pokemon.status_effects.get("Silenced", 0) > 0:
                    status_items.append(("Silenced", "negative"))
                for res_t in ("Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy", "Normal", "All"):
                    if pokemon.status_effects.get(f"{res_t} Resist"):
                        status_items.append((f"{res_t} Res", "positive"))

                spd_stage = pokemon.movement_speed_stage
                if spd_stage == -1:
                    status_items.append(("Slow", "negative"))
                elif spd_stage == 1:
                    status_items.append(("2x Speed", "positive"))
                elif spd_stage == 2:
                    status_items.append(("3x Speed", "positive"))
                elif spd_stage == 3:
                    status_items.append(("4x Speed", "positive"))

                #Format colors based on category: positive (green), negative (red), neutral (white)
                #Display only 1 status effect at a time on the 6th line, cycling once per second if multiple
                if not status_items:
                    status_text = " " * 16
                else:
                    import time
                    cycle_idx = int(time.time()) % len(status_items)
                    name, category = status_items[cycle_idx]

                    if category == "positive":
                        color_code = "\033[92m"  #Green
                    elif category == "negative":
                        color_code = "\033[91m"  #Red
                    else:
                        color_code = "\033[97m"  #White

                    visible_name = name[:16]
                    visible_len = len(visible_name)
                    padding_spaces = 16 - visible_len
                    status_text = f"{color_code}{visible_name}\033[0m" + (" " * padding_spaces)

                rows.append(f"{b_color}│{b_reset}{status_text}{b_color}│{b_reset}")

                rows.append(f"{b_color}└" + "─" * 16 + f"┘{b_reset}")
        return self.sanitize_rendered_rows(rows)

    def make_gauge(self, fraction: float, color_code: str, length: int = 7) -> str:
        """Creates a variable-length gauge using █ and ▌, colored with color_code"""
        fraction = max(0.0, min(1.0, fraction))
        halves = int(fraction * (length * 2))
        if fraction > 0.0 and halves == 0:
            halves = 1
        full = halves // 2
        half = halves % 2
        spaces = length - full - half
        gauge_str = "█" * full + "▌" * half + " " * spaces
        if getattr(self, "compatibility_mode", False):
            return gauge_str
        return f"{color_code}{gauge_str}\033[0m"

    def prompt_forget_and_learn_move(self, pokemon: Pokemon, move_info: dict):
        """Adds a move replacement prompt to the queue"""
        self.move_replacement_queue.append((pokemon, move_info))

    def render_move_replacement_screen(self, pokemon: Pokemon, new_move: dict) -> list[str]:
        """Renders the window that appears when a Pokémon learns a move while not having any free move slots."""
        import textwrap
        interior = []
        interior.append("")
        interior.append(f"{pokemon.name} wants to learn the move {new_move['name']}!")
        interior.append("But it already knows four moves.")
        interior.append("Should a move be forgotten to make room for this move?")
        interior.append("─" * 74)
        interior.append(" Current Moves:")

        poke_types = pokemon.types
        acc_stage = pokemon.stat_modifiers.get("Accuracy", 0)
        acc_stage = max(-6, min(6, acc_stage))
        if acc_stage >= 0:
            acc_mult = (3.0 + acc_stage) / 3.0
        else:
            acc_mult = 3.0 / (3.0 + abs(acc_stage))

        slots = ["Z", "X", "C", "V"]
        for idx, m in enumerate(pokemon.moves[:4]):
            slot_char = slots[idx]
            m_name = m["name"]
            m_type = m["type"]
            m_cat = m["category"]

            #Features ported from the move window of the summary screen.
            #STAB calculation and yellow highlight
            if m.get("power") is not None:
                base_pwr = m["power"]
                if m_type in poke_types:
                    stab_pwr = round(base_pwr * 1.5)
                    pwr_str = f"\033[93m{stab_pwr:<4}\033[0m"
                else:
                    pwr_str = f"{base_pwr:<4}"
            else:
                pwr_str = f"{'--':<4}"

            #Accuracy calculation & stage color coding
            if m.get("accuracy") is not None:
                base_acc = m["accuracy"]
                mod_acc = round(base_acc * acc_mult)
                acc_val_str = f"{mod_acc}%"
                if acc_stage > 0:
                    acc_str = f"\033[91m{acc_val_str:<5}\033[0m"
                elif acc_stage < 0:
                    acc_str = f"\033[94m{acc_val_str:<5}\033[0m"
                else:
                    acc_str = f"{acc_val_str:<5}"
            else:
                acc_str = f"{'--':<5}"

            #Color-coded move type and category
            m_type_color = TYPE_COLORS.get(m_type, "\033[37m")
            m_cat_color = "\033[91m" if m_cat == "Physical" else ("\033[94m" if m_cat == "Special" else "\033[90m")
            type_cat_str = f"{m_type_color}{m_type}\033[0m / {m_cat_color}{m_cat}\033[0m"

            interior.append(f"  [{slot_char}] • {m_name} ({type_cat_str})")
            interior.append(f"      Power: {pwr_str}  Accuracy: {acc_str}  PP Cost: {m['pp_cost']}")
            m_desc = m.get("description", "")
            wrapped = textwrap.wrap(m_desc, width=64)
            interior.append(f"      {wrapped[0]}" if wrapped else "      ")
            interior.append("") #spacer

        interior.append("─" * 74)
        interior.append(f" Move to Learn:")

        #New move STAB, accuracy & color coding
        new_name = new_move["name"]
        new_type = new_move["type"]
        new_cat = new_move["category"]

        if new_move.get("power") is not None:
            base_pwr = new_move["power"]
            if new_type in poke_types:
                stab_pwr = round(base_pwr * 1.5)
                pwr_str = f"\033[93m{stab_pwr:<4}\033[0m"
            else:
                pwr_str = f"{base_pwr:<4}"
        else:
            pwr_str = f"{'--':<4}"

        if new_move.get("accuracy") is not None:
            base_acc = new_move["accuracy"]
            mod_acc = round(base_acc * acc_mult)
            acc_val_str = f"{mod_acc}%"
            if acc_stage > 0:
                acc_str = f"\033[91m{acc_val_str:<5}\033[0m"
            elif acc_stage < 0:
                acc_str = f"\033[94m{acc_val_str:<5}\033[0m"
            else:
                acc_str = f"{acc_val_str:<5}"
        else:
            acc_str = f"{'--':<5}"

        new_type_color = TYPE_COLORS.get(new_type, "\033[37m")
        new_cat_color = "\033[91m" if new_cat == "Physical" else ("\033[94m" if new_cat == "Special" else "\033[90m")
        new_type_cat_str = f"{new_type_color}{new_type}\033[0m / {new_cat_color}{new_cat}\033[0m"

        interior.append(f"      • {new_name} ({new_type_cat_str})")
        interior.append(f"      Power: {pwr_str}  Accuracy: {acc_str}  PP Cost: {new_move['pp_cost']}")
        m_desc = new_move.get("description", "")
        wrapped = textwrap.wrap(m_desc, width=64)
        interior.append(f"      {wrapped[0]}" if wrapped else "      ")

        interior.append("─" * 74)

        #Pad interior lines to exactly 46 rows minus footer and border
        while len(interior) < 45:
            interior.append("")

        interior.append("[Z][X][C][V] Replace Move   [Esc] Keep Current Moves")

        rows = []
        rows.append("┌" + "─" * 74 + "┐")
        for line in interior[:46]:
            padded = self.pad_ansi_string(line, 74)
            rows.append(f"│{padded}│")
        rows.append("└" + "─" * 74 + "┘")
        return self.sanitize_rendered_rows(rows)

    def render_mimic_selection_screen(self, user: Pokemon, target: Pokemon) -> list[str]:
        """Renders the move selection window for Mimic"""
        import textwrap
        interior = []
        interior.append("")
        interior.append(f"Select a move to copy from {target.name}.")
        interior.append("─" * 74)
        interior.append(f"{target.name}'s Moves:")
        
        BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
        known_names = {m["name"] for m in user.moves}
        slots = ["Z", "X", "C", "V"]
        for idx, m in enumerate(target.moves[:4]):
            slot_char = slots[idx]
            pwr_str = str(m["power"]) if m.get("power") is not None else "--"
            acc_str = f"{m['accuracy']}%" if m.get("accuracy") is not None else "--"
            
            status_suffix = ""
            if m["name"] in BLACKLIST_COPIABLE:
                status_suffix = " (Can't copy)"
            elif m["name"] in known_names:
                status_suffix = " (Already known)"
                
            interior.append(f"  [{slot_char}] • {m['name']} ({m['type']} / {m['category']}){status_suffix}")
            interior.append(f"      Power: {pwr_str:<4}  Accuracy: {acc_str:<5}  PP Cost: {m['pp_cost']}")
            m_desc = m.get("description", "")
            wrapped = textwrap.wrap(m_desc, width=64)
            interior.append(f"      {wrapped[0]}" if wrapped else "      ")
            interior.append("") #spacer
            
        interior.append("─" * 74)
        
        #Pad interior lines to exactly 46 rows before footer and border
        while len(interior) < 45:
            interior.append("")
            
        interior.append("[Z][X][C][V] Copy move")
        
        rows = []
        rows.append("┌" + "─" * 74 + "┐")
        for line in interior[:46]:
            padded = self.pad_ansi_string(line, 74)
            rows.append(f"│{padded}│")
        rows.append("└" + "─" * 74 + "┘")
        return self.sanitize_rendered_rows(rows)

    def render_inventory_screen(self) -> list[str]:
        """Renders the inventory screen"""
        import textwrap
        interior = []
        interior.append("                                                                  Capacity")
        capacity_str = f"{len(self.inventory)}/{self.max_inventory_capacity}"
        left_text = "  Toolbox"
        right_margin = f"{capacity_str}  "
        spaces_needed = 74 - len(left_text) - len(right_margin)
        toolbox_line = left_text + " " * spaces_needed + right_margin
        interior.append(toolbox_line)
        interior.append("─" * 74)
        
        #If inventory is empty
        if not self.inventory:
            interior.append("  \033[90m(no items)\033[0m")
        else:
            state = self.inventory_state
            assert state is not None
            selected_idx = state["selected_index"]
            for idx, item in enumerate(self.inventory):
                item_name = items.get_item_display_name(item)
                rarity = item.get("rarity", "Common")
                r_color = items.RARITY_COLORS.get(rarity, "\033[37m")
                if idx == selected_idx:
                    item_line = f"\033[94m► \033[0m{r_color}{item_name}\033[0m"
                else:
                    item_line = f"  {r_color}{item_name}\033[0m"
                
                right_text = ""
                if state["context_menu"] is not None:
                    menu = state["context_menu"]
                    context_idx = state["context_index"]
                    if 0 <= idx < len(menu) + 2:
                        if idx == 0:
                            right_text = "┌" + "─" * 21 + "┐"
                        elif idx == len(menu) + 1:
                            right_text = "└" + "─" * 21 + "┘"
                        else:
                            menu_item_idx = idx - 1
                            menu_item = menu[menu_item_idx]
                            if menu_item_idx == context_idx:
                                right_text = f"│ \033[94m> {menu_item:<17}\033[0m │"
                            else:
                                right_text = f"│   {menu_item:<17} │"
                
                left_part = self.pad_ansi_string(item_line, 45)
                right_part = self.pad_ansi_string(right_text, 26)
                interior.append(left_part + "   " + right_part)
                
        while len(interior) < 42:
            idx = len(interior) - 3
            right_text = ""
            state = self.inventory_state
            if state and state["context_menu"] is not None:
                menu = state["context_menu"]
                context_idx = state["context_index"]
                if 0 <= idx < len(menu) + 2:
                    if idx == 0:
                        right_text = "┌" + "─" * 21 + "┐"
                    elif idx == len(menu) + 1:
                        right_text = "└" + "─" * 21 + "┘"
                    else:
                        menu_item_idx = idx - 1
                        menu_item = menu[menu_item_idx]
                        if menu_item_idx == context_idx:
                            right_text = f"│ \033[94m> {menu_item:<17}\033[0m │"
                        else:
                            right_text = f"│   {menu_item:<17} │"
            left_part = " " * 45
            right_part = self.pad_ansi_string(right_text, 26)
            interior.append(left_part + "   " + right_part)
            
        interior.append("─" * 74)
        
        state = self.inventory_state
        if self.inventory and state:
            sel_item = self.inventory[state["selected_index"]]
            rarity = sel_item.get("rarity", "Common")
            r_color = items.RARITY_COLORS.get(rarity, "\033[37m")
            desc = sel_item.get("description", "")
            wrapped = textwrap.wrap(desc, width=70)
            desc_1 = wrapped[0] if len(wrapped) > 0 else ""
            desc_2 = wrapped[1] if len(wrapped) > 1 else ""
            interior.append(f"  {r_color}Rarity: {rarity}\033[0m")
            interior.append(f"  {desc_1}")
            interior.append(f"  {desc_2}")
        else:
            interior.append("  No item selected.")
            interior.append("")
            interior.append("")
            
        rows = []
        rows.append("┌" + "─" * 74 + "┐")
        for line in interior[:46]:
            padded = self.pad_ansi_string(line, 74)
            rows.append(f"│{padded}│")
        rows.append("└" + "─" * 74 + "┘")
        return self.sanitize_rendered_rows(rows)

    def render_message_history_screen(self) -> list[str]:
        """Renders the message history screen"""
        lines = self.message_log.get_history_lines(max_width=72)
        max_visible = 42
        max_scroll = max(0, len(lines) - max_visible)

        state = getattr(self, "message_history_state", None)
        if state is None:
            scroll = max_scroll
        else:
            scroll = max(0, min(max_scroll, state.get("scroll", max_scroll)))

        msg_count = len(self.message_log.raw_messages)

        rows = []
        rows.append("┌" + "─" * 74 + "┐")

        title = "  Message History"
        spaces_needed = 74 - len(title)
        header_text = title
        rows.append(f"│{self.pad_ansi_string(header_text, 74)}│")

        rows.append("│" + "─" * 74 + "│")

        visible_lines = lines[scroll : scroll + max_visible]
        for i in range(max_visible):
            if i < len(visible_lines):
                line_str = f"  {visible_lines[i]}"
            else:
                line_str = ""
            padded = self.pad_ansi_string(line_str, 74)
            rows.append(f"│{padded}│")

        rows.append("│" + "─" * 74 + "│")

        footer_text = "  [↑/↓/2/8] Scroll  |  [Esc] Return to game"
        padded_footer = self.pad_ansi_string(footer_text, 74)
        rows.append(f"│{padded_footer}│")

        rows.append("└" + "─" * 74 + "┘")

        while len(rows) < 48:
            rows.append(" " * 76)
        return self.sanitize_rendered_rows(rows[:48])

    def render_full_screen_status(self) -> list[str]:
        """Renders the Pokémon status screen."""
        pokemon = self.active_status_pokemon
        if not pokemon:
            return [" " * 76] * 48

        #Calculate EXP progress
        level = pokemon.level
        if level >= 99:
            rem_exp = 0
            f_exp = 1.0
        else:
            req_curr = pokemon.get_experience_required_for_level(level)
            req_next = pokemon.get_experience_required_for_level(level + 1)
            span = req_next - req_curr
            progress = pokemon.experience - req_curr
            f_exp = progress / span if span > 0 else 0.0
            rem_exp = req_next - pokemon.experience

        #Calculate Belly %
        import math
        pct = math.ceil((pokemon.current_belly / pokemon.max_belly) * 100.0) if pokemon.max_belly > 0 else 0.0
        pct = max(0.0, pct)
        f_belly = pokemon.current_belly / pokemon.max_belly if pokemon.max_belly > 0 else 0.0

        #Calculate HP %
        max_hp = pokemon.stats["HP"]
        curr_hp = int(pokemon.current_hp)
        f_hp = pokemon.current_hp / max_hp if max_hp > 0 else 0.0

        #Calculate PP %
        max_pp = getattr(pokemon, "max_pp", 100)
        curr_pp = getattr(pokemon, "current_pp", 100)
        f_pp = curr_pp / max_pp if max_pp > 0 else 0.0

        #Init dynamic interior lines list
        interior = []

        #1. Title Block (Name, Level, ypes, and Pokémon ID No.). Name is in yellow when ready to evolve.
        types = pokemon.types
        formatted_types = " / ".join(f"{TYPE_COLORS.get(t, '\033[37m')}{t}\033[0m" for t in types)
        types_str = f" [{formatted_types}]" if types else ""
        can_evolve = hasattr(pokemon, "can_evolve") and pokemon.can_evolve(game=self)
        name_display = f"\033[93m{pokemon.name}\033[0m" if can_evolve else pokemon.name
        left_text = f" {name_display} (Level {pokemon.level}){types_str}"

        poke_id = pokemon.species_data.get("id") if getattr(pokemon, "species_data", None) else None
        if poke_id is not None:
            try:
                id_num = int(poke_id)
                id_str = f"No. {id_num:03d}"
            except (ValueError, TypeError):
                id_str = f"No. {poke_id}"
        else:
            id_str = "Error!"

        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
        vis_left_len = len(ansi_escape.sub('', left_text))
        vis_right_len = len(id_str)
        spaces_needed = max(1, 74 - vis_left_len - vis_right_len - 1)
        title_line = f"{left_text}{' ' * spaces_needed}{id_str} "
        interior.append(title_line)
        interior.append("─" * 74)

        #2. Gauges block for HP, PP, EXP and Belly
        if f_hp > 0.50:
            hp_color = "\033[92m"  #Green
        elif f_hp >= 0.20:
            hp_color = "\033[93m"  #Yellow
        else:
            hp_color = "\033[91m"  #Red
        hp_gauge_str = self.make_gauge(f_hp, hp_color, length=47)
        pp_gauge_str = self.make_gauge(f_pp, "\033[96m", length=47)
        exp_gauge_str = self.make_gauge(f_exp, "\033[94m", length=47)
        if f_belly > 1:
            belly_color = "\033[97m" #White
        elif f_belly > 0.2:
            belly_color = "\033[90m" #Gray
        elif f_belly > 0.1:
            belly_color = "\033[93m" #Yellow
        else:
            belly_color = "\033[91m" #Red
        belly_gauge_str = self.make_gauge(f_belly, belly_color, length=47)

        hp_val_str = f"{curr_hp:>5,}/{max_hp:>5,}"
        pp_val_str = f"{curr_pp:>5,}/{max_pp:>5,}"
        exp_val_str = f"{pokemon.experience:>9,} (Next:{rem_exp:>6,})"
        belly_val_str = f"{int(pct)}%"

        interior.append(f" HP{hp_val_str:<17}       {hp_gauge_str}")
        interior.append(f" PP{pp_val_str:<17}       {pp_gauge_str}")
        interior.append(f" EXP{exp_val_str:<17}{exp_gauge_str}")
        interior.append(f" Belly   {belly_val_str:<16}  {belly_gauge_str}")
        interior.append("─" * 74)

        #3. Description Block
        interior.append(" Description:")
        desc = pokemon.species_data.get("description", "")
        import textwrap
        wrapped_desc = textwrap.wrap(desc, width=70)
        for line in wrapped_desc:
            interior.append(f"   {line}")
        interior.append("─" * 74)

        #4. Stats Table (with stage change arrows on the right)
        interior.append(" Stats:")
        interior.append("                                  │Value│ Eff.│ EVs │IVs")
        interior.append("                      ────────────┼─────┼─────┼─────┼───")
        
        stat_configs = [
            ("HP", "HP"),
            ("Attack", "Attack"),
            ("Sp. Attack", "Special_Attack"),
            ("Defense", "Defense"),
            ("Sp.Defense", "Special_Defense"),
            ("Speed", "Speed")
        ]
        for label, key in stat_configs:
            val = pokemon.stats[key]
            eff = int(pokemon.current_hp) if key == "HP" else pokemon.get_modified_stat(key, game=self)
            ev = pokemon.evs[key]
            iv = pokemon.ivs[key]

            #Stage change arrows (up to max 6) to the right outside of table
            stage = pokemon.stat_modifiers.get(key, 0) if key != "HP" else 0
            if stage > 0:
                arrow_cnt = min(6, stage)
                arrows = f"\033[91m{'↑' * arrow_cnt}\033[0m"
            elif stage < 0:
                arrow_cnt = min(6, abs(stage))
                arrows = f"\033[94m{'↓' * arrow_cnt}\033[0m"
            else:
                arrows = ""

            #Color effective stat values red if above normal, blue if below
            eff_val_str = f"{eff:>5,}"
            if eff > val:
                eff_str = f"\033[91m{eff_val_str}\033[0m"
            elif eff < val:
                eff_str = f"\033[94m{eff_val_str}\033[0m"
            else:
                eff_str = eff_val_str

            #Color IV values red if 31, blue if 0
            iv_val_str = f"{iv:>2}"
            if iv == 31:
                iv_str = f"\033[91m{iv_val_str}\033[0m"
            elif iv == 0:
                iv_str = f"\033[94m{iv_val_str}\033[0m"
            else:
                iv_str = iv_val_str

            interior.append(f"                       {label:<10} │{val:>5,}│{eff_str}│{ev:>5,}│ {iv_str}  {arrows}")
        interior.append("─" * 74)

        #5. Known Moves (dynamically affected by stat changes and STAB)
        interior.append(" Known Moves:")
        poke_types = pokemon.types
        acc_stage = pokemon.stat_modifiers.get("Accuracy", 0)
        acc_stage = max(-6, min(6, acc_stage))
        if acc_stage >= 0:
            acc_mult = (3.0 + acc_stage) / 3.0
        else:
            acc_mult = 3.0 / (3.0 + abs(acc_stage))

        move_hotkeys = ["Z", "X", "C", "V"]
        is_leader = (pokemon == self.player_pokemon or getattr(pokemon, "is_leader", False))

        for idx, m in enumerate(pokemon.moves[:4]):
            m_name = m["name"]
            m_type = m["type"]
            m_cat = m["category"]
            hk_tag = f"[{move_hotkeys[idx]}] " if idx < len(move_hotkeys) else ""
            is_disabled = not m.get("enabled", True) and not is_leader

            if is_disabled:
                base_pwr = m["power"] if m.get("power") is not None else "--"
                base_acc = f"{m['accuracy']}%" if m.get("accuracy") is not None else "--"
                m_desc = m.get("description", "")
                wrapped_m_desc = textwrap.wrap(m_desc, width=68)

                interior.append(f"\033[90m   • {hk_tag}{m_name} ({m_type} / {m_cat})\033[0m")
                interior.append(f"\033[90m     Power: {base_pwr:<4}  Accuracy: {base_acc:<5}  PP Cost: {m['pp_cost']}\033[0m")
                if wrapped_m_desc:
                    for dline in wrapped_m_desc:
                        interior.append(f"\033[90m     {dline}\033[0m")
                else:
                    interior.append("\033[90m     \033[0m")
            else:
                #STAB calculation and highlight
                if m.get("power") is not None:
                    base_pwr = m["power"]
                    if m_type in poke_types:
                        stab_pwr = round(base_pwr * 1.5)
                        pwr_str = f"\033[93m{stab_pwr:<4}\033[0m"
                    else:
                        pwr_str = f"{base_pwr:<4}"
                else:
                    pwr_str = f"{'--':<4}"

                #Accuracy calculation & stage color coding (red if boosted, blue if decreased)
                if m.get("accuracy") is not None:
                    base_acc = m["accuracy"]
                    mod_acc = round(base_acc * acc_mult)
                    acc_val_str = f"{mod_acc}%"
                    if acc_stage > 0:
                        acc_str = f"\033[91m{acc_val_str:<5}\033[0m"
                    elif acc_stage < 0:
                        acc_str = f"\033[94m{acc_val_str:<5}\033[0m"
                    else:
                        acc_str = f"{acc_val_str:<5}"
                else:
                    acc_str = f"{'--':<5}"

                #Color-coded move type and category
                m_type_color = TYPE_COLORS.get(m_type, "\033[37m")
                m_cat_color = "\033[91m" if m_cat == "Physical" else ("\033[94m" if m_cat == "Special" else "\033[90m")
                type_cat_str = f"{m_type_color}{m_type}\033[0m / {m_cat_color}{m_cat}\033[0m"

                interior.append(f"   • {hk_tag}{m_name} ({type_cat_str})")
                interior.append(f"     Power: {pwr_str}  Accuracy: {acc_str}  PP Cost: {m['pp_cost']}")
                m_desc = m.get("description", "")
                wrapped_m_desc = textwrap.wrap(m_desc, width=68)
                if wrapped_m_desc:
                    for dline in wrapped_m_desc:
                        interior.append(f"     {dline}")
                else:
                    interior.append("     ")

        interior.append("─" * 74)

        #6. Next Level Up Move
        candidates = [item for item in pokemon.species_data["level_up_moves"] if item[0] > pokemon.level]
        if candidates:
            min_lvl = min(item[0] for item in candidates)
            next_moves = [item[1] for item in candidates if item[0] == min_lvl]
            next_move_str = f"{', '.join(next_moves)} at Level {min_lvl}"
        else:
            next_move_str = "No more"
        interior.append(f" Next move: {next_move_str}")
        
        evolutions = pokemon.species_data.get("evolutions", [])
        if evolutions:
            for idx, evo in enumerate(evolutions):
                target = evo.get("to", "Unknown")
                min_lvl = evo.get("min_level", evo.get("level"))
                req_item = evo.get("item", evo.get("evolution_item"))
                if min_lvl is not None and req_item is not None:
                    part = f"Evolves into {target} at Level {min_lvl} using {req_item}"
                elif min_lvl is not None:
                    part = f"Evolves into {target} at Level {min_lvl}"
                elif req_item is not None:
                    part = f"Evolves into {target} using {req_item}"
                else:
                    part = f"Evolves into {target}"
                prefix = " Evolution: " if idx == 0 else "            "
                interior.append(f"{prefix}{part}")

        interior.append("─" * 74)

        #7. Status Effects
        status_line = self.get_status_line(pokemon, max_len=55)
        if not status_line:
            status_line = "None"
        interior.append(f" Status effects: {status_line}")
        interior.append("─" * 74)

        #8. Closing instructions
        opts = self.get_summary_context_menu_options(pokemon)
        has_opts = bool(opts)

        if is_leader:
            if has_opts:
                interior.append("[Return] Options   [↑/↓] Scroll   [Esc] Close")
            else:
                interior.append("[↑/↓] Scroll   [Esc] Close")
        else:
            if has_opts:
                interior.append("[Return] Options   [Z][X][C][V] Toggle Move   [↑/↓] Scroll   [Esc] Close")
            else: #This should never happen
                interior.append("[Z][X][C][V] Toggle Move   [↑/↓] Scroll   [Esc] Close")

        #Store total lines count for scroll clamping
        total_lines = len(interior)
        self._last_summary_total_lines = total_lines
        VIEWPORT_HEIGHT = 46
        max_offset = max(0, total_lines - VIEWPORT_HEIGHT)
        self.summary_scroll_offset = max(0, min(getattr(self, "summary_scroll_offset", 0), max_offset))

        visible_lines = interior[self.summary_scroll_offset : self.summary_scroll_offset + VIEWPORT_HEIGHT]

        can_scroll_up = self.summary_scroll_offset > 0
        can_scroll_down = (self.summary_scroll_offset + VIEWPORT_HEIGHT) < total_lines

        rows = []
        if can_scroll_up:
            rows.append("┌" + "─" * 73 + "\033[92m↑\033[0m")
        else:
            rows.append("┌" + "─" * 74 + "┐")

        for line in visible_lines:
            padded = self.pad_ansi_string(line, 74)
            rows.append(f"│{padded}│")

        while len(rows) < 47:
            rows.append("│" + " " * 74 + "│")

        if can_scroll_down:
            rows.append("└" + "─" * 73 + "\033[92m↓\033[0m")
        else:
            rows.append("└" + "─" * 74 + "┘")

        while len(rows) < 48:
            rows.append(" " * 76)
        rows = self.render_summary_context_menu_overlay(rows)
        return self.sanitize_rendered_rows(rows[:48])

    def get_move_windows_rows(self) -> list[str]:
        """Renders the move windows (the 4 windows at the bottom of the screen)"""
        moves = self.player_pokemon.moves[:4]
        slot_rows: list[list[str]] = [[] for _ in range(6)]

        for slot in range(4):
            move = moves[slot] if slot < len(moves) else None

            #Determine border color prefix and reset suffix
            if move is None:
                border_prefix = "\033[90m"  #Gray
                border_reset = "\033[0m"
            else:
                #Check if enough PP
                if self.player_pokemon.current_pp < move["pp_cost"]:
                    border_prefix = "\033[91m"  #Red
                    border_reset = "\033[0m"
                elif not self.player_pokemon.can_use_move(move, self):
                    border_prefix = "\033[95m"  #Pink / Magenta
                    border_reset = "\033[0m"
                else:
                    border_prefix = ""  #White/Standard
                    border_reset = ""

            #Build the 6 lines for this slot
            if move is None:
                #Empty slot
                t_b = f"{border_prefix}┌────────────┐{border_reset}"
                m_b = f"{border_prefix}│{border_reset}            {border_prefix}│{border_reset}"
                b_b = f"{border_prefix}└────────────┘{border_reset}"

                slot_rows[0].append(t_b)
                for r in range(1, 5):
                    slot_rows[r].append(m_b)
                slot_rows[5].append(b_b)
            else:
                #Line 0: Top border
                t_b = f"{border_prefix}┌────────────┐{border_reset}" if border_prefix else "┌────────────┐"
                slot_rows[0].append(t_b)

                #Line 1: Shortcut (green) on left, PP cost (light blue) on right
                keys = ["Z", "X", "C", "V"]
                shortcut_key = keys[slot]
                shortcut = f"\033[92m[{shortcut_key}]\033[0m"
                pp_cost_str = f"{move['pp_cost']} PP"
                pp_cost_formatted = f"\033[96m{pp_cost_str}\033[0m"
                spaces_line1 = 12 - 3 - len(pp_cost_str)
                line1_content = f"{shortcut}{' ' * spaces_line1}{pp_cost_formatted}"

                #Line 2 & 3: Wrapped, center-aligned name (max 12 characters per line)
                name = move["name"]
                words = name.split()
                lines = []
                current_line: list[str] = []
                current_len = 0
                for w in words:
                    space_len = 1 if current_line else 0
                    if current_len + space_len + len(w) > 12:
                        if current_line:
                            lines.append(" ".join(current_line))
                            current_line = [w]
                            current_len = len(w)
                        else:
                            lines.append(w[:12])
                            current_line = [w[12:]] if len(w) > 12 else []
                            current_len = len(w) - 12
                    else:
                        current_line.append(w)
                        current_len += space_len + len(w)
                if current_line:
                    lines.append(" ".join(current_line))

                lines = lines[:2]
                while len(lines) < 2:
                    lines.append("")

                line2_content = f"{lines[0]:^12}"
                line3_content = f"{lines[1]:^12}"

                #Line 4: Type (left) + Category (right)
                move_type = move["type"][:8]
                type_color = TYPE_COLORS.get(move_type, "\033[37m")

                cat = move["category"]
                if cat == "Physical":
                    cat_str = "Phys"
                    cat_color = "\033[91m"
                elif cat == "Special":
                    cat_str = "Spec"
                    cat_color = "\033[94m"
                else:
                    cat_str = "Stat"
                    cat_color = "\033[90m"

                spaces_line4 = 12 - len(move_type) - len(cat_str)
                spaces_line4 = max(0, spaces_line4)
                line4_content = f"{type_color}{move_type}\033[0m{' ' * spaces_line4}{cat_color}{cat_str}\033[0m"

                #Append wrap in borders
                left_border = f"{border_prefix}│{border_reset}" if border_prefix else "│"
                right_border = f"{border_prefix}│{border_reset}" if border_prefix else "│"

                slot_rows[1].append(f"{left_border}{line1_content}{right_border}")
                slot_rows[2].append(f"{left_border}{line2_content}{right_border}")
                slot_rows[3].append(f"{left_border}{line3_content}{right_border}")
                slot_rows[4].append(f"{left_border}{line4_content}{right_border}")

                #Line 5: Bottom border
                b_b = f"{border_prefix}└────────────┘{border_reset}" if border_prefix else "└────────────┘"
                slot_rows[5].append(b_b)

        return self.sanitize_rendered_rows(["".join(slot_rows[r]) for r in range(6)])

    def process_messages(self):
        """Processes and pages any pending messages in the log"""
        if not self.message_log.has_pending():
            return

        while self.message_log.has_pending():
            has_more = self.message_log.step_page()
            self.render()
            if has_more:
                game_input.get_key()
        self.message_log.has_more_page = False

    def run(self):
        """Main game event loop"""
        #Configure stdout to use UTF-8 representation
        reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
        if reconfigure_stdout is not None:
            try:
                reconfigure_stdout(encoding="utf-8")
            except Exception:
                pass

        #Hide text cursor
        try:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
            atexit.register(self._restore_cursor)
        except Exception:
            pass

        try:
            self._run_loop()
        except (KeyboardInterrupt, SystemExit):
            self.is_running = False
            raise
        except Exception as e:
            self.is_running = False
            try:
                from save_game import attempt_emergency_save
                self._emergency_save_path = attempt_emergency_save(self)
            except Exception:
                self._emergency_save_path = None
            raise
        finally:
            #Restore cursor on quit
            self._restore_cursor()

    def _run_loop(self):
        #Initial render/message processing
        if self.message_log.has_pending():
            self.process_messages()
        else:
            self.render()

        #Waiting for inputs
        while self.is_running:
            if getattr(self, "game_ended", False) or getattr(self, "game_won", False) or (self.player_pokemon is not None and int(self.player_pokemon.current_hp) <= 0):
                self.show_end_screen()
                continue

            if getattr(self, "disclaimer_screen_state", None) is not None:
                import time
                st = self.disclaimer_screen_state.get("start_time", time.time())
                dur = self.disclaimer_screen_state.get("duration", 5.0)
                elapsed = time.time() - st
                if elapsed >= dur:
                    self.transition_disclaimer_to_title()
                    continue

                remaining = max(0.05, dur - elapsed)
                try:
                    action = game_input.get_key(timeout=remaining)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break

                if action is not None:
                    self.transition_disclaimer_to_title()
                else:
                    if time.time() - st >= dur:
                        self.transition_disclaimer_to_title()
                    else:
                        self.render()
                continue

            if getattr(self, "title_screen_state", None) is not None:
                try:
                    action = game_input.get_key(timeout=None)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break
                if action is None:
                    continue
                self.handle_title_screen_input(action)
                continue

            if getattr(self, "starter_select_state", None) is not None:
                try:
                    if self.starter_select_state.get("sub_mode") == "naming":
                        char_in = game_input.get_char_input(timeout=None)
                        if char_in is not None:
                            self.handle_starter_naming_input(char_in)
                    else:
                        action = game_input.get_key(timeout=None)
                        if action is not None:
                            self.handle_starter_select_input(action)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break
                continue

            if getattr(self, "load_game_state", None) is not None:
                try:
                    action = game_input.get_key(timeout=None)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break
                if action is None:
                    continue
                self.handle_load_game_screen_input(action)
                continue

            if getattr(self, "high_scores_state", None) is not None:
                try:
                    action = game_input.get_key(timeout=None)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break
                if action is None:
                    continue
                self.handle_high_scores_screen_input(action)
                continue

            if getattr(self, "pause_menu_state", None) is not None:
                try:
                    action = game_input.get_key(timeout=None)
                except (StopIteration, RuntimeError):
                    self.is_running = False
                    break
                if action is None:
                    continue
                self.handle_pause_menu_input(action)
                continue

            if getattr(self, "replace_recruit_state", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                self.handle_replace_recruit_input(action)
                continue

            if getattr(self, "nickname_prompt_state", None) is not None:
                char_in = game_input.get_char_input(timeout=None)
                if char_in is None:
                    continue
                self.handle_nickname_input(char_in)
                continue

            if getattr(self, "message_history_state", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                self.handle_message_history_input(action)
                continue

            if getattr(self, "inventory_state", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                self.handle_inventory_input(action)
                continue

            if getattr(self, "waiting_for_throw_direction", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                self.handle_throw_input(action)
                continue

            if getattr(self, "waiting_for_orb_direction", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                self.handle_orb_direction_input(action)
                continue

            if getattr(self, "move_replacement_queue", None):
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                pokemon, new_move = self.move_replacement_queue[0]
                slot_index = None
                if action == game_input.USE_MOVE_1:
                    slot_index = 0
                elif action == game_input.USE_MOVE_2:
                    slot_index = 1
                elif action == game_input.USE_MOVE_3:
                    slot_index = 2
                elif action == game_input.USE_MOVE_4:
                    slot_index = 3
                
                if slot_index is not None:
                    old_move = pokemon.moves[slot_index]
                    new_move["enabled"] = True
                    pokemon.moves[slot_index] = new_move
                    self.log_message(f"{pokemon.name} forgot {old_move['name']} and learned {new_move['name']}!")
                    self.move_replacement_queue.pop(0)
                    self.render()
                elif action == game_input.QUIT:
                    self.log_message(f"{pokemon.name} did not learn {new_move['name']}.")
                    self.move_replacement_queue.pop(0)
                    self.render()
                continue

            if getattr(self, "mimic_selection_state", None) is not None:
                action = game_input.get_key(timeout=None)
                if action is None:
                    continue
                state = self.mimic_selection_state
                user = state["user"]
                target = state["target"]
                mimic_move = state["mimic_move"]
                slot = state["slot"]
                
                slot_index = None
                if action == game_input.USE_MOVE_1:
                    slot_index = 0
                elif action == game_input.USE_MOVE_2:
                    slot_index = 1
                elif action == game_input.USE_MOVE_3:
                    slot_index = 2
                elif action == game_input.USE_MOVE_4:
                    slot_index = 3
                elif action == game_input.QUIT:
                    self.log_message(f"But it failed!")
                    self.mimic_selection_state = None
                    self.on_turn_completed()
                    if self.message_log.has_pending():
                        self.process_messages()
                    else:
                        self.render()
                    continue
                
                if slot_index is not None and slot_index < len(target.moves):
                    selected_move = target.moves[slot_index]
                    BLACKLIST_COPIABLE = {"Assist", "Copycat", "Sketch", "Mimic", "Mirror Move", "Metronome", "Struggle", "Sleep Talk", "Snore"}
                    known_names = {m["name"] for m in user.moves}
                    if selected_move["name"] in BLACKLIST_COPIABLE:
                        self.log_message(f"{selected_move['name']} isn't copyable!")
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                    elif selected_move["name"] in known_names:
                        self.log_message(f"You already know {selected_move['name']}!")
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                    else:
                        copied_move = dict(selected_move)
                        user.moves[slot] = copied_move
                        user.mimic_original_state = {
                            "slot": slot,
                            "original_move": mimic_move,
                            "copied_move": copied_move
                        }
                        self.start_player_action()
                        self.log_message(f"{user.name} copied {selected_move['name']}!")
                        self.mimic_selection_state = None
                        self.on_turn_completed()
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                continue

            #If player has no actions left (e.g. when slowed), complete the turn automatically
            if self.player_actions_left <= 0:
                self.turn_in_progress = True
                self.on_turn_completed()
                self.turn_in_progress = False
                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            if self.process_charging_move(self.player_pokemon):
                self.start_player_action()
                self.on_turn_completed()
                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #Player moves automatically while a puppet
            if self.player_pokemon.status_effects.get("Puppet", 0) > 0:
                if not self.suppress_animation_delay:
                    import time
                    time.sleep(0.3)
                self.start_player_action()
                self.process_puppet_ai(self.player_pokemon)
                self.on_turn_completed()
                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #Check if any party member requires window flashing warnings
            needs_flash = False
            for member in self.party:
                hp_pct = member.current_hp / member.stats["HP"] if member.stats["HP"] > 0 else 0.0
                if hp_pct <= 0.20 or member.current_belly <= 0.0:
                    needs_flash = True
                    break

            if getattr(self, "active_status_pokemon", None) is not None:
                timeout = None
            else:
                timeout = 0.5 if (needs_flash or getattr(self, "look_around_mode", False)) else None
            self.party_start_positions = {p: get_pokemon_position(self, p) for p in self.party}
            action = game_input.get_key(timeout=timeout)

            if action is None:
                #Timeout occurred - re-render to update warning flashing states
                if getattr(self, "look_around_mode", False):
                    self.look_around_cursor_visible = not self.look_around_cursor_visible
                self.render()
                continue

            if getattr(self, "active_status_pokemon", None) is not None:
                context_state = getattr(self, "summary_context_menu_state", None)

                if context_state is not None:
                    mode = context_state.get("mode", "menu")
                    if mode == "menu":
                        options = context_state.get("options", [])
                        if action in (game_input.MOVE_UP, "w", "W", "up", "UP"):
                            context_state["selected_index"] = (context_state.get("selected_index", 0) - 1) % len(options)
                            self.render()
                            continue
                        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN"):
                            context_state["selected_index"] = (context_state.get("selected_index", 0) + 1) % len(options)
                            self.render()
                            continue
                        if action in (game_input.CONFIRM, "\r", "\n"):
                            sel_opt = options[context_state.get("selected_index", 0)]
                            if sel_opt == "Evolve":
                                target = self.active_status_pokemon
                                if target and target.can_evolve(game=self):
                                    eligible = target.get_eligible_evolutions(game=self)
                                    if len(eligible) == 1:
                                        target_sp = eligible[0]["to"]
                                        req_item = eligible[0].get("item", eligible[0].get("evolution_item"))
                                        target.evolve(target_sp, game=self, consumed_item_name=req_item)
                                        self.summary_context_menu_state = None
                                        self.render()
                                        continue
                                    elif len(eligible) > 1:
                                        context_state["mode"] = "evolve_select"
                                        context_state["options"] = [e["to"] for e in eligible]
                                        context_state["selected_index"] = 0
                                        self.render()
                                        continue
                            elif sel_opt == "Make Leader":
                                target = self.active_status_pokemon
                                if target and self.can_change_leader(target):
                                    for p in self.party:
                                        p.is_leader = False
                                    target.is_leader = True
                                    self.player_pokemon = target
                                    for m in target.moves:
                                        m["enabled"] = True
                                    if hasattr(target, "x") and hasattr(target, "y"):
                                        self.player_x = target.x
                                        self.player_y = target.y
                                    self.log_message(f"{target.name} became the leader!")
                                self.summary_context_menu_state = None
                                self.render()
                                continue
                            elif sel_opt == "Switch Places":
                                context_state["mode"] = "switch_places"
                                self.render()
                                continue
                            elif sel_opt == "Farewell":
                                context_state["mode"] = "farewell_confirm"
                                self.render()
                                continue
                        if action == game_input.QUIT:
                            self.summary_context_menu_state = None
                            self.render()
                            continue

                    elif mode == "evolve_select":
                        options = context_state.get("options", [])
                        if action in (game_input.MOVE_UP, "w", "W", "up", "UP"):
                            context_state["selected_index"] = (context_state.get("selected_index", 0) - 1) % len(options)
                            self.render()
                            continue
                        if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN"):
                            context_state["selected_index"] = (context_state.get("selected_index", 0) + 1) % len(options)
                            self.render()
                            continue
                        if action in (game_input.CONFIRM, "\r", "\n"):
                            target = self.active_status_pokemon
                            if target:
                                chosen_sp = options[context_state.get("selected_index", 0)]
                                eligible = target.get_eligible_evolutions(game=self)
                                req_item = None
                                for e in eligible:
                                    if e["to"] == chosen_sp:
                                        req_item = e.get("item", e.get("evolution_item"))
                                        break
                                target.evolve(chosen_sp, game=self, consumed_item_name=req_item)
                                self.summary_context_menu_state = None
                                self.render()
                                continue
                        if action == game_input.QUIT:
                            context_state["mode"] = "menu"
                            context_state["options"] = self.get_summary_context_menu_options(self.active_status_pokemon)
                            context_state["selected_index"] = 0
                            self.render()
                            continue

                    elif mode == "switch_places":
                        slot_map = {
                            game_input.STATUS_1: 0, "a": 0, "A": 0, "1": 0,
                            game_input.STATUS_2: 1, "s": 1, "S": 1, "2": 1,
                            game_input.STATUS_3: 2, "d": 2, "D": 2, "3": 2,
                            game_input.STATUS_4: 3, "f": 3, "F": 3, "4": 3,
                            game_input.STATUS_5: 4, "g": 4, "G": 4, "5": 4,
                            game_input.STATUS_6: 5, "h": 5, "H": 5, "6": 5,
                        }
                        chosen_idx = None
                        if action in slot_map:
                            chosen_idx = slot_map[action]

                        if chosen_idx is not None and chosen_idx < len(self.party):
                            poke1 = self.active_status_pokemon
                            if poke1 in self.party:
                                idx1 = self.party.index(poke1)
                                idx2 = chosen_idx
                                poke2 = self.party[idx2]
                                self.party[idx1], self.party[idx2] = self.party[idx2], self.party[idx1]
                                self.summary_context_menu_state = None
                                self.render()
                                continue
                        if action == game_input.QUIT:
                            context_state["mode"] = "menu"
                            self.render()
                            continue

                    elif mode == "farewell_confirm":
                        if action in (game_input.CONFIRM, "\r", "\n", "y", "Y"):
                            poke = self.active_status_pokemon
                            if poke and (poke != self.player_pokemon and not getattr(poke, "is_leader", False)):
                                self.remove_party_member(poke)
                                self.log_message(f"{poke.name} went away...")
                                self.summary_context_menu_state = None
                                self.active_status_pokemon = None
                                self.render()
                                continue
                        if action in (game_input.QUIT, "n", "N"):
                            context_state["mode"] = "menu"
                            self.render()
                            continue

                if action in (game_input.CONFIRM, "\r", "\n"):
                    opts = self.get_summary_context_menu_options(self.active_status_pokemon)
                    if opts:
                        self.summary_context_menu_state = {"mode": "menu", "selected_index": 0, "options": opts}
                        self.render()
                        continue

                if action == game_input.QUIT:
                    self.active_status_pokemon = None
                    self.summary_scroll_offset = 0
                    self.summary_context_menu_state = None
                    self.render()
                    continue

                if action in (game_input.MOVE_UP, "w", "W", "up", "UP"):
                    self.summary_scroll_offset = max(0, getattr(self, "summary_scroll_offset", 0) - 1)
                    self.render()
                    continue

                if action in (game_input.MOVE_DOWN, "s", "S", "down", "DOWN"):
                    total_lines = getattr(self, "_last_summary_total_lines", 46)
                    max_offset = max(0, total_lines - 46)
                    self.summary_scroll_offset = min(max_offset, getattr(self, "summary_scroll_offset", 0) + 1)
                    self.render()
                    continue

                poke = self.active_status_pokemon
                is_leader = (poke == self.player_pokemon or getattr(poke, "is_leader", False))

                slot_idx = None
                if action in (game_input.USE_MOVE_1, "z", "Z", "1"):
                    slot_idx = 0
                elif action in (game_input.USE_MOVE_2, "x", "X", "2"):
                    slot_idx = 1
                elif action in (game_input.USE_MOVE_3, "c", "C", "3"):
                    slot_idx = 2
                elif action in (game_input.USE_MOVE_4, "v", "V", "4"):
                    slot_idx = 3

                if slot_idx is not None and slot_idx < len(poke.moves):
                    if not is_leader:
                        m = poke.moves[slot_idx]
                        m["enabled"] = not m.get("enabled", True)
                        self.render()
                continue

            if action == game_input.QUIT:
                if getattr(self, "look_around_mode", False):
                    self.look_around_mode = False
                    self.render()
                    continue
                if getattr(self, "waiting_for_direction", False):
                    self.waiting_for_direction = False
                    self.direction_move = None
                    self.log_message("Targeting canceled.")
                    self.render()
                    continue
                if getattr(self, "targeting_mode", False):
                    self.log_message("Targeting canceled.")
                    self.targeting_mode = False
                    self.targeting_move = None
                    self.targeting_targets = []
                    self.render()
                    continue
                if getattr(self, "waiting_for_orb_direction", None) is not None:
                    self.log_message("Orb canceled.")
                    self.waiting_for_orb_direction = None
                    self.render()
                    continue
                self.pause_menu_state = {
                    "selected_index": 0,
                    "sub_screen": None,
                    "confirm_give_up": False,
                    "confirm_index": 0
                }
                self.render()
                continue

            #1. Look around mode input interception
            if getattr(self, "look_around_mode", False):
                dx, dy = 0, 0
                if action == game_input.MOVE_UP:
                    dy = -1
                elif action == game_input.MOVE_DOWN:
                    dy = 1
                elif action == game_input.MOVE_LEFT:
                    dx = -1
                elif action == game_input.MOVE_RIGHT:
                    dx = 1
                elif action == game_input.MOVE_UP_LEFT:
                    dx, dy = -1, -1
                elif action == game_input.MOVE_UP_RIGHT:
                    dx, dy = 1, -1
                elif action == game_input.MOVE_DOWN_LEFT:
                    dx, dy = -1, 1
                elif action == game_input.MOVE_DOWN_RIGHT:
                    dx, dy = 1, 1
                #(Esc/QUIT is already handled above)

                if dx != 0 or dy != 0:
                    cx, cy = self.look_around_cursor
                    nx = cx + dx
                    ny = cy + dy
                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                        self.look_around_cursor = (nx, ny)
                    self.look_around_cursor_visible = True

                self.render()
                continue

            #2. Attack direction selection state
            if self.waiting_for_direction:
                dx, dy = 0, 0
                if action == game_input.MOVE_UP:
                    dy = -1
                elif action == game_input.MOVE_DOWN:
                    dy = 1
                elif action == game_input.MOVE_LEFT:
                    dx = -1
                elif action == game_input.MOVE_RIGHT:
                    dx = 1
                elif action == game_input.MOVE_UP_LEFT:
                    dx, dy = -1, -1
                elif action == game_input.MOVE_UP_RIGHT:
                    dx, dy = 1, -1
                elif action == game_input.MOVE_DOWN_LEFT:
                    dx, dy = -1, 1
                elif action == game_input.MOVE_DOWN_RIGHT:
                    dx, dy = 1, 1
                elif action == game_input.QUIT:
                    #Cancel targeting
                    self.waiting_for_direction = False
                    self.direction_move = None
                else:
                    #Ignore other keys while waiting for direction
                    continue

                if dx != 0 or dy != 0:
                    tx = self.player_x + dx
                    ty = self.player_y + dy
                    found_target = None
                    for t in [self.player_pokemon] + self.spawned_pokemon:
                        px, py = get_pokemon_position(self, t)
                        if px == tx and py == ty:
                            found_target = t
                            break

                    assert self.direction_move is not None
                    valid_targets = get_valid_targets(self, self.player_pokemon, self.direction_move)
                    if self.direction_move.get("name") == "Future Sight":
                        if 0 <= tx < self.floor.width and 0 <= ty < self.floor.height and self.floor.grid[ty][tx] != WALL_CHAR:
                            if any(fs["tile"] == (tx, ty) for fs in getattr(self, "future_sight_effects", [])):
                                self.log_message("You've already foreseen an attack there!")
                            else:
                                try:
                                    self.player_pokemon.use_move(self.direction_move, game=self)
                                    self.moved_used_this_turn.add(self.player_pokemon)
                                except ValueError as e:
                                    self.log_message(f"Error! {str(e)} Please report this to C4!")
                                    self.waiting_for_direction = False
                                    self.direction_move = None
                                    continue

                                if not hasattr(self, "future_sight_effects"):
                                    self.future_sight_effects = []
                                self.future_sight_effects.append({
                                    "attacker": self.player_pokemon,
                                    "tile": (tx, ty),
                                    "turns_left": 2,
                                    "move": self.direction_move
                                })
                                self.start_player_action()
                                self.log_message(f"{self.player_pokemon.name} foresaw an attack!")
                                self.on_turn_completed()
                        else:
                            self.log_message("You can't use Future Sight on a wall!")
                        self.waiting_for_direction = False
                        self.direction_move = None
                        continue
                    if found_target and found_target in valid_targets:
                        self.execute_single_move(self.player_pokemon, found_target, self.direction_move)
                        self.on_turn_completed()
                    else:
                        self.log_message("There are no valid targets in that direction!")
                    
                    self.waiting_for_direction = False
                    self.direction_move = None

                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #3. Cursor targeting state
            if self.targeting_mode:
                if self.targeting_move is None:
                    self.targeting_mode = False
                    self.targeting_targets = []
                    continue

                dx, dy = 0, 0
                if action == game_input.MOVE_UP:
                    dy = -1
                elif action == game_input.MOVE_DOWN:
                    dy = 1
                elif action == game_input.MOVE_LEFT:
                    dx = -1
                elif action == game_input.MOVE_RIGHT:
                    dx = 1
                elif action == game_input.MOVE_UP_LEFT:
                    dx, dy = -1, -1
                elif action == game_input.MOVE_UP_RIGHT:
                    dx, dy = 1, -1
                elif action == game_input.MOVE_DOWN_LEFT:
                    dx, dy = -1, 1
                elif action == game_input.MOVE_DOWN_RIGHT:
                    dx, dy = 1, 1
                elif action == game_input.QUIT:
                    #Cancel targeting
                    self.log_message("Targeting canceled.")
                    self.targeting_mode = False
                    self.targeting_move = None
                    self.targeting_targets = []
                elif action == game_input.CONFIRM:
                    cx, cy = self.targeting_cursor
                    selected_target = None
                    for t in self.targeting_targets:
                        px, py = get_pokemon_position(self, t)
                        if px == cx and py == cy:
                            selected_target = t
                            break

                    if selected_target:
                        move = self.targeting_move
                        self.targeting_mode = False
                        self.targeting_move = None
                        self.targeting_targets = []

                        if move is not None:
                            range_str = move.get("range", "")
                            if range_str == "Straight line piercing":
                                ax, ay = get_pokemon_position(self, self.player_pokemon)
                                tx, ty = get_pokemon_position(self, selected_target)
                                dx = 1 if tx > ax else (-1 if tx < ax else 0)
                                dy = 1 if ty > ay else (-1 if ty < ay else 0)
                                line_targets = self.get_line_piercing_targets(self.player_pokemon, move, dx, dy)
                                if not line_targets:
                                    line_targets = [selected_target]
                                self.execute_multi_move(self.player_pokemon, line_targets, move)
                            else:
                                self.execute_single_move(self.player_pokemon, selected_target, move)
                            self.on_turn_completed()
                    else:
                        self.log_message("No valid target there!")

                if dx != 0 or dy != 0:
                    cx, cy = self.targeting_cursor
                    nx = cx + dx
                    ny = cy + dy
                    if 0 <= nx < self.floor.width and 0 <= ny < self.floor.height:
                        if self.targeting_move is not None:
                            range_str = self.targeting_move.get("range", "")
                            max_range = 10
                            if range_str == "Enemy up to 2 tiles away":
                                max_range = 2
                            if max(abs(nx - self.player_x), abs(ny - self.player_y)) <= max_range:
                                self.targeting_cursor = (nx, ny)

                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #4. Standard controls and move selection
            #Use a move
            if action in (game_input.USE_MOVE_1, game_input.USE_MOVE_2, game_input.USE_MOVE_3, game_input.USE_MOVE_4):
                slot_map = {
                    game_input.USE_MOVE_1: 0,
                    game_input.USE_MOVE_2: 1,
                    game_input.USE_MOVE_3: 2,
                    game_input.USE_MOVE_4: 3
                }
                self.select_move(slot_map[action])
                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #5. Open inventory
            if action == game_input.INVENTORY:
                self.inventory_state = {
                    "selected_index": 0,
                    "context_menu": None,
                    "context_index": 0,
                    "mode": "options"
                }
                self.render()
                continue

            #6. Open message history
            if action == game_input.MESSAGE_LOG:
                lines = self.message_log.get_history_lines(max_width=72)
                max_scroll = max(0, len(lines) - 42)
                self.message_history_state = {
                    "scroll": max_scroll
                }
                self.render()
                continue

            #7. Pick up an item
            if action == game_input.PICK_UP:
                self.manual_pickup()
                if self.message_log.has_pending():
                    self.process_messages()
                else:
                    self.render()
                continue

            #8. Enter look around mode
            if action == game_input.LOOK_AROUND:
                self.look_around_mode = True
                self.look_around_cursor = (self.player_x, self.player_y)
                self.look_around_cursor_visible = True
                self.render()
                continue

            #9. Open teammate status window
            if action in (game_input.STATUS_1, game_input.STATUS_2, game_input.STATUS_3, game_input.STATUS_4, game_input.STATUS_5, game_input.STATUS_6):
                status_map = {
                    game_input.STATUS_1: 0,
                    game_input.STATUS_2: 1,
                    game_input.STATUS_3: 2,
                    game_input.STATUS_4: 3,
                    game_input.STATUS_5: 4,
                    game_input.STATUS_6: 5
                }
                idx = status_map[action]
                if idx < len(self.party):
                    self.active_status_pokemon = self.party[idx]
                    self.summary_scroll_offset = 0
                    self.render()
                continue

            #10. Use stairs
            if action == game_input.TAKE_STAIRS:
                if (self.player_x, self.player_y) == getattr(self, "stairs_position", None):
                    if self.floor_number >= 50:
                        self.log_message("CONGRATULATIONS! You have managed to escape the misery dungeon!")
                        self.game_won = True
                        self.game_ended = True
                        self.is_running = False
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                    else:
                        self.floor_number += 1
                        self.log_message("You ascend the stairs.")
                        
                        #Generate new floor
                        self.floor = DungeonFloor(width=self.floor.width)
                        self.explored_tiles.clear()
                        self.radar_active = False
                        self.scanner_active = False
                        self.stairs_revealed = False
                        
                        #Spawn player & party
                        self.player_x, self.player_y = self._get_starting_position()
                        self.player_pokemon.x, self.player_pokemon.y = self.player_x, self.player_y
                        
                        #Spawn other party members in the same room
                        room_cell = None
                        for cell, room in self.floor.rooms.items():
                            if room.x1 <= self.player_x <= room.x2 and room.y1 <= self.player_y <= room.y2:
                                room_cell = cell
                                break
                        
                        room_tiles = []
                        if room_cell is not None:
                            room = self.floor.rooms[room_cell]
                            for ry in range(room.y1, room.y2 + 1):
                                for rx in range(room.x1, room.x2 + 1):
                                    if self.floor.grid[ry][rx] == FLOOR_CHAR and (rx, ry) != (self.player_x, self.player_y):
                                        room_tiles.append((rx, ry))
                        
                        if len(room_tiles) < len(self.party) - 1:
                            for room in self.floor.rooms.values():
                                for ry in range(room.y1, room.y2 + 1):
                                    for rx in range(room.x1, room.x2 + 1):
                                        if self.floor.grid[ry][rx] == FLOOR_CHAR and (rx, ry) != (self.player_x, self.player_y) and (rx, ry) not in room_tiles:
                                            room_tiles.append((rx, ry))
                        
                        random.shuffle(room_tiles)
                        tile_idx = 0
                        for member in self.party:
                            if member is self.player_pokemon:
                                continue
                            if tile_idx < len(room_tiles):
                                member.x, member.y = room_tiles[tile_idx]
                                tile_idx += 1
                            else:
                                member.x, member.y = self.player_x, self.player_y
                        
                        #Set up stairs and Wonder Tile on the new floor
                        self.spawn_stairs()
                        self.spawn_wonder_tile()
                        
                        #Clear spawned enemies and generate new floor spawn list
                        self.spawned_pokemon.clear()
                        self.generate_floor_spawn_list()
                        self.spawn_initial_items()
                        self.spawn_initial_enemies()
                        
                        #Reset floor-level states & bindings
                        self.gravity = False
                        self.weather = "Clear"
                        self.wonder_room_turns = 0
                        self.leech_seed_sources.clear()
                        self.taunt_sources.clear()
                        self.fire_spin_bindings.clear()
                        self.wrap_bindings.clear()
                        self.sand_tomb_bindings.clear()
                        self.whirlpool_bindings.clear()
                        
                        #Cure all party members and reset their stats to normal
                        for member in self.party:
                            member.fake_out_used_this_floor = False
                            member.disable_move_effect = None
                            member.temp_types = None
                            member.status_effects = {k: (0 if isinstance(v, int) else False) for k, v in member.status_effects.items()}
                            for stat in member.stat_modifiers:
                                member.stat_modifiers[stat] = 0
                            member.movement_speed_stage = 0
                            member.movement_speed_duration = 0
                            member.slow_turn_toggle = False
                            
                            #Restore mimicked moves
                            if getattr(member, "mimic_original_state", None) is not None:
                                state = member.mimic_original_state
                                slot = state["slot"]
                                if slot < len(member.moves) and member.moves[slot]["name"] == state["copied_move"]["name"]:
                                    member.moves[slot] = state["original_move"]
                                member.mimic_original_state = None

                             #Restore transformed state
                            if getattr(member, "transform_original_state", None) is not None:
                                t_state = member.transform_original_state
                                if "species_data" in t_state:
                                    member.species_data = t_state["species_data"]
                                member.nickname = t_state.get("nickname")
                                member.temp_types = t_state.get("temp_types")
                                if "moves" in t_state:
                                    member.moves = t_state["moves"]
                                if "stat_modifiers" in t_state:
                                    member.stat_modifiers = t_state["stat_modifiers"]
                                member.recalculate_stats()
                                member.transform_original_state = None
                            
                            #Reset last_used_move_on_floor
                            member.last_used_move_on_floor = None
                        
                        #Reset player actions left for the new floor
                        self.player_actions_left = self.get_pokemon_actions_this_turn(self.player_pokemon)
                        
                        #Render new floor immediately
                        if self.message_log.has_pending():
                            self.process_messages()
                        else:
                            self.render()
                else:
                    self.log_message("There are no stairs here.")
                    if self.message_log.has_pending():
                        self.process_messages()
                    else:
                        self.render()
                continue

            dx, dy = 0, 0
            if action == game_input.MOVE_UP:
                dy = -1
            elif action == game_input.MOVE_DOWN:
                dy = 1
            elif action == game_input.MOVE_LEFT:
                dx = -1
            elif action == game_input.MOVE_RIGHT:
                dx = 1
            elif action == game_input.MOVE_UP_LEFT:
                dx, dy = -1, -1
            elif action == game_input.MOVE_UP_RIGHT:
                dx, dy = 1, -1
            elif action == game_input.MOVE_DOWN_LEFT:
                dx, dy = -1, 1
            elif action == game_input.MOVE_DOWN_RIGHT:
                dx, dy = 1, 1
            elif action == game_input.WAIT:
                pass
            else:
                #Ignore unknown keys
                continue

            moved = self.try_move(dx, dy)
            if action == game_input.WAIT or (action != game_input.WAIT and moved):
                if action == game_input.WAIT:
                    self.start_player_action()
                self.on_turn_completed()
            
            if self.message_log.has_pending():
                self.process_messages()
            else:
                self.render()

        if self.message_log.has_pending():
            self.process_messages()

        if getattr(self, "game_ended", False) or getattr(self, "game_won", False) or (self.player_pokemon is not None and int(self.player_pokemon.current_hp) <= 0):
            self.show_end_screen()

        self.is_running = False

    def _restore_cursor(self):
        """Restore text cursor when exiting game loop."""
        try:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    compat = False
    for arg in sys.argv[1:]:
        if arg in ("--compatibility", "--compat", "--no-color", "--nocolor", "-c"):
            compat = True
            break
    try:
        game = Game(compatibility_mode=compat)
        game.run()
    except Exception as e:
        import traceback
        import datetime
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(project_root, "debug.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- Crash report: {datetime.datetime.now()} ---\n")
                traceback.print_exc(file=f)
        except Exception:
            pass

        saved_msg = ""
        if 'game' in locals() and getattr(game, "_emergency_save_path", None):
            saved_msg = f"\nAn emergency save was created: {os.path.basename(game._emergency_save_path)}\nYou can resume your progress from the Load Game menu.\n"
        elif 'game' in locals() and getattr(game, "player_pokemon", None) and not getattr(game, "game_ended", False):
            try:
                from save_game import attempt_emergency_save
                saved_path = attempt_emergency_save(game)
                if saved_path:
                    saved_msg = f"\nAn emergency save was created: {os.path.basename(saved_path)}\nYou can resume your progress from the Load Game menu.\n"
            except Exception:
                pass

        print(f"Oh no, the game crashed!\n{e}\n{saved_msg}See debug.log for detailed traceback information.\nPlease report this to me on my Discord or on the Pokécommunity thread; make sure to include your debug.log and a description of what you were doing before the game crashed. -C4", file=sys.stderr)
        sys.exit(1)
