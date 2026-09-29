# Render Deployment — HexaMinds SIH 2026

## 1. Push this project to GitHub

Upload the contents of this folder to a GitHub repository. Do not commit real device passwords, API keys, or production secrets.

## 2. Deploy on Render

### Option A — Blueprint

In Render, create a **New Blueprint Instance** and select the repository. Render will read `render.yaml`.

### Option B — Web Service

Use:

- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
- **Health Check Path:** `/api/health`

## 3. Environment variables

Set these in Render:

- `FLASK_SECRET_KEY` — Render can generate this automatically when using `render.yaml`.
- `APP_USERNAME` — the administrator login username.
- `APP_PASSWORD` — choose a strong password for the hosted demo.
- `GEMINI_API_KEY` — optional; only needed for the AI enrichment path.

Do not put these values in source code.

## 4. Important live-device limitation

The hosted dashboard and configuration-file audit can run on Render. The live pfSense SSH workflow requires the Render service to have network reachability to the target device. A private address such as `10.x.x.x` inside a local lab/network is not directly reachable from a public Render service without an appropriate VPN/private-network/tunnel arrangement.

## 5. SIH demo recommendation

For the screening demo, use the configuration-file audit as the guaranteed cloud path. Use the live pfSense path only when the hosted service has verified network connectivity to the lab device.

## 6. Quick verification

After deployment, open:

`https://YOUR-RENDER-DOMAIN/api/health`

Expected response:

```json
{"status":"ok","service":"hexaminds"}
```

Then open the root URL and log in with the Render-configured administrator credentials.
