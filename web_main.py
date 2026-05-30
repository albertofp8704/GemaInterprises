"""Entry point for the Flet web app (PWA for iPhone/Android browser)."""
import os

os.environ.setdefault(
    "GOAT_API_URL",
    "https://gemainterprises-production-a30b.up.railway.app",
)

import flet as ft
from mobile.main import main

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port,
        assets_dir="mobile/assets",
    )
