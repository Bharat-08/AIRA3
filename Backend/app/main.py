# recruiter-platform/backend/app/main.py

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, health, me, orgs, superadmin, favorites, upload, roles, search

app = FastAPI(
    title="Recruiter Platform API",
    description="API for the multi-tenant recruiter platform.",
    version="0.1.0",
)

# --- CORS Middleware Configuration ---
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
# This is the fix to solve the MismatchingStateError
if settings.APP_ENV == "prod":
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        https_only=True,  # Enforce HTTPS for production
        same_site="none"  # Required for cross-domain OAuth redirects
    )
else:
    # Default settings for local development (http://localhost)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY
    )
# --- End of Fix ---


# --- API Routers ---
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(upload.router)
app.include_router(orgs.router)
app.include_router(superadmin.router, prefix="/superadmin", tags=["Super Admin"])
app.include_router(favorites.router, tags=["Favorites"])
app.include_router(search.router, prefix="/search", tags=["Search"])

# The roles router is now included, activating all its endpoints.
app.include_router(roles.router, prefix="/roles", tags=["Roles"])
