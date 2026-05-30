import flet as ft
from ..theme import *
from ..api import APIClient, APIError

# ── Earthy / leather palette (home only) ─────────────────────────────────────
_DARK    = "#0d1408"
_LEATH   = "#1e2d12"
_STONE   = "#363636"
_STONEL  = "#4d4d4d"
_WOOD    = "#2d1c10"
_WOODL   = "#5c3820"
_BRASS   = "#7a5510"
_GOLD_E  = "#b87c14"
_GOLDB   = "#d4a020"
_PARCH   = "#c8a040"
_ROPE    = "#9a8050"
_COPPER  = "#7a4018"


def _label(text: str):
    return ft.Text(
        text.upper(), size=10, color="#8B7340",
        weight=ft.FontWeight.W_600,
        style=ft.TextStyle(letter_spacing=1.6),
    )


def build(page: ft.Page, api: APIClient, state: dict, on_go_quests, on_go_predictions):
    content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)

    def load():
        content_col.controls.clear()
        try:
            profile = api.get_profile()
            state["profile"] = profile
        except APIError:
            content_col.controls.append(ft.Text("Error cargando perfil", color=RED))
            page.update()
            return

        username      = profile.get("username") or "Jugador"
        xp            = profile.get("xp", 0)
        level         = profile.get("level", 1)
        tokens        = profile.get("goat_tokens", 0)
        streak        = profile.get("current_streak", 0)
        villain_on    = profile.get("villain_arc_active", False)
        preds_made    = profile.get("predictions_made", 0)
        preds_correct = profile.get("predictions_correct", 0)
        accuracy      = round(preds_correct / preds_made * 100, 1) if preds_made > 0 else 0.0
        level_xp      = xp - (level - 1) * 500
        xp_pct        = min(level_xp / 500, 1.0)

        # ── Profile card (leather football badge) ─────────────────────────────
        player_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    # Metallic hex avatar
                    ft.Container(
                        content=ft.Text(username[0].upper(), size=26,
                                        color=_GOLDB, weight=ft.FontWeight.BOLD),
                        width=62, height=62,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                            colors=["#565656", "#282828"],
                        ),
                        border_radius=10,
                        border=ft.Border.all(2, _BRASS),
                        alignment=ft.Alignment.CENTER,
                    ),
                    # Name plate
                    ft.Column([
                        ft.Text(f"@{username}", size=16, color="#e8d098",
                                weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Text("⚡", size=12),
                            ft.Text(f"{tokens} GOAT", size=12, color=_GOLDB,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(" · ", size=12, color=_ROPE),
                            ft.Text(f"{streak} d", size=12, color=_ROPE),
                        ], spacing=2),
                    ], spacing=4, expand=True),
                    # XP gauge (analog meter look)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("XP", size=9, color=_BRASS, weight=ft.FontWeight.BOLD),
                            ft.ProgressBar(
                                value=xp_pct, color=_GOLDB, bgcolor="#1a1404",
                                height=5, border_radius=3,
                            ),
                            ft.Text(f"{level_xp}/500", size=9, color=_GOLD_E),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=72,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                            colors=["#4a3014", "#2a1a08"],
                        ),
                        border_radius=10,
                        border=ft.Border.all(1, _BRASS),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=8),
                    ),
                ], spacing=10),
                ft.Container(height=10),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"Lv {level}", size=11, color=_GOLDB,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor="#151008",
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                        border=ft.Border.all(1, _BRASS),
                    ),
                    ft.Container(width=8),
                    ft.Text(f"XP {xp} / {level * 500}", size=11, color=_ROPE),
                ]),
            ], spacing=0),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=["#2d4518", "#1a2d0d", "#0f1a08"],
            ),
            border_radius=18,
            padding=16,
            border=ft.Border.all(2, _COPPER),
        )

        # ── Villain Arc pill ──────────────────────────────────────────────────
        villain_pill = ft.Container(height=0)
        if villain_on:
            villain_pill = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WHATSHOT, size=14, color=TEXT),
                    ft.Text("VILLAIN ARC ACTIVO  😈", size=12, color=TEXT,
                            weight=ft.FontWeight.BOLD),
                ], spacing=6),
                gradient=ft.LinearGradient(colors=["#8B1010", "#5c0808"]),
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                border=ft.Border.all(1, VILLAIN),
            )

        # ── Stone stat tiles ──────────────────────────────────────────────────
        def _stone(label, value, icon, clr):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=14, color=clr),
                        ft.Text(str(value), size=20, color="#e8e8e8",
                                weight=ft.FontWeight.BOLD),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text(label, size=10, color="#909090"),
                ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    colors=["#545454", "#323232", "#1e1e1e"],
                ),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=10, vertical=12),
                expand=True,
                border=ft.Border.all(1, "#585858"),
            )

        stats_row = ft.Row([
            _stone("Quests",       profile.get("quests_completed", 0), ft.Icons.CHECKLIST,     ACCENT),
            _stone("Predicciones", profile.get("predictions_made", 0), ft.Icons.TRACK_CHANGES, _GOLDB),
            _stone("Legados",      profile.get("legacies_dropped", 0), ft.Icons.PLACE,         PRI_L),
        ], spacing=8)

        # ── Quick action cards ─────────────────────────────────────────────────
        action_row = ft.Row([
            ft.GestureDetector(
                on_tap=lambda e: on_go_quests(),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🎯", size=30),
                        ft.Text("Quest\nde hoy", size=11, color="#e8d098",
                                text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_600),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                        colors=["#621e1e", "#3d1010", "#280808"],
                    ),
                    border_radius=14, padding=14, expand=True,
                    border=ft.Border.all(1, "#8B2828"),
                    alignment=ft.Alignment.CENTER,
                ),
            ),
            ft.GestureDetector(
                on_tap=lambda e: on_go_predictions(),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🔮", size=30),
                        ft.Text("Predecir\npartido", size=11, color="#d0d0f0",
                                text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_600),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                        colors=["#1a2a62", "#0d183d", "#080e28"],
                    ),
                    border_radius=14, padding=14, expand=True,
                    border=ft.Border.all(1, "#2a3d8B"),
                    alignment=ft.Alignment.CENTER,
                ),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("⚽", size=30),
                    ft.Text("Mundial\n2026", size=11, color="#2a1404",
                            text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    colors=["#c8a040", "#8a6010", "#5a3c08"],
                ),
                border_radius=14, padding=14, expand=True,
                border=ft.Border.all(2, "#b07820"),
                alignment=ft.Alignment.CENTER,
            ),
        ], spacing=8)

        # ── Radar de predicciones (wooden compass) ────────────────────────────
        radar_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("RADAR DE PREDICCIONES", size=10, color=_ROPE,
                            weight=ft.FontWeight.W_600,
                            style=ft.TextStyle(letter_spacing=1.2)),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text("Información", size=10, color=_GOLDB),
                        bgcolor="#1e1408",
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border=ft.Border.all(1, _BRASS),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Row([
                    # Gut score left
                    ft.Column([
                        ft.Row([
                            ft.Text("💡", size=13),
                            ft.Text("Gut Score", size=12, color=_ROPE,
                                    weight=ft.FontWeight.W_600),
                        ], spacing=6),
                        ft.Container(height=2),
                        ft.Text(f"{accuracy}%", size=38, color=_GOLDB,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(f"{preds_correct} / {preds_made} correctas",
                                size=11, color="#787878"),
                    ], spacing=2, expand=True),
                    # Globe compass
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🌍", size=34),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                           alignment=ft.MainAxisAlignment.CENTER),
                        width=86, height=86,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                            colors=["#5c3820", "#2d1c10", "#181008"],
                        ),
                        border_radius=43,
                        border=ft.Border.all(3, _COPPER),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(width=8),
                    # Prediction timer
                    ft.Container(
                        content=ft.Column([
                            ft.Text("⏳", size=18),
                            ft.Text("Predicciones\nRestantes:", size=8,
                                    color=_ROPE, text_align=ft.TextAlign.CENTER),
                            ft.Text("0", size=24, color=_GOLDB,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text("Límite\n0/1 hoy", size=8, color="#787878",
                                    text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                           spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                        width=66, height=86,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                            colors=["#4a3018", "#281808"],
                        ),
                        border_radius=12,
                        border=ft.Border.all(1, _COPPER),
                        alignment=ft.Alignment.CENTER,
                    ),
                ], spacing=10),
            ], spacing=0),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=["#3d2a16", "#241808", "#161008"],
            ),
            border_radius=16,
            padding=16,
            border=ft.Border.all(2, _COPPER),
        )

        content_col.controls = [
            ft.Container(height=4),
            _label("Tu Perfil"),
            ft.Container(height=4),
            player_card,
            villain_pill,
            ft.Container(height=4),
            _label("Estadísticas"),
            ft.Container(height=4),
            stats_row,
            ft.Container(height=4),
            _label("Acciones Rápidas"),
            ft.Container(height=4),
            action_row,
            ft.Container(height=4),
            radar_card,
            ft.Container(height=24),
        ]
        page.update()

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("GOAT Arc", size=22, color=_PARCH,
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(letter_spacing=1.2)),
                    ft.Text("⚽", size=22),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            colors=["#141f0a", "#0d1408", "#090e06"],
        ),
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
