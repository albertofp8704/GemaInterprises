import flet as ft
from .theme import BG, PRIMARY, CARD, TEXT, MUTED, BORDER, GOLD, VILLAIN
from .api import APIClient
from .screens import auth, home, quests, predictions, villain, legacy, profile, wallet


def main(page: ft.Page):
    page.title        = "GOAT Arc"
    page.bgcolor      = BG
    page.theme_mode   = ft.ThemeMode.DARK
    page.padding      = 0
    page.window_width  = 390
    page.window_height = 844

    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        font_family="Roboto",
    )

    api   = APIClient()
    state = {}

    # ── Content area ─────────────────────────────────────────────────────────
    content_ref = ft.Ref[ft.Container]()
    nav_ref     = ft.Ref[ft.NavigationBar]()

    def swap(widget):
        content_ref.current.content = widget
        content_ref.current.update()

    def show_auth():
        nav_ref.current.visible = False
        swap(auth.build(page, api, on_login=on_login))
        page.update()

    def on_login(data: dict):
        state["user"] = data.get("user", {})
        nav_ref.current.visible = True
        show_tab(0)

    def show_tab(idx: int):
        nav_ref.current.selected_index = idx
        if idx == 0:
            swap(home.build(page, api, state,
                            on_go_quests=lambda: show_tab(1),
                            on_go_predictions=lambda: show_tab(2)))
        elif idx == 1:
            swap(quests.build(page, api, state, on_quest_done=lambda: None))
        elif idx == 2:
            swap(predictions.build(page, api, state))
        elif idx == 3:
            swap(villain.build(page, api, state))
        elif idx == 4:
            swap(legacy.build(page, api, state))
        elif idx == 5:
            swap(wallet.build(page, api, state))
        elif idx == 6:
            swap(profile.build(page, api, state, on_logout=show_auth))
        page.update()

    def on_nav_change(e):
        show_tab(e.control.selected_index)

    nav_bar = ft.NavigationBar(
        ref=nav_ref,
        selected_index=0,
        bgcolor=CARD,
        indicator_color=PRIMARY,
        on_change=on_nav_change,
        visible=False,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,        selected_icon=ft.Icons.HOME,              label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST_OUTLINED,   selected_icon=ft.Icons.CHECKLIST,         label="Quests"),
            ft.NavigationBarDestination(icon=ft.Icons.SPORTS_SOCCER,        selected_icon=ft.Icons.SPORTS_SOCCER,     label="Mundial"),
            ft.NavigationBarDestination(icon=ft.Icons.WHATSHOT_OUTLINED,    selected_icon=ft.Icons.WHATSHOT,          label="Villain"),
            ft.NavigationBarDestination(icon=ft.Icons.PLACE_OUTLINED,       selected_icon=ft.Icons.PLACE,             label="Legados"),
            ft.NavigationBarDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, selected_icon=ft.Icons.ACCOUNT_BALANCE_WALLET, label="Wallet"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINED,      selected_icon=ft.Icons.PERSON,            label="Perfil"),
        ],
    )

    page.add(
        ft.Column([
            ft.Container(
                ref=content_ref,
                expand=True,
                content=ft.Container(),
                bgcolor=BG,
            ),
            nav_bar,
        ], spacing=0, expand=True),
    )

    # ── Boot ─────────────────────────────────────────────────────────────────
    show_auth()

    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
