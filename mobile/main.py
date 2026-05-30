import flet as ft
from .theme import BG, PRIMARY
from .api import APIClient
from .screens import auth, home, quests, predictions, villain, legacy, profile, wallet
from . import i18n


async def main(page: ft.Page):
    page.title      = "GOAT Arc"
    page.bgcolor    = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding    = 0

    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        font_family="Roboto",
    )

    api   = APIClient()
    state = {}

    # Persistent storage: try SharedPreferences (browser localStorage),
    # fall back silently to an in-memory dict so the app always boots.
    _mem: dict = {}
    try:
        _prefs = ft.SharedPreferences()
    except Exception:
        _prefs = None

    async def _store(key: str, value: str):
        _mem[key] = value
        if _prefs:
            try:
                await _prefs.set(key, value)
            except Exception:
                pass

    async def _load(key: str) -> str | None:
        if _prefs:
            try:
                val = await _prefs.get(key)
                if val is not None:
                    _mem[key] = val
                    return val
            except Exception:
                pass
        return _mem.get(key)

    async def _delete(key: str):
        _mem.pop(key, None)
        if _prefs:
            try:
                await _prefs.remove(key)
            except Exception:
                pass

    # ── Content area ─────────────────────────────────────────────────────────
    content_ref = ft.Ref[ft.Container]()
    nav_ref     = ft.Ref[ft.NavigationBar]()

    def _nav_labels():
        return [
            i18n.t("nav.home"),
            i18n.t("nav.quests"),
            i18n.t("nav.mundial"),
            i18n.t("nav.villain"),
            i18n.t("nav.legados"),
            i18n.t("nav.wallet"),
            i18n.t("nav.perfil"),
        ]

    def swap(widget):
        content_ref.current.content = widget
        content_ref.current.update()

    def show_auth():
        nav_ref.current.visible = False
        swap(auth.build(page, api, on_login=on_login))
        page.update()

    def on_login(data: dict):
        state["user"] = data.get("user", {})
        page.run_task(_store, "goat_token", api.token)
        nav_ref.current.visible = True
        show_tab(0)

    def on_logout():
        page.run_task(_delete, "goat_token")
        show_auth()

    def on_lang_change(lang: str):
        i18n.set_lang(lang)
        page.run_task(_store, "goat_lang", lang)
        for i, dest in enumerate(nav_ref.current.destinations):
            dest.label = _nav_labels()[i]
        show_tab(nav_ref.current.selected_index)

    state["on_lang_change"] = on_lang_change

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
            swap(profile.build(page, api, state, on_logout=on_logout))
        page.update()

    def on_nav_change(e):
        show_tab(e.control.selected_index)

    labels = _nav_labels()
    nav_bar = ft.NavigationBar(
        ref=nav_ref,
        selected_index=0,
        bgcolor="#1a1208",
        indicator_color="#d4a02030",
        on_change=on_nav_change,
        visible=False,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,                     selected_icon=ft.Icons.HOME,              label=labels[0]),
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST_OUTLINED,                selected_icon=ft.Icons.CHECKLIST,         label=labels[1]),
            ft.NavigationBarDestination(icon=ft.Icons.SPORTS_SOCCER,                     selected_icon=ft.Icons.SPORTS_SOCCER,     label=labels[2]),
            ft.NavigationBarDestination(icon=ft.Icons.WHATSHOT_OUTLINED,                 selected_icon=ft.Icons.WHATSHOT,          label=labels[3]),
            ft.NavigationBarDestination(icon=ft.Icons.PLACE_OUTLINED,                    selected_icon=ft.Icons.PLACE,             label=labels[4]),
            ft.NavigationBarDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,   selected_icon=ft.Icons.ACCOUNT_BALANCE_WALLET, label=labels[5]),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINED,                   selected_icon=ft.Icons.PERSON,            label=labels[6]),
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

    # ── Boot: restore language + session from browser localStorage ────────────
    saved_lang = await _load("goat_lang")
    if saved_lang:
        i18n.set_lang(saved_lang)

    saved_token = await _load("goat_token")
    if saved_token:
        api.token = saved_token
        try:
            user = api.me()
            state["user"] = user
            nav_ref.current.visible = True
            show_tab(0)
        except Exception:
            page.run_task(_delete, "goat_token")
            show_auth()
    else:
        show_auth()

    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
