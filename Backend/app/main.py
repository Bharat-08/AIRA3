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

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Recruiter Platform API",
    description="API for the multi-tenant recruiter platform.",
    version="0.1.0",
)

# 1) Honor X-Forwarded-* so scheme=HTTPS is detected behind Render
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 2) CORS: explicitly include your prod frontend origin, plus localhost
#    Do not rely solely on FRONTEND_BASE_URL for this.
PROD_FRONTEND = "https://aira3-frontend.onrender.com"
LOCAL_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
ALLOWED_ORIGINS = {PROD_FRONTEND, settings.FRONTEND_BASE_URL, *LOCAL_ORIGINS}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) Sessions
logger.info("Checking APP_ENV: '%s'", settings.APP_ENV)
if settings.APP_ENV == "prod":
    logger.info("✅ RUNNING IN PRODUCTION MODE (prod)")
    logger.info("✅ SessionMiddleware: https_only=True, same_site='none'")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        session_cookie="session",
        same_site="none",     # required for cross-site OAuth redirects
        https_only=True,      # sets Secure
        # no explicit domain -> cookie is scoped to aira3.onrender.com
    )
else:
    logger.warning("⚠️ RUNNING IN DEVELOPMENT MODE (APP_ENV=%s)", settings.APP_ENV)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        session_cookie="session",
        same_site="lax",
        https_only=False,
    )

logger.info("Session secret present: %s", bool(settings.SESSION_SECRET_KEY))

# 4) Register Google OAuth AFTER SessionMiddleware
logger.info("Registering Google OAuth client...")
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
logger.info("Google OAuth client registered.")

# 5) Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(upload.router)
app.include_router(orgs.router)
app.include_router(superadmin.router, prefix="/superadmin", tags=["Super Admin"])
app.include_router(favorites.router, tags=["Favorites"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"])
