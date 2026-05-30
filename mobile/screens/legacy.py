import flet as ft
from ..theme import *
from ..api import APIClient, APIError
from .. import i18n


DEFAULT_LAT = 40.4168
DEFAULT_LNG = -3.7038


def build(page: ft.Page, api: APIClient, state: dict):
    nearby_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    mine_col   = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def load_nearby():
        nearby_col.controls.clear()
        nearby_col.controls.append(ft.Container(height=4))
        try:
            items = api.nearby_legacies(DEFAULT_LAT, DEFAULT_LNG, radius=50)
        except APIError as e:
            nearby_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if not items:
            nearby_col.controls.append(card(ft.Column([
                ft.Text("📍", size=40),
                body(i18n.t("legacy.empty_nearby"), size=16),
                muted(i18n.t("legacy.be_first")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            page.update()
            return

        for item in items:
            nearby_col.controls.append(_nearby_card(item))
        page.update()

    def load_mine():
        mine_col.controls.clear()
        mine_col.controls.append(ft.Container(height=4))
        try:
            items = api.my_legacies()
        except APIError as e:
            mine_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if not items:
            mine_col.controls.append(card(ft.Column([
                ft.Text("📍", size=40),
                body(i18n.t("legacy.empty_mine"), size=16),
                muted(i18n.t("legacy.drop_hint")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            page.update()
            return

        for item in items:
            mine_col.controls.append(_mine_card(item))
        page.update()

    def _nearby_card(item: dict):
        legacy_id = item["id"]
        dist      = item.get("distance_km", 0)
        found     = item.get("found_count", 0)
        is_nft    = item.get("is_nft", False)
        ctype     = item.get("content_type", "text")
        city      = item.get("city") or item.get("location_name") or "—"

        type_icon = {"text": "✍️", "voice": "🎙", "image": "🖼"}.get(ctype, "📍")

        def _find(e):
            try:
                r = api.find_legacy(legacy_id)
                snack(page, f"📍 +{r['tokens_earned']} tokens")
                _show_content_dialog(r["content"], r.get("content_type", "text"), city)
            except APIError as ex:
                snack(page, str(ex), RED)

        return card(ft.Row([
            ft.Container(
                content=ft.Text(type_icon, size=22),
                width=44, height=44, bgcolor=SURFACE, border_radius=10,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column([
                ft.Row([
                    body(city, size=14),
                    badge("NFT 🎨", GOLD, size=9) if is_nft else ft.Container(),
                ], spacing=4),
                ft.Row([
                    ft.Icon(ft.Icons.PLACE, size=12, color=PRIMARY),
                    ft.Text(f"{dist:.1f} km", size=12, color=PRIMARY),
                    ft.Container(width=8),
                    ft.Icon(ft.Icons.VISIBILITY, size=12, color=MUTED),
                    ft.Text(f"{found}", size=12, color=MUTED),
                ], spacing=2),
            ], expand=True, spacing=4),
            primary_btn(i18n.t("legacy.open"), on_click=_find, color=PRIMARY),
        ], spacing=10, alignment=ft.MainAxisAlignment.START))

    def _show_content_dialog(content, ctype, city):
        icon = {"text": "✍️", "voice": "🎙", "image": "🖼"}.get(ctype, "📍")
        dlg = ft.AlertDialog(
            title=ft.Text(f"{icon} {city}", color=TEXT),
            content=ft.Container(
                content=ft.Text(content, color=MUTED, size=14),
                bgcolor=SURFACE, border_radius=10, padding=16, width=280,
            ),
            bgcolor=CARD,
            actions=[ft.TextButton(i18n.t("common.close"), on_click=lambda _: page.pop_dialog())],
        )
        page.show_dialog(dlg)

    def _mine_card(item: dict):
        found  = item.get("found_count", 0)
        active = item.get("is_active", True)
        is_nft = item.get("is_nft", False)
        ctype  = item.get("content_type", "text")
        icon   = {"text": "✍️", "voice": "🎙", "image": "🖼"}.get(ctype, "📍")
        preview = item.get("content", "")[:60]

        return card(ft.Column([
            ft.Row([
                ft.Text(icon, size=20),
                body(preview + ("..." if len(item.get("content", "")) > 60 else ""), size=13, color=MUTED),
                badge("NFT" if is_nft else "ACTIVO" if active else "EXPIRADO",
                      GOLD if is_nft else ACCENT if active else RED, size=9),
            ], spacing=8),
            ft.Row([
                ft.Icon(ft.Icons.VISIBILITY, size=12, color=MUTED),
                ft.Text(f"{found}", size=12, color=MUTED),
            ], spacing=4),
        ], spacing=6))

    def _show_drop_form(e):
        content_f = text_input(i18n.t("legacy.drop_content_lbl"), multiline=True,
                               hint=i18n.t("legacy.drop_content_hint"))
        city_f    = text_input(i18n.t("legacy.city_lbl"), hint="Madrid")
        country_f = text_input(i18n.t("legacy.country_lbl"), hint="España")

        def _drop(e):
            if not content_f.value.strip():
                snack(page, i18n.t("legacy.write_first"), RED)
                return
            try:
                api.drop_legacy(
                    content=content_f.value.strip(),
                    lat=DEFAULT_LAT,
                    lng=DEFAULT_LNG,
                    city=city_f.value.strip() or None,
                    country=country_f.value.strip() or None,
                )
                snack(page, i18n.t("legacy.dropped"))
                page.pop_dialog()
                load_nearby()
            except APIError as ex:
                snack(page, str(ex), RED)
                page.pop_dialog()

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    h2(i18n.t("legacy.drop_title")),
                    muted(i18n.t("legacy.drop_subtitle")),
                    ft.Container(height=8),
                    content_f,
                    ft.Container(height=4),
                    ft.Row([city_f, country_f], spacing=8),
                    ft.Container(height=12),
                    primary_btn(i18n.t("legacy.drop_btn"), on_click=_drop, expand=True, color=PRI_L),
                ], spacing=6),
                bgcolor=CARD,
                padding=24,
                border_radius=ft.BorderRadius.only(top_left=20, top_right=20),
            ),
            bgcolor=CARD,
        )
        page.show_dialog(bs)

    def _on_tab_change(e):
        idx = int(e.data)
        if idx == 0:
            load_nearby()
        else:
            load_mine()

    load_nearby()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1(i18n.t("legacy.title"), size=22),
                    primary_btn(i18n.t("legacy.drop"), on_click=_show_drop_form, color=PRI_L),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            ft.Tabs(
                content=ft.Column([
                    ft.TabBar(
                        tabs=[ft.Tab(label=i18n.t("legacy.nearby")), ft.Tab(label=i18n.t("legacy.mine"))],
                        scrollable=False,
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[nearby_col, mine_col],
                    ),
                ], expand=True, spacing=0),
                length=2,
                selected_index=0,
                expand=True,
                on_change=_on_tab_change,
            ),
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
