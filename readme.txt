DUNGEONA
========

Overview
--------
Dungeona is a small terminal dungeon crawler written in Python using the
built-in curses module. It renders a pseudo-3D first-person dungeon view in
ASCII/ANSI style and includes a separate terminal map editor for changing the
dungeon layout stored in a SQLite database.

[Donate](https://paypal.me/michtatton)

Project contents
----------------
dungeona.py        Main game
dungeon_editor.py  Map editor and validator
dungeon_map.db     SQLite database containing dungeon floor rows
license.txt        Donationware license
readme.txt         This file

Current project behavior
------------------------
This repository currently has two different dungeon data paths:

- dungeona.py uses the built-in FLOORS constant inside the game script.
- dungeon_editor.py reads from and writes to dungeon_map.db.

That means editor changes saved to dungeon_map.db do not affect the current
game script unless dungeona.py is updated to load the database as well.

Gameplay summary
----------------
- Explore a three-floor dungeon from a first-person view.
- Open doors.
- Pick up the sword to reduce combat cost.
- Defeat monsters while managing energy.
- Travel between floors with stair tiles.
- Toggle the minimap as needed.

Requirements
------------
- Python 3.10+ recommended
- A terminal that supports curses and ANSI-style character rendering
- No third-party Python packages are required on Linux/macOS
- On Windows, you may need the windows-curses package for curses support:

  pip install windows-curses

How to run
----------
From the project folder:

  python dungeona.py

To open the map editor:

  python dungeon_editor.py

Game data used by dungeona.py
-----------------------------
The main game currently starts from the built-in FLOORS list in dungeona.py.
It does not load dungeon_map.db.

The default in-code dungeon contains:
- 3 floors
- doors (D)
- monsters (M)
- one sword (S)
- stairs down (>) and stairs up (<)

The player starts on floor 1 at position 1,1, facing east.

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
- Space            Interact with the tile directly ahead
                   (open door / attack / pick up sword / use stairs)
- . or >           Go down when standing on a > stair tile
- <                Go up when standing on a < stair tile
- ,                Wait and recover 1 energy
- M                Toggle minimap
- X                Quit

Notes:
- Moving onto a stair tile also triggers stair travel automatically.
- Space can also use stairs if the stair tile is directly in front of you.

Game systems
------------
- Energy starts at 12 and caps at 12.
- Waiting restores 1 energy.
- Fighting costs:
  - 1 energy with the sword
  - 2 energy without the sword
- Enemies defeated increase the score counter.
- Doors can be opened from the tile directly in front of the player.
- Picking up the sword is permanent for the current run and removes the sword
  tile from the map.
- The status line shows energy, floor, position, facing direction, sword
  status, and defeated enemy count.

Tile meanings
-------------
- #  Wall
- .  Floor
- D  Door
- S  Sword
- M  Monster
- >  Stairs down
- <  Stairs up
- (space) Empty/passable area

Map editor data
---------------
The editor stores dungeon data in dungeon_map.db using the table:

  floor_map_rows

Columns:
- floor_index   Zero-based floor number
- row_index     Zero-based row number within that floor
- row_text      Raw text for the row

If the database is empty, the editor creates floor_map_rows and populates it
with the built-in default three-floor map set.

Legacy compatibility:
- The editor can also read an older single-floor table named map_rows.
- When loading legacy data, it pads the missing floors with defaults until
  there are three floors.

Rows are normalized into rectangular floor grids when loaded. Shorter rows are
padded on the right with wall tiles (#).

Editor features
---------------
The editor lets you place tiles, switch floors, save the dungeon, and run
validation checks across all floors.

Validation looks for issues such as:
- inconsistent row widths before normalization
- missing sword
- missing monsters
- unreachable walkable tiles
- unreachable sword, monsters, or stairs
- leaks in the outer border
- unknown tile values
- invalid stair placement by floor
- missing or extra up/down stair links across the dungeon

Editor controls
---------------
- Arrow keys       Move cursor
- , or <           Previous floor
- . or >           Next floor
- 1                Wall
- 2                Floor
- 3                Door
- 4                Sword
- 5                Monster
- 6                Stairs down
- 7                Stairs up
- 0                Empty space
- [ or ]           Cycle selected tile
- Space / Enter    Place selected tile
- P                Place selected tile
- V                Verify whole dungeon
- S                Save map to dungeon_map.db
- Q                Quit editor

Editor rules
------------
- The editor enforces exactly one sword across the full dungeon by removing any
  existing sword before placing a new one.
- Each floor keeps at most one upstairs tile and one downstairs tile.
- Upstairs cannot be placed on floor 1.
- Downstairs cannot be placed on the final floor.

Notes
-----
- Empty space is shown as . in the editor for visibility, but the actual stored
  tile is a space character.
- The game and editor currently are not synchronized to the same map source.
  The editor saves to dungeon_map.db, while the main game still uses the
  hard-coded FLOORS data in dungeona.py.

License
-------
This project is distributed under the dungeona Donationware License v1.0.
See license.txt for the full license text.

Author
------
Copyright (c) 2026 mtatton
