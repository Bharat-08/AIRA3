# in backend/app/routers/auth.py

from fastapi import APIRouter, Depends, Request, Response, HTTPException
from starlette.responses import RedirectResponse, PlainTextResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import MismatchingStateError

from ..db.session import get_db
from ..services.auth import oauth, provision_via_invite
from ..security.jwt import issue_jwt, set_jwt_cookie, clear_jwt_cookie
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google/login")
async def google_login(request: Request):
    print("\n=== GOOGLE LOGIN START ===")
    print("Incoming request headers:", dict(request.headers))
    print("Incoming request.cookies:", request.cookies)
    try:
        print("Session BEFORE redirect:", dict(request.session))
    except Exception as e:
        print("Session BEFORE redirect: <error reading session>", e)

    redirect_uri = settings.OAUTH_REDIRECT_URI
    # NOTE: prefer top-level navigation on frontend (window.location.href = backend + '/auth/google/login')
    return await oauth.google.authorize_redirect(request, redirect_uri)


# Use api_route so we can accept GET and HEAD explicitly
@router.api_route("/google/callback", methods=["GET", "HEAD"])
async def google_callback(request: Request, db: Session = Depends(get_db)):
    # If it's a HEAD request (probes), just respond 200 quickly
    if request.method == "HEAD":
        print("Received HEAD probe on /auth/google/callback — returning 200")
        return Response(status_code=200)

    print("\n=== GOOGLE CALLBACK ===")
    print("Request method:", request.method)
    print("Query params:", dict(request.query_params))
    print("Incoming request headers:", dict(request.headers))
    print("Incoming request.cookies:", request.cookies)
    try:
        print("Session AT callback:", dict(request.session))
    except Exception as e:
        print("Session AT callback: <error reading session>", e)

    # Attempt authorization and handle state mismatches gracefully
    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError as mse:
        # Log the diagnostic details that matter
        print("MismatchingStateError caught:", repr(mse))
        print("CALLBACK DEBUG: query state:", request.query_params.get("state"))
        try:
            print("CALLBACK DEBUG: session contents:", dict(request.session))
        except Exception:
            print("CALLBACK DEBUG: session contents: <error reading session>")
        print("CALLBACK DEBUG: cookie header:", request.headers.get("cookie"))

        # Redirect user to restart login (friendly fallback)
        # Could also render a page instructing user to retry.
        retry_url = f"{settings.FRONTEND_BASE_URL}/login?error=state_mismatch"
        return RedirectResponse(url=retry_url, status_code=302)

    except Exception as e:
        print("authorize_access_token raised unexpected error:", repr(e))
        raise

    # Normal successful flow below
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not retrieve user info from Google.")

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google profile is missing an email address.")

    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    user, org, membership = provision_via_invite(
        db,
        email=email,
        name=name,
        avatar_url=avatar_url
    )

    access_token = issue_jwt(
        sub=str(user.id),
        org_id=str(membership.org_id),
        role=membership.role
    )

    redirect_url = f"{settings.FRONTEND_BASE_URL}/RecruiterDashboardPage"
    response = RedirectResponse(url=redirect_url)
    set_jwt_cookie(response, access_token)
    return response
