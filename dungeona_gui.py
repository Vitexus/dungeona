import tkinter as tk
from typing import Dict, List, Tuple

import dungeona

CELL_SIZE = 8
MINIMAP_TILE = 14
VIEW_MARGIN = 12
BACKGROUND = "#101215"
CEILING_COLOR = "#1b2026"
FLOOR_BASE = "#2f2a24"
TEXT_COLOR = "#e6e6e6"
STATUS_BG = "#171a1f"

COLOR_MAP = {
    1: "#7f8790",
    2: "#d2a44a",
    3: "#5ccfe6",
    4: "#6a5f52",
    5: "#7a7f86",
    6: "#54d26d",
    7: "#d95f5f",
    8: "#e6d05a",
    9: "#9bc7ff",
    10: "#c070e0",
}

KEY_HELP = "WASD/arrows move, Q/E turn, Z/C strafe, Space act, . wait, M map, </> stairs"


class DungeonaGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dungeona GUI")
        self.root.configure(bg=BACKGROUND)

        self.view_width_cells = 96
        self.view_height_cells = 56
        self.view_width_px = self.view_width_cells * CELL_SIZE
        self.view_height_px = self.view_height_cells * CELL_SIZE
        self.status_height = 90
        self.minimap_size = MINIMAP_TILE * 9

        self.canvas = tk.Canvas(
            self.root,
            width=self.view_width_px + VIEW_MARGIN * 2,
            height=self.view_height_px + VIEW_MARGIN * 2 + self.status_height,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        floors = dungeona.load_floors()
        start_floor, start_x, start_y = dungeona.find_start_position(floors)
        self.state: Dict[str, object] = {
            "floors": floors,
            "floor": start_floor,
            "x": start_x,
            "y": start_y,
            "facing": 1,
            "energy": dungeona.START_ENERGY,
            "score": 0,
            "has_grail": False,
            "quest_complete": False,
            "show_map": True,
            "message": f"Loaded dungeon from {dungeona.DB_PATH.name}.",
            "show_congrats_banner": False,
            "wall_textures": dungeona.load_wall_textures(),
            "animated_sprites": dungeona.load_animated_sprites(),
            "action_count": 0,
            "monster_chase": {},
        }
        dungeona.collect_tile(self.state, dungeona.current_grid(self.state))
        self.state["message"] = (
            f"Find the {dungeona.QUEST_ITEM_NAME} on floor {dungeona.QUEST_START_FLOOR + 1} "
            f"and bring it to the altar on floor {dungeona.QUEST_TARGET_FLOOR + 1}."
        )

        self.root.bind("<KeyPress>", self.on_key)
        self.root.bind("<Configure>", self.on_resize)
        self.redraw()

    def color_for(self, color_id: int, default: str = "#cfcfcf") -> str:
        return COLOR_MAP.get(color_id, default)

    def shade_color(self, color: str, factor: float) -> str:
        color = color.lstrip("#")
        if len(color) != 6:
            return color
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def floor_band_color(self, row: int) -> str:
        ratio = row / max(1, self.view_height_cells - 1)
        if ratio < 0.58:
            return CEILING_COLOR
        depth = (ratio - 0.58) / 0.42
        depth = max(0.0, min(1.0, depth))
        base = FLOOR_BASE.lstrip("#")
        r = int(base[0:2], 16)
        g = int(base[2:4], 16)
        b = int(base[4:6], 16)
        boost = int(24 * (1.0 - depth))
        return f"#{min(255, r + boost):02x}{min(255, g + boost):02x}{min(255, b + boost):02x}"

    def on_resize(self, event) -> None:
        width = max(500, event.width)
        height = max(420, event.height)
        usable_w = max(320, width - VIEW_MARGIN * 2)
        usable_h = max(220, height - VIEW_MARGIN * 2 - self.status_height)
        self.view_width_cells = max(48, usable_w // CELL_SIZE)
        self.view_height_cells = max(32, usable_h // CELL_SIZE)
        self.view_width_px = self.view_width_cells * CELL_SIZE
        self.view_height_px = self.view_height_cells * CELL_SIZE
        self.redraw()

    def advance_if_acted(self, acted: bool) -> None:
        if acted:
            self.state["action_count"] = int(self.state.get("action_count", 0)) + 1
            dungeona.advance_world(self.state)

    def on_key(self, event) -> None:
        key = event.keysym.lower()
        char = event.char
        acted = False

        if self.state.get("show_congrats_banner") and key not in {"x"}:
            self.state["show_congrats_banner"] = False

        if key in {"up", "w"}:
            old_pos = (self.state["x"], self.state["y"])
            dungeona.try_move(self.state, 1)
            self.state["message"] = "You move forward." if old_pos != (self.state["x"], self.state["y"]) else "A wall blocks your way."
            acted = True
        elif key in {"down", "s"}:
            old_pos = (self.state["x"], self.state["y"])
            dungeona.try_move(self.state, -1)
            self.state["message"] = "You move backward." if old_pos != (self.state["x"], self.state["y"]) else "You cannot move there."
            acted = True
        elif key in {"q"}:
            self.state["facing"] = (int(self.state["facing"]) - 1) % 4
            self.state["message"] = "You turn left."
            acted = True
        elif key in {"e"}:
            self.state["facing"] = (int(self.state["facing"]) + 1) % 4
            self.state["message"] = "You turn right."
            acted = True
        elif key in {"z"}:
            old_pos = (self.state["x"], self.state["y"])
            dungeona.try_strafe(self.state, -1)
            self.state["message"] = "You sidestep left." if old_pos != (self.state["x"], self.state["y"]) else "Blocked on the left."
            acted = True
        elif key in {"c"}:
            old_pos = (self.state["x"], self.state["y"])
            dungeona.try_strafe(self.state, 1)
            self.state["message"] = "You sidestep right." if old_pos != (self.state["x"], self.state["y"]) else "Blocked on the right."
            acted = True
        elif key in {"space", "return"}:
            self.state["message"] = dungeona.use_action(self.state)
            acted = True
        elif char == ".":
            self.state["energy"] = min(dungeona.MAX_ENERGY, int(self.state["energy"]) + dungeona.WAIT_ENERGY_GAIN)
            self.state["message"] = "You wait and regain a little energy."
            acted = True
        elif key == "m":
            self.state["show_map"] = not bool(self.state["show_map"])
            self.state["message"] = f"Map {'shown' if self.state['show_map'] else 'hidden'}."
            acted = True
        elif char == ">":
            self.state["message"] = dungeona.travel_stairs(self.state, 1)
            acted = True
        elif char == "<":
            self.state["message"] = dungeona.travel_stairs(self.state, -1)
            acted = True
        elif key == "x":
            self.root.destroy()
            return

        self.advance_if_acted(acted)
        self.redraw()

    def draw_cell_rect(self, x: int, y: int, color: str) -> None:
        x0 = VIEW_MARGIN + x * CELL_SIZE
        y0 = VIEW_MARGIN + y * CELL_SIZE
        self.canvas.create_rectangle(x0, y0, x0 + CELL_SIZE, y0 + CELL_SIZE, fill=color, outline=color)

    def draw_background(self) -> None:
        for y in range(self.view_height_cells):
            color = self.floor_band_color(y)
            self.canvas.create_rectangle(
                VIEW_MARGIN,
                VIEW_MARGIN + y * CELL_SIZE,
                VIEW_MARGIN + self.view_width_px,
                VIEW_MARGIN + (y + 1) * CELL_SIZE,
                fill=color,
                outline=color,
            )

    def draw_view(self) -> None:
        grid = dungeona.current_grid(self.state)
        items = dungeona.render_view(
            grid,
            int(self.state["x"]),
            int(self.state["y"]),
            int(self.state["facing"]),
            self.view_width_cells,
            self.view_height_cells,
            self.state.get("wall_textures"),
            self.state.get("animated_sprites"),
            int(self.state.get("action_count", 0)),
        )
        for y, x, ch, color_id in items:
            if 0 <= x < self.view_width_cells and 0 <= y < self.view_height_cells:
                if ch == " ":
                    continue
                base = self.color_for(color_id)
                if ch in {"░", ".", ",", "`", "_"}:
                    fill = self.shade_color(base, 0.6)
                elif ch in {"▒", "|", "/", "\\"}:
                    fill = self.shade_color(base, 0.8)
                elif ch in {"▓", "=", "+", "#"}:
                    fill = self.shade_color(base, 1.0)
                else:
                    fill = self.shade_color(base, 1.15)
                self.draw_cell_rect(x, y, fill)

    def draw_minimap(self) -> None:
        if not bool(self.state.get("show_map")):
            return
        grid = dungeona.current_grid(self.state)
        px = int(self.state["x"])
        py = int(self.state["y"])
        facing = int(self.state["facing"])
        left = VIEW_MARGIN + 10
        top = VIEW_MARGIN + 10
        radius = 4

        self.canvas.create_rectangle(
            left - 8,
            top - 22,
            left + self.minimap_size + 8,
            top + self.minimap_size + 8,
            fill="#0d1015",
            outline="#5a6a7a",
        )
        self.canvas.create_text(left, top - 12, anchor="w", fill="#9bc7ff", text=f"F{int(self.state['floor']) + 1}", font=("TkFixedFont", 10, "bold"))

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                mx = px + dx
                my = py + dy
                cell = dungeona.cell_at(grid, mx, my)
                x0 = left + (dx + radius) * MINIMAP_TILE
                y0 = top + (dy + radius) * MINIMAP_TILE
                color = "#20252c"
                if cell == "#":
                    color = "#7a7f86"
                elif cell == "D":
                    color = "#d2a44a"
                elif dungeona.is_monster(cell):
                    info = dungeona.monster_info(cell if cell in dungeona.MONSTER_TILES else "R")
                    color = self.color_for(int(info["color"]))
                elif cell == dungeona.QUEST_ITEM_TILE:
                    color = "#e6d05a"
                elif cell == dungeona.QUEST_TARGET_TILE:
                    color = "#b06ad6"
                elif cell in {"<", ">"}:
                    color = "#8dbbff"
                elif cell in {".", " "}:
                    color = "#3d352d"
                self.canvas.create_rectangle(x0, y0, x0 + MINIMAP_TILE - 1, y0 + MINIMAP_TILE - 1, fill=color, outline="#0f1114")

        center_x = left + radius * MINIMAP_TILE + MINIMAP_TILE // 2
        center_y = top + radius * MINIMAP_TILE + MINIMAP_TILE // 2
        self.canvas.create_oval(center_x - 4, center_y - 4, center_x + 4, center_y + 4, fill="#54d26d", outline="")
        dx, dy = dungeona.DIRECTIONS[facing]
        self.canvas.create_line(center_x, center_y, center_x + dx * 8, center_y + dy * 8, fill="#54d26d", width=2)

    def draw_status(self) -> None:
        y0 = VIEW_MARGIN + self.view_height_px + 8
        width = self.view_width_px
        self.canvas.create_rectangle(
            VIEW_MARGIN,
            y0,
            VIEW_MARGIN + width,
            y0 + self.status_height,
            fill=STATUS_BG,
            outline="#2e3742",
        )

        energy = int(self.state["energy"])
        bar_w = 220
        fill_w = int(bar_w * energy / max(1, dungeona.MAX_ENERGY))
        self.canvas.create_text(VIEW_MARGIN + 12, y0 + 16, anchor="w", fill=TEXT_COLOR, text="Energy", font=("TkFixedFont", 10, "bold"))
        self.canvas.create_rectangle(VIEW_MARGIN + 72, y0 + 8, VIEW_MARGIN + 72 + bar_w, y0 + 24, fill="#2b3138", outline="#495463")
        self.canvas.create_rectangle(VIEW_MARGIN + 72, y0 + 8, VIEW_MARGIN + 72 + fill_w, y0 + 24, fill="#54d26d", outline="")

        quest_status = "done" if bool(self.state["quest_complete"]) else ("carrying" if bool(self.state["has_grail"]) else "missing")
        line1 = (
            f"Floor {int(self.state['floor']) + 1}/{len(self.state['floors'])}   "
            f"Pos {self.state['x']},{self.state['y']}   "
            f"Facing {dungeona.DIRECTION_NAMES[int(self.state['facing'])]}   "
            f"Defeated {self.state['score']}"
        )
        line2 = f"Inventory {dungeona.inventory_count(self.state)}/{dungeona.MAX_CARRIED_ITEMS}   Grail {quest_status}"
        line3 = str(self.state["message"])

        self.canvas.create_text(VIEW_MARGIN + 12, y0 + 40, anchor="w", fill=TEXT_COLOR, text=line1, font=("TkFixedFont", 10))
        self.canvas.create_text(VIEW_MARGIN + 12, y0 + 58, anchor="w", fill="#e6d05a", text=line2, font=("TkFixedFont", 10))
        self.canvas.create_text(VIEW_MARGIN + 12, y0 + 76, anchor="w", fill="#9bc7ff", text=line3[:120], font=("TkFixedFont", 10))

        self.canvas.create_text(VIEW_MARGIN + width - 12, y0 + 16, anchor="e", fill="#9aa7b5", text=KEY_HELP, font=("TkFixedFont", 9))

    def draw_congrats_overlay(self) -> None:
        if not bool(self.state.get("show_congrats_banner")):
            return
        width = self.view_width_px
        height = self.view_height_px
        left = VIEW_MARGIN + 40
        top = VIEW_MARGIN + 40
        right = VIEW_MARGIN + width - 40
        bottom = VIEW_MARGIN + height - 40
        self.canvas.create_rectangle(left, top, right, bottom, fill="#121212", outline="#e6d05a", width=3)
        for idx, line in enumerate(dungeona.CONGRATS_BANNER):
            self.canvas.create_text(
                (left + right) // 2,
                top + 40 + idx * 18,
                text=line,
                fill="#f3dd75",
                font=("TkFixedFont", 11, "bold"),
            )
        self.canvas.create_text(
            (left + right) // 2,
            bottom - 28,
            text="Press any movement/action key to continue",
            fill="#ffffff",
            font=("TkFixedFont", 10),
        )

    def redraw(self) -> None:
        self.canvas.delete("all")
        self.draw_background()
        self.draw_view()
        self.draw_minimap()
        self.draw_status()
        self.draw_congrats_overlay()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = DungeonaGUI()
    app.run()


if __name__ == "__main__":
    main()
