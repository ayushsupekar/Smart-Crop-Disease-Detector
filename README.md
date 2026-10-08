# AgroScan — Smart Crop Disease Detector & Agricultural Health Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg?style=flat&logo=Vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![MobileNetV2](https://img.shields.io/badge/AI_Model-MobileNetV2_Transfer_Learning-FF6F00.svg?style=flat&logo=tensorflow&logoColor=white)](https://tensorflow.org)

**AgroScan** is a production-grade full-stack precision agriculture web application. It enables farmers, agronomists, and agricultural enterprises to photograph or upload crop foliage, execute convolutional neural network (CNN) pathology diagnostics, and immediately receive detailed clinical assessments including disease classification, confidence ratings, etiology, visual symptoms, and both **OMRI-certified organic** and **conventional chemical treatment protocols**.

---

## Key Features

1. **AgroControl Minimalist SaaS Aesthetic:**
   - Curated palette: Deep forest charcoal (`#14251B`), muted sage green (`#7C8B6B`), and off-white (`#FAFAFA`).
   - Clean typography with tight tracking, generous padding, soft rounded corners (12–16px), and subtle elevations.
2. **Dual-Intake Diagnostic Studio:**
   - Drag-and-drop leaf image uploader with quick one-click demo presets (Tomato Late Blight, Potato Early Blight, Corn Rust, Healthy foliage).
   - Real-time HTML5 camera capture with targeting reticle and camera switching (rear/front).
   - Multi-stage holographic scanning line animation simulating tensor preprocessing and neural feature evaluation.
3. **Clinical Actionable Diagnostic Reports:**
   - PlantVillage pathology classes across high-impact crops (Tomato, Potato, Corn, Apple, Grape, Bell Pepper).
   - Confidence percentage meter with probability distribution breakdown.
   - Color-coded severity badges (Healthy, Low, Moderate, High, Critical).
   - Dual treatment protocols:
     - **Organic / Biological:** Copper fungicides, *Bacillus subtilis*, neem azadirachtin, compost teas.
     - **Chemical / Conventional:** Strobilurins, chlorothalonil, mancozeb, systemic modes of action, pre-harvest safety guidelines.
     - **Preventative Cultural IPM:** Crop rotation, drip irrigation hygiene, airflow spacing.
4. **Interactive Farm Telemetry Dashboard:**
   - KPI Stat Cards: Total Scans, Pathologies Identified, Foliar Health Rate %, Most Affected Crop.
   - Recharts Visualizations: Weekly foliar health trends & crop family distribution.
   - Recent scans table with quick report modal preview.
5. **Historical Scan Log & Encyclopedia:**
   - Filterable scan log with search, crop filtering, severity filtering, and grid/table toggles.
   - Full Crop Library reference encyclopedia with disease profiles and cultural remedies.
6. **Robust Auth & API Architecture:**
   - JWT authentication (`/auth/signup`, `/auth/login`, `/auth/me`) with 1-click Demo Account sign-in.
   - Interactive Swagger API documentation automatically served at `/docs`.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, React Router v7, Tailwind CSS 3.4, Axios, Recharts, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy ORM, Pydantic v2, PyJWT, Passlib, Pillow |
| **AI / ML** | MobileNetV2 (Keras / TFLite) transfer learning with intelligent chromatic vision fallback |
| **Database** | SQLite (zero-config local development) |

---

## Quickstart: Local Development

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create local environment configuration and replace the example secret
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/macOS

# Create and activate virtual environment (optional)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server (auto-reloads on port 8000)
uvicorn main:app --reload --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc API Reference: `http://localhost:8000/redoc`

> **Note:** On first startup, SQLAlchemy creates missing tables. This is not a migration system. Disease reference data is seeded automatically; demo users and sample scans are only created when `SEED_DEMO_DATA=true`.

### Production Deployment: Persistent User and Scan Data

The default `sqlite:///./agroscan.db` database is intended for local development only. Render's service filesystem is ephemeral unless a persistent disk is explicitly attached, and multiple backend instances do not share a local SQLite file. An SQLite database on the default Render filesystem can therefore disappear after a restart or deploy, making accounts and scans appear to be lost. The backend now refuses to start on Render when `DATABASE_URL` is SQLite, rather than silently accepting a database that cannot meet the persistence requirement.

For production, create or use a managed PostgreSQL database and set the backend's `DATABASE_URL` environment variable to its **internal** connection URL. This project uses SQLAlchemy (not MongoDB), includes the PostgreSQL driver, and accepts both `postgres://` and `postgresql://` URLs. Keep the database URL and the same `SECRET_KEY` configured on the backend service across deployments. Switching databases does not automatically copy accounts from an existing SQLite file: preserve/backup the existing database and migrate its users and scans before switching `DATABASE_URL`. Do not delete the old database until the migrated accounts have been verified.

For the Render services described below, configure:

| Service | Setting | Value |
|---|---|---|
| Backend | Root directory | `backend` |
| Backend | Build command | `pip install -r requirements.txt` |
| Backend | Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Backend | `SECRET_KEY` | A stable, randomly generated value with at least 32 characters |
| Backend | `DATABASE_URL` | Connection URL for the persistent PostgreSQL database |
| Backend | `CORS_ORIGINS` | `https://smart-crop-disease-detector-1.onrender.com,http://localhost:5173,http://localhost:3000` |
| Frontend | Root directory | `frontend` |
| Frontend | Build command | `npm ci && npm run build` |
| Frontend | Publish directory | `dist` |
| Frontend | `VITE_API_URL` | `https://smart-crop-disease-detector.onrender.com` |

Vite embeds `VITE_API_URL` at build time, so rebuild/redeploy the frontend after changing it. Keep one Uvicorn worker: each worker loads its own TensorFlow model and increases memory use. The leaf model file is 25 MB and is included in the repository. Fruit training arrays are bundled under `backend/app/ml/fruit_data` so they are available when Render builds the backend with `backend` as its root; the Citrus SVM remains separate from the leaf model. Use persistent storage for `UPLOAD_DIR` if uploaded images must survive backend restarts. The `/readyz` endpoint reports the connected database dialect and whether it is non-SQLite.

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server (runs on port 5173)
npm run dev
```

- Web App: `http://localhost:5173`

---

## Demo Account Credentials

Demo data is disabled by default. Set `SEED_DEMO_DATA=true` in the backend environment before startup to enable this account.

Use the **"Instant Demo Sign-In"** button on the login screen or enter:
- **Email:** `farmer@agroscan.com`
- **Password:** `AgroScan2025!`

---

---

## AI Model: MobileNetV2 Transfer Learning

Inference is modularized in `backend/app/ml/model.py`.

- **Verified pretrained model:** Run `python -m app.ml.download_verify_model` from `backend` to download the Hugging Face MobileNetV2 model and generate its matching `class_indices.json` file. The verifier checks archive integrity, rejects unsafe executable layers, confirms the MobileNetV2 backbone, and requires a 38-unit softmax output.
- **Inference preprocessing:** The model contains its own `[-1, 1]` preprocessing layer. The backend only converts uploads to RGB and resizes them to `224x224`; it does not normalize them a second time.
- **Missing model behavior:** If the verified model file is missing or cannot be loaded, scans return HTTP 503 instead of a heuristic or fabricated diagnosis. Download the verified weights before scanning.
- **Confidence limits:** The displayed model score is a softmax probability, not a calibrated guarantee of diagnostic accuracy. The model card reports 98.75% accuracy on a held-out PlantVillage image set; performance on field photos and unsupported plants can be substantially lower. Confirm results with an agronomist before treatment decisions.
- **Training Script:** You can train your own MobileNetV2 model on the complete PlantVillage dataset using `backend/app/ml/train_mobilenet.py`:
  ```bash
  python app/ml/train_mobilenet.py --data_dir /path/to/PlantVillage --epochs 15 --batch_size 32
  ```

### Fruit Disease Classifier

Choose **Citrus disease** in the scan page before uploading or capturing a citrus fruit photo. This repository does not contain a separate Citrus Keras model: the existing Citrus implementation trains an SVM from the tracked feature arrays bundled in `backend/app/ml/fruit_data/`. The classifier is warmed once during backend startup, moving training time out of the first user prediction; a cold backend start takes longer as a result. The class order comes from that project's training script: Black spot, Canker, Greening, Healthy, and Scab. It does not identify fruit species. The supplied project contains only 150 feature samples and no verified treatment reference, so its score is approximate and the app intentionally does not show leaf treatment advice for fruit results.

---

## Project Structure

```
smart crop disease/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py                  # FastAPI entrypoint, startup seeder & routes
│   └── app/
│       ├── config.py            # Pydantic settings & CORS configuration
│       ├── database.py          # SQLAlchemy session engine
│       ├── models/              # User, Scan, and DiseaseInfo ORM models
│       ├── schemas/             # Pydantic input/output schemas
│       ├── routes/              # Auth, Scans, Crops, and Analytics REST APIs
│       ├── ml/
│       │   ├── model.py         # Isolated inference engine & singleton loader
│       │   ├── classes.py       # PlantVillage class IDs & parsers
│       │   └── train_mobilenet.py # MobileNetV2 transfer learning training pipeline
│       ├── data/
│       │   └── disease_seed.json# Full agronomic knowledge base & treatments
│       └── utils/
│           ├── security.py      # Bcrypt hashing & PyJWT token handler
│           └── file_storage.py  # Image upload handler
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js       # AgroControl theme tokens & soft shadows
    ├── index.html
    └── src/
        ├── api/                 # Axios client, auth, scans, and crops services
        ├── context/             # React AuthContext (JWT & demo user state)
        ├── components/
        │   ├── common/          # Navbar, Sidebar, StatCard, SeverityBadge, Modal
        │   ├── scan/            # Dropzone, CameraCapture, ScanningAnimation, ResultCard
        │   └── dashboard/       # ScanTrendsChart, DiseaseDistributionChart, RecentScans
        └── pages/
            ├── LandingPage.jsx  # Hero, how it works, feature highlights
            ├── LoginPage.jsx    # Auth login + 1-click demo button
            ├── SignupPage.jsx   # Agronomist registration
            ├── DashboardPage.jsx# SaaS dashboard with KPI metrics & charts
            ├── ScanPage.jsx     # Leaf upload, camera capture & diagnosis
            ├── HistoryPage.jsx  # Searchable scan log with grid/table view
            ├── CropLibraryPage.jsx # Plant disease encyclopedia
            └── SettingsPage.jsx # Farm profile & language preferences
```

---

## License
MIT License. Created for precision agriculture disease prevention.
