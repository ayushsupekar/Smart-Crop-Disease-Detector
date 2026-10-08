import os
import json
import logging
from time import perf_counter
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine, SessionLocal, get_db
from app.models.disease import DiseaseInfo
from app.models.user import User
from app.models.scan import Scan
from app.ml.fruit_model import fruit_classifier
from app.utils.security import get_password_hash
from app.utils.file_storage import ensure_upload_dir
from app.routes import auth, scans, crops, analytics

ensure_upload_dir()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgroScan: AI-powered Crop Health & Disease Diagnostic Platform REST API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_prediction_request_ids(request: Request, call_next):
    if request.url.path not in {"/api/scans/predict", "/scans/predict"}:
        return await call_next(request)

    cf_ray = request.headers.get("cf-ray", "-")
    rndr_id = request.headers.get("rndr-id", "-")
    started_at = perf_counter()
    logger.info(
        "Prediction HTTP request received method=%s path=%s cf_ray=%s rndr_id=%s",
        request.method,
        request.url.path,
        cf_ray,
        rndr_id,
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Prediction HTTP request raised method=%s path=%s duration_ms=%.1f cf_ray=%s rndr_id=%s",
            request.method,
            request.url.path,
            (perf_counter() - started_at) * 1000,
            cf_ray,
            rndr_id,
        )
        raise

    logger.info(
        "Prediction HTTP response method=%s path=%s status=%s duration_ms=%.1f cf_ray=%s rndr_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started_at) * 1000,
        cf_ray,
        rndr_id,
    )
    return response

# Mount upload directory for static leaf images
upload_dir_path = Path(settings.UPLOAD_DIR).resolve()
upload_dir_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.STATIC_URL_PREFIX, StaticFiles(directory=str(upload_dir_path)), name="uploads")

# Include Routers with both /api/ prefix and root prefix as requested in prompt
app.include_router(auth.router, prefix="/api/auth")
app.include_router(auth.router, prefix="/auth")

app.include_router(scans.router, prefix="/api/scans")
app.include_router(scans.router, prefix="/scans")

app.include_router(crops.router, prefix="/api/crops")
app.include_router(crops.router, prefix="/crops")

app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(analytics.router, prefix="/analytics")

@app.on_event("startup")
def startup_populate_seed():
    """Create tables and seed demo data on the first application startup."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Upsert disease reference data so new classes are added on existing deployments.
        seed_file = Path(__file__).parent / "app" / "data" / "disease_seed.json"
        if seed_file.exists():
            with open(seed_file, "r", encoding="utf-8") as f:
                disease_data = json.load(f)
            for item in disease_data:
                disease = db.query(DiseaseInfo).filter(
                    DiseaseInfo.class_id == item["class_id"]
                ).first()
                values = {
                    "class_id": item["class_id"],
                    "crop_name": item["crop_name"],
                    "disease_name": item["disease_name"],
                    "scientific_name": item.get("scientific_name"),
                    "description": item["description"],
                    "causes": item["causes"],
                    "symptoms": item["symptoms"],
                    "severity": item["severity"],
                    "organic_treatment": item["organic_treatment"],
                    "chemical_treatment": item["chemical_treatment"],
                    "prevention": item["prevention"],
                    "sample_image_url": item.get("sample_image_url"),
                }
                if disease:
                    for key, value in values.items():
                        setattr(disease, key, value)
                else:
                    db.add(DiseaseInfo(**values))
            db.commit()
            print(f"[AgroScan Startup] Upserted {len(disease_data)} crop disease reference records.")

        if not settings.SEED_DEMO_DATA:
            return

        # Seed Demo User
        demo_user = db.query(User).filter(User.email == "farmer@agroscan.com").first()
        if not demo_user:
            demo_user = User(
                full_name="Dr. Elena Vance",
                email="farmer@agroscan.com",
                hashed_password=get_password_hash("AgroScan2025!"),
                farm_name="Verdant Valley Orchards",
                farm_location="Salinas Valley, CA"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print("[AgroScan Startup] Created default demo user: farmer@agroscan.com / AgroScan2025!")

        # Seed Sample Historical Scans for instant demoability
        scan_count = db.query(Scan).count()
        if scan_count == 0:
            sample_scans = [
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69109853?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "tomato_field_south.jpg",
                    "crop_name": "Tomato",
                    "disease_name": "Late Blight",
                    "class_id": "Tomato___Late_blight",
                    "confidence": 97.4,
                    "severity": "Critical",
                    "field_location": "Field Zone A - Greenhouse 2",
                    "notes": "Spotted water-soaked margins after continuous overnight misting."
                },
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "sweet_corn_plot4.jpg",
                    "crop_name": "Corn (Maize)",
                    "disease_name": "Common Rust",
                    "class_id": "Corn_(maize)___Common_rust_",
                    "confidence": 94.2,
                    "severity": "Moderate",
                    "field_location": "Field Zone C - East Acre",
                    "notes": "Cinnamon pustules starting on lower leaves; sulfur spray queued."
                },
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "potato_canopy_north.jpg",
                    "crop_name": "Potato",
                    "disease_name": "Healthy",
                    "class_id": "Potato___healthy",
                    "confidence": 98.9,
                    "severity": "Healthy",
                    "field_location": "Field Zone B - Row 12",
                    "notes": "Routine weekly scouting. Optimal turgor and dark green coloration."
                },
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1590005354167-6da97870c757?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "bell_pepper_seedling.jpg",
                    "crop_name": "Bell Pepper",
                    "disease_name": "Bacterial Spot",
                    "class_id": "Pepper,_bell___Bacterial_spot",
                    "confidence": 93.1,
                    "severity": "High",
                    "field_location": "Field Zone A - High Tunnel",
                    "notes": "Observed water-soaked specks with yellow chlorotic halos."
                },
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "honeycrisp_apple_spur.jpg",
                    "crop_name": "Apple",
                    "disease_name": "Apple Scab",
                    "class_id": "Apple___Apple_scab",
                    "confidence": 96.0,
                    "severity": "High",
                    "field_location": "Orchard Block 7",
                    "notes": "Velvety dark spots on foliage. Pruned surrounding branches."
                },
                {
                    "user_id": demo_user.id,
                    "image_url": "https://images.unsplash.com/photo-1533038590840-1cde6e668a91?auto=format&fit=crop&w=600&q=80",
                    "original_filename": "grape_vineyard_block2.jpg",
                    "crop_name": "Grape",
                    "disease_name": "Healthy",
                    "class_id": "Grape___healthy",
                    "confidence": 99.1,
                    "severity": "Healthy",
                    "field_location": "Vineyard Hillside Slope",
                    "notes": "Post-flowering canopy check; vigorous tendril expansion."
                }
            ]
            for s in sample_scans:
                scan = Scan(**s)
                db.add(scan)
            db.commit()
            print(f"[AgroScan Startup] Seeded {len(sample_scans)} demo scan records.")

    finally:
        db.close()
        try:
            fruit_classifier.load()
        except Exception:
            logger.exception("Fruit classifier warm-up failed; fruit predictions may be unavailable.")

@app.get("/")
def health_check():
    return {
        "status": "online",
        "app": "AgroScan API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "message": "AI-Powered Crop Disease Diagnostic System Ready"
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not ready") from error
    return {
        "status": "ready",
        "database": engine.dialect.name,
        "database_persistent": engine.dialect.name != "sqlite",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
