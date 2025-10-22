# recruiter-platform/backend/app/main.py
import logging
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware  # <-- 1. IMPORT THIS

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

# --- NEW FIX: Add ProxyHeadersMiddleware FIRST ---
# This forces the app to respect X-Forwarded-Proto (https)
# *before* any other middleware runs.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
# --- END OF NEW FIX ---


# --- CORS Middleware Configuration ---
origins = [
    settings.FRONTEND_BASE_URL,  # <-- This was the typo I fixed
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
    logger.info("✅ Setting SessionMiddleware with https_only=True and same_site='none'")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        same_site="none",
        https_only=True  # <-- This is the CORRECT argument, not 'secure'
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