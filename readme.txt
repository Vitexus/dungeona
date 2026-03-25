DUNGEONA
========

Overview
--------
Dungeona is a terminal dungeon crawler written in Python with the built-in
curses module. It renders a pseudo-3D first-person ASCII view, stores dungeon
data in SQLite, and includes a separate terminal editor for building and
validating multi-floor dungeons.

This version is themed as a Holy Grail quest. You explore three connected
floors, fight monsters, recover the grail, and deliver it to the altar on the
final floor.

[Donate](https://paypal.me/michtatton)

Project contents
----------------
dungeona.py        Main game
dungeon_editor.py  Terminal editor and dungeon validator
license.txt        Donationware license
readme.txt         This file

dungeon_map.db is created automatically the first time you run the game or
editor if it does not already exist.

Features
--------
- First-person ASCII dungeon exploration
- Three connected dungeon floors in the default data set
- Holy Grail quest objective with altar turn-in
- Multiple monster types: rats, skeletons, and ogres
- Doors that can be opened from the tile directly ahead
- Stairs for moving between floors
- Toggleable minimap with player position and facing direction
- Energy-based combat and waiting to recover energy
- SQLite-backed dungeon storage
- Built-in dungeon editor with verification tools

Requirements
------------
- Python 3.10 or newer recommended
- A terminal with curses support
- No third-party packages required on Linux or macOS
- On Windows, install curses support first:

  pip install windows-curses

How to run
----------
From the project folder:

  python dungeona.py

To open the dungeon editor:

  python dungeon_editor.py

Game summary
------------
The game loads dungeon floors from dungeon_map.db and starts on the first
walkable tile it finds. You explore in first-person view, manage energy, open
doors, defeat monsters, collect the Holy Grail, and bring it to the altar on
floor 3.

The default dungeon contains three floors linked by stair tiles:
- >  stairs down
- <  stairs up

The minimap can be shown or hidden during play. The status line displays
energy, current floor, map position, facing direction, carried items,
Holy Grail status, and defeated enemy count.

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
- Space / Enter    Interact with the tile ahead
- .                Wait and regain 1 energy
- M                Toggle minimap
- >                Use stairs down immediately
- <                Use stairs up immediately
- X                Quit

Gameplay rules
--------------
- Energy starts at 12 and is capped at 12.
- Waiting restores 1 energy.
- Doors open when you interact with a door tile directly in front of you.
- Defeating a monster costs:
  - 2 energy while not carrying the grail
  - 1 energy while carrying the grail
- The Holy Grail can be picked up by stepping onto it or interacting with it.
- The grail must be delivered to the altar on floor 3 to complete the quest.
- Standing on a stair tile automatically moves you between linked floors.
- You can also use < or > to travel stairs directly.
- Defeated monsters increase the on-screen score counter.
- A congratulations banner is shown when the quest is completed.

Monster reference
-----------------
- R  Rat
- S  Skeleton
- O  Ogre
- M  Legacy generic monster marker (supported by the editor and validator)

Dungeon data
------------
Dungeon data is stored in dungeon_map.db in the table:

  floor_map_rows

Columns:
- floor_index   Zero-based floor number
- row_index     Zero-based row number within that floor
- row_text      Raw text for the row

If the database is empty, the game and editor populate it with the built-in
default floors.

The editor can also read legacy single-floor data from a map_rows table. The
game supports legacy M monster markers by converting them into rat,
skeleton, or ogre encounters when floors are loaded.

Tile reference
--------------
- #  Wall
- .  Floor
- D  Door
- G  Holy Grail
- A  Altar
- R  Rat
- S  Skeleton
- O  Ogre
- M  Generic monster marker (legacy/editor support)
- >  Stairs down
- <  Stairs up
- (space) Empty walkable tile

Dungeon editor
--------------
The editor lets you inspect and modify dungeon floors stored in the database.
It can switch between floors, place tiles, verify the dungeon, and save changes
back to dungeon_map.db.

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
- 6                Rat
- 7                Skeleton
- 8                Ogre
- 9                Stairs down
- 0                Stairs up
- -                Generic monster marker
- =                Empty space
- [ or ]           Cycle selected tile
- Space / Enter    Place selected tile
- P                Place selected tile
- V                Verify the whole dungeon
- S                Save to dungeon_map.db
- Q                Quit editor

Editor behavior and validation
------------------------------
- The editor maintains exactly one Holy Grail across the full dungeon.
- The editor maintains exactly one altar across the full dungeon.
- Each floor can have at most one upstairs tile and one downstairs tile.
- Upstairs cannot be placed on floor 1.
- Downstairs cannot be placed on the final floor.
- Verification checks for:
  - empty maps
  - inconsistent row widths
  - unknown tile values
  - unreachable walkable tiles
  - unreachable quest tiles, monsters, or stairs
  - leaks on the outer border
  - missing or extra stair links across floors
  - missing or extra grails
  - missing or extra altars
  - missing monsters

Notes
-----
- Empty space is displayed as . in the editor for visibility, but it is stored
  as a literal space character in the map.
- The default floor data is built into the Python files and written to the
  database automatically if the table is empty.
- If you change the database outside the editor, keep stair links consistent
  between floors.

License
-------
This project is distributed under the dungeona Donationware License v1.0.
See license.txt for the full license text.

Author
------
Copyright (c) 2026 mtatton
