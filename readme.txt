DUNGEONA
========

Overview
--------
Dungeona is a small terminal dungeon crawler written in Python with the built-in
curses module. It renders an ASCII/ANSI-style first-person dungeon view and
includes a separate terminal editor for maintaining the dungeon map stored in a
SQLite database.

Donation link:
https://paypal.me/michtatton

Project contents
----------------
dungeona.py        Main game
dungeon_editor.py  Map editor and validator
dungeon_map.db     SQLite database containing dungeon floor rows
license.txt        Donationware license
readme.txt         This file

Current project behavior
------------------------
This version uses a shared database-backed dungeon layout:

- dungeona.py loads dungeon floors from dungeon_map.db at startup.
- dungeon_editor.py reads from and writes to the same dungeon_map.db file.
- If the database table is missing or empty, the project seeds it with the
  built-in default three-floor dungeon.
- Both scripts can still read an older legacy table named map_rows, but all
  current saves use floor_map_rows.

Gameplay summary
----------------
- Explore a three-floor dungeon from a first-person view.
- Find the Holy Grail (G).
- Bring the Grail to the altar (A) on the final floor to complete the quest.
- Open doors, fight monsters, manage energy, and travel between floors by
  using stair tiles.
- Toggle the minimap whenever needed.

Requirements
------------
- Python 3.10+ recommended
- A terminal that supports curses and ANSI-style character rendering
- No third-party Python packages are required on Linux/macOS
- On Windows, you may need the windows-curses package:

  pip install windows-curses

How to run
----------
From the project folder:

  python dungeona.py

To open the map editor:

  python dungeon_editor.py

Starting state
--------------
- The game loads the current dungeon from dungeon_map.db.
- If the database has not been initialized yet, the default 3-floor dungeon is
  written to it automatically.
- The player starts on the first passable tile found while scanning the loaded
  dungeon, facing east.
- Energy starts at 12 and is capped at 12.
- The minimap starts enabled.

Game controls
-------------
Movement and view:
- Up arrow / W     Move forward
- Down arrow / S   Move backward
- Q                Turn left
- E                Turn right
- Z                Strafe left
- C                Strafe right

Actions:
- Space / Enter    Act on the tile directly ahead
                   (open door / attack / take grail / use altar / use stairs)
- .                Wait and regain 1 energy
- >                Go down when standing on a downstairs tile
- <                Go up when standing on an upstairs tile
- M                Toggle minimap
- X                Quit

Notes:
- Stepping onto a stair tile also triggers stair travel automatically.
- Standing on the altar with the Grail also completes the quest automatically.

Game systems
------------
- Energy starts at 12 and is capped at 12.
- Waiting restores 1 energy.
- Defeating a monster costs:
  - 2 energy normally
  - 1 energy while carrying the Holy Grail
- Defeated monsters increase the score counter.
- Doors can be opened from the tile directly in front of the player.
- Taking the Grail removes it from the map.
- Inventory capacity is 3 items, although the current quest only uses the
  Grail as a carried item.
- The status line shows energy, floor, position, facing direction, inventory,
  grail status, and defeated enemy count.
- Completing the quest shows a congratulatory banner.

Tile meanings
-------------
- #  Wall
- .  Floor
- D  Door
- G  Holy Grail
- A  Altar
- M  Monster
- >  Stairs down
- <  Stairs up
- (space) Empty/passable area

Dungeon database format
-----------------------
The map is stored in dungeon_map.db using the table:

  floor_map_rows

Columns:
- floor_index   Zero-based floor number
- row_index     Zero-based row number within that floor
- row_text      Raw text for the row

Rows are normalized into rectangular floor grids when loaded. Shorter rows are
padded on the right with wall tiles (#).

Legacy compatibility:
- Older single-floor data can be read from a table named map_rows.
- When legacy data is loaded, missing floors are filled with built-in defaults
  until the dungeon has three floors.

Editor features
---------------
The editor lets you place tiles, switch floors, save the dungeon, and verify
that the full dungeon is valid.

Validation checks include:
- empty maps or maps with no walkable tiles
- unreachable walkable tiles
- unreachable Grail, altar, monsters, or stairs
- passable leaks in the outer border
- unknown tile values
- invalid stair placement by floor
- missing required upstairs/downstairs tiles on interior floors
- missing or duplicate quest objects across the dungeon
- incorrect total counts for stair links across all floors

Editor controls
---------------
- Arrow keys       Move cursor
- , or <           Previous floor
- . or >           Next floor
- 1                Wall
- 2                Floor
- 3                Door
- 4                Holy Grail
- 5                Altar
- 6                Monster
- 7                Stairs down
- 8                Stairs up
- 0                Empty space
- [ or ]           Cycle selected tile
- Space / Enter    Place selected tile
- P                Place selected tile
- V                Verify whole dungeon
- S                Save map to dungeon_map.db
- Q                Quit editor

Editor rules
------------
- The editor enforces exactly one Holy Grail across the full dungeon by
  removing any existing Grail before placing a new one.
- The editor enforces exactly one altar across the full dungeon by removing
  any existing altar before placing a new one.
- Each floor keeps at most one upstairs tile and one downstairs tile.
- Upstairs cannot be placed on floor 1.
- Downstairs cannot be placed on the final floor.

Notes
-----
- Empty space is shown as . in the editor for visibility, but the stored tile
  value is a space character.
- The game and editor now use the same dungeon_map.db file, so saved editor
  changes affect the next game session.

License
-------
This project is distributed under the dungeona Donationware License v1.0.
See license.txt for the full license text.

Author
------
Copyright (c) 2026 mtatton
