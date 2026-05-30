import flet as ft
from ..theme import *
from ..api import APIClient, APIError


def build(page: ft.Page, api: APIClient, state: dict):
    tab_content = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    current_tab = {"v": 0}

    def load_matches():
        tab_content.controls.clear()
        try:
            matches = api.matches(status="upcoming")
        except APIError as e:
            tab_content.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if not matches:
            tab_content.controls.append(card(ft.Column([
                ft.Text("⚽", size=40),
                body("No hay partidos próximos", size=16),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            page.update()
            return

        tab_content.controls.append(ft.Container(height=4))
        for m in matches:
            tab_content.controls.append(_match_card(m))
        page.update()

    def load_my_predictions():
        tab_content.controls.clear()
        try:
            preds = api.my_predictions()
        except APIError as e:
            tab_content.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if not preds:
            tab_content.controls.append(card(ft.Column([
                ft.Text("🔮", size=40),
                body("Aún no has predicho nada", size=16),
                muted("Predice el marcador de un partido"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            page.update()
            return

        tab_content.controls.append(ft.Container(height=4))
        for p in preds:
            tab_content.controls.append(_prediction_card(p))
        page.update()

    def _match_card(m: dict):
        stage_labels = {"group": "Fase de grupos", "r32": "Octavos", "r16": "Dieciseisavos",
                        "qf": "Cuartos", "sf": "Semis", "final": "FINAL 🏆"}
        stage = stage_labels.get(m.get("stage", ""), m.get("stage", ""))
        city  = m.get("city", "")

        home_score_f = text_input("", hint="0")
        away_score_f = text_input("", hint="0")
        home_score_f.width = 60
        away_score_f.width = 60

        def _predict(e):
            try:
                h = int(home_score_f.value or 0)
                a = int(away_score_f.value or 0)
                api.predict_match(m["id"], h, a)
                snack(page, f"Predicción guardada: {m['team_home']} {h} - {a} {m['team_away']} 🔒")
                bs.open = False
                load_matches()
            except (APIError, ValueError) as ex:
                snack(page, str(ex), RED)
                bs.open = False
                page.update()

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    h2("Predice el marcador"),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Column([
                            ft.Text(m.get("flag_home", ""), size=32),
                            body(m["team_home"], size=13),
                            home_score_f,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                        ft.Text("VS", size=20, color=MUTED, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text(m.get("flag_away", ""), size=32),
                            body(m["team_away"], size=13),
                            away_score_f,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Container(height=12),
                    primary_btn("Bloquear predicción 🔒", on_click=_predict, expand=True),
                ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD,
                padding=24,
                border_radius=ft.BorderRadius.only(top_left=20, top_right=20),
            ),
            bgcolor=CARD,
        )
        page.overlay.append(bs)

        from datetime import datetime
        try:
            dt = datetime.fromisoformat(m["match_date"])
            date_str = dt.strftime("%d %b · %H:%M")
        except Exception:
            date_str = m.get("match_date", "")

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    badge(stage, color=PRIMARY if m.get("stage") != "final" else GOLD, size=10),
                    ft.Text(f"🏟 {city}", size=11, color=MUTED) if city else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([
                        ft.Text(m.get("flag_home", "🏳"), size=36),
                        body(m["team_home"], size=13),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([
                        ft.Text("VS", size=16, color=MUTED),
                        muted(date_str),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(m.get("flag_away", "🏳"), size=36),
                        body(m["team_away"], size=13),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ]),
                ft.Container(height=8),
                primary_btn("🔮 Predecir marcador", on_click=lambda e: (setattr(bs, 'open', True), page.update()), expand=True),
            ], spacing=2),
            bgcolor=CARD, border_radius=16, padding=16, border=ft.border.all(1, BORDER),
        )

    def _prediction_card(p: dict):
        if p.get("type") == "match":
            h = p.get("predicted_home", "?")
            a = p.get("predicted_away", "?")
            score_txt = f"{h} - {a}"
        else:
            score_txt = p.get("predicted_outcome", "")[:40]

        is_correct = p.get("is_correct")
        color = ACCENT if is_correct is True else (RED if is_correct is False else MUTED)
        icon  = ft.Icons.CHECK_CIRCLE if is_correct is True else (ft.Icons.CANCEL if is_correct is False else ft.Icons.SCHEDULE)
        label = "Correcta ✓" if is_correct is True else ("Incorrecta ✗" if is_correct is False else "Pendiente")

        return card(ft.Row([
            ft.Icon(icon, size=24, color=color),
            ft.Column([
                body(score_txt, size=15),
                muted(p.get("description") or f"Partido #{p.get('match_id')}" or "Predicción de vida"),
            ], expand=True, spacing=2),
            ft.Column([
                ft.Text(label, size=11, color=color),
                ft.Text(f"+{p.get('points_earned', 0)} pts", size=12, color=GOLD if p.get('points_earned') else MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
        ], spacing=10))

    def _on_tab_change(e):
        current_tab["v"] = e.control.selected_index
        if current_tab["v"] == 0:
            load_matches()
        else:
            load_my_predictions()

    load_matches()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        on_change=_on_tab_change,
        tabs=[
            ft.Tab(text="Partidos ⚽"),
            ft.Tab(text="Mis predicciones 🔮"),
        ],
        indicator_color=PRIMARY,
        label_color=TEXT,
        unselected_label_color=MUTED,
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=h1("Mundial 2026 🏆", size=22),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            tabs,
            ft.Container(height=8),
            tab_content,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
