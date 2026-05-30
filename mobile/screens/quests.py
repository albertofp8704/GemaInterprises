import flet as ft
from ..theme import *
from ..api import APIClient, APIError
from .. import i18n


def build(page: ft.Page, api: APIClient, state: dict, on_quest_done):
    list_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def load():
        list_col.controls.clear()
        list_col.controls.append(ft.Container(height=4))
        try:
            quests = api.today_quests()
        except APIError as e:
            list_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if not quests:
            list_col.controls.append(card(ft.Column([
                ft.Text("🎯", size=40),
                body(i18n.t("quests.empty"), size=16),
                muted(i18n.t("quests.come_back")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            page.update()
            return

        for q in quests:
            list_col.controls.append(_quest_card(q))
        page.update()

    def _quest_card(q: dict):
        diff    = q.get("difficulty", "normal")
        cat     = q.get("category", "personal")
        done    = q.get("completed", False)
        emoji   = DIFF_EMOJI.get(diff, "🔥")
        d_color = DIFF_COLOR.get(diff, PRIMARY)
        c_color = CAT_COLOR.get(cat, PRIMARY)

        reflection_f = text_input(i18n.t("quests.reflection"), hint=i18n.t("quests.reflection_hint"), multiline=True)

        def _complete(e):
            page.show_dialog(bs)

        def _confirm(e):
            try:
                result = api.complete_quest(q["id"], reflection=reflection_f.value or None)
                page.pop_dialog()
                snack(page, f"+{result['xp_earned']} XP  +{result['tokens_earned']} 🪙  Racha: {result['current_streak']} días 🔥")
                on_quest_done()
                load()
            except APIError as ex:
                snack(page, str(ex), RED)
                page.pop_dialog()

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    h2(f"{i18n.t('quests.complete')}: {q['title']}"),
                    ft.Container(height=4),
                    body(q["description"], size=13),
                    ft.Container(height=8),
                    reflection_f,
                    ft.Container(height=12),
                    primary_btn(i18n.t("common.confirm"), on_click=_confirm, expand=True, color=ACCENT),
                ], spacing=6),
                bgcolor=CARD,
                padding=24,
                border_radius=ft.BorderRadius.only(top_left=20, top_right=20),
            ),
            bgcolor=CARD,
        )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(emoji, size=20),
                        width=42, height=42, bgcolor=SURFACE, border_radius=10,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(q["title"], size=14, color=TEXT if not done else MUTED,
                                    weight=ft.FontWeight.W_600, expand=True),
                            badge(diff.upper(), color=d_color, size=9),
                        ]),
                        ft.Row([
                            badge(cat, color=c_color, size=9),
                            ft.Container(width=4),
                            ft.Icon(ft.Icons.STAR, size=12, color=GOLD),
                            ft.Text(f"+{q['xp_reward']} XP", size=11, color=GOLD),
                            ft.Icon(ft.Icons.PAID, size=12, color=MUTED),
                            ft.Text(f"+{q['token_reward']}", size=11, color=MUTED),
                        ], spacing=2),
                    ], expand=True, spacing=4),
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.CHECK_CIRCLE if done else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            size=24,
                            color=ACCENT if done else BORDER,
                        ),
                    ),
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
                ft.Container(height=4),
                body(q["description"], size=12, color=MUTED if done else None),
                ft.Container(height=6),
                ft.Container() if done else primary_btn(
                    i18n.t("quests.complete"), on_click=_complete, expand=True,
                    color=d_color,
                ),
            ], spacing=2),
            bgcolor=CARD,
            border_radius=16,
            padding=16,
            border=ft.Border.all(1, ACCENT if done else BORDER),
            opacity=0.6 if done else 1.0,
        )

    load()

    from datetime import date
    today_str = date.today().strftime("%d %b %Y")

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        h1(i18n.t("nav.quests"), size=22),
                        muted(f"{i18n.t('common.today')} · {today_str}"),
                    ], spacing=2),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, icon_color=MUTED, icon_size=20,
                        on_click=lambda e: load(),
                        tooltip=i18n.t("common.reload"),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            list_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
