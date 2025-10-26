# recruiter-platform/backend/app/main.py
import logging
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.routing import Mount # <-- You might need to import this if not already
from fastapi.staticfiles import StaticFiles # <-- Or this one, but it's likely not needed

from .config import settings
from .services.auth import oauth
from .routers import (
    auth, health, me, orgs, superadmin,
    favorites, upload, roles, search
)

# --- Setup Logger ---
logger = logging.getLogger("uvicorn")


# --- THIS IS THE FIX ---
# By setting redirect_slashes=True, FastAPI will automatically
# handle the trailing slash added by Render.
# A request to /auth/google/callback/ will be correctly
# routed to your /auth/google/callback endpoint.
app = FastAPI(
    title="Recruiter Platform API",
    description="API for the multi-tenant recruiter platform.",
    version="0.1.0",
    redirect_slashes=True, # <-- ADD THIS LINE
)
# --- END OF FIX ---


# --- ProxyHeadersMiddleware FIRST (so X-Forwarded-* are honored early) ---
# Ensures the app correctly detects scheme (https) behind Render/Cloudflare proxies.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# --- CORS Middleware Configuration ---
# Cleaned up the origins list to avoid duplicates/typos
origins = [
    settings.FRONTEND_BASE_URL,
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
        session_cookie="session",
        same_site="none",
        https_only=True,
        # domain="aira3.onrender.com", # <-- This line is correctly removed
    )
else:
    logger.warning(f"⚠️ RUNNING IN DEVELOPMENT MODE (APP_ENV={settings.APP_ENV})")
    # For local dev (http) use https_only=False and safer SameSite
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        session_cookie="session",
        same_site="lax",
        https_only=False,
    )

# Log whether we have a session secret present (do not log the secret itself)
logger.info("Session secret present: %s", bool(settings.SESSION_SECRET_KEY))

#  Configure OAuth *AFTER* SessionMiddleware 
logger.info("Registering Google OAuth client...")
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
logger.info("Google OAuth client registered.")

#  API Routers 
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(upload.router)
app.include_router(orgs.router)
app.include_router(superadmin.router, prefix="/superadmin", tags=["Super Admin"])
app.include_router(favorites.router, tags=["Favorites"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"])