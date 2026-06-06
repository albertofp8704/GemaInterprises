# GemaInterprises — GOAT Arc Mobile App

## Stack
- **Frontend**: Flet 0.85.2 (Python), deployed on Railway
- **Backend**: FastAPI, deployed on Railway (separate service)
- **Branch activo**: `claude/app-build-xSlhG` → PR #1

## Estructura
```
mobile/
├── main.py          # Boot: SharedPreferences + in-memory fallback, nav
├── i18n.py          # 20 idiomas — t(key) con fallback a "es"
├── api.py           # APIClient → FastAPI backend
├── theme.py         # Colores, helpers UI (card, badge, h1, muted…)
└── screens/
    ├── auth.py      # Login / registro
    ├── home.py      # Dashboard principal
    ├── quests.py    # Misiones diarias
    ├── predictions.py  # Predicciones Mundial 2026
    ├── villain.py   # Villain Arc (racha + check-in)
    ├── legacy.py    # Legados geolocalizados
    ├── wallet.py    # MetaMask / Polygon bridge
    └── profile.py   # Perfil, avatares, idioma
```

## Reglas críticas
- `page.client_storage` NO existe en Flet 0.85.2 — usar `ft.SharedPreferences()` con fallback `_mem` dict
- API keys NUNCA en código — solo Railway env vars
- Todas las cadenas UI deben pasar por `i18n.t("clave")`, nunca hardcoded
- Deploy: `git push origin claude/app-build-xSlhG`

## i18n — 20 idiomas
`es en pt fr de it zh ar hi ru ja ko tr id nl vi pl bn sw ur`

Fallback: si la clave no existe en el idioma activo → cae a "es".
Nuevas claves van en `_EXT` al final de `i18n.py`, luego se fusionan con `_T[lang].update(...)`.

## Persistent storage (Flet 0.85)
```python
try:
    _prefs = ft.SharedPreferences()
except Exception:
    _prefs = None
# _mem: dict  ← fallback siempre disponible
```

## Railway services
- `72d33d33` = backend FastAPI
- `74fcce2c` = frontend Flet
