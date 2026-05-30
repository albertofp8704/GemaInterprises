"""
Wallet screen — MetaMask connection via challenge/signature flow.

Mobile flow: copy challenge → sign in MetaMask → paste signature → verify
Web flow   : JS bridge calls window.ethereum directly (auto-fills signature)
"""
import flet as ft
from ..theme import *
from ..api import APIClient, APIError

METAMASK_DEEP_LINK = "https://metamask.app.link"


def build(page: ft.Page, api: APIClient, state: dict):
    content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)

    def load():
        content_col.controls.clear()
        try:
            status = api.wallet_status()
        except APIError as e:
            content_col.controls.append(ft.Text(str(e), color=RED))
            page.update()
            return

        if status.get("connected"):
            _show_connected(status)
        else:
            _show_connect_flow()
        page.update()

    def _show_connected(status: dict):
        address = status.get("wallet_address", "")
        short   = f"{address[:6]}...{address[-4:]}" if len(address) > 12 else address
        contracts = status.get("contracts", {})

        balance_row = ft.Container()
        try:
            bal = api.token_balance()
            balance_row = card(ft.Row([
                ft.Icon(ft.Icons.PAID, size=22, color=GOLD),
                ft.Column([
                    h2(f"{bal['goat_tokens']} GOAT Tokens", color=GOLD),
                    muted("balance in-app"),
                ], spacing=2, expand=True),
            ], spacing=10))
        except APIError:
            pass

        content_col.controls = [
            ft.Container(height=8),
            ft.Container(
                content=ft.Column([
                    ft.Text("🦊", size=48, text_align=ft.TextAlign.CENTER),
                    h2("Wallet conectada", color=ACCENT),
                    ft.Container(
                        content=ft.Text(short, size=14, color=TEXT, font_family="monospace",
                                        selectable=True),
                        bgcolor=SURFACE, border_radius=8, padding=12,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                bgcolor=CARD,
                border_radius=20,
                padding=24,
                border=ft.Border.all(1, ACCENT),
            ),
            balance_row,
            ft.Container(height=4),
            section_title("Red"),
            card(ft.Column([
                ft.Row([
                    ft.Container(width=10, height=10, bgcolor=ACCENT, border_radius=5),
                    body("Polygon Mainnet", size=14),
                    ft.Container(expand=True),
                    badge("Chain ID 137", ACCENT, size=10),
                ], spacing=8),
                divider(),
                _contract_row("GOAT Token (ERC-20)",    contracts.get("goat_token", "No desplegado")),
                _contract_row("Legacy NFT (ERC-721)",   contracts.get("legacy_nft", "No desplegado")),
                _contract_row("FlashCard NFT (ERC-1155)", contracts.get("flashcard_nft", "No desplegado")),
            ], spacing=8)),
            ft.Container(height=4),
            section_title("Acciones on-chain"),
            _mint_panel(address),
        ]

    def _contract_row(label: str, address: str) -> ft.Control:
        short = f"{address[:10]}..." if len(address) > 12 and address.startswith("0x") else address
        return ft.Row([
            body(label, size=12, color=MUTED),
            ft.Container(expand=True),
            ft.Text(short, size=11, color=TEXT, font_family="monospace"),
        ])

    def _mint_panel(wallet_address: str) -> ft.Control:
        amount_f = text_input("Tokens a bridgear (mín 100)", hint="500")

        def _bridge(e):
            try:
                amount = int(amount_f.value or 0)
                r = api.mint_tokens_onchain(amount)
                snack(page, r["message"])
                load()
            except (APIError, ValueError) as ex:
                snack(page, str(ex), RED)

        return card(ft.Column([
            h2("Bridge tokens on-chain"),
            muted("Convierte tus GOAT tokens in-app a ERC-20 en Polygon"),
            ft.Container(height=6),
            amount_f,
            ft.Container(height=8),
            primary_btn("Bridge a Polygon 🔗", on_click=_bridge, expand=True, color=PRIMARY),
            ft.Container(height=4),
            muted("Fee: 50 tokens · Mínimo: 100 tokens"),
        ], spacing=4))

    def _show_connect_flow():
        challenge_txt = ft.TextField(
            label="Mensaje a firmar",
            read_only=True,
            multiline=True,
            min_lines=4,
            max_lines=6,
            bgcolor=SURFACE,
            border_color=BORDER,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=TEXT, font_family="monospace", size=12),
            border_radius=12,
            visible=False,
        )
        address_f   = text_input("Tu wallet address (0x...)", hint="0xABCD...")
        signature_f = text_input("Firma (0x...)", hint="0x...", multiline=True)
        signature_f.visible = False
        address_f.visible   = False
        connect_btn = primary_btn("Verificar y conectar 🦊", on_click=None, expand=True)
        connect_btn.visible = False
        step_indicator = ft.Text("Paso 1 de 3: Solicitar mensaje de firma", size=13, color=GOLD)

        def _step1_get_challenge(e):
            try:
                r = api.wallet_challenge()
                challenge_txt.value   = r["message"]
                challenge_txt.visible = True
                signature_f.visible   = True
                address_f.visible     = True
                connect_btn.visible   = True
                step_indicator.value  = "Paso 2: Copia el mensaje, fírmalo en MetaMask y pega la firma"
                page.update()
            except APIError as ex:
                snack(page, str(ex), RED)

        def _connect(e):
            addr = address_f.value.strip()
            sig  = signature_f.value.strip()
            if not addr or not sig:
                snack(page, "Rellena address y firma", RED)
                return
            try:
                r = api.wallet_connect(addr, sig)
                snack(page, r["message"])
                load()
            except APIError as ex:
                snack(page, str(ex), RED)

        connect_btn.on_click = _connect

        def _open_metamask(e):
            page.launch_url(METAMASK_DEEP_LINK)

        content_col.controls = [
            ft.Container(height=8),
            ft.Container(
                content=ft.Column([
                    ft.Text("🦊", size=56, text_align=ft.TextAlign.CENTER),
                    h1("Conecta MetaMask", size=24),
                    body("Vincula tu wallet para acceder\nal ecosistema GOAT on-chain", size=14, color=MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=CARD,
                border_radius=20,
                padding=24,
                border=ft.Border.all(1, GOLD),
            ),
            ft.Container(height=4),
            card(ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text("1", size=14, color=TEXT, weight=ft.FontWeight.BOLD),
                        width=28, height=28, bgcolor=PRIMARY, border_radius=14,
                        alignment=ft.Alignment.CENTER,
                    ),
                    body("Solicita el mensaje de firma", size=14),
                ], spacing=10),
                ft.Row([
                    ft.Container(
                        content=ft.Text("2", size=14, color=TEXT, weight=ft.FontWeight.BOLD),
                        width=28, height=28, bgcolor=SURFACE, border_radius=14,
                        alignment=ft.Alignment.CENTER,
                        border=ft.Border.all(1, BORDER),
                    ),
                    body("Cópialo y fírmalo en MetaMask", size=14, color=MUTED),
                ], spacing=10),
                ft.Row([
                    ft.Container(
                        content=ft.Text("3", size=14, color=TEXT, weight=ft.FontWeight.BOLD),
                        width=28, height=28, bgcolor=SURFACE, border_radius=14,
                        alignment=ft.Alignment.CENTER,
                        border=ft.Border.all(1, BORDER),
                    ),
                    body("Pega la firma aquí y verifica", size=14, color=MUTED),
                ], spacing=10),
            ], spacing=10)),
            ft.Container(height=4),
            step_indicator,
            primary_btn("1. Generar mensaje de firma", on_click=_step1_get_challenge, expand=True),
            challenge_txt,
            ft.Container(
                content=ghost_btn("Abrir MetaMask 🦊", on_click=_open_metamask),
                visible=True,
            ),
            address_f,
            signature_f,
            connect_btn,
            ft.Container(height=20),
        ]

    load()

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    h1("Wallet 🦊", size=22),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color=MUTED,
                                  on_click=lambda e: load(), icon_size=20),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(top=16, bottom=8),
            ),
            content_col,
        ], spacing=0, expand=True),
        bgcolor=BG,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16),
    )
