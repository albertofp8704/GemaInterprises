import flet as ft
from ..theme import *
from ..api import APIClient, APIError
from .. import i18n


def build(page: ft.Page, api: APIClient, state: dict):
    content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)

    def load():
        content_col.controls.clear()
        try:
            arc_data = api.active_villain_arc()
        except APIError as e:
            content_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if arc_data.get("active"):
            _show_active_arc(arc_data)
        else:
            _show_start_form()
        page.update()

    def _show_active_arc(arc: dict):
        streak  = arc.get("streak_days", 0)
        power   = arc.get("power_level", 1)
        arc_id  = arc.get("id")
        goals   = arc.get("goals") or []
        quote   = arc.get("quote") or ""

        power_emojis = ["", "⚡", "🔥", "💀", "🐐", "😈", "👹", "👑"]
        power_icon   = power_emojis[min(power, len(power_emojis) - 1)]

        def _checkin(e):
            try:
                r = api.villain_checkin(arc_id)
                snack(page, f"Day {r['streak_days']} 😈  +{r['xp_earned']} XP  Power Lv {r['power_level']}")
                load()
            except APIError as ex:
                snack(page, str(ex), RED)

        def _complete_arc(e):
            dlg = ft.AlertDialog(
                title=ft.Text(i18n.t("villain.confirm_complete"), color=TEXT),
                content=ft.Text(i18n.t("villain.confirm_text"), color=MUTED),
                bgcolor=CARD,
                actions=[
                    ft.TextButton(i18n.t("common.cancel"), on_click=lambda _: page.pop_dialog()),
                    primary_btn(i18n.t("villain.complete_arc"), color=ACCENT, on_click=lambda _: _do_complete(dlg)),
                ],
            )
            page.show_dialog(dlg)

        def _do_complete(dlg):
            try:
                r = api.complete_villain_arc(arc_id)
                page.pop_dialog()
                snack(page, f"{i18n.t('villain.complete_arc')}! +{r['bonus_tokens']} tokens 🏆")
                load()
            except APIError as ex:
                snack(page, str(ex), RED)
                page.pop_dialog()

        arc_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("😈", size=32),
                    ft.Column([
                        h2(arc.get("title", i18n.t("villain.title"))),
                        ft.Text(f'"{quote}"', size=13, color=MUTED, italic=True) if quote else ft.Container(),
                    ], expand=True, spacing=2),
                ], spacing=12),
                ft.Container(height=12),
                ft.Row([
                    ft.Column([
                        ft.Text(str(streak), size=36, color=VILLAIN, weight=ft.FontWeight.W_900),
                        muted(i18n.t("villain.days_streak")),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(width=1, bgcolor=BORDER, height=60),
                    ft.Column([
                        ft.Text(f"Lv {power} {power_icon}", size=28, color=GOLD, weight=ft.FontWeight.W_900),
                        muted(i18n.t("villain.power")),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ]),
                ft.Container(height=12),
                primary_btn(i18n.t("villain.checkin"), on_click=_checkin, expand=True, color=VILLAIN),
                ft.Container(height=6),
                ghost_btn(i18n.t("villain.complete_arc"), on_click=_complete_arc),
            ], spacing=4),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#1a0000", "#2d0000"],
            ),
            border_radius=20,
            padding=20,
            border=ft.Border.all(1, VILLAIN),
        )

        goal_rows = [
            ft.Row([ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, size=18, color=MUTED), body(g, size=14)], spacing=8)
            for g in goals
        ] if goals else [muted(i18n.t("villain.no_goals"))]
        goals_col = ft.Column([section_title(i18n.t("villain.goals")), *goal_rows], spacing=8)

        next_milestone = next((m for m in [7, 14, 21, 30, 60, 90] if m > streak), 90)
        milestone_pct  = min(streak / next_milestone, 1.0)

        power_progress = card(ft.Column([
            ft.Row([
                body(i18n.t("villain.next_powerup"), size=13),
                ft.Text(f"Día {next_milestone}", size=13, color=VILLAIN, weight=ft.FontWeight.W_600),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=milestone_pct, bgcolor=SURFACE, color=VILLAIN, height=6, border_radius=3),
            muted(f"{next_milestone - streak} {i18n.t('villain.days_remaining')}"),
        ], spacing=6))

        content_col.controls = [
            ft.Container(height=4), arc_card,
            ft.Container(height=4), power_progress,
            ft.Container(height=4), goals_col,
            ft.Container(height=20),
        ]

    def _show_start_form():
        title_f  = text_input(i18n.t("villain.name_lbl"), hint=i18n.t("villain.name_hint"))
        quote_f  = text_input(i18n.t("villain.mantra_lbl"), hint='"Messi no pidió permiso."')
        goals_f  = text_input(i18n.t("villain.goals_lbl"), multiline=True,
                               hint="Terminar el proyecto\nEntrenar 5 días/semana")

        def _start(e):
            if not title_f.value.strip():
                snack(page, i18n.t("villain.no_name"), RED)
                return
            goals = [g.strip() for g in (goals_f.value or "").split("\n") if g.strip()]
            try:
                api.start_villain_arc(
                    title=title_f.value.strip(),
                    quote=quote_f.value.strip() or None,
                    goals=goals,
                )
                snack(page, i18n.t("villain.activate_btn"))
                load()
            except APIError as ex:
                snack(page, str(ex), RED)

        content_col.controls = [
            ft.Container(height=8),
            ft.Column([
                ft.Text("😈", size=64, text_align=ft.TextAlign.CENTER),
                h1(i18n.t("villain.activate_title"), size=28),
                body(i18n.t("villain.activate_subtitle"), size=15, color=MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            ft.Container(height=16),
            card(ft.Column([
                title_f,
                ft.Container(height=6),
                quote_f,
                ft.Container(height=6),
                goals_f,
                ft.Container(height=12),
                primary_btn(i18n.t("villain.activate_btn"), on_click=_start, expand=True, color=VILLAIN),
            ], spacing=4)),
            ft.Container(height=20),
        ]

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=h1(i18n.t("villain.title"), size=22),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
