"""
message_log.py

Code related to the in-game message log and the message history (buffer)
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import re


def len_ansi(s: str) -> int:
    """Returns the visual printable length of a string, ignoring ANSI escape codes"""
    return len(re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', s))


def wrap_text(text: str, max_width: int = 56) -> list[str]:
    """Wraps text into a list of lines with length at most max_width, splitting by words"""
    words = text.split()
    if not words:
        return []

    lines = []
    current_line: list[str] = []
    current_len = 0

    for word in words:
        word_len = len_ansi(word)
        if word_len > max_width:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
                current_len = 0
            #Split long words over multiple lines. Supercagifragilisticexpialidocius...
            for i in range(0, len(word), max_width):
                lines.append(word[i:i + max_width])
            continue

        space_len = 1 if current_line else 0
        if current_len + space_len + word_len > max_width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_len = word_len
        else:
            current_line.append(word)
            current_len += space_len + word_len

    if current_line:
        lines.append(" ".join(current_line))

    return lines


class MessageLog:
    """Manages text wrapping, pending line buffers, and visible message history"""

    def __init__(self):
        #Stores all processed lines as tuples: (line_str, turn_number, is_important)
        self.history: list[tuple] = []
        #Stores pending lines as tuples: (line_str, turn_number, is_important)
        self.pending_lines: list[tuple] = []
        self.has_more_page: bool = False
        #Stores raw colorized messages (up to 99 messages): (text, turn_number, is_important)
        self.raw_messages: list[tuple] = []

    def log(self, text: str, turn_number: int, important: bool = False):
        """Wraps and adds a new message with its turn number."""
        self.raw_messages.append((text, turn_number, important))
        #99 is an arbitrary limit, it's unlikely players will need more than 99 lines for the history. Larger values increase save file sizes
        if len(self.raw_messages) > 99:
            self.raw_messages = self.raw_messages[-99:]

        wrapped = wrap_text(text, max_width=56)
        for line in wrapped:
            self.history.append((line, turn_number, important))
        if len(self.history) > 500:
            self.history = self.history[-500:]

    def get_history_lines(self, max_width: int = 72) -> list[str]:
        """Returns wrapped lines for the last 99 messages"""
        lines = []
        for item in self.raw_messages:
            text = item[0]
            wrapped = wrap_text(text, max_width=max_width)
            lines.extend(wrapped)
        return lines

    def has_pending(self) -> bool:
        """Returns True if there are new lines waiting to be paged to the user. This is for displaying the [MORE] tag in-game"""
        return len(self.pending_lines) > 0 or self.has_more_page

    def get_visible_lines_with_turns(self) -> list[tuple]:
        """Returns the last 5 line tuples from the scrolling history, padded to exactly 5 lines"""
        visible = [(item[0], item[1]) for item in self.history[-5:]]
        while len(visible) < 5:
            visible.insert(0, ("", 0))
        return visible

    def step_page(self) -> bool:
        """Processes the next page of messages."""
        if not self.pending_lines:
            self.has_more_page = False
            return False

        cutoff = min(5, len(self.pending_lines))
        page_lines = self.pending_lines[:cutoff]
        self.pending_lines = self.pending_lines[cutoff:]

        self.history.extend(page_lines)
        if len(self.history) > 500:
            self.history = self.history[-500:]

        if len(self.pending_lines) > 0:
            self.has_more_page = True
            return True
        else:
            self.has_more_page = False
            return False
