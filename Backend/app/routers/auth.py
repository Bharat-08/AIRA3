# recruiter-platform/backend/app/routers/auth.py

from fastapi import APIRouter, Depends, Request, Response, HTTPException
from starlette.responses import RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import MismatchingStateError

from ..db.session import get_db
from ..services.auth import oauth, provision_via_invite
from ..security.jwt import issue_jwt, set_jwt_cookie, clear_jwt_cookie
from ..config import settings  # already used elsewhere

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google/login")
async def google_login(request: Request):
    """
    Start Google OAuth flow: redirect user to Google.
    Debug prints added to inspect incoming headers/cookies/session.
    """
    print("\n=== GOOGLE LOGIN START ===")
    # Show the incoming request headers (useful when a reverse proxy may alter them)
    print("Incoming request headers:", dict(request.headers))
    # Show cookies sent with the request (should normally be empty for login start)
    print("Incoming request.cookies:", request.cookies)
    # Show session content on the server before redirect (Authlib stores 'state' here)
    try:
        session_snapshot = dict(request.session)
    except Exception as e:
        session_snapshot = f"<error reading session: {e}>"
    print("Session BEFORE redirect:", session_snapshot)

    redirect_uri = settings.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google OAuth callback handler.
    Debug prints added to inspect query params, headers, cookies and session.
    Defensive handling for MismatchingStateError is included.
    """
    print("\n=== GOOGLE CALLBACK ===")
    # Query params include "state" and "code" from Google
    print("Query params:", dict(request.query_params))

    # Show the incoming request headers (important to see Cookie header present)
    print("Incoming request headers:", dict(request.headers))

    # Show cookies present on the request
    print("Incoming request.cookies:", request.cookies)

    # Show server session contents at callback time
    try:
        session_snapshot = dict(request.session)
    except Exception as e:
        session_snapshot = f"<error reading session: {e}>"
    print("Session AT callback:", session_snapshot)

    # Try to authorize and catch MismatchingStateError for clearer logs
    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError as mse:
        # Important debug info to collect when state mismatch occurs
        print("MismatchingStateError caught:", repr(mse))
        print("CALLBACK DEBUG: query state:", request.query_params.get("state"))
        print("CALLBACK DEBUG: session contents:", session_snapshot)
        print("CALLBACK DEBUG: cookie header:", request.headers.get("cookie"))
        # Return friendly response
        return PlainTextResponse(
            "Error: state mismatch (CSRF suspected). Try logging in again.",
            status_code=400
        )
    except Exception as e:
        # Log other unexpected errors and re-raise so they appear in the app logs
        print("authorize_access_token raised unexpected error:", repr(e))
        raise

    # If token is present, get userinfo (Authlib places 'userinfo' into token for OpenID)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not retrieve user info from Google.")

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google profile is missing an email address.")

    # Extract fields from Google profile
    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    # Provision or update user, create membership as required
    user, org, membership = provision_via_invite(
        db,
        email=email,
        name=name,
        avatar_url=avatar_url
    )

    # Issue JWT and set cookie, then redirect to frontend landing/dashboard
    access_token = issue_jwt(
        sub=str(user.id),
        org_id=str(membership.org_id),
        role=membership.role
    )

    redirect_url = f"{settings.FRONTEND_BASE_URL}/RecruiterDashboardPage"
    response = RedirectResponse(url=redirect_url)
    set_jwt_cookie(response, access_token)
    return response


@router.post("/logout")
def logout():
    """
    Logs the user out by clearing their session/cookie.
    """
    response = Response(status_code=204)
    clear_jwt_cookie(response)
    return response
