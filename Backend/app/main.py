# recruiter-platform/backend/app/main.py
import logging
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .services.auth import oauth 
from .routers import (
    auth, health, me, orgs, superadmin, 
    favorites, upload, roles, search
)

# --- Setup Logger ---
logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Recruiter Platform API",
    description="API for the multi-tenant recruiter platform.",
    version="0.1.0",
)

# --- CORS Middleware Configuration ---
origins = [
    settings.FRONT_END_BASE_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SessionMiddleware Configuration (Production & Development) ---
logger.info(f"Checking APP_ENV: '{settings.APP_ENV}'")
if settings.APP_ENV == "prod":
    logger.info("✅ RUNNING IN PRODUCTION MODE (prod)")
    logger.info("✅ Setting SessionMiddleware with secure=True and same_site='none'")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        same_site="none",
        secure=True  # <-- THIS IS THE FINAL FIX: Force the Secure flag
    )
else:
    logger.warning(f"⚠️ RUNNING IN DEVELOPMENT MODE (APP_ENV={settings.APP_ENV})")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY
    )

# --- Configure OAuth *AFTER* SessionMiddleware ---
logger.info("Registering Google OAuth client...")
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
logger.info("Google OAuth client registered.")


# --- API Routers ---
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(upload.router)
app.include_router(orgs.router)
app.include_router(superadmin.router, prefix="/superadmin", tags=["Super Admin"])
app.include_router(favorites.router, tags=["Favorites"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"])