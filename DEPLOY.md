# GOAT Arc — Deploy Guide

## Backend en Railway

### 1. Crear proyecto en Railway

1. Ve a [railway.app](https://railway.app) → New Project
2. **Deploy from GitHub repo** → selecciona `GemaInterprises`
3. Railway detecta automáticamente el `railway.toml`

### 2. Añadir PostgreSQL

En tu proyecto Railway:
- **New** → **Database** → **Add PostgreSQL**
- Railway inyecta `DATABASE_URL` automáticamente

### 3. Variables de entorno (Settings → Variables)

| Variable | Cómo obtenerla |
|---|---|
| `JWT_SECRET` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `INTERNAL_API_KEY` | `python -c "import secrets; print(secrets.token_hex(24))"` |
| `STRIPE_SECRET_KEY` | Dashboard de [Stripe](https://dashboard.stripe.com/apikeys) |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks → tu endpoint |
| `DATABASE_URL` | Auto-inyectada por Railway al añadir PostgreSQL |

Variables opcionales (para activar Web3):

| Variable | Valor |
|---|---|
| `GOAT_TOKEN_ADDRESS` | Address del contrato desplegado en Polygon |
| `LEGACY_NFT_ADDRESS` | Address del contrato LegacyNFT |
| `FLASHCARD_NFT_ADDRESS` | Address del contrato FlashCardNFT |
| `BACKEND_WALLET_KEY` | Private key del wallet dueño de los contratos |
| `WEB3_RPC_URL` | `https://polygon-rpc.com` |

### 4. Verificar deploy

```bash
curl https://TU-APP.railway.app/health
# → {"status":"ok","app":"GOAT Arc"}
```

---

## Contratos en Polygon (Mainnet / Mumbai testnet)

### Prerequisitos
```bash
npm install -g hardhat
npm install @openzeppelin/contracts
```

### Compilar y desplegar

```bash
cd contracts
npx hardhat compile
npx hardhat run scripts/deploy.js --network polygon
```

### Deploy script básico (`contracts/scripts/deploy.js`)

```js
const { ethers } = require("hardhat");

async function main() {
  const GoatToken    = await ethers.deployContract("GOATToken");
  const LegacyNFT   = await ethers.deployContract("LegacyNFT");
  const FlashCardNFT = await ethers.deployContract("FlashCardNFT");

  await GoatToken.waitForDeployment();
  await LegacyNFT.waitForDeployment();
  await FlashCardNFT.waitForDeployment();

  console.log("GOATToken:    ", await GoatToken.getAddress());
  console.log("LegacyNFT:    ", await LegacyNFT.getAddress());
  console.log("FlashCardNFT: ", await FlashCardNFT.getAddress());
}

main();
```

Copia las addresses en las variables de entorno de Railway.

---

## App Móvil

### Prerequisitos
```bash
pip install -r requirements.txt
# Android: instalar Flutter SDK + Android Studio
# iOS: instalar Xcode (solo macOS)
```

### Desarrollo local
```bash
# Arranca el backend primero:
make backend

# En otra terminal, la app en modo escritorio:
GOAT_API_URL=http://localhost:8000 make mobile
```

### Build Android (APK)
```bash
GOAT_API_URL=https://TU-APP.railway.app make android
# → build/android/GOAT Arc.apk
```

### Build Web (desplegable en Vercel/Netlify)
```bash
GOAT_API_URL=https://TU-APP.railway.app make web
# → build/web/ (carpeta lista para servir)
```
