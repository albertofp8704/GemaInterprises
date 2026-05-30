import flet as ft
from ..theme import *
from ..api import APIClient, APIError

AVATAR_EMOJIS = [
    "🐐", "👑", "😈", "🔥",
    "⚽", "🏆", "💀", "⚡",
    "🎯", "🚀", "💎", "🌟",
    "🦁", "🐺", "👊", "🎭",
]

TITLES = [
    "El GOAT 🐐",
    "El Villano 😈",
    "El Leyenda 👑",
    "El Predictor 🔮",
    "El Conquistador ⚔️",
    "El Campeón 🏆",
    "El Imparable 🔥",
    "Sin título",
]


def _tx_rows(history: list) -> list:
    if not history:
        return [muted("Sin transacciones")]
    rows = []
    for tx in history[:6]:
        rows.append(ft.Row([
            ft.Icon(ft.Icons.ARROW_UPWARD if tx["amount"] > 0 else ft.Icons.ARROW_DOWNWARD,
                    size=14, color=ACCENT if tx["amount"] > 0 else RED),
            ft.Column([body(tx.get("description", tx.get("type", "")), size=12)], expand=True),
            ft.Text(f"+{tx['amount']}" if tx["amount"] > 0 else str(tx["amount"]),
                    size=13, color=ACCENT if tx["amount"] > 0 else RED, weight=ft.FontWeight.W_600),
        ], spacing=8))
    return rows


def _is_emoji_avatar(val: str) -> bool:
    return bool(val) and not val.startswith("http") and "::" not in val


def _parse_avatar(val: str):
    """Returns (emoji_or_None, title_or_None)."""
    if not val:
        return None, None
    if "::" in val:
        parts = val.split("::", 1)
        return parts[0] or None, parts[1] or None
    if _is_emoji_avatar(val):
        return val, None
    return None, None


def build(page: ft.Page, api: APIClient, state: dict, on_logout):
    content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)

    def load():
        content_col.controls.clear()
        try:
            profile  = api.get_profile()
            balance  = api.token_balance()
            history  = api.token_history()
            cards    = api.my_flashcards()
            shop     = api.flashcards()
        except APIError as e:
            content_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        username  = profile.get("username") or "Jugador"
        xp        = profile.get("xp", 0)
        level     = profile.get("level", 1)
        tokens    = profile.get("goat_tokens", 0)
        accuracy  = 0.0
        if profile.get("predictions_made", 0) > 0:
            accuracy = round(profile["predictions_correct"] / profile["predictions_made"] * 100, 1)

        raw_avatar             = profile.get("avatar_url", "")
        avatar_emoji, av_title = _parse_avatar(raw_avatar)

        # ── Edit profile sheet ────────────────────────────────────────────────
        def _show_edit():
            sel = {"emoji": avatar_emoji, "title": av_title or "Sin título"}

            # Preview avatar (updated live)
            preview = ft.Container(
                content=ft.Text(avatar_emoji or username[0].upper(), size=48,
                                color=TEXT if not avatar_emoji else None,
                                weight=ft.FontWeight.BOLD),
                width=100, height=100,
                bgcolor=SURFACE if avatar_emoji else PRIMARY,
                border_radius=50,
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(blur_radius=24, color=PRIMARY, spread_radius=3),
            )

            emoji_cells = {}

            def _pick_emoji(em):
                sel["emoji"] = em
                preview.content = ft.Text(em, size=48)
                preview.bgcolor = SURFACE
                for e2, cell in emoji_cells.items():
                    cell.border = ft.Border.all(2, PRIMARY if e2 == em else BORDER)
                    cell.bgcolor = "#2d1f5e" if e2 == em else CARD
                page.update()

            # Build 4-column emoji grid
            emoji_rows = []
            for row_start in range(0, len(AVATAR_EMOJIS), 4):
                row_emojis = AVATAR_EMOJIS[row_start:row_start + 4]
                cells = []
                for em in row_emojis:
                    is_sel = em == avatar_emoji
                    cell = ft.Container(
                        content=ft.Text(em, size=28),
                        width=66, height=66,
                        bgcolor="#2d1f5e" if is_sel else CARD,
                        border_radius=16,
                        border=ft.Border.all(2, PRIMARY if is_sel else BORDER),
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda e, x=em: _pick_emoji(x),
                    )
                    emoji_cells[em] = cell
                    cells.append(cell)
                emoji_rows.append(ft.Row(cells, spacing=8, alignment=ft.MainAxisAlignment.CENTER))

            username_f = text_input("Username", hint="@leyenda")
            username_f.value = username

            title_dd = ft.Dropdown(
                label="Tu título",
                value=sel["title"] if sel["title"] in TITLES else "Sin título",
                options=[ft.DropdownOption(key=t, text=t) for t in TITLES],
                bgcolor=SURFACE, border_color=BORDER, border_radius=12, color=TEXT,
                on_select=lambda e: sel.update({"title": e.control.value}),
            )

            def _save(e):
                new_name  = username_f.value.strip() or username
                em        = sel["emoji"]
                title     = sel["title"] if sel["title"] != "Sin título" else ""
                avatar_val = f"{em}::{title}" if em and title else (em or "")
                try:
                    api.update_profile(
                        username=new_name if new_name != username else None,
                        avatar_url=avatar_val or None,
                    )
                    page.pop_dialog()
                    snack(page, "Perfil actualizado ✓")
                    load()
                except APIError as ex:
                    snack(page, str(ex), RED)

            bs = ft.BottomSheet(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            h2("Editar perfil"),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE, icon_color=MUTED, icon_size=20,
                                on_click=lambda _: page.pop_dialog(),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=8),
                        preview,
                        ft.Container(height=12),
                        muted("Elige tu avatar"),
                        ft.Container(height=8),
                        *emoji_rows,
                        ft.Container(height=12),
                        username_f,
                        ft.Container(height=8),
                        title_dd,
                        ft.Container(height=16),
                        primary_btn("Guardar cambios ✓", on_click=_save, expand=True, color=ACCENT),
                        ft.Container(height=8),
                    ], spacing=6,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       scroll=ft.ScrollMode.AUTO),
                    bgcolor=CARD,
                    padding=ft.Padding.only(left=24, right=24, top=24, bottom=0),
                    border_radius=ft.BorderRadius.only(top_left=24, top_right=24),
                ),
                bgcolor=CARD,
            )
            page.show_dialog(bs)

        # ── Avatar card ───────────────────────────────────────────────────────
        if avatar_emoji:
            avatar_widget = ft.Text(avatar_emoji, size=52)
            avatar_bg     = SURFACE
        else:
            avatar_widget = ft.Text(username[0].upper(), size=40, color=TEXT, weight=ft.FontWeight.BOLD)
            avatar_bg     = PRIMARY

        title_row = (
            ft.Row([badge(av_title, color=PRI_L, size=10)],
                   alignment=ft.MainAxisAlignment.CENTER)
            if av_title else ft.Container(height=0)
        )

        avatar_card = ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=avatar_widget,
                            width=90, height=90, bgcolor=avatar_bg, border_radius=45,
                            alignment=ft.Alignment.CENTER,
                            shadow=ft.BoxShadow(blur_radius=24, color=PRIMARY, spread_radius=3),
                        ),
                        h1(f"@{username}", size=20),
                        title_row,
                        muted(f"Level {level} · {xp} XP total"),
                        ft.Container(height=4),
                        xp_bar(xp, level),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=ft.Padding.only(top=20, bottom=20, left=20, right=20),
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.EDIT, icon_color=MUTED, icon_size=18,
                        on_click=lambda _: _show_edit(),
                        tooltip="Editar perfil",
                    ),
                    alignment=ft.Alignment.TOP_RIGHT,
                    padding=ft.Padding.only(top=8, right=8),
                ),
            ]),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#1a1040", "#1a1a2e"],
            ),
            border_radius=20,
            border=ft.Border.all(1, PRIMARY),
        )

        # ── Stats grid ────────────────────────────────────────────────────────
        stats  = ft.Row([
            stat_tile("Quests",       profile.get("quests_completed", 0),  ft.Icons.CHECKLIST,         ACCENT),
            stat_tile("Predicciones", profile.get("predictions_made", 0),  ft.Icons.TRACK_CHANGES,     GOLD),
        ], spacing=8)
        stats2 = ft.Row([
            stat_tile("Legados",  profile.get("legacies_dropped", 0),  ft.Icons.PLACE,                PRI_L),
            stat_tile("Racha",    profile.get("current_streak", 0),    ft.Icons.LOCAL_FIRE_DEPARTMENT, VILLAIN),
        ], spacing=8)

        # ── Token balance ─────────────────────────────────────────────────────
        token_card = card(ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PAID, size=24, color=GOLD),
                h2(f"{tokens} GOAT Tokens", color=GOLD),
            ], spacing=8),
            muted(f"Gut Score: {accuracy}%"),
            divider(),
            section_title("Últimas transacciones"),
            *_tx_rows(history),
        ], spacing=6))

        # ── Flash Cards ───────────────────────────────────────────────────────
        owned_ids = {c["id"] for c in cards}

        def _buy(card_id, card_name, price):
            try:
                api.buy_flashcard(card_id)
                snack(page, f"🃏 {card_name} desbloqueada!")
                load()
            except APIError as ex:
                snack(page, str(ex), RED)

        card_grid = ft.GridView(
            runs_count=2, max_extent=200, child_aspect_ratio=0.65,
            spacing=8, run_spacing=8, expand=False,
        )
        TYPE_EMOJI = {"player": "⚽", "stadium": "🏟", "tactic": "📋", "moment": "⭐"}
        for fc in shop[:8]:
            r_color   = RARITY_COLOR.get(fc["rarity"], MUTED)
            owned     = fc["id"] in owned_ids
            img_url   = fc.get("image_url")
            ctype     = fc.get("card_type", "")
            fallback_emoji = TYPE_EMOJI.get(ctype, "🃏")

            # Top visual: photo if available, else emoji block
            if img_url:
                top = ft.Container(
                    content=ft.Image(
                        src=img_url,
                        fit=ft.BoxFit.COVER,
                        error_content=ft.Text(fallback_emoji, size=32),
                    ),
                    height=115,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
                )
            else:
                top = ft.Container(
                    content=ft.Text(fallback_emoji, size=32),
                    height=80,
                    bgcolor=SURFACE,
                    border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
                    alignment=ft.Alignment.CENTER,
                )

            card_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        top,
                        ft.Container(
                            content=ft.Column([
                                ft.Text(fc["name"][:20], size=11, color=TEXT,
                                        weight=ft.FontWeight.W_600, max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Container(height=2),
                                badge(fc["rarity"].upper(), r_color, size=8),
                                ft.Container(height=4),
                                primary_btn(
                                    "✓ Tuya" if owned else f"🪙 {fc['token_price']}",
                                    on_click=(lambda e, cid=fc["id"], cn=fc["name"], cp=fc["token_price"]: _buy(cid, cn, cp)) if not owned else lambda e: None,
                                    color=BORDER if owned else r_color,
                                    disabled=owned,
                                ),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=8),
                        ),
                    ], spacing=0),
                    bgcolor=CARD,
                    border_radius=14,
                    border=ft.Border.all(2, r_color if owned else BORDER),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                )
            )

        # ── Logout ────────────────────────────────────────────────────────────
        def _logout(e):
            api.token = None
            state.clear()
            on_logout()

        content_col.controls = [
            ft.Container(height=4),
            avatar_card,
            ft.Container(height=4),
            section_title("Estadísticas"),
            stats, stats2,
            ft.Container(height=4),
            section_title("Tokens & economía"),
            token_card,
            ft.Container(height=4),
            section_title("Flash Cards"),
            card_grid,
            ft.Container(height=12),
            ghost_btn("Cerrar sesión", on_click=_logout, icon=ft.Icons.LOGOUT),
            ft.Container(height=40),
        ]
        page.update()

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1("Mi Perfil", size=22),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color=MUTED, on_click=lambda e: load(), icon_size=20),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
