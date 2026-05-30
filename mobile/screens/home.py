import flet as ft
from ..theme import *
from ..api import APIClient, APIError


def build(page: ft.Page, api: APIClient, state: dict, on_go_quests, on_go_predictions):
    content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)

    def load():
        content_col.controls.clear()
        try:
            profile   = api.get_profile()
            state["profile"] = profile
        except APIError:
            content_col.controls.append(ft.Text("Error cargando perfil", color=RED))
            page.update()
            return

        username = profile.get("username") or state.get("user", {}).get("email", "Jugador")
        xp       = profile.get("xp", 0)
        level    = profile.get("level", 1)
        tokens   = profile.get("goat_tokens", 0)
        streak   = profile.get("current_streak", 0)
        villain  = profile.get("villain_arc_active", False)

        # ── Player card ──────────────────────────────────────────────────────
        player_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(username[0].upper(), size=28, color=TEXT, weight=ft.FontWeight.BOLD),
                        width=56, height=56, bgcolor=PRIMARY, border_radius=28,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text(f"@{username}", size=16, color=TEXT, weight=ft.FontWeight.W_600),
                        ft.Row([
                            ft.Icon(ft.icons.BOLT, size=14, color=GOLD),
                            ft.Text(f"{tokens} GOAT", size=13, color=GOLD, weight=ft.FontWeight.W_600),
                            ft.Container(width=8),
                            ft.Icon(ft.icons.LOCAL_FIRE_DEPARTMENT, size=14, color=ACCENT),
                            ft.Text(f"{streak} días", size=13, color=ACCENT),
                        ], spacing=2),
                    ], spacing=3, expand=True),
                    ft.Container(
                        content=ft.Text(f"⚽", size=22),
                        width=44, height=44, bgcolor=SURFACE, border_radius=12,
                        alignment=ft.alignment.center,
                        tooltip="Nivel",
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=12),
                ft.Container(height=10),
                xp_bar(xp, level),
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[CARD, SURFACE],
            ),
            border_radius=20,
            padding=20,
            border=ft.border.all(1, PRIMARY if villain else BORDER),
        )

        # ── Villain Arc pill ─────────────────────────────────────────────────
        villain_pill = ft.Container()
        if villain:
            villain_pill = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.WHATSHOT, size=16, color=TEXT),
                    ft.Text("VILLAIN ARC ACTIVO  😈", size=13, color=TEXT, weight=ft.FontWeight.BOLD),
                ], spacing=6),
                bgcolor=VILLAIN,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )

        # ── Quick stats ──────────────────────────────────────────────────────
        stats_row = ft.Row([
            stat_tile("Quests", profile.get("quests_completed", 0), ft.icons.CHECKLIST, ACCENT),
            stat_tile("Predicciones", profile.get("predictions_made", 0), ft.icons.TRACK_CHANGES, GOLD),
            stat_tile("Legados", profile.get("legacies_dropped", 0), ft.icons.PLACE, PRI_L),
        ], spacing=8)

        # ── Quick action cards ────────────────────────────────────────────────
        def _quest_tap(e):
            on_go_quests()

        def _pred_tap(e):
            on_go_predictions()

        action_cards = ft.Row([
            ft.GestureDetector(
                on_tap=_quest_tap,
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🎯", size=28),
                        ft.Text("Quest\nde hoy", size=13, color=TEXT, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=SURFACE, border_radius=14, padding=14, expand=True,
                    border=ft.border.all(1, BORDER),
                ),
            ),
            ft.GestureDetector(
                on_tap=_pred_tap,
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🔮", size=28),
                        ft.Text("Predecir\npartido", size=13, color=TEXT, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=SURFACE, border_radius=14, padding=14, expand=True,
                    border=ft.border.all(1, BORDER),
                ),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("⚽", size=28),
                    ft.Text("Mundial\n2026", size=13, color=GOLD, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=SURFACE, border_radius=14, padding=14, expand=True,
                border=ft.border.all(1, GOLD),
            ),
        ], spacing=8)

        # ── Gut score card ────────────────────────────────────────────────────
        accuracy = 0.0
        if profile.get("predictions_made", 0) > 0:
            accuracy = round(profile.get("predictions_correct", 0) / profile["predictions_made"] * 100, 1)

        gut_card = card(ft.Row([
            ft.Column([
                ft.Text("🔮 Gut Score", size=14, color=MUTED),
                ft.Text(f"{accuracy}%", size=32, color=GOLD, weight=ft.FontWeight.BOLD),
                muted(f"{profile.get('predictions_correct', 0)} / {profile.get('predictions_made', 0)} correctas"),
            ], spacing=2, expand=True),
            ft.Container(
                content=ft.CircleAvatar(
                    content=ft.Text(f"{int(accuracy)}", size=18, color=TEXT, weight=ft.FontWeight.BOLD),
                    bgcolor=PRIMARY if accuracy >= 50 else RED,
                    radius=30,
                ),
            ),
        ]))

        content_col.controls = [
            ft.Container(height=8),
            section_title("Tu perfil"),
            player_card,
            villain_pill,
            ft.Container(height=4),
            section_title("Estadísticas"),
            stats_row,
            ft.Container(height=4),
            section_title("Acciones rápidas"),
            action_cards,
            ft.Container(height=4),
            section_title("Radar de predicciones"),
            gut_card,
            ft.Container(height=20),
        ]
        page.update()

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1("GOAT Arc", size=22),
                    ft.Text("⚽", size=22),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=16, left=0, right=0, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.padding.symmetric(horizontal=16),
    )
