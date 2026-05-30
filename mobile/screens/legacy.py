import flet as ft
from ..theme import *
from ..api import APIClient, APIError


# Default coords = Madrid (users will use GPS in production)
DEFAULT_LAT = 40.4168
DEFAULT_LNG = -3.7038


def build(page: ft.Page, api: APIClient, state: dict):
    content_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    view_mode   = {"v": "nearby"}   # "nearby" | "mine"

    def load():
        content_col.controls.clear()
        try:
            if view_mode["v"] == "nearby":
                items = api.nearby_legacies(DEFAULT_LAT, DEFAULT_LNG, radius_km=50)
                _render_nearby(items)
            else:
                items = api.my_legacies()
                _render_mine(items)
        except APIError as e:
            content_col.controls.append(ft.Text(str(e), color=RED))
        page.update()

    def _render_nearby(items):
        if not items:
            content_col.controls.append(card(ft.Column([
                ft.Text("📍", size=40),
                body("No hay legados cercanos", size=16),
                muted("Sé el primero en dejar uno"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            return

        for item in items:
            content_col.controls.append(_nearby_card(item))

    def _nearby_card(item: dict):
        legacy_id = item["id"]
        dist      = item.get("distance_km", 0)
        found     = item.get("found_count", 0)
        is_nft    = item.get("is_nft", False)
        ctype     = item.get("content_type", "text")
        city      = item.get("city") or item.get("location_name") or "Ubicación desconocida"

        type_icon = {"text": "✍️", "voice": "🎙", "image": "🖼"}.get(ctype, "📍")

        def _find(e):
            try:
                r = api.find_legacy(legacy_id)
                snack(page, f"📍 Legado encontrado! +{r['tokens_earned']} tokens")
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
                    ft.Text(f"{found} encontrados", size=12, color=MUTED),
                ], spacing=2),
            ], expand=True, spacing=4),
            primary_btn("Abrir 📍", on_click=_find, color=PRIMARY),
        ], spacing=10, alignment=ft.MainAxisAlignment.START))

    def _show_content_dialog(content, ctype, city):
        icon = {"text": "✍️", "voice": "🎙", "image": "🖼"}.get(ctype, "📍")
        dlg = ft.AlertDialog(
            title=ft.Text(f"{icon} Legado de {city}", color=TEXT),
            content=ft.Container(
                content=ft.Text(content, color=MUTED, size=14),
                bgcolor=SURFACE,
                border_radius=10,
                padding=16,
                width=280,
            ),
            bgcolor=CARD,
            actions=[ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())],
        )
        page.show_dialog(dlg)

    def _render_mine(items):
        if not items:
            content_col.controls.append(card(ft.Column([
                ft.Text("📍", size=40),
                body("Aún no has dejado legados", size=16),
                muted("Dropea uno y que lo encuentren"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=32))
            return

        for item in items:
            content_col.controls.append(_mine_card(item))

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
                ft.Text(f"{found} personas lo encontraron", size=12, color=MUTED),
            ], spacing=4),
        ], spacing=6))

    def _show_drop_form(e):
        content_f  = text_input("Tu mensaje para el mundo", multiline=True, hint="Escribe lo que quieras que alguien encuentre...")
        city_f     = text_input("Ciudad", hint="Madrid")
        country_f  = text_input("País", hint="España")

        def _drop(e):
            if not content_f.value.strip():
                snack(page, "Escribe algo primero", RED)
                return
            try:
                api.drop_legacy(
                    content=content_f.value.strip(),
                    lat=DEFAULT_LAT,
                    lng=DEFAULT_LNG,
                    city=city_f.value.strip() or None,
                    country=country_f.value.strip() or None,
                )
                snack(page, "📍 Legado dropeado. Alguien lo encontrará.")
                page.pop_dialog()
                load()
            except APIError as ex:
                snack(page, str(ex), RED)
                page.pop_dialog()

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    h2("Drop un Legado 📍"),
                    muted("Tu mensaje quedará en este lugar para que alguien lo encuentre"),
                    ft.Container(height=8),
                    content_f,
                    ft.Container(height=4),
                    ft.Row([city_f, country_f], spacing=8),
                    ft.Container(height=12),
                    primary_btn("Dropear Legado 📍", on_click=_drop, expand=True, color=PRI_L),
                ], spacing=6),
                bgcolor=CARD,
                padding=24,
                border_radius=ft.BorderRadius.only(top_left=20, top_right=20),
            ),
            bgcolor=CARD,
        )
        page.show_dialog(bs)

    def _toggle_view(e):
        view_mode["v"] = "mine" if view_mode["v"] == "nearby" else "nearby"
        tabs.selected_index = 0 if view_mode["v"] == "nearby" else 1
        load()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        on_change=lambda e: (view_mode.update({"v": "nearby" if e.control.selected_index == 0 else "mine"}), load()),
        tabs=[ft.Tab(text="Cercanos 📍"), ft.Tab(text="Mis legados ✍️")],
        indicator_color=PRIMARY,
        label_color=TEXT,
        unselected_label_color=MUTED,
    )

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1("Legados 📍", size=22),
                    primary_btn("+ Drop", on_click=_show_drop_form, color=PRI_L),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            tabs,
            ft.Container(height=8),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
