import flet as ft
from ..theme import *
from ..api import APIClient, APIError


def build(page: ft.Page, api: APIClient, on_login):
    """Returns the auth screen content (login / register toggle)."""
    mode = {"v": "login"}  # "login" | "register"

    email_f    = text_input("Email", hint="tu@email.com")
    password_f = text_input("Contraseña", password=True)
    username_f = text_input("Username (tu apodo GOAT)", hint="@leyenda")
    error_txt  = ft.Text("", color=RED, size=13)
    submit_btn = primary_btn("Entrar", on_click=None, expand=True)
    toggle_btn = ft.TextButton("", style=ft.ButtonStyle(color=PRI_L))

    def _submit(e):
        email = email_f.value.strip()
        pwd   = password_f.value
        if not email or not pwd:
            error_txt.value = "Rellena todos los campos"
            page.update()
            return
        try:
            if mode["v"] == "register":
                if not username_f.value.strip():
                    error_txt.value = "Elige un username"
                    page.update()
                    return
                data = api.register(email, pwd)
                api.update_profile(username=username_f.value.strip())
            else:
                data = api.login(email, pwd)
            on_login(data)
        except APIError as ex:
            error_txt.value = str(ex)
            page.update()

    submit_btn.on_click = _submit

    def _toggle(e):
        mode["v"] = "register" if mode["v"] == "login" else "login"
        _refresh()

    toggle_btn.on_click = _toggle

    username_row = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=200,
    )

    def _refresh():
        is_reg = mode["v"] == "register"
        submit_btn.text   = "Crear cuenta" if is_reg else "Entrar"
        toggle_btn.text   = "¿Ya tienes cuenta? Inicia sesión" if is_reg else "¿No tienes cuenta? Regístrate"
        username_row.content = username_f if is_reg else ft.Container()
        error_txt.value   = ""
        page.update()

    _refresh()

    logo = ft.Column([
        ft.Text("GOAT", size=52, color=PRIMARY, weight=ft.FontWeight.W_900, style=ft.TextStyle(letter_spacing=-2)),
        ft.Text("ARC", size=52, color=GOLD, weight=ft.FontWeight.W_900, style=ft.TextStyle(letter_spacing=-2)),
        ft.Container(height=4),
        muted("Escribe tu historia. Gana tu legado.", size=14),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

    return ft.Container(
        content=ft.Column([
            ft.Container(height=60),
            logo,
            ft.Container(height=40),
            card(ft.Column([
                error_txt,
                email_f,
                ft.Container(height=4),
                password_f,
                ft.Container(height=4),
                username_row,
                ft.Container(height=8),
                submit_btn,
                ft.Container(height=4),
                ft.Row([toggle_btn], alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=6)),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=24),
    )
