# recruiter-platform/backend/app/main.py
import logging
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

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

# --- ProxyHeadersMiddleware FIRST (so X-Forwarded-* are honored early) ---
# Ensures the app correctly detects scheme (https) behind Render/Cloudflare proxies.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# --- CORS Middleware Configuration ---
origins = [
    settings.FRONTEND_BASE_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "https.aira3-frontend.onrender.com", # <- This had a typo, but let's fix it properly
    "https://aira3-frontend.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    # Let's clean up origins to only be the ones from settings + localhost
    allow_origins=[
        settings.FRONTEND_BASE_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SessionMiddleware Configuration (Production & Development) ---
logger.info(f"Checking APP_ENV: '{settings.APP_ENV}'")
if settings.APP_ENV == "prod":
    logger.info("✅ RUNNING IN PRODUCTION MODE (prod)")
    # --- THIS IS THE FIX ---
    # We are removing the explicit `domain` attribute.
    # This is safer and lets the browser scope the cookie to the request host.
    logger.info("✅ Setting SessionMiddleware with https_only=True and same_site='none'")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        session_cookie="session",
        same_site="none",
        https_only=True,
        # domain="aira3.onrender.com", # <-- THIS LINE IS NOW REMOVED
    )
    # --- END OF FIX ---
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

