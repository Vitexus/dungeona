import tkinter as tk
from typing import Dict, List, Optional, Tuple

import dungeona

CELL_SIZE = 8
MINIMAP_TILE = 14
VIEW_MARGIN = 12
BACKGROUND = "#0a0c0f"
CEILING_COLOR = "#11161c"
FLOOR_BASE = "#1c1815"
TEXT_COLOR = "#d8dee9"
STATUS_BG = "#101419"

COLOR_MAP = {
    1: "#586270",
    2: "#b58a3b",
    3: "#4fa7bf",
    4: "#4e463e",
    5: "#5c6670",
    6: "#45a85a",
    7: "#b45151",
    8: "#c9b24a",
    9: "#6f95c8",
    10: "#8f5db0",
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

        self.static_cache: Dict[str, object] = {
            "background_key": None,
            "background_items": [],
            "frame_key": None,
            "frame_items": [],
            "last_render_key": None,
            "last_render_items": [],
        }
        self.dynamic_scene_items: List[int] = []
        self.dynamic_overlay_items: List[int] = []

        self.root.bind("<KeyPress>", self.on_key)
        self.root.bind("<Configure>", self.on_resize)
        self.redraw(force_scene=True)

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

    def scene_origin(self) -> Tuple[int, int]:
        return VIEW_MARGIN, VIEW_MARGIN

    def clear_item_list(self, items: List[int]) -> None:
        for item in items:
            self.canvas.delete(item)
        items.clear()

    def rect_from_cells(self, x: int, y: int, w: int = 1, h: int = 1) -> Tuple[int, int, int, int]:
        ox, oy = self.scene_origin()
        return (
            ox + x * CELL_SIZE,
            oy + y * CELL_SIZE,
            ox + (x + w) * CELL_SIZE,
            oy + (y + h) * CELL_SIZE,
        )

    def draw_cell_rect(self, x: int, y: int, color: str) -> int:
        x0, y0, x1, y1 = self.rect_from_cells(x, y)
        return self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)

    def batch_runs_by_row(self, rects: List[Tuple[int, int, str]]) -> List[Tuple[int, int, int, str]]:
        if not rects:
            return []
        rects = sorted(rects, key=lambda item: (item[1], item[0]))
        runs: List[Tuple[int, int, int, str]] = []
        start_x, y, color = rects[0]
        width = 1
        prev_x = start_x
        for x, row_y, row_color in rects[1:]:
            if row_y == y and row_color == color and x == prev_x + 1:
                width += 1
            else:
                runs.append((start_x, y, width, color))
                start_x, y, color = x, row_y, row_color
                width = 1
            prev_x = x
        runs.append((start_x, y, width, color))
        return runs

    def create_batched_rectangles(self, rects: List[Tuple[int, int, str]], target_items: List[int]) -> None:
        for x, y, width, color in self.batch_runs_by_row(rects):
            x0, y0, x1, y1 = self.rect_from_cells(x, y, width, 1)
            target_items.append(self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color))

    def ensure_background_layer(self) -> None:
        background_key = (self.view_width_cells, self.view_height_cells, CELL_SIZE)
        if self.static_cache.get("background_key") == background_key:
            return
        old_items = self.static_cache.get("background_items", [])
        if isinstance(old_items, list):
            self.clear_item_list(old_items)
        items: List[int] = []
        for y in range(self.view_height_cells):
            color = self.floor_band_color(y)
            x0, y0, x1, y1 = self.rect_from_cells(0, y, self.view_width_cells, 1)
            items.append(self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color))
        self.static_cache["background_key"] = background_key
        self.static_cache["background_items"] = items

    def ensure_frame_layer(self) -> None:
        frame_key = (self.view_width_px, self.view_height_px, self.status_height)
        if self.static_cache.get("frame_key") == frame_key:
            return
        old_items = self.static_cache.get("frame_items", [])
        if isinstance(old_items, list):
            self.clear_item_list(old_items)
        items: List[int] = []
        left, top = self.scene_origin()
        right = left + self.view_width_px
        bottom = top + self.view_height_px
        items.append(self.canvas.create_rectangle(left - 2, top - 2, right + 2, bottom + 2, outline="#20262d", width=2))
        items.append(self.canvas.create_line(left + self.view_width_px // 2, top + self.view_height_px // 2 - 8, left + self.view_width_px // 2, top + self.view_height_px // 2 + 8, fill="#33404d"))
        items.append(self.canvas.create_line(left + self.view_width_px // 2 - 8, top + self.view_height_px // 2, left + self.view_width_px // 2 + 8, top + self.view_height_px // 2, fill="#33404d"))
        self.static_cache["frame_key"] = frame_key
        self.static_cache["frame_items"] = items

    def on_resize(self, event) -> None:
        width = max(500, event.width)
        height = max(420, event.height)
        usable_w = max(320, width - VIEW_MARGIN * 2)
        usable_h = max(220, height - VIEW_MARGIN * 2 - self.status_height)
        new_view_width_cells = max(48, usable_w // CELL_SIZE)
        new_view_height_cells = max(32, usable_h // CELL_SIZE)
        size_changed = (
            new_view_width_cells != self.view_width_cells
            or new_view_height_cells != self.view_height_cells
        )
        self.view_width_cells = new_view_width_cells
        self.view_height_cells = new_view_height_cells
        self.view_width_px = self.view_width_cells * CELL_SIZE
        self.view_height_px = self.view_height_cells * CELL_SIZE
        self.redraw(force_scene=size_changed)

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
        self.redraw(force_scene=acted)

    def scene_render_key(self) -> Tuple[object, ...]:
        return (
            int(self.state["floor"]),
            int(self.state["x"]),
            int(self.state["y"]),
            int(self.state["facing"]),
            int(self.state.get("action_count", 0)),
            self.view_width_cells,
            self.view_height_cells,
        )

    def char_fill(self, ch: str, color_id: int) -> Optional[str]:
        if ch == " ":
            return None
        base = self.color_for(color_id)
        if ch in {"░", ".", ",", "`", "_"}:
            return self.shade_color(base, 0.62)
        if ch in {"▒", "|", "/", "\\"}:
            return self.shade_color(base, 0.80)
        if ch in {"▓", "=", "+", "#"}:
            return self.shade_color(base, 0.96)
        if ch in {"█", "@", "%", "&"}:
            return self.shade_color(base, 1.08)
        return self.shade_color(base, 1.00)

    def compute_scene_rects(self) -> List[Tuple[int, int, str]]:
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
        rects: List[Tuple[int, int, str]] = []
        for y, x, ch, color_id in items:
            if 0 <= x < self.view_width_cells and 0 <= y < self.view_height_cells:
                fill = self.char_fill(ch, color_id)
                if fill is not None:
                    rects.append((x, y, fill))
        return rects

    def draw_view(self, force_scene: bool = False) -> None:
        render_key = self.scene_render_key()
        if force_scene or self.static_cache.get("last_render_key") != render_key:
            rects = self.compute_scene_rects()
            self.static_cache["last_render_key"] = render_key
            self.static_cache["last_render_items"] = rects
        else:
            rects = self.static_cache.get("last_render_items", [])
        self.clear_item_list(self.dynamic_scene_items)
        if isinstance(rects, list):
            self.create_batched_rectangles(rects, self.dynamic_scene_items)

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

        self.dynamic_overlay_items.append(self.canvas.create_rectangle(
            left - 8,
            top - 22,
            left + self.minimap_size + 8,
            top + self.minimap_size + 8,
            fill="#0b0f14",
            outline="#2c3742",
        ))
        self.dynamic_overlay_items.append(self.canvas.create_text(left, top - 12, anchor="w", fill="#7f9bb8", text=f"F{int(self.state['floor']) + 1}", font=("TkFixedFont", 10, "bold")))

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                mx = px + dx
                my = py + dy
                cell = dungeona.cell_at(grid, mx, my)
                x0 = left + (dx + radius) * MINIMAP_TILE
                y0 = top + (dy + radius) * MINIMAP_TILE
                color = "#161b21"
                if cell == "#":
                    color = "#4e5762"
                elif cell == "D":
                    color = "#9f7833"
                elif dungeona.is_monster(cell):
                    info = dungeona.monster_info(cell if cell in dungeona.MONSTER_TILES else "R")
                    color = self.color_for(int(info["color"]))
                elif cell == dungeona.QUEST_ITEM_TILE:
                    color = "#bba643"
                elif cell == dungeona.QUEST_TARGET_TILE:
                    color = "#7f4ea1"
                elif cell in {"<", ">"}:
                    color = "#5d7fae"
                elif cell in {".", " "}:
                    color = "#2a241f"
                self.dynamic_overlay_items.append(self.canvas.create_rectangle(x0, y0, x0 + MINIMAP_TILE - 1, y0 + MINIMAP_TILE - 1, fill=color, outline="#0a0d10"))

        center_x = left + radius * MINIMAP_TILE + MINIMAP_TILE // 2
        center_y = top + radius * MINIMAP_TILE + MINIMAP_TILE // 2
        self.dynamic_overlay_items.append(self.canvas.create_oval(center_x - 4, center_y - 4, center_x + 4, center_y + 4, fill="#48b060", outline=""))
        dx, dy = dungeona.DIRECTIONS[facing]
        self.dynamic_overlay_items.append(self.canvas.create_line(center_x, center_y, center_x + dx * 8, center_y + dy * 8, fill="#48b060", width=2))

    def draw_status(self) -> None:
        y0 = VIEW_MARGIN + self.view_height_px + 8
        width = self.view_width_px
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(
            VIEW_MARGIN,
            y0,
            VIEW_MARGIN + width,
            y0 + self.status_height,
            fill=STATUS_BG,
            outline="#26303a",
        ))

        energy = int(self.state["energy"])
        bar_w = 220
        fill_w = int(bar_w * energy / max(1, dungeona.MAX_ENERGY))
        self.dynamic_overlay_items.append(self.canvas.create_text(VIEW_MARGIN + 12, y0 + 16, anchor="w", fill=TEXT_COLOR, text="Energy", font=("TkFixedFont", 10, "bold")))
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(VIEW_MARGIN + 72, y0 + 8, VIEW_MARGIN + 72 + bar_w, y0 + 24, fill="#1e252c", outline="#34404c"))
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(VIEW_MARGIN + 72, y0 + 8, VIEW_MARGIN + 72 + fill_w, y0 + 24, fill="#48b060", outline=""))

        quest_status = "done" if bool(self.state["quest_complete"]) else ("carrying" if bool(self.state["has_grail"]) else "missing")
        line1 = (
            f"Floor {int(self.state['floor']) + 1}/{len(self.state['floors'])}   "
            f"Pos {self.state['x']},{self.state['y']}   "
            f"Facing {dungeona.DIRECTION_NAMES[int(self.state['facing'])]}   "
            f"Defeated {self.state['score']}"
        )
        line2 = f"Inventory {dungeona.inventory_count(self.state)}/{dungeona.MAX_CARRIED_ITEMS}   Grail {quest_status}"
        line3 = str(self.state["message"])

        self.dynamic_overlay_items.append(self.canvas.create_text(VIEW_MARGIN + 12, y0 + 40, anchor="w", fill=TEXT_COLOR, text=line1, font=("TkFixedFont", 10)))
        self.dynamic_overlay_items.append(self.canvas.create_text(VIEW_MARGIN + 12, y0 + 58, anchor="w", fill="#c9b24a", text=line2, font=("TkFixedFont", 10)))
        self.dynamic_overlay_items.append(self.canvas.create_text(VIEW_MARGIN + 12, y0 + 76, anchor="w", fill="#7f9bb8", text=line3[:120], font=("TkFixedFont", 10)))
        self.dynamic_overlay_items.append(self.canvas.create_text(VIEW_MARGIN + width - 12, y0 + 16, anchor="e", fill="#7f8b97", text=KEY_HELP, font=("TkFixedFont", 9)))

    def draw_congrats_overlay(self) -> None:
        if not bool(self.state.get("show_congrats_banner")):
            return
        width = self.view_width_px
        height = self.view_height_px
        left = VIEW_MARGIN + 80
        top = VIEW_MARGIN + max(60, height // 3)
        right = VIEW_MARGIN + width - 80
        bottom = top + 120
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(left, top, right, bottom, fill="#0d1014", outline="#c9b24a", width=3))
        self.dynamic_overlay_items.append(self.canvas.create_text(
            (left + right) // 2,
            top + 42,
            text="Congratulations.",
            fill="#d8c15f",
            font=("TkFixedFont", 22, "bold"),
        ))
        self.dynamic_overlay_items.append(self.canvas.create_text(
            (left + right) // 2,
            top + 78,
            text="Press any movement/action key to continue",
            fill="#d8dee9",
            font=("TkFixedFont", 10),
        ))

    def redraw(self, force_scene: bool = False) -> None:
        self.ensure_background_layer()
        self.ensure_frame_layer()
        self.draw_view(force_scene=force_scene)
        self.clear_item_list(self.dynamic_overlay_items)
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
