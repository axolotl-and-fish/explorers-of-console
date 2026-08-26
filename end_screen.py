"""
end_screen.py

Generates the uncolored end screen statistics report, formats digit grouping,
renders the scrollable End Screen UI, handles text file dumps to team_dumps/,
and manages input for scroll/dump/quit.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import re
import math
import time
import sys
import datetime
from items import ITEMS_DB
import input as game_input


def strip_ansi(text: str) -> str:
    """Strips all ANSI escape sequences from a string."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)


def fmt(val: int | float, decimals: int = 0) -> str:
    """Formats numbers with digit grouping commas (e.g. 1,234)."""
    return f"{int(val):,}"


def get_item_value(item: dict) -> int:
    """Returns the total value of an item stack in inventory."""
    name = item.get("name", "")
    unit_val = item.get("value", ITEMS_DB.get(name, {}).get("value", 0))
    count = item.get("count", 1) if item.get("stackable", False) else 1
    return unit_val * count


def generate_end_screen_report(game, game_won: bool) -> list[str]:
    """Generates complete uncolored text report lines for the End Screen."""
    lines: list[str] = []

    # Calculate variables for score
    total_exp = getattr(game, "total_enemy_exp", 0)

    inventory = getattr(game, "inventory", [])
    item_value = sum(get_item_value(item) for item in inventory)

    wallet = getattr(game, "money", 0)
    floor_num = getattr(game, "floor_number", 1)
    recruited_count = getattr(game, "total_recruited_count", 0)
    turns = getattr(game, "turn_number", 0) or getattr(game, "turn_count", 0)
    end_bonus = 1.5 if game_won else 1.0

    base_val = total_exp + item_value + (wallet * 10)
    floor_recruit_sum = floor_num + recruited_count
    subtotal = base_val * floor_recruit_sum
    turn_divider = 1.0 + math.sqrt(turns)
    raw_score = (subtotal * end_bonus) / turn_divider
    final_score = math.floor(raw_score)

    if game and not getattr(game, "_high_score_saved", False):
        game._high_score_saved = True
        floor_val = "**" if game_won else floor_num
        now_iso = datetime.datetime.now().isoformat()
        try:
            from high_scores import add_high_score
            add_high_score(
                score=final_score,
                floor=floor_val,
                turns=turns,
                dt_iso=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            )
            floor_str = "**" if str(floor_val) == "**" else f"{int(floor_val):02d}"[:2]
            game.last_run_score_entry = {
                "score": min(9999999, max(0, int(final_score))),
                "floor": floor_str,
                "turns": min(999999, max(0, int(turns))),
                "datetime": now_iso
            }
        except Exception:
            pass

    #Ranks
    if final_score >= 1000000:
        rank = "Swampert Loaf Rank"
    elif final_score >= 750000:
        rank = "Grandmaster Rank"
    elif final_score >= 500000:
        rank = "Master Rank"
    elif final_score >= 300000:
        rank = "Hyper Rank"
    elif final_score >= 200000:
        rank = "Ultra Rank"
    elif final_score >= 100000:
        rank = "Ace Rank"
    elif final_score >= 75000:
        rank = "Emerald Rank"
    elif final_score >= 50000:
        rank = "Sapphire Rank"
    elif final_score >= 40000:
        rank = "Ruby Rank"
    elif final_score >= 30000:
        rank = "Diamond Rank"
    elif final_score >= 20000:
        rank = "Pearl Rank"
    elif final_score >= 15000:
        rank = "Platinum Rank"
    elif final_score >= 10000:
        rank = "Gold Rank"
    elif final_score >= 6000:
        rank = "Silver Rank"
    elif final_score >= 3000:
        rank = "Bronze Rank"
    elif final_score >= 1000:
        rank = "Normal Rank"
    else:
        rank = "Rookie Rank"

    # Title Banner
    if game_won:
        lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒PMD:▒Explorers▒of▒the▒Console▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")
        lines.append("▒ █   █  ██   █  ██   ██ ███ █ █ █    ██ ███ █  █  ██   █ █▒")
        lines.append("▒█ █ █ █ █ █ █ █ █ █ █ █  █  █ █ █   █ █  █  █ █ █ █ █ █ ██▒")
        lines.append("▒█   █ █ █ █ █   █ █ █ █  █  █ █ █   █ █  █  █ █ █ █ █ █  █▒")
        lines.append("▒█   █ █ █ █ █   █ █ █ █  █  █ █ █   █ █  █  █ █ █ █ █  █ █▒")
        lines.append("▒█   █ █ █ █ █ █ █ █ █ █  █  █ █ █   █ █  █  █ █ █ █ █   ██▒")
        lines.append("▒█   █ █ █ █ █ █ ██  ███  █  █ █ █   ███  █  █ █ █ █ █   ██▒")
        lines.append("▒█ █ █ █ █ █ █ █ █ █ █ █  █  █ █ █   █ █  █  █ █ █ █ █ █ █ ▒")
        lines.append("▒ █   █  █ █  ██ █ █ █ █  █   ██ ███ █ █  █  █  █  █ █  █ █▒")
        lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ver.▒0.1.0▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")

        
    else:
        lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒PMD:▒Explorers▒of▒the▒Console▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")
        lines.append("▒     ███     ██ █   █ █████     ███  █   █ █████ ████     ▒")
        lines.append("▒    █   █   █ █ ██ ██ █        █   █ █   █ █     █   █    ▒")
        lines.append("▒    █      █  █ ██ ██ █        █   █ █   █ █     █   █    ▒")
        lines.append("▒    █     █   █ █ █ █ ████     █   █  █ █  ████  █   █    ▒")
        lines.append("▒    █ ███ █   █ █ █ █ █        █   █  █ █  █     █   █    ▒")
        lines.append("▒    █   █ █████ █ █ █ █        █   █  █ █  █     ████     ▒")
        lines.append("▒    █   █ █   █ █   █ █        █   █   █   █     █  █     ▒")
        lines.append("▒     ████ █   █ █   █ █████     ███    █   █████ █   █    ▒")
        lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ver.▒0.1.0▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")

    # ---------------------------------------------------------
    # SECTION 1: FINAL SCORE CALCULATION
    # ---------------------------------------------------------
    lines.append("─────────────────YOUR SCORE───────────────────")
    lines.append(f"TOTAL EXP GAINED:                {fmt(total_exp):>11}")
    lines.append("──────────────────────+───────────────────────")
    lines.append(f"Total inventory value:           {fmt(item_value):>11}")
    lines.append(f"Money:                          +{fmt(wallet):>11}x10")
    lines.append(f"= PLAYER NET WORTH SCORE:        {fmt(base_val):>11}")
    lines.append("──────────────────────x───────────────────────")
    lines.append(f"Floor reached:                   {fmt(floor_num):>11}")
    lines.append(f"Recruited Pokémon:              +{fmt(recruited_count):>11}")
    lines.append(f"SCORE MULTIPLIER:              =x{fmt(floor_recruit_sum):>11}")
    lines.append("──────────────────────=───────────────────────")
    lines.append(f"SUBTOTAL:                        {fmt(subtotal):>11}")
    if end_bonus > 1.0:
        lines.append(f"GAME CLEAR MULTIPLIER:           x{end_bonus:>11.1f}")
    lines.append("──────────────────────/───────────────────────")
    lines.append(f"Number of turns taken:           {fmt(turns):>11}")
    lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")
    lines.append(f"▒FINAL SCORE:                    {fmt(final_score):>11}▒")
    lines.append(f"▒YOUR RANK:             {rank:>20}▒")
    lines.append("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")

    #---------------------------------------------------------
    #SECTION 2: PLAY TIME STATISTICS
    #---------------------------------------------------------
    play_time_val = None
    if hasattr(game, "get_elapsed_play_time"):
        try:
            val = game.get_elapsed_play_time()
            if isinstance(val, (int, float)):
                play_time_val = val
        except Exception:
            pass

    if play_time_val is not None:
        elapsed_seconds = int(max(0, play_time_val))
    else:
        start_time = getattr(game, "start_time", time.time())
        if isinstance(start_time, (int, float)):
            elapsed_seconds = int(max(0, time.time() - start_time))
        else:
            elapsed_seconds = 0
    hrs = elapsed_seconds // 3600
    mins = (elapsed_seconds % 3600) // 60
    secs = elapsed_seconds % 60
    time_str = f"{hrs:02d}h {mins:02d}m {secs:02d}s"
    end_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"Total play time: {time_str}")
    lines.append(f"Game ended:      {end_dt}")
    lines.append("")

    #---------------------------------------------------------
    #SECTION 3: ENCOUNTERED POKÉMON SPECIES
    #---------------------------------------------------------
    lines.append("──────────────ENCOUNTERED POKÉMON─────────────")
    enc = getattr(game, "encountered_species", {})
    lines.append("┌" + "─" * 45 + "┐")
    lines.append(f"│{'Species':<24}│{'Defeated':>10}│{'Recruited':>9}│")
    lines.append("─" * 47)

    tot_def = 0
    tot_rec = 0
    for species in sorted(enc.keys()):
        counts = enc[species]
        d_cnt = counts.get("defeated", 0)
        r_cnt = counts.get("recruited", 0)
        tot_def += d_cnt
        tot_rec += r_cnt
        lines.append(f"│{species:<24}│{fmt(d_cnt):>10}│{fmt(r_cnt):>9}│")

    lines.append("─" * 47)
    lines.append(f"│{'TOTAL':<24}│{fmt(tot_def):>10}│{fmt(tot_rec):>9}│")
    lines.append("└" + "─" * 45 + "┘")

    #---------------------------------------------------------
    #SECTION 4: TEAM MEMBERS HISTORY
    #---------------------------------------------------------
    lines.append("────────────────YOUR TEAMMATES────────────────")
    history = getattr(game, "all_team_members", [])
    for rec in history:
        poke = rec.get("pokemon")
        is_starter = rec.get("is_starter", False)

        poke_name = getattr(poke, "name", None) or rec.get("name", "Pokemon")
        species_name = getattr(poke, "species_name", None) or rec.get("species_name", "")
        display_name = f"{poke_name} ({species_name})" if species_name and species_name != poke_name else poke_name
        starter_label = " [STARTER]" if is_starter else ""

        #Fallback if fate not recorded
        if rec.get("fate") is None:
            if game_won and poke in getattr(game, "party", []) and int(getattr(poke, "current_hp", 0)) > 0:
                fate_str = "Escaped the dungeon!"
            elif poke in getattr(game, "party", []) and int(getattr(poke, "current_hp", 0)) > 0:
                fate_str = f"Departed the team on {floor_num}F on turn {fmt(turns)}"
            else:
                src = getattr(poke, "last_damage_source", None)
                if src == "poison":
                    fate_str = f"Succumbed to poison on {floor_num}F on turn {fmt(turns)}"
                elif src == "burn":
                    fate_str = f"Succumbed to burn on {floor_num}F on turn {fmt(turns)}"
                elif src == "hunger":
                    fate_str = f"Fainted from hunger on {floor_num}F on turn {fmt(turns)}"
                elif src == "Give Up":
                    fate_str = f"Gave up on {floor_num}F on turn {fmt(turns)}"
                elif src == "Chestnut":
                    fate_str = f"Pricked to death by a chestnut on {floor_num}F on turn {fmt(turns)}"
                elif src == "Geo Pebble":
                    fate_str = f"Defeated by a Geo Pebble on {floor_num}F on turn {fmt(turns)}"
                elif src == "Gravelerock":
                    fate_str = f"Defeated by a Gravelerock on {floor_num}F on turn {fmt(turns)}"
                elif src == "Stick":
                    fate_str = f"Defeated by a Stick on {floor_num}F on turn {fmt(turns)}"
                elif src == "Iron Thorn":
                    fate_str = f"Defeated by an Iron Thorn on {floor_num}F on turn {fmt(turns)}"
                elif src == "Silver Spike":
                    fate_str = f"Defeated by a Silver Spike on {floor_num}F on turn {fmt(turns)}"
                elif src == "Corsola Twig":
                    fate_str = f"Defeated by a Corsola Twig on {floor_num}F on turn {fmt(turns)}"
                elif src == "Cacnea Spike":
                    fate_str = f"Defeated by a Cacnea Spike on {floor_num}F on turn {fmt(turns)}"
                elif src == "Gold Fang":
                    fate_str = f"Defeated by a Gold Fang on {floor_num}F on turn {fmt(turns)}"
                elif src == "Leech Seed":
                    fate_str = f"Drained to nothing by Leech Seed on {floor_num}F on turn {fmt(turns)}"
                elif src == "Destiny Bond":
                    fate_str = f"Taken down by Destiny Bond on {floor_num}F on turn {fmt(turns)}"
                elif src == "Leech Seed":
                    fate_str = f"Drained to nothing by Leech Seed on {floor_num}F on turn {fmt(turns)}"
                elif src == "Hail":
                    fate_str = f"Battered by hail on {floor_num}F on turn {fmt(turns)}"
                elif src == "Sandstorm":
                    fate_str = f"Blasted by blowing sand on {floor_num}F on turn {fmt(turns)}"
                elif src == "Perish Song":
                    fate_str = f"Perished on {floor_num}F on turn {fmt(turns)}"
                elif src in ("Reflect", "Mirror Coat", "Counter"):
                    fate_str = f"Defeated by a reflected attack on {floor_num}F on turn {fmt(turns)}"
                elif src in ("Healing Wish", "Memento"):
                    fate_str = f"Sacrificed themselves on {floor_num}F on turn {fmt(turns)}"
                elif src in ("Self-Destruct", "Explosion"):
                    fate_str = f"Exploded on {floor_num}F on turn {fmt(turns)}"
                elif src == "recoil":
                    fate_str = f"Finished off by recoil damage on {floor_num}F on turn {fmt(turns)}"
                elif src:
                    fate_str = f"Defeated by {src} on {floor_num}F on turn {fmt(turns)}"
                else:
                    fate_str = f"Defeated on {floor_num}F on turn {fmt(turns)}"

            rec["fate"] = fate_str
            rec["final_hp"] = max(0, int(getattr(poke, "current_hp", 0))) if poke else rec.get("final_hp", 0)
            rec["final_max_hp"] = int(poke.stats.get("HP", 1)) if poke and getattr(poke, "stats", None) else rec.get("final_max_hp", 1)
            rec["final_level"] = getattr(poke, "level", 1) if poke else rec.get("final_level", 1)
            rec["final_moves"] = [m["name"] for m in poke.moves if isinstance(m, dict) and "name" in m] if poke and getattr(poke, "moves", None) else rec.get("final_moves", [])
            rec["final_stats"] = dict(poke.stats) if poke and getattr(poke, "stats", None) else rec.get("final_stats", {})

        lvl = rec.get("final_level")
        if lvl is None and poke:
            lvl = getattr(poke, "level", 1)
        if lvl is None:
            lvl = 1

        moves_list = rec.get("final_moves")
        if moves_list is None and poke and getattr(poke, "moves", None):
            moves_list = [m["name"] for m in poke.moves if isinstance(m, dict) and "name" in m]
        if moves_list is None:
            moves_list = []
        moves = ", ".join(moves_list)

        stats = rec.get("final_stats")
        if (not stats) and poke and getattr(poke, "stats", None):
            stats = dict(poke.stats)
        if not stats:
            stats = {}

        atk = stats.get("Attack", 0)
        df = stats.get("Defense", 0)
        sp_atk = stats.get("Special_Attack", 0)
        sp_def = stats.get("Special_Defense", 0)
        spd = stats.get("Speed", 0)
        stats_str = f"Atk {atk} / Def {df} / SpA {sp_atk} / SpD {sp_def} / Spe {spd}"

        fate = rec.get("fate", "Unknown")
        cur_hp = rec.get("final_hp")
        if cur_hp is None and poke:
            cur_hp = max(0, int(getattr(poke, "current_hp", 0)))
        if cur_hp is None:
            cur_hp = 0

        max_hp = rec.get("final_max_hp")
        if max_hp is None and poke and getattr(poke, "stats", None):
            max_hp = poke.stats.get("HP", 1)
        if max_hp is None:
            max_hp = 1

        hp_str = f"HP {int(cur_hp)}/{max_hp}"

        lines.append(f"{display_name}{starter_label} (Lv {lvl})")
        lines.append(f"{moves}")
        lines.append(f"{stats_str}")
        lines.append(f"{fate} ({hp_str})")
        lines.append("")

    #---------------------------------------------------------
    #SECTION 5: FINAL INVENTORY
    #---------------------------------------------------------
    lines.append("──────────────────TOOLBOX─────────────────────")
    if not inventory:
        lines.append("(empty)")
    else:
        for idx, item in enumerate(inventory, 1):
            raw_name = strip_ansi(item.get("name", "(BUG!)"))
            val = get_item_value(item)
            if item.get("stackable", False):
                cnt = item.get("count", 1)
                lines.append(f"{raw_name} ({cnt})")
            else:
                lines.append(f"{raw_name}")
    lines.append("")

    #---------------------------------------------------------
    #SECTION 6: MESSAGE HISTORY
    #---------------------------------------------------------
    lines.append("─────MESSAGE HISTORY─────")
    raw_msgs = getattr(game.message_log, "raw_messages", [])
    if not raw_msgs:
        lines.append("(no messages)")
    else:
        for msg in raw_msgs:
            if isinstance(msg, (tuple, list)):
                text = msg[0]
            else:
                text = msg
            clean_msg = strip_ansi(str(text))
            lines.append(clean_msg)
    lines.append("")
    lines.append("=" * 60)

    return lines


def dump_team_report_to_file(report_lines: list[str]) -> str:
    """Writes the summary lines to a txt file"""
    from data_utils import get_app_base_dir
    dumps_dir = os.path.join(get_app_base_dir(), "team_dumps")
    os.makedirs(dumps_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"teamdump-{timestamp}.txt"
    filepath = os.path.join(dumps_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    return filepath


class EndScreenController:
    """Manages state and input for rendering the summary in console"""

    def __init__(self, game, game_won: bool):
        self.game = game
        self.game_won = game_won
        self.report_lines = generate_end_screen_report(game, game_won)
        self.scroll_offset = 0
        self.dump_status_message: str | None = None
        self.is_active = True

    def render(self) -> list[str]:
        """Renders 48 rows of uncolored End Screen UI for terminal frame."""
        viewport_height = 41
        max_scroll = max(0, len(self.report_lines) - viewport_height)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))

        rows = []
        rows.append("┌" + "─" * 74 + "┐")

        header = "=== Run Statistics ==="
        pad_hdr = header.center(74)
        rows.append(f"│{pad_hdr}│")

        status_line = self.dump_status_message or "[Return] Export to .txt | [Esc] Quit | [↑/↓] Scroll"
        pad_stat = status_line.center(74)
        rows.append(f"│{pad_stat}│")
        rows.append("├" + "─" * 74 + "┤")

        visible_lines = self.report_lines[self.scroll_offset : self.scroll_offset + viewport_height]
        for i in range(viewport_height):
            if i < len(visible_lines):
                line = visible_lines[i][:72]
                rows.append(f"│ {line:<72} │")
            else:
                rows.append(f"│ {'':<72} │")

        rows.append("├" + "─" * 74 + "┤")
        scroll_info = f"Line {self.scroll_offset + 1}/{len(self.report_lines)}"
        rows.append(f"│ {scroll_info:<72} │")
        rows.append("└" + "─" * 74 + "┘")

        return rows

    def handle_input(self, action: str):
        """Processes input actions on the End Screen."""
        if action in (game_input.MOVE_UP, "k", "K"):
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif action in (game_input.MOVE_DOWN, "j", "J"):
            viewport_height = 41
            max_scroll = max(0, len(self.report_lines) - viewport_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        elif action in (game_input.MOVE_UP_LEFT, game_input.STATUS_1, "u", "U"):
            self.scroll_offset = max(0, self.scroll_offset - 10)
        elif action in (game_input.MOVE_DOWN_RIGHT, game_input.STATUS_2, "d", "D"):
            viewport_height = 41
            max_scroll = max(0, len(self.report_lines) - viewport_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + 10)
        elif action in (game_input.CONFIRM, "RETURN", "ENTER", "\r", "\n"):
            filepath = dump_team_report_to_file(self.report_lines)
            basename = os.path.basename(filepath)
            self.dump_status_message = f"Exported to team_dumps/{basename}!"
        elif action in (game_input.QUIT, "\x1b", "ESC", "q", "Q"):
            self.is_active = False
