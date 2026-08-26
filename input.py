"""
input.py

(Hopefully) cross-platform input handler for PMD: Explorers of the Console.
It's specifically designed for Windows Terminal and the macOS/Linux console. Other terminals on obscure and esoteric operating systems may not work properly with this.
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import sys

#Define standard action codes
MOVE_UP = "UP"
MOVE_DOWN = "DOWN"
MOVE_LEFT = "LEFT"
MOVE_RIGHT = "RIGHT"
MOVE_UP_LEFT = "UP_LEFT"
MOVE_UP_RIGHT = "UP_RIGHT"
MOVE_DOWN_LEFT = "DOWN_LEFT"
MOVE_DOWN_RIGHT = "DOWN_RIGHT"
WAIT = "WAIT"
QUIT = "QUIT"
UNKNOWN = "UNKNOWN"
LOOK_AROUND = "LOOK_AROUND"
STATUS_1 = "STATUS_1"
STATUS_2 = "STATUS_2"
STATUS_3 = "STATUS_3"
STATUS_4 = "STATUS_4"
STATUS_5 = "STATUS_5"
STATUS_6 = "STATUS_6"

USE_MOVE_1 = "USE_MOVE_1"
USE_MOVE_2 = "USE_MOVE_2"
USE_MOVE_3 = "USE_MOVE_3"
USE_MOVE_4 = "USE_MOVE_4"

CONFIRM = "CONFIRM"
TAKE_STAIRS = "TAKE_STAIRS"
INVENTORY = "INVENTORY"
PICK_UP = "PICK_UP"

MESSAGE_LOG = "MESSAGE_LOG"

#Key mappings for standard character presses
KEY_MAP = {
    ">": TAKE_STAIRS,
    "i": INVENTORY,
    "I": INVENTORY,
    "p": MESSAGE_LOG,
    "P": MESSAGE_LOG,
    ",": PICK_UP,
    "l": LOOK_AROUND,
    "L": LOOK_AROUND,
    "a": STATUS_1,
    "A": STATUS_1,
    "s": STATUS_2,
    "S": STATUS_2,
    "d": STATUS_3,
    "D": STATUS_3,
    "f": STATUS_4,
    "F": STATUS_4,
    "g": STATUS_5,
    "G": STATUS_5,
    "h": STATUS_6,
    "H": STATUS_6,
    #Move shortcuts
    "z": USE_MOVE_1,
    "Z": USE_MOVE_1,
    "x": USE_MOVE_2,
    "X": USE_MOVE_2,
    "c": USE_MOVE_3,
    "C": USE_MOVE_3,
    "v": USE_MOVE_4,
    "V": USE_MOVE_4,
    #Numpad (Num Lock ON) - cardinal and diagonal movement keys
    "8": MOVE_UP,
    "2": MOVE_DOWN,
    "4": MOVE_LEFT,
    "6": MOVE_RIGHT,
    "7": MOVE_UP_LEFT,
    "9": MOVE_UP_RIGHT,
    "1": MOVE_DOWN_LEFT,
    "3": MOVE_DOWN_RIGHT,
    "5": WAIT,
    ".": WAIT,
    #Confirm / Selection keys
    "\r": CONFIRM,
    "\n": CONFIRM,
    " ": CONFIRM,
    #Standard exit keys
    "\x1b": QUIT, #Esc key
}


def _get_key_windows(timeout: float | None = None) -> str | None:
    """Windows key press input reader"""
    import msvcrt
    import ctypes
    import time

    if timeout is not None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if msvcrt.kbhit():
                break
            time.sleep(0.01)
        else:
            return None

    ch = msvcrt.getch()
    #Handle arrow keys or special keys (which start with 0x00 or 0xe0)
    #Future todo: Make controls remappable? Keyboard terminal input is annoying to work with
    if ch in (b"\x00", b"\xe0"):
        ch2 = msvcrt.getch()
        #Modifier states for the diagonal laptop shortcut (SHIFT+arrow, CTRL+arrow)
        shift_pressed = (ctypes.windll.user32.GetKeyState(0x10) & 0x8000) != 0
        ctrl_pressed = (ctypes.windll.user32.GetKeyState(0x11) & 0x8000) != 0

        #Scan codes:
        #H (72) -> Up, P (80) -> Down, K (75) -> Left, M (77) -> Right
        #G (71) -> Home/Up-Left, I (73) -> PgUp/Up-Right, O (79) -> End/Down-Left, Q (81) -> PgDn/Down-Right
        if ch2 == b"H":
            return MOVE_UP
        elif ch2 == b"P":
            return MOVE_DOWN
        elif ch2 == b"K":
            if shift_pressed:
                return MOVE_UP_LEFT
            elif ctrl_pressed:
                return MOVE_DOWN_LEFT
            return MOVE_LEFT
        elif ch2 == b"M":
            if shift_pressed:
                return MOVE_UP_RIGHT
            elif ctrl_pressed:
                return MOVE_DOWN_RIGHT
            return MOVE_RIGHT
        elif ch2 == b"s":  #Ctrl + Left Arrow scan code
            return MOVE_DOWN_LEFT
        elif ch2 == b"t":  #Ctrl + Right Arrow scan code
            return MOVE_DOWN_RIGHT
        elif ch2 == b"G":
            return MOVE_UP_LEFT
        elif ch2 == b"I":
            return MOVE_UP_RIGHT
        elif ch2 == b"O":
            return MOVE_DOWN_LEFT
        elif ch2 == b"Q":
            return MOVE_DOWN_RIGHT
        elif ch2 == b"S":  #Delete
            return QUIT
        return UNKNOWN

    try:
        char_str = ch.decode("utf-8", errors="replace")
    except Exception:
        return UNKNOWN

    return KEY_MAP.get(char_str, UNKNOWN)


def _get_key_unix(timeout: float | None = None) -> str | None:
    """Linux and macOS input reader"""
    import tty  # type: ignore
    import termios  # type: ignore
    import select

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)  # type: ignore
    ch = ""
    try:
        #Set raw mode to read character-by-character without buffering or echo
        tty.setraw(fd)  # type: ignore

        if timeout is not None:
            rlist, _, _ = select.select([fd], [], [], timeout)
            if not rlist:
                return None

        ch_bytes = os.read(fd, 1)
        if ch_bytes:
            ch = ch_bytes.decode("utf-8", errors="replace")

        #Handle escape sequences (like arrow keys)
        if ch == "\x1b":
            #Set stdin to non-blocking to check if more characters are in the buffer (which indicates a multi-byte escape sequence rather than just Esc key)
            rlist, _, _ = select.select([fd], [], [], 0.05)
            if rlist:
                ch2_bytes = os.read(fd, 1)
                ch2 = ch2_bytes.decode("utf-8", errors="replace") if ch2_bytes else ""
                if ch2 in ("[", "O"):
                    ch3_bytes = os.read(fd, 1)
                    ch3 = ch3_bytes.decode("utf-8", errors="replace") if ch3_bytes else ""
                    if ch3 == "A":
                        return MOVE_UP
                    elif ch3 == "B":
                        return MOVE_DOWN
                    elif ch3 == "C":
                        return MOVE_RIGHT
                    elif ch3 == "D":
                        return MOVE_LEFT
                    elif ch3 in ("E", "G"):
                        return WAIT
                    elif ch3 == "1":
                        #Multi-byte modified arrow sequence: e.g. [1;2D (Shift+Left), [1;5D (Ctrl+Left)
                        semi_bytes = os.read(fd, 1)
                        semi = semi_bytes.decode("utf-8", errors="replace") if semi_bytes else ""
                        mod_bytes = os.read(fd, 1)
                        mod = mod_bytes.decode("utf-8", errors="replace") if mod_bytes else ""
                        dir_char_bytes = os.read(fd, 1)
                        dir_char = dir_char_bytes.decode("utf-8", errors="replace") if dir_char_bytes else ""
                        if semi == ";":
                            if mod == "2":  #Shift
                                if dir_char == "D":
                                    return MOVE_UP_LEFT
                                elif dir_char == "C":
                                    return MOVE_UP_RIGHT
                            elif mod == "5":  #Ctrl
                                if dir_char == "D":
                                    return MOVE_DOWN_LEFT
                                elif dir_char == "C":
                                    return MOVE_DOWN_RIGHT
                        return UNKNOWN
                    #Home, End, PgUp, PgDn codes can vary across terminal setups:
                    #Home: '[H' or '1~' or '7~'
                    #End: '[F' or '4~' or '8~'
                    #PgUp: '5~'
                    #PgDn: '6~'
                    elif ch3 == "H":
                        return MOVE_UP_LEFT
                    elif ch3 == "F":
                        return MOVE_DOWN_LEFT
                    elif ch3 in ("1", "7", "5", "6", "4", "8"):
                        #Read the remaining character in seq (like '~')
                        _ = os.read(fd, 1)
                        if ch3 in ("1", "7"):  #Home
                            return MOVE_UP_LEFT
                        elif ch3 == "5":  #PgUp
                            return MOVE_UP_RIGHT
                        elif ch3 in ("4", "8"):  #End
                            return MOVE_DOWN_LEFT
                        elif ch3 == "6":  #PgDn
                            return MOVE_DOWN_RIGHT
                    return UNKNOWN
                return UNKNOWN
            return QUIT  #Standard escape is treated as Quit

        return KEY_MAP.get(ch, UNKNOWN)

    finally:
        #Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # type: ignore


def get_key(timeout: float | None = None) -> str | None:
    """Reads a key press (blockingly or with a timeout) and returns the mapped action code.
    
    If timeout is specified and no key is pressed within that time, returns None
    """
    if os.name == "nt":
        return _get_key_windows(timeout=timeout)
    else:
        return _get_key_unix(timeout=timeout)


def get_char_input(timeout: float | None = None) -> str | None:
    """Reads a key press for text input and returns 'ENTER', 'BACKSPACE', 'ESC', or the typed character"""
    if os.name == "nt":
        import msvcrt
        import time
        if timeout is not None:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if msvcrt.kbhit():
                    break
                time.sleep(0.01)
            else:
                return None
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            if ch2 == b"S":  #Delete
                return "BACKSPACE"
            return None
        if ch in (b"\r", b"\n"):
            return "ENTER"
        if ch == b"\x08":
            return "BACKSPACE"
        if ch == b"\x1b":
            return "ESC"
        try:
            return ch.decode("utf-8", errors="replace")
        except Exception:
            return None
    else:
        import select
        import tty  # type: ignore
        import termios  # type: ignore
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)  # type: ignore
        try:
            tty.setraw(fd)  # type: ignore
            if timeout is not None:
                rlist, _, _ = select.select([fd], [], [], timeout)
                if not rlist:
                    return None
            ch_bytes = os.read(fd, 1)
            if not ch_bytes:
                return None
            if ch_bytes in (b"\r", b"\n"):
                return "ENTER"
            if ch_bytes in (b"\x08", b"\x7f"):
                return "BACKSPACE"
            if ch_bytes == b"\x1b":
                rlist, _, _ = select.select([fd], [], [], 0.05)
                if rlist:
                    os.read(fd, 10)
                    return None
                return "ESC"
            return ch_bytes.decode("utf-8", errors="replace")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # type: ignore
