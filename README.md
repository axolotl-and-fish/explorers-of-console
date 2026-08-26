                                         █                               
          ███            ██            ███                               
      ████  ███          ██         ███                                  
     █████    ██         ██       ██                                     
        ██     █         ███         ████                                
        ██     █         ███   █   ██   ██  ██ ██          ██            
        ██    ██  ████   ██████   █C4'26██  █████████    ██████  ██      
        ██████   ███ ██  ████    ██   ███   ██  ██  ██  ███   ██ ████    
        ██      ███   █  ███     █████      ██  ██  ██  ███    █ ██ ██   
        ███     ███   ██ ███      █     █   ██  ██  ██ ███     █ █    █  
        ███     ███ ████ █████    ██████    ██  █   ██ ███   ██  █    █  
        ███     ███████  ███ ███            ██      █  ████████  █    █  
         ██       ███    ███   ██                   █  ███████   █    █  
                                                        █████    █    █  
													   
		█  █  █                       ███                                 
		████      ███  ██  █ ██ █  █  █  █ █  █ █ █   ███  ██   ██  █ █   
		████  █  ███  █  █ ██   █  █  █  █ █  █ ██ █ █  █ █  █ █  █ ██ █  
		█  █  █     █ ███  █     ███  █  █ █ ██ █  █  ███ ███  █  █ █  █  
		█  █  █  ███   ███ █       █  ███   █ █ █  █    █  ███  ██  █  █  
				        		 ██                   ██                  
							   
						     ✩ Explorers of the Console ✩
                                     by C437RP13
# Pokémon Misery Dungeon: Explorers of the Console
Some speak of a very special Mystery Dungeon known as the "Misery Dungeon", a 50-floor long gauntlet of Pokémon out for blood and ruin, but also a treasure trove of loot, money and glory. Many Rescue Teams and Explorer Guilds have tried their hands at this dungeon, but few have ever lived to tell the tale and reap the benefits. Now you, a lowly Pokémon explorer, have dared to defy the odds and try to conquer this Misery Dungeon; will you succeed where others have failed?

Pokémon Misery Dungeon: Explorers of the Console is a text-based PMD fangame presented in the style of a traditional "roguelike" game. Choose a starter Pokémon from any of the 11 canon PMD starters from gen 1 and lead them through fifty randomly-generated floors full of useful items and dangerous foes. By no  means must you undertake this task alone, however; you can recruit the dungeon's Pokémon to your side by enticing them with special Apricorn items. Lead a team of up to six Pokemon to the top of the dungeon, and aim for a high  score! Will YOU be the first person to beat the legendary score of 1 million?

**For detailed information on how to play the game, please refer to the [Manual](manual.txt).**

**Also, join my Discord server, where I have a dedicated channel for discussion of this game!** https://discord.gg/qr9V6FvMEz

# Controls
PMD: Explorers of the Console is entirely controlled with your keyboard.

Use the numpad or arrow keys to move your character around the dungeon.
**MAKE SURE YOUR NUMLOCK IS TURNED ON!**

                       7  8  9    [Return/Enter] - Confirm
						\ | /	  [Esc] - Cancel/Open pause menu
					   4- @ -6    [Z][X][C][V] - Use a move
						/ | \	  [A][S][D][F][G][H] - Open Pokemon summary
					   1  2  3    [I] - Open inventory
					  Movement	  [P] - Open message history
								  [L] - Enable "look around" mode
								  [>] - Use stairs
					  
Some smaller laptops ("notebooks") have a smaller keyboard without a numpad, so alternatively you can use the Shift, CTRL and arrow keys to move your character, like so:

					Shift+←  ↑  Shift+→
				     	   \ | /  
					      ←- @ -→ 
						   / | \	
				     CTRL+←  ↓  CTRL+→
				  
To wait a turn without moving or attacking, press the 5 key on the numpad,
or the . key on your keyboard.

For further information, refer to the [Manual](manual.txt).
# System Requirements
- For the executable package, Windows 10 or later on any x86-64 system. For other OSes and platforms, **Python 3.10 or later** must be installed.
- A terminal emulator that supports 16 colors and code page 437, minimum 76x48 characters. Pretty much every modern terminal should support this happily.
- A monospaced font that supports Code Page 437. Sadly, this means no Wonder Mail font :( You can find some cool-looking retro fonts that support all the characters the game needs here: https://int10h.org/oldschool-pc-fonts/

# (IMPORTANT!) Reporting Bugs
As an early beta, PMD: Explorers of the Console is lacking many features and contains a lot of bugs, many of which may potentially crash your game. If you encounter bugs or crashes, **PLEASE PLEASE** report them to me via one of the following:

1. Open an issue in the GitHub repo.

2. Post a message on the Pokecommunity thread: https://www.pokecommunity.com/threads/pok%C3%A9mon-misery-dungeon-explorers-of-the-console.543129/
   
Make sure to include a description of the issue and what you were doing at the time it occurred! If it's a game crash, please attach the debug.log file, which contains the stack backtrace which will help me pinpoint where exactly the problem is. After a crash, you will find the file in the game's directory. The more detail you include in your description, the better; screenshots are nice to have, too.

Explorers of the Console is designed to be as platform-agnostic as possible, so feel free to send bug reports regardless of what OS you are using. I may not be able to be much help to you if you're using something that's really out there, though, or it is something that I'm unable to replicate.

# Installation & Play

## Windows x64
If you are on Windows on a x86-64 system, a pre-compiled version of the game using PyInstaller is available, and there is no need to install Python. Head to the Releases tab and download the Windows version of the latest release. Extract the file, open your Terminal/Command Prompt/Powershell window and run the executable through there. **Don't double-click the EXE from Explorer, it won't work! You must run it from the CLI.**

## Other platforms
You will need **Python 3.10 or higher** installed on your system. I believe macOS and many Linux distros nowadays come with Python pre-installed, but you can check if you have Python by typing ````python3```` in your terminal. If it shows an error, that most likely means Python 3 is not installed. You can install the latest version of Python from here: https://www.python.org/

Head to the Releases tab and download the Source Code (zip), extract the file, and either run PMD_Explorers_of_the_Console.bat, or type the following command in your terminal:
````python3 visualize.py --play````

# CLI Arguments

````--play````: Starts the game. Only used for the non-compiled version, which defaults to a dungeon generation visualizer if this is not specified

````--generate````: Generates and displays a dungeon using the game's generation algorithm. Only used for the compiled version, which defaults to playing the actual game if not specified.

````--compat````: Runs the game in compatibility mode, which removes all ANSI color. The game is designed with color in mind, so this should only be used as a last resort if your terminal is incompatible, but you should really just use a different terminal.

````--width````: Specify a width between 32 and 56 for the generated floor. Can only be used with ````--generate````.

# Contributing

Human-written issues and PRs are welcome, though I will mainly be accepting PRs for bug fixes and additions to the JSON files in the data folder. Apologies in advance if I determine your feature request is out of scope, as I do have a specific roadmap for this project in mind. Maybe this will change in future once I finally get to 1.0.

**LLM-WRITTEN ISSUES & PRs ARE STRICTLY PROHIBITED.** You will be banned from the repo. Don't even try it. I will know. All contributions to this repo **must** be human-written.

# Legal
Pokémon Misery Dungeon: Explorers of the Console's engine & code are 

**© 2026 C437RP13 (Axolotl and Fish)**

and are licensed under the GNU General Public License, version 3 or later. Please see the LICENSE file for further information. I'm looking forward to seeing what kinds of mods and forks people make for it :>

This program is distributed WITH ABSOLUTELY NO WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Additionally, Explorers of the Console is a FREE-OF-CHARGE NON-PROFIT FANGAME. It **MUST NOT** be sold or distributed for profit by any means.

All trademarks belong to their respective authors.

# FAQ (WIP)
Feel free to ask more questions and I will answer them here if there's enough demand.

**Why is it called Pokémon Misery Dungeon?**
I dunno, I just thought it was funny. The game is also supposed to be much harder than any PMD game would be, so that's something too!

**Will there be a mobile version? Can I play this on my phone?**
Sadly, not yet. This game is only really a hobby project for me, and I know nothing about mobile development. Pretty sure literally the entire game's code would have to be completely rewritten from scratch to make it work on mobile. I'd definitely be open to someone making a fork of this for mobile though, if they felt up to it ;) But I mainly want to focus on making a good game.

**Will the game always be text-based? Will there be a graphical version someday?**
tbh the fact that the game is entirely text-based is what separates this game from other PMD fan-games, so I don't really want to add proper graphics to it. If you really want a graphical PMD fan-game, I would highly recommend Pokémon Mystery Dungeon Origins: https://www.pokecommunity.com/threads/pokémon-mystery-dungeon-origins-updated-v0-8-11-2025-09-03.447489/ . The devs behind Origins are super talented and it has been in development for many years, and it served as a lot of the inspiration for my game. Of course, someone could always add SDL/pygame to the game to give it graphics in a fork :>

**The game won't start and gives a TypeError: unsupported operand type(s) for | exception.**
This means that your version of Python is too old and doesn't support the | operand that the code uses. Please update to Python 3.10 or higher.

**Help, the game has broken graphics!**
This could be the result of a few issues:

- You're using a font that doesn't support all of the CP437 character set. Try using a different font.
- You're using a font that isn't monospaced. I know some terminal emulators allow using non-monospaced fonts, but this will result in graphical issues most likely. Try using a monospaced font.
- Your terminal window is too small. Make sure it is 76 columns by 48 rows minimum.
- If everything else is correct, it could be some kind of weirdness specific to whatever terminal emulator you're using, in which case try using a different terminal? idk. Or you may have found an actual bug with the rendering engine, in which case you should file a bug report :)

**This game is very difficult, any advice for a new player?**
**USE. YOUR. ITEMS.** I can't stress this enough. Items will be your lifeline while you're in the dungeon. The more items you have, the more options you have, and the more options you have, the better your chances of survival. Also, don't just charge forward; you can take all the time you want when deciding your next action, so think very carefully and strategize. Eevee is also the strongest and most versatile out of all the starter choices, so I would recommend choosing them for beginners.

Sadly given the random nature of this game, there will be situations where there is nothing you can really do, but that's the way the cookie crumbles for this genre. Don't worry; with every failed run, you'll learn something new!

# Compiling
The game's source code can be compiled using **PyInstaller**: https://pyinstaller.org/en/stable/

It's not required to play the game since it can be run using the Python interpreter anyway with the same performance, but it is more convenient for most users.

Further information and instructions will be added here at a later date.
