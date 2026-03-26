DUNGEONA
========

Version
-------
README for the project archive: 20260326_dungeona_015.zip

Overview
--------
Dungeona is a terminal-based first-person dungeon crawler written in Python.
It uses the built-in curses module for display, stores dungeon layouts in a
SQLite database, and includes a separate dungeon editor for creating and
validating multi-floor maps.

This build uses a Holy Grail quest theme: explore the dungeon, defeat monsters,
recover the grail, and carry it to the altar on the final floor.

Included files
--------------
dungeona.py         Main game

dungeon_editor.py   Terminal map editor and validator

ans.py              ANSI/ANS texture parser and optional viewer

dungeon_map.db      SQLite dungeon data file used by the game/editor

textures/
  wall.ans          Wall texture art
  door.ans          Door texture art

license.txt         Donationware license
readme.txt          This file

Features
--------
- First-person ASCII dungeon exploration
- Pseudo-3D corridor rendering in the terminal
- ANSI/ANS wall and door textures
- Three connected floors in the default adventure
- Holy Grail quest objective with altar turn-in
- Multiple monster types: rats, skeletons, and ogres
- Door interaction from the tile directly ahead
- Stairs connecting floors
- Toggleable minimap with facing direction
- Energy-based combat and waiting system
- SQLite-backed dungeon storage
- Full-screen terminal dungeon editor with verification tools

Requirements
------------
- Python 3.10 or newer recommended
- A terminal with curses support
- No third-party packages required on Linux or macOS
- Windows users may need:

  pip install windows-curses

How to run the game
-------------------
From the project folder:

  python dungeona.py

How to run the editor
---------------------
From the project folder:

  python dungeon_editor.py

How to view the ANSI textures
-----------------------------
The included ans.py utility can display or print the .ANS texture files.

Open a texture in the curses viewer:

  python ans.py textures/wall.ans

Open with autoscroll:

  python ans.py textures/wall.ans --autoscroll

Print the texture as plain text only:

  python ans.py textures/wall.ans --plain

Game objective
--------------
1. Explore the dungeon.
2. Find the Holy Grail.
3. Reach the altar on floor 3.
4. Place the grail on the altar to complete the quest.

Game controls
-------------
Movement and facing:
- Up Arrow / W      Move forward
- Down Arrow / S    Move backward
- Q                 Turn left
- E                 Turn right
- Z                 Strafe left
- C                 Strafe right

Actions:
- Space / Enter     Interact with the tile directly ahead
- .                 Wait and regain energy
- M                 Toggle minimap
- >                 Use stairs down
- <                 Use stairs up
- X                 Quit the game

Game rules
----------
- Energy starts at 12 and is capped at 12.
- Waiting restores 1 energy.
- Monsters are defeated by interacting with them when they are directly ahead.
- Combat costs:
  - 2 energy before you have the grail
  - 1 energy while carrying the grail
- Doors open when you interact with a door tile in front of you.
- Standing on stairs can move you between linked floors.
- The grail can be picked up when reached.
- The quest ends when the grail is placed on the altar on floor 3.

Monster reference
-----------------
- R   Rat
- S   Skeleton
- O   Ogre
- M   Legacy monster marker supported by the editor/loader

Tile reference
--------------
- #   Wall
- .   Floor
- D   Door
- G   Holy Grail
- A   Altar
- R   Rat
- S   Skeleton
- O   Ogre
- M   Generic monster marker (legacy support)
- >   Stairs down
- <   Stairs up
- (space) Empty walkable tile

Dungeon data
------------
Dungeon data is stored in the SQLite database file:

  dungeon_map.db

The main table used by the multi-floor system is:

  floor_map_rows

Columns:
- floor_index   Zero-based floor number
- row_index     Zero-based row number within the floor
- row_text      Raw text for that row

Notes:
- If the database is empty, the game/editor can repopulate it with built-in
  default floors.
- Legacy data in a single-floor map_rows table is also supported by the code.

Dungeon editor
--------------
The editor allows you to inspect, build, validate, and save multi-floor maps.
It includes a tile palette, floor switching, and whole-dungeon verification.

Editor controls
---------------
- Arrow Keys        Move cursor
- , or <            Previous floor
- . or >            Next floor
- 1                 Wall
- 2                 Floor
- 3                 Door
- 4                 Holy Grail
- 5                 Altar
- 6                 Rat
- 7                 Skeleton
- 8                 Ogre
- 9                 Stairs down
- 0                 Stairs up
- -                 Generic monster marker
- =                 Empty space
- [ or ]            Cycle selected tile
- Space / Enter     Place selected tile
- P                 Place selected tile
- V                 Verify the whole dungeon
- S                 Save to dungeon_map.db
- Q                 Quit editor

Editor validation checks
------------------------
The validator checks for problems such as:
- empty maps
- inconsistent row widths
- unknown tile values
- unreachable walkable areas
- unreachable quest tiles, monsters, or stairs
- leaks on the outer border
- missing or extra stair links
- missing or extra Holy Grails
- missing or extra altars
- missing monsters

Project notes
-------------
- Empty space is shown as a visible marker in the editor, but it is stored as a
  literal space character in the map data.
- The default adventure contains three linked floors.
- The project is terminal-focused and works best in a reasonably large console
  window.
- The texture loader in ans.py is reusable outside the game if you want to load
  ANSI art in other Python tools.

License
-------
This project is distributed under the dungeona Donationware License v1.0.
See license.txt for the full text.

Author
------
Copyright (c) 2026 mtatton

Donation
--------
PayPal: https://paypal.me/michtatton

