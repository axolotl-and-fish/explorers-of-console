"""
pokemon.py

This class defines all the information about a Pokémon, including its stats, level, moves, status effects, and everything else that makes a Pokémon an individual.
"""

import os
import random
from pokemon_db import load_pokemon_database, VALID_STATS

_species_cache: dict[str, dict] = {}
_moves_cache: dict[str, dict] = {}


def _get_species_data(species_identifier: str) -> dict:
    """Loads and caches pokemon.json, searching by species name or ID"""
    global _species_cache
    if not _species_cache:
        from data_utils import get_data_file_path
        db_path = get_data_file_path("pokemon.json")
        db = load_pokemon_database(db_path)
        for entry in db:
            #Map both ID and Name to the species entry for lookup flexibility
            _species_cache[entry["id"]] = entry
            _species_cache[entry["name"].lower()] = entry

    key = species_identifier.lower()
    if key not in _species_cache:
        raise ValueError(f"Unknown Pokémon species: {species_identifier}")
    return _species_cache[key]


def _get_move_data(move_name: str) -> dict:
    """Loads and caches moves.json, searching by name"""
    global _moves_cache
    if not _moves_cache:
        from moves_db import load_moves_database
        from data_utils import get_data_file_path
        db_path = get_data_file_path("moves.json")
        db = load_moves_database(db_path)
        for entry in db:
            _moves_cache[entry["name"].lower()] = entry

    key = move_name.lower()
    if key not in _moves_cache:
        raise ValueError(f"Unknown move: {move_name}")
    res = dict(_moves_cache[key])
    res.setdefault("enabled", True)
    return res


class Pokemon:
    """Represents an instance of a Pokémon with all of its stats."""

    def __init__(self, species_identifier: str | dict, level: int = 1, nickname: str | None = None):
        if isinstance(species_identifier, dict):
            self.species_data = species_identifier
        else:
            self.species_data = _get_species_data(species_identifier)

        self.nickname = nickname
        self._level = level
        self.experience = self.get_experience_required_for_level(level)
        self.x: int = 0
        self.y: int = 0
        self.napping: bool = False #Pokémon that spawn when the floor generates are in an inactive "napping" state
        self.last_dx: int = 0
        self.last_dy: int = 0
        self.target_exit: tuple[int, int] | None = None #Enemy AI only
        self.just_woke_up: bool = False #Pokémon can't move on the first turn it wakes up
        self.fake_out_used_this_floor: bool = False #Fake Out can only be used once per floor, disable Fake Out if this is true
        self.temp_types: list[str] | None = None #Pokémon whose types have been changed by e.g., Reflect Type

        self.max_pp = 100
        self.current_pp = 100

        #Randomize IVs when spawning
        self.ivs = {stat: random.randint(0, 31) for stat in VALID_STATS}

        #Spawn with no EVs
        self.evs = {stat: 0 for stat in VALID_STATS}

        self.moves: list[dict] = []
        self.learn_level_up_moves()

        self.stats: dict[str, int] = {}
        self.recalculate_stats()
        self.current_hp: float = float(self.stats["HP"])
        #Internally we need to treat HP as a float for the HP regeneration mechanic (1%/turn)

        #Rate of belly decay is dependent on BST, stronger mons get fewer total "belly points" and thus get hungry faster
        base_stat_total = sum(self.species_data["base_stats"][stat] for stat in VALID_STATS)
        self.max_belly = 5000.0 * (200.0 / base_stat_total)
        self.current_belly = self.max_belly

        #For printing belly warning messages
        self.warned_20 = False
        self.warned_10 = False
        self.warned_0 = False

        self.seen_moves: set[str] = set()

        #Stat modifiers stages (Attack, Defense, Special_Attack, Special_Defense, Speed, Accuracy, Evasion)
        self.stat_modifiers = {
            "Attack": 0,
            "Defense": 0,
            "Special_Attack": 0,
            "Special_Defense": 0,
            "Speed": 0,
            "Accuracy": 0,
            "Evasion": 0,
        }

        #Movement speed modifiers
        self.movement_speed_stage: int = 0
        self.movement_speed_duration: int = 0
        self.slow_turn_toggle: bool = False
        self.cannot_be_revived: bool = False
        self.last_damage_source: str | None = None
        self.has_been_attacked_by_team: bool = False

        #Status effects
        self.status_effects: dict[str, int | bool] = {
            "Sleep": 0,
            "Paralysis": 0,
            "Poison": False,
            "Toxic": False,
            "Burn": False,
            "Frozen": 0,
            "Flinch": 0,
            "Petrified": 0,
            "Confusion": 0,
            "Leech Seed": 0,
            "Sleepless": False,
            "Protect": 0,
            "Safeguard": 0,
            "Laser Focus": False,
            "Focus Energy": 0,
            "Wrap": 0,
            "Stockpile": 0,
            "Light Screen": 0,
            "Reflect": 0,
            "Sand Tomb": 0,
            "Digging": 0,
            "Encore": 0,
            "Magnet Rise": 0,
            "Telekinesis": 0,
            "Resting": 0,
            "Stuck": 0,
            "Quick Guard": 0,
            "Wide Guard": 0,
            "Vital Throw": 0,
            "Curse": False,
            "Drowsy": 0,
            "Lock-On": False,
            "Aqua Ring": False,
            "Diving": 0,
            "Paused": 0,
            "Ingrain": 0,
            "Decoy": 0,
            "Landed": 0,
            "Charging": 0,
            "Terrified": 0,
            "Hallucinating": 0,
            "Snatch": 0,
            "Cowering": 0,
            "Rebound": 0,
            "Silenced": 0,
            "Invisible": 0,
        }
        self.protect_consecutive: int = 0 #How many times have protection moves been used?
        self.last_used_move: str | None = None #Last move this mon used, for some move effects
        self.charging_move: dict | None = None #What move is this mon charging?
        self.disable_move_effect: str | None = None #What move is disabled?
        self.imprisoned_moves: list[str] = [] #What moves have been imprisoned?
        self.last_used_move_on_floor: str | None = None #Last move this mon used (on the given floor)
        self.mimic_original_state: dict | None = None #Original state for the move Mimic
        self.transform_original_state: dict | None = None #Original state for transformed mons
        self.last_hit_by_move: dict | None = None #Move this mon was last hit by
        self.is_leader: bool = False #Is this mon the player-controlled mon?
        self.swapped_this_turn: bool = False #Was this teammate swapped by the leader this turn?
        self.echoed_voice_count: int = 0 #Number of times Echoed Voice has been used
        self.damage_hit_turns: list[int] = [] #Turns when hit by damaging moves (for Rage Fist)
        self.last_move_failed_turn: int | None = None #Turn when move missed or failed (for Stomping Tantrum)
        self.last_teammate_fainted_turn: int | None = None #Turn when teammate fainted (for Retaliate)
        self.damaged_by_pokemons: dict[Pokemon, int] = {} #Map of attacker -> turn_number when damaged (for Revenge)

    def learn_level_up_moves(self, game=None, old_level=None):
        """Pokémon spawn knowing the last 4 moves they know via level-up, so this populates known moves based on current level from level_up_moves database"""
        #Check if this is the initial load (e.g. self.moves is empty or not yet fully populated)
        is_initial = not hasattr(self, "moves") or not self.moves

        if is_initial:
            self.moves = []
            candidates_by_name = {}
            for idx, (learn_lvl, move_name) in enumerate(self.species_data["level_up_moves"]):
                if 1 <= learn_lvl <= self._level:
                    try:
                        move_info = _get_move_data(move_name)
                        if move_name not in candidates_by_name:
                            candidates_by_name[move_name] = {
                                "learn_lvl": learn_lvl,
                                "move_info": move_info,
                                "index": idx
                            }
                        else:
                            if learn_lvl > candidates_by_name[move_name]["learn_lvl"]:
                                candidates_by_name[move_name]["learn_lvl"] = learn_lvl
                                candidates_by_name[move_name]["index"] = idx
                    except ValueError:
                        pass

            if not candidates_by_name:
                return

            grouped_by_lvl = {}
            for cand in candidates_by_name.values():
                lvl = cand["learn_lvl"]
                if lvl not in grouped_by_lvl:
                    grouped_by_lvl[lvl] = []
                grouped_by_lvl[lvl].append(cand)

            sorted_lvls = sorted(grouped_by_lvl.keys(), reverse=True)

            selected_candidates = []
            slots_remaining = 4

            for lvl in sorted_lvls:
                group = grouped_by_lvl[lvl]
                if len(group) <= slots_remaining:
                    selected_candidates.extend(group)
                    slots_remaining -= len(group)
                else:
                    sampled = random.sample(group, slots_remaining)
                    selected_candidates.extend(sampled)
                    slots_remaining = 0

                if slots_remaining == 0:
                    break

            def _is_damaging(cand):
                cat = cand["move_info"].get("category")
                return cat in ("Physical", "Special")

            has_damaging = any(_is_damaging(c) for c in selected_candidates)
            if not has_damaging:
                all_damaging = [c for c in candidates_by_name.values() if _is_damaging(c)]
                if all_damaging:
                    max_dam_lvl = max(c["learn_lvl"] for c in all_damaging)
                    top_damaging = [c for c in all_damaging if c["learn_lvl"] == max_dam_lvl]
                    chosen_damaging = random.choice(top_damaging)

                    if len(selected_candidates) < 4:
                        selected_candidates.append(chosen_damaging)
                    else:
                        min_selected_lvl = min(c["learn_lvl"] for c in selected_candidates)
                        lowest_status = [c for c in selected_candidates if c["learn_lvl"] == min_selected_lvl]
                        to_replace = random.choice(lowest_status)
                        selected_candidates.remove(to_replace)
                        selected_candidates.append(chosen_damaging)

            selected_candidates.sort(key=lambda c: (c["learn_lvl"], c["index"]))
            self.moves = [c["move_info"] for c in selected_candidates]
        else:
            #Level-up move learning during gameplay.
            if old_level is None:
                old_level = self._level - 1
                
            for learn_lvl, move_name in self.species_data["level_up_moves"]:
                if old_level < learn_lvl <= self._level:
                    try:
                        move_info = _get_move_data(move_name)
                        #Check if the Pokémon already knows this move
                        if any(m["name"] == move_info["name"] for m in self.moves):
                            continue
                        
                        if len(self.moves) < 4:
                            self.moves.append(move_info)
                            if game and hasattr(game, "party") and self in game.party:
                                game.log_message(f"{self.name} learned {move_info['name']}!")
                        else:
                            if game and hasattr(game, "party") and self in game.party:
                                game.prompt_forget_and_learn_move(self, move_info)
                            else:
                                if self.moves:
                                    self.moves.pop(0)
                                self.moves.append(move_info)
                    except ValueError:
                        pass

    def can_use_move(self, move: dict, game=None) -> bool:
        """Returns True if the Pokémon meets the criteria for a move to be used (and isn't blocked due to PP, Belly, disablement, status effects etc.)"""
        move_name = move.get("name")
        
        #Moves that can be disabled by status effects
        if move_name == getattr(self, "disable_move_effect", None):
            return False
        if move_name in getattr(self, "imprisoned_moves", []):
            return False

        if self.status_effects.get("Taunted") and move.get("category") == "Status":
            return False

        if self.status_effects.get("Silenced", 0) > 0 and move.get("sound_based", False):
            return False

        if move_name == "Fake Out" and getattr(self, "fake_out_used_this_floor", False):
            return False

        #Bypass PP cost for moves that don't cost PP
        if move_name == "Belch":
            if game is not None and self in game.party:
                return self.current_belly >= 0.1 * self.max_belly
            return True

        if move_name == "Belly Drum":
            if self.stat_modifiers.get("Attack", 0) >= 6:
                return False
            if game is not None and self in game.party:
                return self.current_belly >= 0.5 * self.max_belly
            return True

        #Struggle can always be used no matter what
        if move_name == "Struggle":
            return True

        if self.current_pp < move["pp_cost"]:
            return False

        if self.status_effects.get("Encore", 0) > 0:
            last = getattr(self, "last_used_move", None)
            if last and move_name != last:
                return False

        if game is not None and getattr(game, "gravity", False):
            if move_name in ("Bounce", "Fly", "Flying Press", "Jump Kick", "High Jump Kick", "Magnet Rise", "Splash", "Telekinesis"):
                return False

        if move_name == "Stockpile":
            if self.status_effects.get("Stockpile", 0) >= 3:
                return False
        elif move_name in ("Swallow", "Spit Up"):
            if self.status_effects.get("Stockpile", 0) <= 0:
                return False
        elif move_name == "Final Gambit":
            if int(self.current_hp) <= 1:
                return False
        elif move_name == "Recycle":
            if game is not None:
                if not hasattr(game, "party") or self not in game.party:
                    return False
                if not any(item.get("name") == "Plain Seed" for item in getattr(game, "inventory", [])):
                    return False

        return True

    def can_struggle(self, game=None) -> bool:
        """Returns True if the Pokémon has no moves, or if all of its moves are unusable"""
        if not self.moves:
            return True
        return all(not self.can_use_move(move, game) for move in self.moves)

    def use_move(self, move: dict, game=None):
        """Consumes PP/Belly for using a move. Raises ValueError if insufficient."""
        move_name = move.get("name")
        if self.status_effects.get("Taunted") and move.get("category") == "Status":
            raise ValueError(f"{self.name} cannot use status moves while Taunted!")
        if move_name == "Fake Out" and getattr(self, "fake_out_used_this_floor", False):
            raise ValueError(f"{self.name} cannot use Fake Out again on this floor!")
        if not self.can_use_move(move, game):
            raise ValueError(f"Insufficient resources/stacks to use move {move.get('name', 'Unknown')}.")
            
        move_name = move.get("name")
        if move_name == "Belch":
            if game is not None and self in game.party:
                self.current_belly = max(0.0, self.current_belly - 0.1 * self.max_belly)
        elif move_name == "Belly Drum":
            if game is not None and self in game.party:
                self.current_belly = max(0.0, self.current_belly - 0.5 * self.max_belly)
        elif move_name == "Struggle":
            pass
        else:
            self.current_pp -= move["pp_cost"]

    @property
    def nickname(self) -> str | None:
        """Returns the nickname of the Pokémon, if set"""
        return getattr(self, "_nickname", None)

    @nickname.setter
    def nickname(self, value: str | None):
        """Sets the nickname of the Pokémon (12 characters max)"""
        if value:
            stripped = str(value).strip()
            self._nickname = stripped[:12] if stripped else None
        else:
            self._nickname = None

    @property
    def name(self) -> str:
        """Returns 'Decoy' if target has Decoy status and is not the team leader, otherwise nickname or species name."""
        if self.status_effects.get("Decoy", 0) > 0 and not getattr(self, "is_leader", False):
            return "Decoy"
        return self.nickname if self.nickname else self.species_data["name"]

    @property
    def level(self) -> int:
        """Returns the Pokémon's current level."""
        return self._level

    @level.setter
    def level(self, value: int):
        """Sets the Pokémon's level, updates experience accordingly, and recalculates stats."""
        if value < 1 or value > 99:
            raise ValueError("Invalid level (must be between 1 and 99)")
        self._level = value
        self.experience = self.get_experience_required_for_level(value)
        self.learn_level_up_moves()
        self.recalculate_stats()

    def get_experience_required_for_level(self, n: int) -> int:
        """Returns the total experience required to reach level N using the experience group curve."""
        if n <= 1:
            return 0 #n<1 should never happen. I dread to think what would happen if it did

        import math
        group = self.species_data["experience_group"]

        if group == "Fast":
            val = (4 * (n ** 3)) / 5
        elif group == "Medium Fast":
            val = float(n ** 3)
        elif group == "Medium Slow":
            val = (6 / 5) * (n ** 3) - 15 * (n ** 2) + 100 * n - 140
        elif group == "Slow":
            val = (5 * (n ** 3)) / 4
        elif group == "Erratic":
            if n < 50:
                val = ((n ** 3) * (100 - n)) / 50
            elif n <= 67:
                val = ((n ** 3) * (150 - n)) / 100
            elif n <= 97:
                val = ((n ** 3) * (1911 - 10 * n)) / 500
            else:
                val = ((n ** 3) * (160 - n)) / 100
        elif group == "Fluctuating":
            if n < 15:
                val = (((n ** 3) * ((n + 1) / 3)) + 24) / 50
            elif n <= 35:
                val = ((n ** 3) * (n + 14)) / 50
            else:
                val = (((n ** 3) * (n / 2)) + 32) / 50
        else:
            raise ValueError(f"Unknown experience group: {group}")

        return max(0, math.floor(val))

    def can_evolve(self, game=None) -> bool:
        """Returns True if the Pokémon meets the criteria to evolve. Used to display the Evolution option in the party menu"""
        return len(self.get_eligible_evolutions(game)) > 0

    def get_eligible_evolutions(self, game=None) -> list[dict]:
        """Returns a list of evolution dictionaries from species_data['evolutions'] whose criteria are met"""
        eligible = []
        for evo in self.species_data.get("evolutions", []):
            target_species = evo.get("to")
            if not target_species:
                continue
            
            #Check level requirement if specified
            min_lvl = evo.get("min_level", evo.get("level"))
            if min_lvl is not None and self.level < min_lvl:
                continue

            #Check item requirement if specified
            req_item = evo.get("item", evo.get("evolution_item"))
            if req_item is not None:
                if not game or not hasattr(game, "inventory"):
                    continue
                has_item = any(it.get("name") == req_item for it in game.inventory)
                if not has_item:
                    continue

            eligible.append(evo)
        return eligible

    def check_evolution_notifications(self, game=None):
        """Prints log message '[Pokémon] can now evolve!' when eligibility transitions to True"""
        if not game or not hasattr(game, "party") or self not in game.party:
            return
        eligible = self.can_evolve(game=game)
        was_eligible = getattr(self, "has_notified_can_evolve", False)
        if eligible and not was_eligible:
            self.has_notified_can_evolve = True
            game.log_message(f"{self.name} can now evolve!")
        elif not eligible:
            self.has_notified_can_evolve = False

    def evolve(self, target_species_name: str, game=None, consumed_item_name: str | None = None):
        """Evolves a Pokémon into a new species, recalculates stats, and learns moves labeled as level '0'"""
        import copy

        old_display_name = self.name
        old_species_name = self.species_data.get("name", "Unknown")

        #Find target species data
        new_species_data = _get_species_data(target_species_name)

        if game:
            game.log_message(f"{old_display_name} evolved into {target_species_name}!")

        #Save old stats before recalculation
        old_stats = dict(self.stats)

        #Update nickname if nickname was species name
        if getattr(self, "_nickname", None) == old_species_name:
            self._nickname = target_species_name

        self.species_data = copy.deepcopy(new_species_data)
        self.recalculate_stats()

        #Heal HP to new max HP if current HP was at old max HP or higher
        self.current_hp = float(self.stats["HP"])

        #Print stat increases
        if game and hasattr(game, "party") and self in game.party:
            stat_changes = []
            for stat in VALID_STATS:
                diff = self.stats[stat] - old_stats[stat]
                if diff > 0:
                    stat_changes.append(f"{stat.replace('_', ' ')} +{diff}")
            if stat_changes:
                game.log_message(", ".join(stat_changes))

        #Learn level 0 moves
        for learn_lvl, move_name in self.species_data.get("level_up_moves", []):
            if learn_lvl == 0:
                try:
                    move_info = _get_move_data(move_name)
                    if any(m["name"] == move_info["name"] for m in self.moves):
                        continue
                    if len(self.moves) < 4:
                        self.moves.append(move_info)
                        if game and hasattr(game, "party") and self in game.party:
                            game.log_message(f"{self.name} learned {move_info['name']}!")
                    else:
                        if game and hasattr(game, "party") and self in game.party:
                            game.prompt_forget_and_learn_move(self, move_info)
                        else:
                            if self.moves:
                                self.moves.pop(0)
                            self.moves.append(move_info)
                except ValueError:
                    pass

        #Consume item on item evolution
        if consumed_item_name and game and hasattr(game, "inventory"):
            for idx, it in enumerate(game.inventory):
                if it.get("name") == consumed_item_name:
                    game.inventory.pop(idx)
                    break

        self.has_notified_can_evolve = False

    def gain_experience(self, amount: int, game=None):
        """Adds experience points and checks for level ups"""
        if int(getattr(self, "current_hp", 1)) <= 0:
            return

        if amount < 0:
            raise ValueError("Experience amount cannot be negative.")

        import math
        if self.can_evolve(game=game):
            amount = math.floor(amount * 1.2)

        if self.status_effects.get("EXP Up"):
            amount = math.floor(amount * 1.5)

        if game and amount > 0 and hasattr(game, "party") and self in game.party:
            from game import get_pokemon_position
            px, py = get_pokemon_position(game, self)
            game.flash_damages[(px, py)] = (amount, "EXP")
            game.trigger_damage_flash()
        
        old_level = self._level
        old_stats = dict(self.stats)
        self.experience += amount

        leveled_up = False
        while True:
            if self._level >= 99:
                break
            next_level_req = self.get_experience_required_for_level(self._level + 1)
            if self.experience >= next_level_req:
                self._level += 1
                leveled_up = True
            else:
                break

        if leveled_up:
            self.learn_level_up_moves(game=game, old_level=old_level)
            self.recalculate_stats()

            if game and hasattr(game, "party") and self in game.party:
                game.log_message(f"{self.name} reached level {self._level}!")
                stat_changes = []
                for stat in VALID_STATS:
                    diff = self.stats[stat] - old_stats[stat]
                    if diff > 0:
                        stat_changes.append(f"{stat.replace('_', ' ')} +{diff}")
                if stat_changes:
                    game.log_message(", ".join(stat_changes))

        self.check_evolution_notifications(game=game)

    def recalculate_stats(self):
        """Recalculates the Pokémon's current stats (called when a Pokémon defeats an enemy)"""
        import math
        old_max_hp = self.stats.get("HP", 0) if hasattr(self, "stats") and self.stats else 0

        self.stats = {}
        for stat in VALID_STATS:
            base = self.species_data["base_stats"][stat]
            iv = self.ivs[stat]
            ev = self.evs[stat]
            level = self._level

            if stat == "HP":
                val = (((2 * base + iv + (ev / 2)) * level) / 100) + level + 10
                self.stats[stat] = math.floor(val)
            else:
                val = (((2 * base + iv + (ev / 2)) * level) / 100) + 5
                self.stats[stat] = math.floor(val)

        new_max_hp = float(self.stats["HP"])
        if not hasattr(self, "current_hp"):
            self.current_hp = new_max_hp
        else:
            if old_max_hp > 0:
                hp_diff = new_max_hp - float(old_max_hp)
                if hp_diff > 0:
                    self.current_hp += hp_diff
            self.current_hp = min(float(self.current_hp), new_max_hp)

    def gain_evs(self, ev_yield: dict[str, int], game=None):
        """Grants EVs to a Pokémon and recalculates stats."""
        old_stats = dict(self.stats)
        for stat, val in ev_yield.items():
            if stat in self.evs:
                if val < 0:
                    raise ValueError("EV yield value cannot be negative.")
                self.evs[stat] += val
        self.recalculate_stats()

        #Prints a stat increase message if a party member gains enough EVs to raise a stat
        if game and hasattr(game, "party") and self in game.party:
            for stat in VALID_STATS:
                diff = self.stats[stat] - old_stats[stat]
                if diff > 0:
                    formatted = stat.replace("_", " ")
                    game.log_message(f"{self.name}'s {formatted} increased by {diff}!")

    def defeat_pokemon(self, opponent: "Pokemon", game=None):
        """Gains EVs and EXP according to the defeated Pokémon's yields."""
        if int(getattr(self, "current_hp", 1)) <= 0:
            return

        import math
        import random

        #EV gain goes to defeater
        self.gain_evs(opponent.species_data.get("ev_yield", {}), game=game)

        #Calculate base total EXP yield
        exp_yield = opponent.species_data.get("exp_yield", 50)
        opponent_level = opponent.level
        post_evo_bonus = 1.2 if self.can_evolve(game=game) else 1.0
        
        total_exp = math.floor(((3 * exp_yield * opponent_level) / 14) * post_evo_bonus)

        #EXP is distributed to all party members if one of them defeated an enemy or attacked them
        is_team_defeater = game is not None and hasattr(game, "party") and self in game.party
        is_enemy_opponent = game is not None and hasattr(game, "party") and opponent not in game.party
        was_attacked_by_team = getattr(opponent, "has_been_attacked_by_team", False) or is_team_defeater

        if is_enemy_opponent:
            if was_attacked_by_team:
                if hasattr(game, "on_enemy_defeated"):
                    game.on_enemy_defeated(opponent, total_exp)
                if getattr(game, "exp_batching_active", False):
                    game.pending_team_exp = getattr(game, "pending_team_exp", 0) + total_exp
                else:
                    team_members = [p for p in game.party if int(getattr(p, "current_hp", 0)) > 0]
                    if team_members:
                        #Distribution is based on a party member's level. Lower level means more EXP
                        weights = [1.0 / float(p.level) for p in team_members]
                        total_weight = sum(weights)

                        shares: dict = {}
                        sum_allocated = 0
                        for p, w in zip(team_members, weights):
                            fraction = w / total_weight
                            allocated = math.floor(total_exp * fraction)
                            shares[p] = allocated
                            sum_allocated += allocated

                        remainder = total_exp - sum_allocated
                        #All EXP should go somewhere
                        if remainder > 0:
                            min_lvl = min(p.level for p in team_members)
                            lowest_pokes = [p for p in team_members if p.level == min_lvl]

                            #Prioritize team leader if leader is among the lowest level, or choose at random if not
                            leader_in_lowest = [p for p in lowest_pokes if p is getattr(game, "player_pokemon", None) or getattr(p, "is_leader", False)]
                            if leader_in_lowest:
                                chosen_recipient = leader_in_lowest[0]
                            else:
                                chosen_recipient = random.choice(lowest_pokes)

                            shares[chosen_recipient] += remainder

                        for p, share in shares.items():
                            if share > 0:
                                p.gain_experience(share, game=game)
                    else:
                        self.gain_experience(total_exp, game=game)
        else:
            self.gain_experience(total_exp, game=game)

        if game:
            allies = game.party if opponent in game.party else game.spawned_pokemon
            for ally in list(allies):
                if ally != opponent and int(getattr(ally, "current_hp", 0)) > 0:
                    ally.last_teammate_fainted_turn = getattr(game, "turn_number", 0)

    @property
    def species_name(self) -> str:
        """Returns the species name of the Pokémon."""
        return self.species_data.get("name", "Unknown")

    @property
    def types(self) -> list[str]:
        """Returns the current types of the Pokémon, incorporating temporary overrides like Soak."""
        if getattr(self, "temp_types", None) is not None:
            return self.temp_types  # type: ignore[return-value]
        return self.species_data.get("types", [])

    def get_modified_stat(self, stat_name: str, game=None) -> int:
        """Returns the stat value after applying temporary stat modifier stages and weather bonuses."""
        actual_stat_name = stat_name
        if game and getattr(game, "wonder_room_turns", 0) > 0:
            if stat_name == "Defense":
                actual_stat_name = "Special_Defense"
            elif stat_name == "Special_Defense":
                actual_stat_name = "Defense"

        base_val = self.stats.get(actual_stat_name, 1)
        stage = self.stat_modifiers.get(actual_stat_name, 0)
        
        #Clamp stat stages to [-6, +6] as a safety guard
        stage = max(-6, min(6, stage))

        if stage >= 0:
            multiplier = (2.0 + stage) / 2.0
        else:
            multiplier = 2.0 / (2.0 + abs(stage))
            
        import math
        val = max(1, math.floor(base_val * multiplier))

        #Apply weather-based boosts (Defense / Special Defense)
        if game and hasattr(game, "weather"):
            p_types = self.types
            if actual_stat_name in ("Defense", "Special_Defense"):
                if game.weather == "Hail" and "Ice" in p_types:
                    val = max(1, math.floor(val * 1.33))
                elif game.weather == "Sandstorm" and "Ground" in p_types:
                    val = max(1, math.floor(val * 1.33))

        #Apply status effect changes
        if actual_stat_name == "Attack" and self.status_effects.get("Burn"):
            val = max(1, math.floor(val * 0.5))
        if actual_stat_name in ("Defense", "Special_Defense") and (self.status_effects.get("Sleep", 0) > 0 or self.status_effects.get("Resting", 0) > 0):
            val = max(1, math.floor(val * 0.5))
        if actual_stat_name == "Special_Attack" and (self.status_effects.get("Poison") or self.status_effects.get("Toxic")):
            val = max(1, math.floor(val * 0.5))
        if actual_stat_name == "Defense" and self.status_effects.get("Reflect", 0) > 0:
            val = max(1, math.floor(val * 2.0))
        if actual_stat_name == "Special_Defense" and self.status_effects.get("Light Screen", 0) > 0:
            val = max(1, math.floor(val * 2.0))

        return val

    def apply_stat_modifier(self, stat: str, stages: int, game):
        """Applies a temporary stat modifier to the Pokémon."""
        if stages == 0:
            return

        display_names = {
            "Attack": "Attack",
            "Defense": "Defense",
            "Special_Attack": "Sp. Attack",
            "Special_Defense": "Sp. Defense",
            "Speed": "Speed",
            "Accuracy": "Accuracy",
            "Evasion": "Evasion"
        }
        display_stat = display_names.get(stat, stat)

        current = self.stat_modifiers.get(stat, 0)

        if stages < 0:
            if game and getattr(game, "weather", None) == "Mist":
                game.log_message(f"Mist protected {self.name}'s stats!")
                return
            if current <= -6:
                game.log_message(f"{self.name}'s {display_stat} cannot go any lower.")
                return
            new_stage = max(-6, current + stages)
            self.stat_modifiers[stat] = new_stage
            
            abs_stages = abs(stages)
            if abs_stages == 1:
                game.log_message(f"{self.name}'s {display_stat} fell!")
            elif abs_stages == 2:
                game.log_message(f"{self.name}'s {display_stat} fell sharply!")
            else:
                game.log_message(f"{self.name}'s {display_stat} fell severely!")
        else:
            if current >= 6:
                game.log_message(f"{self.name}'s {display_stat} cannot go any higher.")
                return
            new_stage = min(6, current + stages)
            self.stat_modifiers[stat] = new_stage

            if stages == 1:
                game.log_message(f"{self.name}'s {display_stat} rose!")
            elif stages == 2:
                game.log_message(f"{self.name}'s {display_stat} rose sharply!")
            else:
                game.log_message(f"{self.name}'s {display_stat} rose drastically!")

    def change_movement_speed(self, new_stage: int, game):
        """Changes the Pokémon's movement speed stage (between -1 and 3) and sets the temporary turn duration. (-1 = slowed, 1 = 2x speed, 2 = 3x speed, 3 = 4x speed)"""
        orig_suppress = getattr(game, "suppress_target_logs", False) if game else False
        if game and hasattr(game, "is_in_team_sight") and not game.is_in_team_sight(self):
            game.suppress_target_logs = True
        try:
            self._change_movement_speed_internal(new_stage, game)
        finally:
            if game:
                game.suppress_target_logs = orig_suppress

    def _change_movement_speed_internal(self, new_stage: int, game):
        old_stage = self.movement_speed_stage

        #Check boundary conditions when already at max/min speed
        if old_stage >= 3 and new_stage >= 3:
            if game:
                game.log_message(f"{self.name} can't go any faster!")
            return
        if old_stage <= -1 and new_stage <= -1:
            if game:
                game.log_message(f"{self.name} can't go any slower!")
            return

        #Clamp to [-1, 3]
        new_stage = max(-1, min(3, new_stage))
        if new_stage == old_stage:
            return

        self.movement_speed_stage = new_stage

        #Define duration
        if new_stage == -1:
            self.movement_speed_duration = 10
        elif new_stage == 1:
            self.movement_speed_duration = 10
        elif new_stage == 2:
            self.movement_speed_duration = 7
        elif new_stage == 3:
            self.movement_speed_duration = 5
        else:
            self.movement_speed_duration = 0

        #Reset slow turn toggle on speed change for safety
        self.slow_turn_toggle = False

        #Print message to log
        if game:
            if new_stage == -1:
                game.log_message(f"{self.name} was slowed!")
            elif new_stage == 0:
                game.log_message(f"{self.name} returned to normal speed.")
            elif new_stage == 1:
                game.log_message(f"{self.name} is moving at double speed!")
            elif new_stage == 2:
                game.log_message(f"{self.name} is moving at triple speed!")
            elif new_stage == 3:
                game.log_message(f"{self.name} is moving at quadruple speed!")

    def apply_status(self, status: str, game, duration: int | None = None):
        """Applies a negative status effect to the Pokémon and prints the log message."""
        orig_suppress = getattr(game, "suppress_target_logs", False) if game else False
        if game and hasattr(game, "is_in_team_sight") and not game.is_in_team_sight(self):
            game.suppress_target_logs = True
        try:
            self._apply_status_internal(status, game, duration=duration)
        finally:
            if game:
                game.suppress_target_logs = orig_suppress

    def _apply_status_internal(self, status: str, game, duration: int | None = None):
        """Applies a negative status effect to the Pokémon and prints the log message."""
        import random
        
        #Type immunities for specific status effects
        p_types = self.types
        if status in ("Poison", "Toxic") and any(t in p_types for t in ("Poison", "Steel")):
            return
        if status == "Burn" and "Fire" in p_types:
            return
        if status == "Paralysis" and "Electric" in p_types:
            return
        if status == "Frozen" and any(t in p_types for t in ("Fire", "Ice")):
            return

        #Check Safeguard protection
        if status in ("Sleep", "Paralysis", "Poison", "Toxic", "Burn", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Fire Spin", "Slow", "Stuck", "Curse", "Drowsy", "Whirlpool", "Perishing", "Terrified", "Puppet", "Hallucinating", "Blind"):
            if self.status_effects.get("Safeguard", 0) > 0:
                game.log_message(f"{self.name} is protected by Safeguard!")
                return

        #Check Electric Terrain immunity for non-Flying Pokemon
        if status in ("Sleep", "Resting", "Drowsy"):
            if game and getattr(game, "weather", None) == "Electric Terrain":
                p_types = getattr(self, "temp_types", None) or self.species_data.get("types", [])
                if "Flying" not in p_types:
                    return

        if status == "Sleep":
            if self.status_effects.get("Sleepless"):
                return
            self.status_effects["Sleep"] = duration if duration is not None else random.randint(3, 6)
            game.log_message(f"{self.name} fell asleep!")
            if self.charging_move:
                c_move_name = self.charging_move.get("move", {}).get("name", "move")
                game.log_message(f"{self.name}'s {c_move_name} was interrupted!")
                self.charging_move = None
                if self.status_effects.get("Digging", 0) > 0:
                    self.status_effects["Digging"] = 0
                if self.status_effects.get("Diving", 0) > 0:
                    self.status_effects["Diving"] = 0
        elif status == "Resting":
            if self.status_effects.get("Sleepless"):
                return
            self.status_effects["Resting"] = 3
            game.log_message(f"{self.name} went to sleep!")
        elif status == "Paralysis":
            self.status_effects["Paralysis"] = 5
            game.log_message(f"{self.name} became paralyzed!")
        elif status == "Poison":
            self.status_effects["Poison"] = True
            game.log_message(f"{self.name} was poisoned!")
        elif status == "Toxic":
            self.status_effects["Toxic"] = True
            game.log_message(f"{self.name} was badly poisoned!")
        elif status == "Burn":
            if self.status_effects.get("Frozen", 0) > 0:
                #Can't burn a frozen target or frozen cures it, let's just ignore or thaw
                return
            if hasattr(game, "weather") and game.weather == "Rain":
                #Rain prevents burn
                return
            self.status_effects["Burn"] = True
            game.log_message(f"{self.name} sustained a burn!")
        elif status == "Frozen":
            self.status_effects["Frozen"] = duration if duration is not None else random.randint(3, 6)
            game.log_message(f"{self.name} was frozen solid!")
            #Being frozen cures burn
            if self.status_effects.get("Burn"):
                self.cure_status("Burn", game)
        elif status == "Flinch":
            self.status_effects["Flinch"] = 1
            game.log_message(f"{self.name} flinched!")
        elif status == "Petrified":
            is_team = hasattr(game, "party") and self in game.party
            self.status_effects["Petrified"] = 20 if is_team else -1
            game.log_message(f"{self.name} became petrified!")
        elif status == "Confusion":
            if self.status_effects.get("Confusion", 0) > 0:
                game.log_message(f"{self.name} is already confused.")
                return
            self.status_effects["Confusion"] = duration if duration is not None else random.randint(6, 10)
            game.log_message(f"{self.name} became confused!")
        elif status == "Leech Seed":
            self.status_effects["Leech Seed"] = duration if duration is not None else random.randint(6, 9)
            game.log_message(f"{self.name} was seeded!")
        elif status == "Sleepless":
            self.status_effects["Sleepless"] = True
            game.log_message(f"{self.name} became sleepless!")
            self.napping = False
            if self.status_effects.get("Sleep", 0) > 0:
                self.cure_status("Sleep", game)
            if self.status_effects.get("Drowsy", 0) > 0:
                self.cure_status("Drowsy", game)
            if self.status_effects.get("Resting", 0) > 0:
                self.cure_status("Resting", game, early=True)
        elif status == "Fire Spin":
            self.status_effects["Fire Spin"] = duration if duration is not None else random.randint(2, 5)
            game.log_message(f"{self.name} became trapped by Fire Spin!")
        elif status == "Protect":
            self.status_effects["Protect"] = duration if duration is not None else 1
            game.log_message(f"{self.name} protected itself!")
        elif status == "Safeguard":
            self.status_effects["Safeguard"] = duration if duration is not None else random.randint(10, 15)
            game.log_message(f"{self.name} is protected by Safeguard!")
        elif status == "Slow":
            self.change_movement_speed(-1, game)
        elif status == "2x Speed":
            self.change_movement_speed(self.movement_speed_stage + 1, game)
        elif status == "3x Speed":
            self.change_movement_speed(self.movement_speed_stage + 2, game)
        elif status == "4x Speed":
            self.change_movement_speed(self.movement_speed_stage + 3, game)
        elif status == "Laser Focus":
            self.status_effects["Laser Focus"] = True
            game.log_message(f"{self.name} focused its sights!")
        elif status == "Focus Energy":
            self.status_effects["Focus Energy"] = duration if duration is not None else 3
            game.log_message(f"{self.name} is getting pumped!")
        elif status == "Charging":
            self.status_effects["Charging"] = duration if duration is not None else 1
            if game:
                game.log_message(f"{self.name} began charging power!")
        elif status == "Wrap":
            self.status_effects["Wrap"] = duration if duration is not None else random.randint(2, 5)
            game.log_message(f"{self.name} was wrapped!")
        elif status == "Light Screen":
            self.status_effects["Light Screen"] = duration if duration is not None else 10
            game.log_message(f"{self.name} is protected by Light Screen!")
        elif status == "Reflect":
            self.status_effects["Reflect"] = duration if duration is not None else 10
            game.log_message(f"{self.name} is protected by Reflect!")
        elif status == "Sand Tomb":
            self.status_effects["Sand Tomb"] = duration if duration is not None else random.randint(2, 5)
            game.log_message(f"{self.name} became trapped by Sand Tomb!")
        elif status == "Digging":
            self.status_effects["Digging"] = duration if duration is not None else 1
            game.log_message(f"{self.name} dug a hole!")
        elif status == "Encore":
            self.status_effects["Encore"] = duration if duration is not None else random.randint(5, 8)
            game.log_message(f"{self.name} received an Encore!")
        elif status == "Magnet Rise":
            self.status_effects["Magnet Rise"] = duration if duration is not None else 5
            game.log_message(f"{self.name} levitated with Magnet Rise!")
        elif status == "Telekinesis":
            self.status_effects["Telekinesis"] = duration if duration is not None else 3
            game.log_message(f"{self.name} was floated by Telekinesis!")
        elif status == "Stuck":
            self.status_effects["Stuck"] = duration if duration is not None else random.randint(5, 7)
            game.log_message(f"{self.name} became stuck!")
        elif status == "Quick Guard":
            self.status_effects["Quick Guard"] = duration if duration is not None else 1
            game.log_message(f"{self.name} is protected by Quick Guard!")
        elif status == "Wide Guard":
            self.status_effects["Wide Guard"] = duration if duration is not None else 1
            game.log_message(f"{self.name} is protected by Wide Guard!")
        elif status == "Vital Throw":
            self.status_effects["Vital Throw"] = duration if duration is not None else random.randint(15, 20)
            game.log_message(f"{self.name} readied Vital Throw!")
        elif status == "Taunted":
            self.status_effects["Taunted"] = True
            game.log_message(f"{self.name} fell for the Taunt!")
        elif status == "Curse":
            self.status_effects["Curse"] = True
            game.log_message(f"{self.name} was cursed!")
        elif status == "Decoy":
            self.status_effects["Decoy"] = duration if duration is not None else 6
            game.log_message(f"{self.name} became a Decoy!")
        elif status == "Pierce Throw":
            self.status_effects["Pierce Throw"] = True
            game.log_message(f"{self.name} gained Pierce Throw status!")
        elif status == "Rebound":
            self.status_effects["Rebound"] = duration if duration is not None else 10
            game.log_message(f"{self.name} gained Rebound status!")
        elif status == "Cowering":
            self.status_effects["Cowering"] = duration if duration is not None else random.randint(4, 6)
            game.log_message(f"{self.name} began cowering!")
        elif status == "Silenced":
            self.status_effects["Silenced"] = duration if duration is not None else random.randint(5, 8)
            game.log_message(f"{self.name} was silenced!")
        elif status == "Snatch":
            self.status_effects["Snatch"] = duration if duration is not None else random.randint(10, 15)
            game.log_message(f"{self.name} is ready to Snatch!")
        elif status == "Landed":
            self.status_effects["Landed"] = duration if duration is not None else 1
        elif status == "Drowsy":
            if self.status_effects.get("Sleepless") or self.status_effects.get("Sleep", 0) > 0:
                return
            if self.status_effects.get("Drowsy", 0) > 0:
                game.log_message(f"{self.name} is already drowsy.")
                return
            self.status_effects["Drowsy"] = duration if duration is not None else 3
            game.log_message(f"{self.name} became drowsy!")
        elif status == "Lock-On":
            self.status_effects["Lock-On"] = True
            game.log_message(f"{self.name} took aim!")
        elif status == "Aqua Ring":
            self.status_effects["Aqua Ring"] = True
            game.log_message(f"{self.name} surrounded itself with a veil of water!")
        elif status == "Diving":
            self.status_effects["Diving"] = duration if duration is not None else 1
            game.log_message(f"{self.name} dived underwater!")
        elif status == "Minimized":
            self.status_effects["Minimized"] = True
        elif status == "Whirlpool":
            self.status_effects["Whirlpool"] = duration if duration is not None else random.randint(2, 5)
            game.log_message(f"{self.name} became trapped by Whirlpool!")
        elif status == "Perishing":
            if self.status_effects.get("Perishing", 0) > 0:
                game.log_message(f"{self.name} already heard the song!")
                return
            self.status_effects["Perishing"] = duration if duration is not None else 5
            game.log_message(f"{self.name} heard the Perish Song!")
        elif status == "Counter":
            self.status_effects["Counter"] = duration if duration is not None else random.randint(7, 10)
            game.log_message(f"{self.name} readied Counter!")
        elif status == "Destiny Bond":
            self.status_effects["Destiny Bond"] = duration if duration is not None else 6
            game.log_message(f"{self.name} is trying to take down its foes with it!")
        elif status == "Focusing":
            self.status_effects["Focusing"] = True
            game.log_message(f"{self.name} is focusing its mind!")
        elif status == "Mirror Coat":
            self.status_effects["Mirror Coat"] = duration if duration is not None else random.randint(7, 10)
            game.log_message(f"{self.name} readied Mirror Coat!")
        elif status == "Endure":
            self.status_effects["Endure"] = duration if duration is not None else random.randint(2, 3)
            game.log_message(f"{self.name} is set to endure!")
        elif status == "Paused":
            self.status_effects["Paused"] = duration if duration is not None else 1
            game.log_message(f"{self.name} must recharge!")
        elif status == "Ingrain":
            self.status_effects["Ingrain"] = duration if duration is not None else random.randint(10, 15)
            game.log_message(f"{self.name} planted its roots!")
        elif status in ("Light Screen", "Reflect"):
            self.status_effects[status] = duration if duration is not None else random.randint(5, 7)
            game.log_message(f"{self.name}'s {status} took effect!")
        elif status == "Terrified":
            self.status_effects["Terrified"] = duration if duration is not None else random.randint(10, 15)
            game.log_message(f"{self.name} became terrified!")
        elif status == "Blind":
            self.status_effects["Blind"] = duration if duration is not None else 10
            game.log_message(f"{self.name} was blinded!")
        elif status == "Hallucinating":
            self.status_effects["Hallucinating"] = duration if duration is not None else 10
            game.log_message(f"{self.name} can't see straight!")
        elif status == "Sluggish":
            self.status_effects["Sluggish"] = duration if duration is not None else 99999
            game.log_message(f"{self.name} was slowed!")
        elif status == "Invisible":
            self.status_effects["Invisible"] = duration if duration is not None else 10
            game.log_message(f"{self.name} vanished from sight!")
        elif status == "Power Toss":
            self.status_effects["Power Toss"] = duration if duration is not None else 99999
            game.log_message(f"{self.name}'s throws became more powerful!")
        elif status == "Mobile":
            self.status_effects["Mobile"] = duration if duration is not None else 99999
            game.log_message(f"{self.name} can walk through walls!")
        elif status == "Decoy":
            self.status_effects["Decoy"] = duration if duration is not None else 99999
            game.log_message(f"{self.name} became a Decoy!")
        elif status == "Puppet":
            # Only intended to be obtainable by teammate Pokémon
            is_team = hasattr(game, "party") and self in game.party
            if not is_team:
                return
            if self.status_effects.get("Puppet", 0) > 0:
                return
            self.status_effects["Puppet"] = duration if duration is not None else random.randint(5, 8)
            game.log_message(f"{self.name} became a puppet!")

    def cure_status(self, status: str, game, early: bool = False):
        """Cures a status effect from the Pokémon and prints the log message if it was active."""
        orig_suppress = getattr(game, "suppress_target_logs", False) if game else False
        if game and hasattr(game, "is_in_team_sight") and not game.is_in_team_sight(self):
            game.suppress_target_logs = True
        try:
            self._cure_status_internal(status, game, early=early)
        finally:
            if game:
                game.suppress_target_logs = orig_suppress

    def _cure_status_internal(self, status: str, game, early: bool = False):
        if status == "Sleep":
            if self.status_effects.get("Sleep", 0) > 0:
                self.status_effects["Sleep"] = 0
                game.log_message(f"{self.name} woke up.")
        elif status == "Minimized":
            self.status_effects["Minimized"] = False
        elif status == "Lock-On":
            self.status_effects["Lock-On"] = False
        elif status == "Drowsy":
            if self.status_effects.get("Drowsy", 0) > 0:
                self.status_effects["Drowsy"] = 0
                if not self.status_effects.get("Sleepless"):
                    self.apply_status("Sleep", game)
        elif status == "Resting":
            if self.status_effects.get("Resting", 0) > 0:
                self.status_effects["Resting"] = 0
                game.log_message(f"{self.name} woke up from resting.")
                if early:
                    heal_amt = int(float(self.stats["HP"]) * 0.5)
                    self.current_hp = min(float(self.stats["HP"]), self.current_hp + heal_amt)
                    game.log_message(f"{self.name} restored {heal_amt} HP.")
                else:
                    self.current_hp = float(self.stats["HP"])
                    game.log_message(f"{self.name} fully restored its HP!")
                    for neg_status in ["Sleep", "Paralysis", "Poison", "Toxic", "Burn", "Frozen", "Flinch", "Petrified", "Confusion", "Leech Seed", "Slow", "Encore", "Taunted", "Puppet"]:
                        self.cure_status(neg_status, game)
        elif status == "Paralysis":
            if self.status_effects.get("Paralysis", 0) > 0:
                self.status_effects["Paralysis"] = 0
                game.log_message(f"{self.name} was freed from paralysis.")
        elif status == "Poison":
            if self.status_effects.get("Poison"):
                self.status_effects["Poison"] = False
                game.log_message(f"{self.name} was cured of its poisoning.")
        elif status == "Decoy":
            if self.status_effects.get("Decoy", 0) > 0:
                self.status_effects["Decoy"] = 0
                game.log_message(f"{self.name} is no longer a decoy.")
        elif status == "Landed":
            if self.status_effects.get("Landed", 0) > 0:
                self.status_effects["Landed"] = 0
                game.log_message(f"{self.name} is no longer landed.")
        elif status == "Toxic":
            if self.status_effects.get("Toxic"):
                self.status_effects["Toxic"] = False
                game.log_message(f"{self.name} was cured of its bad poisoning.")
        elif status == "Burn":
            if self.status_effects.get("Burn"):
                self.status_effects["Burn"] = False
                game.log_message(f"{self.name}'s burn was healed.")
        elif status == "Frozen":
            if self.status_effects.get("Frozen", 0) > 0:
                self.status_effects["Frozen"] = 0
                game.log_message(f"{self.name} thawed out.")
        elif status == "Flinch":
            if self.status_effects.get("Flinch", 0) > 0:
                self.status_effects["Flinch"] = 0
                game.log_message(f"{self.name} is no longer flinching.")
        elif status == "Petrified":
            val = self.status_effects.get("Petrified", 0)
            if val > 0 or val == -1:
                self.status_effects["Petrified"] = 0
                game.log_message(f"{self.name} can move again.")
        elif status == "Confusion":
            if self.status_effects.get("Confusion", 0) > 0:
                self.status_effects["Confusion"] = 0
                game.log_message(f"{self.name} snapped out of confusion.")
        elif status == "Leech Seed":
            if self.status_effects.get("Leech Seed", 0) > 0:
                self.status_effects["Leech Seed"] = 0
                game.log_message(f"{self.name} is no longer seeded.")
                if hasattr(game, "leech_seed_sources") and self in game.leech_seed_sources:
                    del game.leech_seed_sources[self]
        elif status == "Blind":
            if self.status_effects.get("Blind", 0) > 0:
                self.status_effects["Blind"] = 0
                game.log_message(f"{self.name}'s vision returned to normal!")
        elif status == "Hallucinating":
            if self.status_effects.get("Hallucinating", 0) > 0:
                self.status_effects["Hallucinating"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer hallucinating.")
        elif status == "Sleepless":
            if self.status_effects.get("Sleepless"):
                self.status_effects["Sleepless"] = False
                game.log_message(f"{self.name} is no longer sleepless.")
        elif status == "Fire Spin":
            if self.status_effects.get("Fire Spin", 0) > 0:
                self.status_effects["Fire Spin"] = 0
                game.log_message(f"{self.name} was freed from Fire Spin.")
        elif status == "Whirlpool":
            if self.status_effects.get("Whirlpool", 0) > 0:
                self.status_effects["Whirlpool"] = 0
                game.log_message(f"{self.name} was freed from Whirlpool.")
        elif status == "Perishing":
            if self.status_effects.get("Perishing", 0) > 0:
                self.status_effects["Perishing"] = 0
                game.log_message(f"{self.name} was cured of Perish Song.")
        elif status == "Counter":
            if self.status_effects.get("Counter", 0) > 0:
                self.status_effects["Counter"] = 0
                game.log_message(f"{self.name}'s Counter wore off.")
        elif status == "Mirror Coat":
            if self.status_effects.get("Mirror Coat", 0) > 0:
                self.status_effects["Mirror Coat"] = 0
                game.log_message(f"{self.name}'s Mirror Coat wore off.")
        elif status == "Endure":
            if self.status_effects.get("Endure", 0) > 0:
                self.status_effects["Endure"] = 0
                game.log_message(f"{self.name}'s Endure wore off.")
        elif status == "Paused":
            if self.status_effects.get("Paused", 0) > 0:
                self.status_effects["Paused"] = 0
                game.log_message(f"{self.name} is no longer paused.")
        elif status == "Ingrain":
            if self.status_effects.get("Ingrain", 0) > 0:
                self.status_effects["Ingrain"] = 0
                game.log_message(f"{self.name} unrooted itself.")
        elif status in ("Light Screen", "Reflect"):
            if self.status_effects.get(status, 0) > 0:
                self.status_effects[status] = 0
                game.log_message(f"{self.name}'s {status} wore off.")
        elif status == "Destiny Bond":
            if self.status_effects.get("Destiny Bond", 0) > 0:
                self.status_effects["Destiny Bond"] = 0
                game.log_message(f"{self.name}'s Destiny Bond wore off.")
        elif status == "Focusing":
            if self.status_effects.get("Focusing"):
                self.status_effects["Focusing"] = False
        elif status == "Protect":
            if self.status_effects.get("Protect", 0) > 0:
                self.status_effects["Protect"] = 0
                game.log_message(f"{self.name} is no longer protecting itself.")
        elif status == "Safeguard":
            if self.status_effects.get("Safeguard", 0) > 0:
                self.status_effects["Safeguard"] = 0
                game.log_message(f"{self.name}'s Safeguard wore off.")
        elif status == "Slow":
            if self.movement_speed_stage < 0:
                self.change_movement_speed(0, game)
        elif status == "Laser Focus":
            if self.status_effects.get("Laser Focus"):
                self.status_effects["Laser Focus"] = False
        elif status == "Focus Energy":
            if self.status_effects.get("Focus Energy", 0) > 0:
                self.status_effects["Focus Energy"] = 0
                game.log_message(f"{self.name} is no longer getting pumped.")
        elif status == "Wrap":
            if self.status_effects.get("Wrap", 0) > 0:
                self.status_effects["Wrap"] = 0
                game.log_message(f"{self.name} was freed from Wrap.")
        elif status == "Light Screen":
            if self.status_effects.get("Light Screen", 0) > 0:
                self.status_effects["Light Screen"] = 0
                game.log_message(f"{self.name}'s Light Screen wore off.")
        elif status == "Reflect":
            if self.status_effects.get("Reflect", 0) > 0:
                self.status_effects["Reflect"] = 0
                game.log_message(f"{self.name}'s Reflect wore off.")
        elif status == "Sand Tomb":
            if self.status_effects.get("Sand Tomb", 0) > 0:
                self.status_effects["Sand Tomb"] = 0
                game.log_message(f"{self.name} was freed from Sand Tomb.")
        elif status == "Digging":
            if self.status_effects.get("Digging", 0) > 0:
                self.status_effects["Digging"] = 0
                game.log_message(f"{self.name} emerged from the ground.")
        elif status == "Encore":
            if self.status_effects.get("Encore", 0) > 0:
                self.status_effects["Encore"] = 0
                game.log_message(f"{self.name}'s Encore ended.")
        elif status == "Magnet Rise":
            if self.status_effects.get("Magnet Rise", 0) > 0:
                self.status_effects["Magnet Rise"] = 0
                game.log_message(f"{self.name}'s Magnet Rise wore off.")
        elif status == "Telekinesis":
            if self.status_effects.get("Telekinesis", 0) > 0:
                self.status_effects["Telekinesis"] = 0
                game.log_message(f"{self.name}'s Telekinesis wore off.")
        elif status == "Stuck":
            if self.status_effects.get("Stuck", 0) > 0:
                self.status_effects["Stuck"] = 0
                game.log_message(f"{self.name} is no longer stuck.")
        elif status == "Quick Guard":
            if self.status_effects.get("Quick Guard", 0) > 0:
                self.status_effects["Quick Guard"] = 0
                game.log_message(f"{self.name}'s Quick Guard wore off.")
        elif status == "Wide Guard":
            if self.status_effects.get("Wide Guard", 0) > 0:
                self.status_effects["Wide Guard"] = 0
                game.log_message(f"{self.name}'s Wide Guard wore off.")
        elif status == "Vital Throw":
            if self.status_effects.get("Vital Throw", 0) > 0:
                self.status_effects["Vital Throw"] = 0
                game.log_message(f"{self.name}'s Vital Throw stance ended.")
        elif status == "Taunted":
            if self.status_effects.get("Taunted"):
                self.status_effects["Taunted"] = False
                game.log_message(f"{self.name} is no longer Taunted.")
                if hasattr(game, "taunt_sources") and self in game.taunt_sources:
                    del game.taunt_sources[self]
        elif status == "Aqua Ring":
            if self.status_effects.get("Aqua Ring"):
                self.status_effects["Aqua Ring"] = False
                game.log_message(f"{self.name}'s Aqua Ring disappated.")
        elif status == "Diving":
            if self.status_effects.get("Diving", 0) > 0:
                self.status_effects["Diving"] = 0
        elif status == "Charging":
            if self.status_effects.get("Charging", 0) > 0:
                self.status_effects["Charging"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer charging.")
        elif status == "Landed":
            if self.status_effects.get("Landed", 0) > 0:
                self.status_effects["Landed"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer grounded.")
        elif status == "Terrified":
            if self.status_effects.get("Terrified", 0) > 0:
                self.status_effects["Terrified"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer terrified.")
        elif status == "Mobile":
            if self.status_effects.get("Mobile", 0) > 0:
                self.status_effects["Mobile"] = 0
                if game:
                    game.log_message(f"{self.name}'s Mobile status wore off.")
                    if hasattr(game, "ensure_valid_position"):
                        game.ensure_valid_position(self)
        elif status == "Puppet":
            if self.status_effects.get("Puppet", 0) > 0:
                self.status_effects["Puppet"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer a puppet.")
        elif status == "Snatch":
            if self.status_effects.get("Snatch", 0) > 0:
                self.status_effects["Snatch"] = 0
                if game:
                    game.log_message(f"{self.name}'s Snatch wore off.")
        elif status == "Cowering":
            if self.status_effects.get("Cowering", 0) > 0:
                self.status_effects["Cowering"] = 0
                if game:
                    game.log_message(f"{self.name} stopped cowering.")
        elif status == "Rebound":
            if self.status_effects.get("Rebound", 0) > 0:
                self.status_effects["Rebound"] = 0
                if game:
                    game.log_message(f"{self.name}'s Rebound wore off.")
        elif status == "Silenced":
            if self.status_effects.get("Silenced", 0) > 0:
                self.status_effects["Silenced"] = 0
                if game:
                    game.log_message(f"{self.name} is no longer silenced.")
        elif status == "Invisible":
            if self.status_effects.get("Invisible", 0) > 0:
                self.status_effects["Invisible"] = 0
                if game:
                    game.log_message(f"{self.name} reappeared.")

