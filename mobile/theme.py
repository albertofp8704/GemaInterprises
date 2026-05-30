import flet as ft

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0a0a0f"
CARD     = "#1a1a2e"
SURFACE  = "#16213e"
PRIMARY  = "#7c3aed"
PRI_L    = "#8b5cf6"
ACCENT   = "#10b981"
GOLD     = "#f59e0b"
RED      = "#ef4444"
VILLAIN  = "#dc2626"
TEXT     = "#f9fafb"
MUTED    = "#9ca3af"
BORDER   = "#2d2d4e"

RARITY_COLOR = {
    "common":    "#6b7280",
    "rare":      "#3b82f6",
    "epic":      "#8b5cf6",
    "legendary": "#f59e0b",
}

DIFF_COLOR = {"easy": ACCENT, "normal": "#3b82f6", "hard": GOLD, "legendary": RED}
DIFF_EMOJI = {"easy": "⚡", "normal": "🔥", "hard": "💀", "legendary": "👑"}

CAT_COLOR = {
    "social":   "#3b82f6",
    "personal": PRIMARY,
    "football": GOLD,
    "career":   ACCENT,
    "creative": "#ec4899",
}


# ── Component helpers ─────────────────────────────────────────────────────────

def card(content, padding=16, border_color=BORDER, gradient=None):
    return ft.Container(
        content=content,
        bgcolor=None if gradient else CARD,
        gradient=gradient,
        border_radius=16,
        padding=padding,
        border=ft.border.all(1, border_color),
    )


def h1(text, size=26, color=TEXT):
    return ft.Text(text, size=size, color=color, weight=ft.FontWeight.BOLD)


def h2(text, size=18, color=TEXT):
    return ft.Text(text, size=size, color=color, weight=ft.FontWeight.W_600)


def body(text, size=14, color=None):
    return ft.Text(text, size=size, color=color or TEXT)


def muted(text, size=12):
    return ft.Text(text, size=size, color=MUTED)


def badge(text, color=PRIMARY, size=10):
    return ft.Container(
        content=ft.Text(text, size=size, color=TEXT, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
    )


def primary_btn(text, on_click, icon=None, disabled=False, color=PRIMARY, expand=False):
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: color, ft.ControlState.DISABLED: BORDER},
            color=TEXT,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
        ),
    )


def ghost_btn(text, on_click, icon=None):
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=TEXT,
            side=ft.BorderSide(1, BORDER),
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        ),
    )


def text_input(label, password=False, hint=None, value="", multiline=False):
    return ft.TextField(
        label=label,
        hint_text=hint,
        value=value,
        password=password,
        can_reveal_password=password,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        max_lines=5 if multiline else 1,
        bgcolor=SURFACE,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        label_style=ft.TextStyle(color=MUTED),
        text_style=ft.TextStyle(color=TEXT),
        cursor_color=PRIMARY,
        border_radius=12,
    )


def xp_bar(current_xp: int, level: int):
    base = (level - 1) * 500
    level_xp = current_xp - base
    pct = min(level_xp / 500, 1.0)
    return ft.Column([
        ft.Row([
            ft.Text(f"Lv {level}", size=12, color=GOLD, weight=ft.FontWeight.BOLD),
            ft.Text(f"{level_xp} / 500 XP", size=11, color=MUTED),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.ProgressBar(value=pct, bgcolor=SURFACE, color=PRIMARY, height=5, border_radius=3),
    ], spacing=5)


def stat_tile(label, value, icon, color=PRIMARY):
    return ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(icon, size=16, color=color), ft.Text(str(value), size=18, color=TEXT, weight=ft.FontWeight.BOLD)], spacing=4),
            ft.Text(label, size=11, color=MUTED),
        ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE,
        border_radius=12,
        padding=12,
        expand=True,
    )


def snack(page, message, color=ACCENT):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=TEXT),
        bgcolor=color,
        duration=2500,
    )
    page.snack_bar.open = True
    page.update()


def divider():
    return ft.Container(height=1, bgcolor=BORDER, margin=ft.margin.symmetric(vertical=4))


def section_title(text):
    return ft.Text(text.upper(), size=11, color=MUTED, weight=ft.FontWeight.W_600, letter_spacing=1.2)
