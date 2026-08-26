"""
visualize.py

Command-line script that generates and prints a PMD-style dungeon floor in the terminal. Also bootstraps the actual game.
See dungeon.py for the dungeon generation code
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import ctypes
import sys
import os
import argparse
import time

#Allow importing from the same directory (src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dungeon import DungeonFloor  # type: ignore

def enable_vt100():
    """Enables ANSI escape code support for certain Windows-based systems and command prompts so that they can show color. Special thanks to PorygonSeizure for the bug report!"""
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    handle = kernel32.GetStdHandle(-11) #Get stdout handle
    
    #Get current console mode
    mode = ctypes.c_ulong()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        raise ctypes.WinError(ctypes.get_last_error())
        
    #Enable VT100 emulation
    if not kernel32.SetConsoleMode(handle, mode.value | 0x0004):
        raise ctypes.WinError(ctypes.get_last_error())

def main():
    #Configure stdout to use UTF-8 to handle the solid block character (█) on all platforms
    reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
    if reconfigure_stdout is not None:
        try:
            reconfigure_stdout(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Launch PMD: Explorers of the Console, or test dungeon generation. Written by C437RP13"
    )
    parser.add_argument(
        "--width", type=int, default=None, help="Dungeon width (32-56). If not defined, width is chosen randomly."
    )
    parser.add_argument(
        "--play", action="store_true", default=False, help="Play PMD: EotC"
    )
    parser.add_argument(
        "--generate", "--test", action="store_true", default=False, help="Generate and print a test floor without playing"
    )
    parser.add_argument(
        "--compat", "--compatibility", "--no-color", "--nocolor", "-c", action="store_true", default=False, help="Run in compatibility mode (no ANSI colors)"
    )
    args = parser.parse_args()

    try:
        if not args.generate:
            from game import Game  # type: ignore
            if sys.platform.startswith('win32'):
                try:
                    enable_vt100()
                except Exception as e:
                    print(f"Error initializing VT100 display: {e}. Expect graphical issues! Try using a different terminal or using the --compat flag to run without ANSI color.")
                    time.sleep(5.0)
                    pass
            game = Game(width=args.width, compatibility_mode=args.compat)
            game.run()
            return

        start_time = time.perf_counter()
        floor = DungeonFloor(width=args.width)
        print(f"Generated dungeon floor ({floor.width}x{floor.height}):")
        print(f"Total rooms: {len(floor.rooms)}")

        #Calculate merged room count
        merged_count = 0
        visited = set()
        for cell, room in floor.rooms.items():
            if cell in visited:
                continue
            if room.merged_with:
                merged_group = {cell} | room.merged_with
                visited.update(merged_group)
                merged_count += 1
        print(f"Merged room groups: {merged_count}")
        print(f"Corridor tiles: {len(floor.corridor_tiles)}")
        print(f"Dead end tiles: {len(floor.dead_end_tiles)}")
        print("-" * floor.width)
        print(floor.to_ascii())
        print("-" * floor.width)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"Generation time: {execution_time:.6f} s")
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
            saved_msg = f"\nA backup save file was created at {os.path.basename(game._emergency_save_path)}\nYou can attempt to resume your progress from the Load Game menu.\n"
        elif 'game' in locals() and getattr(game, "player_pokemon", None) and not getattr(game, "game_ended", False):
            try:
                from save_game import attempt_emergency_save
                saved_path = attempt_emergency_save(game)
                if saved_path:
                    saved_msg = f"\nA backup save file was created at {os.path.basename(saved_path)}\nYou can attempt to resume your progress from the Load Game menu.\n"
            except Exception:
                pass

        print(f"Oh no, the game crashed!\n{e}\n{saved_msg}See debug.log for detailed traceback information.\nPlease report this to me on GitHub or the Pokécommunity thread;\nmake sure to include your debug.log and a description of what you were doing before the game crashed. -C4", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
