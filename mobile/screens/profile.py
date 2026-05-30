import flet as ft
from ..theme import *
from ..api import APIClient, APIError


def _tx_rows(history: list) -> list:
    if not history:
        return [muted("Sin transacciones")]
    rows = []
    for tx in history[:6]:
        rows.append(ft.Row([
            ft.Icon(ft.icons.ARROW_UPWARD if tx["amount"] > 0 else ft.icons.ARROW_DOWNWARD,
                    size=14, color=ACCENT if tx["amount"] > 0 else RED),
            ft.Column([body(tx.get("description", tx.get("type", "")), size=12)], expand=True),
            ft.Text(f"+{tx['amount']}" if tx["amount"] > 0 else str(tx["amount"]),
                    size=13, color=ACCENT if tx["amount"] > 0 else RED, weight=ft.FontWeight.W_600),
        ], spacing=8))
    return rows


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

        # ── Avatar ────────────────────────────────────────────────────────────
        avatar_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(username[0].upper(), size=40, color=TEXT, weight=ft.FontWeight.BOLD),
                    width=80, height=80, bgcolor=PRIMARY, border_radius=40,
                    alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(blur_radius=20, color=PRIMARY, spread_radius=2),
                ),
                h1(f"@{username}", size=20),
                muted(f"Level {level} · {xp} XP total"),
                ft.Container(height=4),
                xp_bar(xp, level),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            bgcolor=CARD,
            border_radius=20,
            padding=24,
            border=ft.border.all(1, PRIMARY),
        )

        # ── Stats grid ────────────────────────────────────────────────────────
        stats = ft.Row([
            stat_tile("Quests",       profile.get("quests_completed", 0),   ft.icons.CHECKLIST,   ACCENT),
            stat_tile("Predicciones", profile.get("predictions_made", 0),   ft.icons.TRACK_CHANGES, GOLD),
        ], spacing=8)
        stats2 = ft.Row([
            stat_tile("Legados",  profile.get("legacies_dropped", 0), ft.icons.PLACE,               PRI_L),
            stat_tile("Racha",    profile.get("current_streak", 0),   ft.icons.LOCAL_FIRE_DEPARTMENT, VILLAIN),
        ], spacing=8)

        # ── Token balance ─────────────────────────────────────────────────────
        token_card = card(ft.Column([
            ft.Row([
                ft.Icon(ft.icons.PAID, size=24, color=GOLD),
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
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=0.75,
            spacing=8,
            run_spacing=8,
            expand=False,
        )
        for fc in shop[:8]:
            r_color = RARITY_COLOR.get(fc["rarity"], MUTED)
            owned   = fc["id"] in owned_ids
            card_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(
                                {"player": "⚽", "stadium": "🏟", "tactic": "📋", "moment": "⭐"}.get(fc.get("card_type", ""), "🃏"),
                                size=32,
                            ),
                            bgcolor=SURFACE, border_radius=10, padding=12,
                            alignment=ft.alignment.center,
                        ),
                        body(fc["name"][:22], size=11),
                        badge(fc["rarity"].upper(), r_color, size=8),
                        ft.Container(height=2),
                        primary_btn(
                            "✓" if owned else f"🪙 {fc['token_price']}",
                            on_click=(lambda e, cid=fc["id"], cn=fc["name"], cp=fc["token_price"]: _buy(cid, cn, cp)) if not owned else lambda e: None,
                            color=BORDER if owned else r_color,
                            disabled=owned,
                        ) if not owned or True else ft.Container(),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CARD,
                    border_radius=14,
                    padding=10,
                    border=ft.border.all(2, r_color if owned else BORDER),
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
            ghost_btn("Cerrar sesión", on_click=_logout, icon=ft.icons.LOGOUT),
            ft.Container(height=40),
        ]
        page.update()

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1("Mi Perfil", size=22),
                    ft.IconButton(icon=ft.icons.REFRESH, icon_color=MUTED, on_click=lambda e: load(), icon_size=20),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=16, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.padding.symmetric(horizontal=16),
    )
