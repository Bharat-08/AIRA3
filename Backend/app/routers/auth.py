import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import MismatchingStateError

from ..services.auth import oauth, provision_via_invite
from ..config import settings
from ..db.session import get_db
from ..security.jwt import create_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auth/google/login", tags=["Auth"])
async def google_login(request: Request, redirect_url: str | None = None):
    """
    Initiate Google OAuth login.
    """
    print("\n=== GOOGLE LOGIN START ===")
    # The debug print you added - you can leave or remove this
    print(f"DEBUG: Request scheme: {request.url.scheme}")
    
    print(f"Incoming request headers: {dict(request.headers)}")
    print(f"Incoming request.cookies: {request.cookies}")

    # Store redirect_url in session if provided
    if redirect_url:
        request.session["redirect_url"] = redirect_url
    else:
        # Clear any old redirect_url
        request.session.pop("redirect_url", None)

    # Check if user is already authenticated
    if "access_token" in request.session:
        # If already logged in, redirect to frontend dashboard
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/RecruiterDashboardPage")

    print(f"Session BEFORE redirect (after write): {request.session}")
    print("✅ Session modification forced, response will include Set-Cookie.")
    
    # This forces the session to be saved even if it's new
    request.session.update({"init": True})

    redirect_uri = settings.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


#
# --- THIS IS THE FIX ---
# We are adding a second route handler for the URL with the trailing slash
# that Render's proxy is forcing. Both routes point to the *same function*.
#
@router.get("/auth/google/callback", include_in_schema=False)
@router.get("/auth/google/callback/", include_in_schema=False) # <-- ADD THIS LINE
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    """
    print("\n=== GOOGLE CALLBACK ===")
    print(f"Request method: {request.method}")
    print(f"Query params: {request.query_params}")
    print(f"Incoming request headers: {dict(request.headers)}")
    print(f"Incoming request.cookies: {request.cookies}")
    print(f"Session AT callback: {request.session}")

    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError as e:
        logger.error(f"MismatchingStateError caught: {e}")
        print(f"MismatchingStateError caught: <{e}>")
        print(f"CALLBACK DEBUG: query state: {request.query_params.get('state')}")
        print(f"CALLBACK DEBUG: session contents: {request.session}")
        print(f"CALLBACK DEBUG: cookie header: {request.headers.get('cookie')}")
        # Redirect to frontend login page with error
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/login?error=state_mismatch")
    except Exception as e:
        logger.error(f"Error authorizing access token: {e}")
        print(f"Error authorizing access token: <{e}>")
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/login?error=auth_failed")

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user info")

    email = user_info.get("email")
    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found in user info")

    try:
        user, organization, membership = provision_via_invite(
            db=db,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
    except HTTPException as e:
        # This will catch the "No valid invitation" error
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/login?error={e.detail}")

    # Create access token (JWT)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": membership.role,
            "org_id": str(organization.id),
            "is_superadmin": user.is_superadmin,
        }
    )

    # Store token and user info in the session (server-side)
    request.session["access_token"] = access_token
    request.session["user"] = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "role": membership.role,
        "org_id": str(organization.id),
        "is_superadmin": user.is_superadmin,
    }

    print(f"✅ User {user.email} authenticated successfully.")
    print(f"Session AFTER auth: {request.session}")
    
    # Check for a stored redirect_url
    redirect_url = request.session.pop("redirect_url", None)
    if redirect_url:
        # Note: This is a simple redirect. For robustness, you'd validate this URL.
        return RedirectResponse(url=redirect_url)

    # Redirect to the main frontend app
    return RedirectResponse(url=settings.FRONTEND_BASE_URL)