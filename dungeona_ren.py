import tkinter as tk
from typing import Dict, List, Optional, Tuple

import dungeona
from ans import AnsiCell, AnsiTexture, COLOR_NAME_BY_CODE

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 400
STATUS_HEIGHT = 64
VIEW_HEIGHT = WINDOW_HEIGHT - STATUS_HEIGHT
BACKGROUND = "#0a0c0f"
STATUS_BG = "#101419"
TEXT_COLOR = "#d8dee9"
CELL_W = 4
CELL_H = 4
VIEW_WIDTH_CELLS = WINDOW_WIDTH // CELL_W
VIEW_HEIGHT_CELLS = VIEW_HEIGHT // CELL_H
MINIMAP_TILE = 10
MIN_RENDER_SCALE = 1
MAX_RENDER_SCALE = 4

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
ANSI_RGB = {
    "Bk": "#000000",
    "Re": "#aa0000",
    "Gr": "#00aa00",
    "Ye": "#aa5500",
    "Bl": "#0000aa",
    "Ma": "#aa00aa",
    "Cy": "#00aaaa",
    "Wh": "#aaaaaa",
}
BRIGHT_ANSI_RGB = {
    "Bk": "#555555",
    "Re": "#ff5555",
    "Gr": "#55ff55",
    "Ye": "#ffff55",
    "Bl": "#5555ff",
    "Ma": "#ff55ff",
    "Cy": "#55ffff",
    "Wh": "#ffffff",
}
DARK_ANSI_RGB = {
    "Bk": "#000000",
    "Re": "#550000",
    "Gr": "#005500",
    "Ye": "#553300",
    "Bl": "#000055",
    "Ma": "#550055",
    "Cy": "#005555",
    "Wh": "#555555",
}

KEY_HELP = "WASD/arrows move  Q/E turn  Z/C strafe  Space act  . wait  M map  X quit"


class DungeonaRenderer:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dungeona Renderer")
        self.root.configure(bg=BACKGROUND)
        self.root.resizable(True, True)

        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        self.status_height = STATUS_HEIGHT
        self.render_scale = MIN_RENDER_SCALE
        self.cell_w = CELL_W
        self.cell_h = CELL_H
        self.minimap_tile = MINIMAP_TILE
        self.view_height = self.window_height - self.status_height
        self.view_width_cells = self.window_width // self.cell_w
        self.view_height_cells = self.view_height // self.cell_h

        self.canvas = tk.Canvas(
            self.root,
            width=self.window_width,
            height=self.window_height,
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
            "floor_texture": dungeona.load_surface_texture(dungeona.FLOOR_TEXTURE_FILE),
            "ceiling_texture": dungeona.load_surface_texture(dungeona.CEILING_TEXTURE_FILE),
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
        self.monster_detail_items: List[int] = []
        self.item_detail_items: List[int] = []

        self.root.bind("<KeyPress>", self.on_key)
        self.root.bind("<Configure>", self.on_resize)
        self.draw_scene(force_scene=True)

    def color_for(self, color_id: int, default: str = "#cfcfcf") -> str:
        return COLOR_MAP.get(color_id, default)

    def shade_color(self, color: str, factor: float) -> str:
        color = color.lstrip("#")
        if len(color) != 6:
            return "#cfcfcf"
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def blend_colors(self, low: str, high: str, high_weight: float) -> str:
        low = low.lstrip("#")
        high = high.lstrip("#")
        if len(low) != 6 or len(high) != 6:
            return high if high_weight >= 0.5 else low
        high_weight = max(0.0, min(1.0, high_weight))
        low_weight = 1.0 - high_weight
        lr = int(low[0:2], 16)
        lg = int(low[2:4], 16)
        lb = int(low[4:6], 16)
        hr = int(high[0:2], 16)
        hg = int(high[2:4], 16)
        hb = int(high[4:6], 16)
        r = int(lr * low_weight + hr * high_weight)
        g = int(lg * low_weight + hg * high_weight)
        b = int(lb * low_weight + hb * high_weight)
        return f"#{r:02x}{g:02x}{b:02x}"

    def floor_band_color(self, row: int) -> str:
        ratio = row / max(1, self.view_height_cells - 1)
        if ratio < 0.58:
            return "#11161c"
        depth = (ratio - 0.58) / 0.42
        depth = max(0.0, min(1.0, depth))
        base = "#1c1815".lstrip("#")
        r = int(base[0:2], 16)
        g = int(base[2:4], 16)
        b = int(base[4:6], 16)
        boost = int(24 * (1.0 - depth))
        return f"#{min(255, r + boost):02x}{min(255, g + boost):02x}{min(255, b + boost):02x}"

    def clear_item_list(self, items: List[int]) -> None:
        for item in items:
            self.canvas.delete(item)
        items.clear()

    def update_render_metrics(self, width: int, height: int) -> None:
        self.window_width = max(320, width)
        self.window_height = max(240, height)
        self.status_height = max(48, int(self.window_height * 0.16))
        self.view_height = max(CELL_H * 24, self.window_height - self.status_height)
        width_scale = max(1, self.window_width // WINDOW_WIDTH)
        height_scale = max(1, self.view_height // VIEW_HEIGHT)
        self.render_scale = max(MIN_RENDER_SCALE, min(MAX_RENDER_SCALE, min(width_scale, height_scale)))
        self.cell_w = CELL_W * self.render_scale
        self.cell_h = CELL_H * self.render_scale
        self.minimap_tile = MINIMAP_TILE * self.render_scale
        self.view_width_cells = max(48, self.window_width // self.cell_w)
        self.view_height_cells = max(24, self.view_height // self.cell_h)

    def rect_from_cells(self, x: int, y: int, w: int = 1, h: int = 1) -> Tuple[int, int, int, int]:
        return (
            x * self.cell_w,
            y * self.cell_h,
            (x + w) * self.cell_w,
            (y + h) * self.cell_h,
        )

    def fill_rows_to_runs(self, fill_rows: List[List[Optional[str]]]) -> List[Tuple[int, int, int, str]]:
        runs: List[Tuple[int, int, int, str]] = []
        for y, row in enumerate(fill_rows):
            start_x: Optional[int] = None
            current_color: Optional[str] = None
            for x, color in enumerate(row):
                if color == current_color:
                    continue
                if current_color is not None and start_x is not None:
                    runs.append((start_x, y, x - start_x, current_color))
                start_x = x if color is not None else None
                current_color = color
            if current_color is not None and start_x is not None:
                runs.append((start_x, y, len(row) - start_x, current_color))
        return runs

    def create_batched_rectangles(self, runs: List[Tuple[int, int, int, str]], target_items: List[int]) -> None:
        for x, y, width, color in runs:
            x0, y0, x1, y1 = self.rect_from_cells(x, y, width, 1)
            target_items.append(self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color))

    def ensure_background_layer(self) -> None:
        background_key = (self.view_width_cells, self.view_height_cells, self.cell_w, self.cell_h)
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
        frame_key = (self.window_width, self.view_height, self.status_height)
        if self.static_cache.get("frame_key") == frame_key:
            return
        old_items = self.static_cache.get("frame_items", [])
        if isinstance(old_items, list):
            self.clear_item_list(old_items)
        items: List[int] = []
        items.append(self.canvas.create_rectangle(0, 0, self.window_width - 1, self.view_height - 1, outline="#20262d", width=2))
        center_x = self.window_width // 2
        center_y = self.view_height // 2
        items.append(self.canvas.create_line(center_x, center_y - 8, center_x, center_y + 8, fill="#33404d"))
        items.append(self.canvas.create_line(center_x - 8, center_y, center_x + 8, center_y, fill="#33404d"))
        self.static_cache["frame_key"] = frame_key
        self.static_cache["frame_items"] = items

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

    def ansi_color_to_hex(self, color_name: str, intensity: str = "me") -> str:
        if intensity == "hi":
            return BRIGHT_ANSI_RGB.get(color_name, ANSI_RGB["Wh"])
        if intensity == "lo":
            return DARK_ANSI_RGB.get(color_name, ANSI_RGB["Wh"])
        return ANSI_RGB.get(color_name, ANSI_RGB["Wh"])

    def texture_cell_fill(self, cell: AnsiCell) -> Optional[str]:
        ch = cell.char
        fg = self.ansi_color_to_hex(cell.fg, cell.intensity)
        bg = self.ansi_color_to_hex(cell.bg, "me")
        if ch == " ":
            return bg
        if ch in {"█", "■"}:
            return fg
        if ch in {"▀", "▄"}:
            return self.blend_colors(bg, fg, 0.50)
        if ch == "▓":
            return self.blend_colors(bg, fg, 0.72)
        if ch == "▒":
            return self.blend_colors(bg, fg, 0.50)
        if ch == "░":
            return self.blend_colors(bg, fg, 0.28)
        if ch in {".", ",", "`", "_"}:
            return self.blend_colors(bg, fg, 0.20)
        return fg

    def distance_shade_factor(self, distance: float, side: int = 0) -> float:
        depth = max(0.0, min(1.0, distance / max(0.001, dungeona.MAX_RENDER_DEPTH)))
        factor = 1.05 - depth * 0.55
        if side == 1:
            factor *= 0.84
        return max(0.22, min(1.08, factor))

    def sample_texture_cell(self, texture: Optional[AnsiTexture], x_ratio: float, y_ratio: float) -> Optional[AnsiCell]:
        if texture is None or texture.width <= 0 or texture.height <= 0:
            return None
        tx = min(texture.width - 1, max(0, int(x_ratio * max(1, texture.width - 1))))
        ty = min(texture.height - 1, max(0, int(y_ratio * max(1, texture.height - 1))))
        return texture.rows[ty][tx]

    def sample_repeating_texture_cell(self, texture: Optional[AnsiTexture], x_ratio: float, y_ratio: float) -> Optional[AnsiCell]:
        if texture is None or texture.width <= 0 or texture.height <= 0:
            return None
        wrapped_x = x_ratio % 1.0
        wrapped_y = y_ratio % 1.0
        tx = min(texture.width - 1, max(0, int(wrapped_x * texture.width)))
        ty = min(texture.height - 1, max(0, int(wrapped_y * texture.height)))
        return texture.rows[ty][tx]

    def texture_identity(self, texture: Optional[AnsiTexture]) -> Optional[Tuple[object, ...]]:
        if texture is None:
            return None
        return (
            getattr(texture, "source_path", None),
            texture.width,
            texture.height,
            id(texture),
        )

    def texture_fill_rows(self, texture: Optional[AnsiTexture]) -> Optional[Tuple[Tuple[Optional[str], ...], ...]]:
        texture_id = self.texture_identity(texture)
        if texture_id is None:
            return None
        cache = self.static_cache.setdefault("texture_fill_rows", {})
        if not isinstance(cache, dict):
            cache = {}
            self.static_cache["texture_fill_rows"] = cache
        cached_rows = cache.get(texture_id)
        if isinstance(cached_rows, tuple):
            return cached_rows
        assert texture is not None
        fill_rows = tuple(tuple(self.texture_cell_fill(cell) for cell in row) for row in texture.rows)
        cache[texture_id] = fill_rows
        return fill_rows

    def sample_texture_fill(
        self,
        texture: Optional[AnsiTexture],
        x_ratio: float,
        y_ratio: float,
        *,
        repeat: bool = False,
    ) -> Optional[str]:
        fill_rows = self.texture_fill_rows(texture)
        if fill_rows is None or texture is None or texture.width <= 0 or texture.height <= 0:
            return None
        if repeat:
            x_ratio %= 1.0
            y_ratio %= 1.0
            tx = min(texture.width - 1, max(0, int(x_ratio * texture.width)))
            ty = min(texture.height - 1, max(0, int(y_ratio * texture.height)))
        else:
            tx = min(texture.width - 1, max(0, int(x_ratio * max(1, texture.width - 1))))
            ty = min(texture.height - 1, max(0, int(y_ratio * max(1, texture.height - 1))))
        return fill_rows[ty][tx]

    def surface_fill_rows(self) -> Tuple[Tuple[Optional[str], ...], ...]:
        floor_texture = self.state.get("floor_texture")
        ceiling_texture = self.state.get("ceiling_texture")
        surface_key = (
            self.view_width_cells,
            self.view_height_cells,
            self.texture_identity(floor_texture),
            self.texture_identity(ceiling_texture),
        )
        if self.static_cache.get("surface_key") == surface_key:
            cached_rows = self.static_cache.get("surface_rows")
            if isinstance(cached_rows, tuple):
                return cached_rows

        horizon = self.view_height_cells // 2
        rows: List[List[Optional[str]]] = [
            [None for _ in range(self.view_width_cells)]
            for _ in range(self.view_height_cells)
        ]

        if ceiling_texture is not None:
            for y in range(1, horizon):
                ceiling_depth = (horizon - y) / max(1, horizon)
                shade = max(0.30, min(1.00, 0.48 + (1.0 - ceiling_depth) * 0.42))
                row = rows[y]
                for x in range(self.view_width_cells):
                    ceiling_x_ratio = x / max(1, self.view_width_cells)
                    fill = self.sample_texture_fill(
                        ceiling_texture,
                        ceiling_x_ratio * 2.0 + ceiling_depth * 0.35,
                        ceiling_depth * 3.0,
                        repeat=True,
                    )
                    if fill is not None:
                        row[x] = self.shade_color(fill, shade)

        for y in range(horizon + 1, self.view_height_cells - 2):
            row = rows[y]
            if floor_texture is not None:
                floor_depth = (y - horizon) / max(1, self.view_height_cells - horizon - 1)
                shade = max(0.28, min(1.08, 0.34 + floor_depth * 0.74))
                for x in range(self.view_width_cells):
                    floor_x_ratio = x / max(1, self.view_width_cells)
                    fill = self.sample_texture_fill(
                        floor_texture,
                        floor_x_ratio * (1.2 + floor_depth * 2.8),
                        floor_depth * 3.2,
                        repeat=True,
                    )
                    if fill is not None:
                        row[x] = self.shade_color(fill, shade)
            else:
                base_fill = self.char_fill(dungeona.floor_char(y, horizon, self.view_height_cells), 4)
                if base_fill is not None:
                    for x in range(self.view_width_cells):
                        row[x] = base_fill

        frozen_rows = tuple(tuple(row) for row in rows)
        self.static_cache["surface_key"] = surface_key
        self.static_cache["surface_rows"] = frozen_rows
        return frozen_rows

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

    def detailed_monster_palette(self, monster_tile: str) -> Dict[str, str]:
        info = dungeona.monster_info(monster_tile)
        base = self.color_for(int(info["color"]))
        if monster_tile == "S":
            base = "#c9ced6"
            return {
                "base": base,
                "shadow": self.shade_color(base, 0.42),
                "mid": self.shade_color(base, 0.74),
                "light": self.shade_color(base, 1.08),
                "accent": "#7a5dcb",
                "eye": "#7fd7ff",
                "bone": self.shade_color(base, 1.18),
            }
        if monster_tile == "O":
            base = "#6f8d52"
            return {
                "base": base,
                "shadow": self.shade_color(base, 0.40),
                "mid": self.shade_color(base, 0.72),
                "light": self.shade_color(base, 1.02),
                "accent": "#b8a06a",
                "eye": "#ffb347",
                "bone": self.shade_color(base, 1.12),
            }
        return {
            "base": base,
            "shadow": self.shade_color(base, 0.38),
            "mid": self.shade_color(base, 0.72),
            "light": self.shade_color(base, 1.06),
            "accent": "#d9a35f",
            "eye": "#ff6b57",
            "bone": self.shade_color(base, 1.10),
        }

    def detailed_item_palette(self, item_tile: str) -> Dict[str, str]:
        if item_tile == dungeona.QUEST_TARGET_TILE:
            base = "#8f5db0"
            return {
                "base": base,
                "shadow": self.shade_color(base, 0.42),
                "mid": self.shade_color(base, 0.76),
                "light": self.shade_color(base, 1.08),
                "accent": "#d9d2ea",
                "glow": "#b794d8",
                "spark": "#efe6ff",
            }
        base = "#c9b24a"
        return {
            "base": base,
            "shadow": self.shade_color(base, 0.42),
            "mid": self.shade_color(base, 0.78),
            "light": self.shade_color(base, 1.08),
            "accent": "#fff2a6",
            "glow": "#e0c85d",
            "spark": "#fff7cc",
        }

    def visible_monster_info(self) -> Optional[Tuple[int, int, int, str]]:
        grid = dungeona.current_grid(self.state)
        return dungeona.visible_monster(
            grid,
            int(self.state["x"]),
            int(self.state["y"]),
            int(self.state["facing"]),
        )

    def draw_enhanced_item_detail_art(self, item_tile: str, distance: int, side: int) -> None:
        palette = self.detailed_item_palette(item_tile)
        center_x = self.view_width_cells // 2 + side * max(2, self.view_width_cells // max(9, 10 + distance * 2))
        floor_y = self.view_height_cells - 4
        scale = max(0.85, 3.0 / (distance + 0.2))
        scale *= 1.12 if side == 0 else 0.82

        if item_tile == dungeona.QUEST_TARGET_TILE:
            body_w = max(7, int(round(12 * scale)))
            body_h = max(6, int(round(9 * scale)))
        else:
            body_w = max(6, int(round(9 * scale)))
            body_h = max(7, int(round(10 * scale)))

        left = center_x - body_w // 2
        top = floor_y - body_h + 1

        shadow_w = max(4, int(body_w * 0.95))
        shadow_h = max(2, int(body_h * 0.18))
        x0, y0, x1, y1 = self.rect_from_cells(center_x - shadow_w // 2, floor_y + 1, shadow_w, shadow_h)
        self.item_detail_items.append(self.canvas.create_oval(x0, y0, x1, y1, fill="#090a0c", outline=""))

        def add_rect(cx: int, cy: int, cw: int, ch: int, color: str, outline: str = "") -> None:
            x0, y0, x1, y1 = self.rect_from_cells(cx, cy, cw, ch)
            self.item_detail_items.append(self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline or color))

        def add_glow(cx: int, cy: int, cw: int, ch: int, color: str) -> None:
            x0, y0, x1, y1 = self.rect_from_cells(cx, cy, cw, ch)
            pad = max(1, self.cell_w // 2)
            self.item_detail_items.append(self.canvas.create_oval(x0 - pad, y0 - pad, x1 + pad, y1 + pad, fill=color, outline=""))

        if item_tile == dungeona.QUEST_TARGET_TILE:
            add_rect(left + 1, top + body_h - 2, max(5, body_w - 2), 2, palette["shadow"])
            add_rect(left + 2, top + body_h - 4, max(4, body_w - 4), 2, palette["mid"])
            add_rect(left + 3, top + 2, max(3, body_w - 6), max(2, body_h - 6), palette["base"])
            add_rect(left + 2, top + 1, max(5, body_w - 4), 2, palette["light"])
            add_rect(left + 1, top + 2, 1, max(3, body_h - 4), palette["shadow"])
            add_rect(left + body_w - 2, top + 2, 1, max(3, body_h - 4), palette["shadow"])
            add_rect(left + body_w // 2 - 1, top + 2, 2, max(2, body_h - 5), palette["accent"])
            add_rect(left + body_w // 3, top + body_h // 2, max(1, body_w // 6), 1, palette["accent"])
            add_rect(left + body_w - 1 - max(1, body_w // 6) - body_w // 3, top + body_h // 2, max(1, body_w // 6), 1, palette["accent"])
            add_glow(left + body_w // 2 - 1, top + 1, 2, 1, self.shade_color(palette["glow"], 0.95))
            add_rect(left + body_w // 2, top + 0, 1, 1, palette["spark"])
        else:
            cup_w = max(4, body_w - 3)
            add_rect(left + 1, top + body_h - 2, max(3, body_w - 2), 1, palette["shadow"])
            add_rect(left + 2, top + 1, cup_w, max(2, body_h // 3), palette["light"])
            add_rect(left + 1, top + 2, 1, max(2, body_h // 3), palette["accent"])
            add_rect(left + body_w - 2, top + 2, 1, max(2, body_h // 3), palette["accent"])
            add_rect(left + 3, top + body_h // 3 + 1, max(2, body_w - 6), max(1, body_h // 4), palette["mid"])
            add_rect(left + body_w // 2 - 1, top + body_h // 2, 2, max(2, body_h // 3), palette["base"])
            add_rect(left + body_w // 2 - max(2, body_w // 4), top + body_h - 1, max(4, body_w // 2), 1, palette["mid"])
            add_glow(left + 2, top + 0, max(2, body_w - 4), 1, self.shade_color(palette["glow"], 0.9))
            add_rect(left + body_w // 2, top + 0, 1, 1, palette["spark"])

    def draw_item_detail_art(self) -> None:
        self.clear_item_list(self.item_detail_items)
        grid = dungeona.current_grid(self.state)
        px = int(self.state["x"])
        py = int(self.state["y"])
        facing = int(self.state["facing"])
        visible_grail = dungeona.grail_in_view(grid, px, py, facing)
        visible_altar = dungeona.altar_in_view(grid, px, py, facing)
        candidates: List[Tuple[int, int, str]] = []
        if visible_grail is not None:
            distance, side, _ = visible_grail
            candidates.append((distance, side, dungeona.QUEST_ITEM_TILE))
        if visible_altar is not None:
            distance, side, _ = visible_altar
            candidates.append((distance, side, dungeona.QUEST_TARGET_TILE))
        if not candidates:
            return
        distance, side, item_tile = sorted(candidates, key=lambda entry: entry[0])[0]
        self.draw_enhanced_item_detail_art(item_tile, distance, side)

    def draw_monster_detail_art(self) -> None:
        self.clear_item_list(self.monster_detail_items)
        seen = self.visible_monster_info()
        if seen is None:
            return
        distance, side, _lateral, monster_tile = seen
        palette = self.detailed_monster_palette(monster_tile)
        center_x = self.view_width_cells // 2 + side * max(3, self.view_width_cells // max(8, 9 + distance * 2))
        floor_y = self.view_height_cells - 4
        scale = max(0.9, 3.2 / (distance + 0.15))
        scale *= 1.12 if side == 0 else 0.84
        body_w = max(6, int(round(10 * scale)))
        body_h = max(6, int(round(10 * scale)))
        left = center_x - body_w // 2
        top = floor_y - body_h + 1

        shadow_w = max(4, int(body_w * 0.9))
        shadow_h = max(2, int(body_h * 0.18))
        x0, y0, x1, y1 = self.rect_from_cells(center_x - shadow_w // 2, floor_y + 1, shadow_w, shadow_h)
        self.monster_detail_items.append(self.canvas.create_oval(x0, y0, x1, y1, fill="#0a0b0d", outline=""))

        def add_rect(cx: int, cy: int, cw: int, ch: int, color: str, outline: str = "") -> None:
            x0, y0, x1, y1 = self.rect_from_cells(cx, cy, cw, ch)
            self.monster_detail_items.append(self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline or color))

        def add_eye(ex: int, ey: int, glow: str, pupil: str) -> None:
            gx0, gy0, gx1, gy1 = self.rect_from_cells(ex, ey, 1, 1)
            pad = max(1, self.cell_w // 2)
            self.monster_detail_items.append(self.canvas.create_oval(gx0 - pad, gy0 - pad, gx1 + pad, gy1 + pad, fill=glow, outline=""))
            self.monster_detail_items.append(self.canvas.create_oval(gx0 + 1, gy0 + 1, gx1 - 1, gy1 - 1, fill=pupil, outline=""))

        if monster_tile == "R":
            add_rect(left + 2, top + 3, max(4, body_w - 4), max(3, body_h - 4), palette["mid"])
            add_rect(left + 3, top + 2, max(4, body_w - 5), max(3, body_h // 2), palette["light"])
            add_rect(left + body_w - 3, top + body_h // 2, 2, 2, palette["accent"])
            add_rect(left + 1, top + 2, 2, 2, palette["light"])
            add_rect(left + body_w - 1, top + 1, 1, max(3, body_h // 2), palette["bone"])
            add_rect(left + 0, top + body_h - 2, max(2, body_w // 4), 1, palette["shadow"])
            add_rect(left + body_w // 3, top + body_h - 1, max(2, body_w // 5), 1, palette["shadow"])
            add_rect(left + body_w - 3, top + body_h - 2, 1, 2, palette["shadow"])
            add_eye(left + body_w // 3, top + max(1, body_h // 3), self.shade_color(palette["eye"], 1.2), palette["eye"])
            add_eye(left + body_w // 2 + 1, top + max(1, body_h // 3), self.shade_color(palette["eye"], 1.2), palette["eye"])
        elif monster_tile == "S":
            skull_w = max(4, body_w - 4)
            skull_h = max(3, body_h // 3)
            rib_w = max(3, body_w - 6)
            add_rect(left + 2, top + 1, skull_w, skull_h, palette["bone"])
            add_rect(left + 3, top + 2, skull_w - 2, max(1, skull_h - 2), palette["light"])
            add_rect(left + 3, top + skull_h + 1, rib_w, max(3, body_h // 3), palette["mid"])
            add_rect(left + body_w // 2 - 1, top + skull_h, 2, max(4, body_h // 2), palette["shadow"])
            add_rect(left + 2, top + body_h - 3, 1, 3, palette["bone"])
            add_rect(left + body_w - 3, top + body_h - 3, 1, 3, palette["bone"])
            add_rect(left + 1, top + body_h - 1, max(2, body_w // 3), 1, palette["shadow"])
            add_rect(left + body_w - 1 - max(2, body_w // 3), top + body_h - 1, max(2, body_w // 3), 1, palette["shadow"])
            add_eye(left + body_w // 3, top + 2, self.shade_color(palette["eye"], 0.7), palette["eye"])
            add_eye(left + body_w // 2 + 1, top + 2, self.shade_color(palette["eye"], 0.7), palette["eye"])
            add_rect(left + body_w // 2 - 1, top + skull_h - 1, 2, 1, palette["accent"])
        else:
            add_rect(left + 1, top + 2, max(5, body_w - 2), max(4, body_h - 3), palette["base"])
            add_rect(left + 2, top + 1, max(4, body_w - 4), max(3, body_h // 2), palette["light"])
            add_rect(left + 0, top + body_h // 2, 2, max(3, body_h // 2), palette["shadow"])
            add_rect(left + body_w - 2, top + body_h // 2, 2, max(3, body_h // 2), palette["shadow"])
            add_rect(left + body_w // 3, top + body_h - 2, max(2, body_w // 5), 2, palette["shadow"])
            add_rect(left + body_w // 2 + 1, top + body_h - 2, max(2, body_w // 5), 2, palette["shadow"])
            add_rect(left + 2, top + 0, max(2, body_w // 4), 2, palette["accent"])
            add_rect(left + body_w - 2 - max(2, body_w // 4), top + 0, max(2, body_w // 4), 2, palette["accent"])
            add_eye(left + body_w // 3, top + max(1, body_h // 3), self.shade_color(palette["eye"], 0.9), palette["eye"])
            add_eye(left + body_w // 2 + 1, top + max(1, body_h // 3), self.shade_color(palette["eye"], 0.9), palette["eye"])

    def compute_scene_rects(self) -> List[Tuple[int, int, int, str]]:
        grid = dungeona.current_grid(self.state)
        px = int(self.state["x"])
        py = int(self.state["y"])
        facing = int(self.state["facing"])
        wall_textures = self.state.get("wall_textures") or {}
        horizon = self.view_height_cells // 2
        cam_x = px + 0.5
        cam_y = py + 0.5
        dir_x, dir_y = dungeona.facing_vector(facing)
        plane_x, plane_y = -dir_y * dungeona.FOV_SCALE, dir_x * dungeona.FOV_SCALE

        fill_rows = [list(row) for row in self.surface_fill_rows()]
        overlay_items: List[Tuple[int, int, str, int]] = []

        for x in range(self.view_width_cells):
            camera_x = 2.0 * x / max(1, self.view_width_cells - 1) - 1.0
            ray_dir_x = dir_x + plane_x * camera_x
            ray_dir_y = dir_y + plane_y * camera_x
            distance, cell, side, wall_hit = dungeona.cast_perspective_ray(grid, cam_x, cam_y, ray_dir_x, ray_dir_y)
            if cell not in {"#", "D"}:
                continue

            line_height = int((self.view_height_cells * 0.92) / max(0.001, distance))
            draw_start = max(1, horizon - line_height // 2)
            draw_end = min(self.view_height_cells - 3, horizon + line_height // 2)
            color_id = 2 if cell == "D" else 1
            texture = wall_textures.get(cell)
            shade = self.distance_shade_factor(distance, side)
            mid = (draw_start + draw_end) // 2

            for y in range(draw_start, draw_end + 1):
                wall_fill: Optional[str]
                if texture is not None:
                    y_ratio = (y - draw_start) / max(1, draw_end - draw_start)
                    base_fill = self.sample_texture_fill(texture, wall_hit, y_ratio)
                    wall_fill = self.shade_color(base_fill, shade) if base_fill is not None else None
                else:
                    draw_char = dungeona.wall_char(distance, side, cell)
                    if cell == "D":
                        if abs(y - mid) <= max(1, line_height // 10):
                            draw_char = "="
                        elif x % 2 == 0:
                            draw_char = "|"
                    elif side == 1 and draw_char in {"█", "▓", "▒"}:
                        draw_char = {"█": "▓", "▓": "▒", "▒": "░"}.get(draw_char, draw_char)
                    wall_fill = self.char_fill(draw_char, color_id)
                    if wall_fill is not None:
                        wall_fill = self.shade_color(wall_fill, shade)
                if wall_fill is not None:
                    fill_rows[y][x] = wall_fill

            ceiling_limit = max(1, draw_start - 1)
            if ceiling_limit > 1 and x % 3 == 0:
                edge_fill = self.char_fill("_", 4)
                if edge_fill is not None:
                    fill_rows[ceiling_limit][x] = edge_fill

        visible_stairs = dungeona.stairs_in_view(grid, px, py, facing)
        if visible_stairs is not None:
            distance, side, _, tile = visible_stairs
            dungeona.render_stairs_sprite(overlay_items, self.view_width_cells, self.view_height_cells, distance, side, tile)

        visible_grail = dungeona.grail_in_view(grid, px, py, facing)
        if visible_grail is not None:
            distance, side, _ = visible_grail
            dungeona.render_grail_sprite(overlay_items, self.view_width_cells, self.view_height_cells, distance, side)

        visible_altar = dungeona.altar_in_view(grid, px, py, facing)
        if visible_altar is not None:
            distance, side, _ = visible_altar
            dungeona.render_altar_sprite(overlay_items, self.view_width_cells, self.view_height_cells, distance, side)

        seen_monster = dungeona.visible_monster(grid, px, py, facing)
        if seen_monster is not None:
            distance, side, _, tile = seen_monster
            dungeona.render_monster_sprite(
                overlay_items,
                self.view_width_cells,
                self.view_height_cells,
                distance,
                side,
                tile,
                self.state.get("animated_sprites"),
                int(self.state.get("action_count", 0)),
            )

        for y, x, ch, color_id in overlay_items:
            if not (0 <= x < self.view_width_cells and 0 <= y < self.view_height_cells):
                continue
            fill = self.char_fill(ch, color_id)
            if fill is not None:
                fill_rows[y][x] = fill

        return self.fill_rows_to_runs(fill_rows)

    def draw_view(self, force_scene: bool = False) -> None:
        render_key = self.scene_render_key()
        if force_scene or self.static_cache.get("last_render_key") != render_key:
            runs = self.compute_scene_rects()
            self.static_cache["last_render_key"] = render_key
            self.static_cache["last_render_items"] = runs
        else:
            runs = self.static_cache.get("last_render_items", [])
        self.clear_item_list(self.dynamic_scene_items)
        if isinstance(runs, list):
            self.create_batched_rectangles(runs, self.dynamic_scene_items)

    def draw_minimap(self) -> None:
        if not bool(self.state.get("show_map")):
            return
        grid = dungeona.current_grid(self.state)
        px = int(self.state["x"])
        py = int(self.state["y"])
        facing = int(self.state["facing"])
        radius = 4
        left = 10 * self.render_scale
        top = 10 * self.render_scale

        self.dynamic_overlay_items.append(self.canvas.create_rectangle(
            left - 6,
            top - 18,
            left + self.minimap_tile * 9 + 6,
            top + self.minimap_tile * 9 + 6,
            fill="#0b0f14",
            outline="#2c3742",
        ))
        self.dynamic_overlay_items.append(self.canvas.create_text(left, top - 10, anchor="w", fill="#7f9bb8", text=f"F{int(self.state['floor']) + 1}", font=("TkFixedFont", 9, "bold")))

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                mx = px + dx
                my = py + dy
                cell = dungeona.cell_at(grid, mx, my)
                color = "#1a1d21"
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
                x0 = left + (dx + radius) * self.minimap_tile
                y0 = top + (dy + radius) * self.minimap_tile
                self.dynamic_overlay_items.append(self.canvas.create_rectangle(x0, y0, x0 + self.minimap_tile - 1, y0 + self.minimap_tile - 1, fill=color, outline="#0a0d10"))

        cx = left + radius * self.minimap_tile + self.minimap_tile // 2
        cy = top + radius * self.minimap_tile + self.minimap_tile // 2
        self.dynamic_overlay_items.append(self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#48b060", outline=""))
        dx, dy = dungeona.DIRECTIONS[facing]
        self.dynamic_overlay_items.append(self.canvas.create_line(cx, cy, cx + dx * 8, cy + dy * 8, fill="#48b060", width=2))

    def draw_status(self) -> None:
        y0 = self.view_height
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(0, y0, self.window_width, self.window_height, fill=STATUS_BG, outline="#26303a"))

        energy = int(self.state["energy"])
        bar_w = 180
        fill_w = int(bar_w * energy / max(1, dungeona.MAX_ENERGY))
        self.dynamic_overlay_items.append(self.canvas.create_text(12, y0 + 14, anchor="w", fill=TEXT_COLOR, text="Energy", font=("TkFixedFont", 10, "bold")))
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(70, y0 + 6, 70 + bar_w, y0 + 22, fill="#1e252c", outline="#34404c"))
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(70, y0 + 6, 70 + fill_w, y0 + 22, fill="#48b060", outline=""))

        quest_status = "done" if bool(self.state["quest_complete"]) else ("carrying" if bool(self.state["has_grail"]) else "missing")
        line1 = (
            f"Floor {int(self.state['floor']) + 1}/{len(self.state['floors'])}   "
            f"Pos {self.state['x']},{self.state['y']}   "
            f"Facing {dungeona.DIRECTION_NAMES[int(self.state['facing'])]}   "
            f"Defeated {self.state['score']}"
        )
        line2 = f"Inventory {dungeona.inventory_count(self.state)}/{dungeona.MAX_CARRIED_ITEMS}   Grail {quest_status}"
        line3 = str(self.state["message"])[:100]

        self.dynamic_overlay_items.append(self.canvas.create_text(12, y0 + 34, anchor="w", fill=TEXT_COLOR, text=line1, font=("TkFixedFont", 10)))
        self.dynamic_overlay_items.append(self.canvas.create_text(12, y0 + 50, anchor="w", fill="#c9b24a", text=line2, font=("TkFixedFont", 10)))
        self.dynamic_overlay_items.append(self.canvas.create_text(self.window_width - 12, y0 + 14, anchor="e", fill="#7f8b97", text=KEY_HELP, font=("TkFixedFont", 9)))
        self.dynamic_overlay_items.append(self.canvas.create_text(12, y0 + 62, anchor="w", fill="#7f9bb8", text=line3, font=("TkFixedFont", 9)))

    def draw_congrats_overlay(self) -> None:
        if not bool(self.state.get("show_congrats_banner")):
            return
        left = max(40, self.window_width // 8)
        top = max(60, self.view_height // 3)
        right = self.window_width - max(40, self.window_width // 8)
        bottom = min(self.view_height - 20, top + 110)
        self.dynamic_overlay_items.append(self.canvas.create_rectangle(left, top, right, bottom, fill="#0d1014", outline="#c9b24a", width=3))
        self.dynamic_overlay_items.append(self.canvas.create_text((left + right) // 2, top + 36, text="Congratulations.", fill="#d8c15f", font=("TkFixedFont", 20, "bold")))
        self.dynamic_overlay_items.append(self.canvas.create_text((left + right) // 2, top + 74, text="Quest complete.", fill="#d8dee9", font=("TkFixedFont", 11)))

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
        elif key == "q":
            self.state["facing"] = (int(self.state["facing"]) - 1) % 4
            self.state["message"] = "You turn left."
            acted = True
        elif key == "e":
            self.state["facing"] = (int(self.state["facing"]) + 1) % 4
            self.state["message"] = "You turn right."
            acted = True
        elif key == "z":
            old_pos = (self.state["x"], self.state["y"])
            dungeona.try_strafe(self.state, -1)
            self.state["message"] = "You sidestep left." if old_pos != (self.state["x"], self.state["y"]) else "Blocked on the left."
            acted = True
        elif key == "c":
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
        self.draw_scene(force_scene=acted)

    def draw_scene(self, force_scene: bool = False) -> None:
        self.ensure_background_layer()
        self.ensure_frame_layer()
        self.draw_view(force_scene=force_scene)
        self.draw_monster_detail_art()
        self.draw_item_detail_art()
        self.clear_item_list(self.dynamic_overlay_items)
        self.draw_minimap()
        self.draw_status()
        self.draw_congrats_overlay()

    def run(self) -> None:
        self.root.mainloop()

    def on_resize(self, event) -> None:
        if event.widget is not self.root:
            return
        prev_metrics = (
            self.window_width,
            self.window_height,
            self.view_height,
            self.view_width_cells,
            self.view_height_cells,
            self.render_scale,
        )
        self.update_render_metrics(event.width, event.height)
        new_metrics = (
            self.window_width,
            self.window_height,
            self.view_height,
            self.view_width_cells,
            self.view_height_cells,
            self.render_scale,
        )
        if new_metrics == prev_metrics:
            return
        self.canvas.config(width=self.window_width, height=self.window_height)
        self.draw_scene(force_scene=True)


def main() -> None:
    app = DungeonaRenderer()
    app.run()


if __name__ == "__main__":
    main()
