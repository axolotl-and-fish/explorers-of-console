"""
high_scores.py

Manages the HIGHSCORES file, which stores high scores (duh), and also handles rendering of the high scores screen itself.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

#!!!CAUTION!!!
#Changing anything in this source file may break compatability with your existing HIGHSCORES file.
#Only modify this file if you know what you're doing and understand that you'll probably lose your high scores.

import os
import json
import base64
import hashlib
import datetime

SECRET_SALT = "SWAMPERT_LOAF_FOR_PRESIDENT_2028"

def get_high_scores_filepath() -> str:
    from save_game import get_save_dir
    save_dir = get_save_dir()
    return os.path.join(save_dir, "HIGHSCORES")


def compute_checksum(data_str: str) -> str:
    """Computes SHA-256 checksum for the high score data string"""
    return hashlib.sha256((data_str + SECRET_SALT).encode("utf-8")).hexdigest()


def wipe_high_scores():
    """Wipes the HIGHSCORES file if checksum fails"""
    filepath = get_high_scores_filepath()
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")


def load_high_scores() -> list[dict]:
    """Loads and validates high scores from the save_data/HIGHSCORES file.
    If the checksum mismatches or decoding fails, the file is wiped and [] is returned (you broke it son!)
    """
    filepath = get_high_scores_filepath()
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return []

        #Decode outer container
        container_bytes = base64.b64decode(content)
        container = json.loads(container_bytes.decode("utf-8"))

        stored_checksum = container.get("checksum")
        encoded_payload = container.get("payload")

        if not stored_checksum or not encoded_payload:
            wipe_high_scores()
            return []

        raw_json_bytes = base64.b64decode(encoded_payload)
        raw_json = raw_json_bytes.decode("utf-8")

        expected_checksum = compute_checksum(raw_json)
        if stored_checksum != expected_checksum:
            wipe_high_scores()
            return []

        scores = json.loads(raw_json)
        if not isinstance(scores, list):
            wipe_high_scores()
            return []

        valid_scores = []
        for entry in scores:
            if isinstance(entry, dict) and "score" in entry:
                valid_scores.append(entry)

        return valid_scores

    except Exception:
        wipe_high_scores()
        return []


def save_high_scores(scores: list[dict]):
    """Saves high scores into save_data/HIGHSCORES with encoding and checksum. Up to 50 can be stored."""
    filepath = get_high_scores_filepath()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    #Sort descending by score
    scores = sorted(scores, key=lambda x: int(x.get("score", 0)), reverse=True)

    #Cap at top 50 scores 
    #This limit is arbitrary and can be increased, though it will increase the size of the HIGHSCORE file, and in extreme cases lead to extra decoding time. The High Score screen is only designed for 50 at most anyway.
    scores = scores[:50]

    raw_json = json.dumps(scores, separators=(",", ":"))
    checksum = compute_checksum(raw_json)
    encoded_payload = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")

    container = {
        "checksum": checksum,
        "payload": encoded_payload
    }

    container_json = json.dumps(container, separators=(",", ":"))
    content = base64.b64encode(container_json.encode("utf-8")).decode("utf-8")

    filepath = get_high_scores_filepath()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def add_high_score(score: int, floor: str | int, turns: int, dt_iso: str | None = None) -> list[dict]:
    """Adds a new score entry to the HIGHSCORES file."""
    scores = load_high_scores()

    score_val = min(9999999, max(0, int(score)))

    #Game completed
    if str(floor) == "**":
        floor_val = "**"
    else:
        try:
            floor_val = f"{min(99, max(1, int(floor))):02d}"
        except Exception:
            floor_val = str(floor)[:2]

    turns_val = min(999999, max(0, int(turns)))

    if not dt_iso:
        dt_iso = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    new_entry = {
        "score": score_val,
        "floor": floor_val,
        "turns": turns_val,
        "datetime": dt_iso
    }

    scores.append(new_entry)
    save_high_scores(scores)
    return scores


def format_high_scores_table(scores: list[dict], highlight_entry: dict | None = None) -> list[str]:
    """Formats high scores into a borderless table, optionally with a single entry highlit (is that word?)"""
    lines = []
    lines.append("=== HIGH SCORES ===")
    lines.append("")

    if not scores:
        lines.append("No high scores recorded yet.")
        return lines

    lines.append(f"{'Rank':<6} {'Score':>11}   {'Floor':>5}   {'Turns':>8}   {'Time':<20}")

    for idx, entry in enumerate(scores, 1):
        rank_str = f"{idx}."
        score_val = entry.get("score", 0)
        score_str = f"{score_val:,}"
        floor_val = entry.get("floor", "**")
        floor_str = str(floor_val)
        turns_val = entry.get("turns", 0)
        turns_str = f"{turns_val:,}"
        dt_str = str(entry.get("datetime", ""))

        row_str = f"{rank_str:<6} {score_str:>11}   {floor_str:>5}   {turns_str:>8}   {dt_str:<20}"

        is_highlighted = False
        if highlight_entry and isinstance(highlight_entry, dict):
            if (entry.get("datetime") == highlight_entry.get("datetime") and
                entry.get("score") == highlight_entry.get("score")):
                is_highlighted = True

        if is_highlighted:
            lines.append(f"\033[1;93m{row_str}\033[0m")
        else:
            lines.append(row_str)

    return lines


class HighScoreController:
    """Controller for viewing the High Score screen"""
    def __init__(self, game=None, highlight_entry: dict | None = None):
        self.game = game
        self.is_active = True
        self.scroll_offset = 0
        self.highlight_entry = highlight_entry if highlight_entry is not None else getattr(game, "last_run_score_entry", None)

    def render(self) -> list[str]:
        scores = load_high_scores()
        lines = format_high_scores_table(scores, highlight_entry=self.highlight_entry)
        viewport_height = 40
        visible_lines = lines[self.scroll_offset : self.scroll_offset + viewport_height]
        if getattr(self.game, "compatibility_mode", False):
            import re
            return [re.sub(r'\x1b\[[0-9;]*m', '', l) for l in visible_lines]
        return list(visible_lines)

    def handle_input(self, action: str):
        from input import MOVE_UP, MOVE_DOWN, CONFIRM, QUIT
        if action in (MOVE_UP, "w", "W", "up", "UP", "k", "K"):
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif action in (MOVE_DOWN, "s", "S", "down", "DOWN", "j", "J"):
            scores = load_high_scores()
            lines = format_high_scores_table(scores, highlight_entry=self.highlight_entry)
            max_scroll = max(0, len(lines) - 40)
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        elif action in (QUIT, CONFIRM, "\x1b", "ESC", "q", "Q", "\r", "\n", "z", "Z"):
            self.is_active = False
