"""Entry point for the Flet web app (PWA for iPhone/Android browser)."""
import os
import flet as ft
from mobile.main import main

os.environ.setdefault(
    "GOAT_API_URL",
    "https://gemainterprises-production-a30b.up.railway.app",
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port,
        web_renderer=ft.WebRenderer.HTML,
    )
