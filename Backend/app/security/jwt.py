# In Backend/app/security/jwt.py

import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Request, Response, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from sqlalchemy.orm import Session

from ..config import settings
from ..db.session import get_db
from ..models.user import User
from ..models.membership import Membership

ALGORITHM = settings.JWT_ALGORITHM
PRIVATE_KEY = settings.JWT_PRIVATE_KEY
PUBLIC_KEY = settings.JWT_PUBLIC_KEY
EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES


def issue_jwt(sub: str, org_id: str, role: str) -> str:
    """
    Generates a new RS256 JWT token.
    """
    if not PRIVATE_KEY:
        raise ValueError("JWT_PRIVATE_KEY is not set.")
    
    now = datetime.now(timezone.utc)
    payload = {
        "iat": now,
        "exp": now + timedelta(minutes=EXPIRATION_MINUTES),
        "sub": sub,
        "org_id": org_id,
        "role": role,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str):
    """
    Decodes and validates an RS256 JWT token.
    """
    if not PUBLIC_KEY:
        raise ValueError("JWT_PUBLIC_KEY is not set.")
    
    try:
        decoded = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub"]}
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")


def set_jwt_cookie(response: Response, token: str):
    """
    Attaches the JWT as an HttpOnly, samesite=none, secure cookie to the response.
    """
    
    # --- THIS IS THE FIX ---
    # The parameter is 'max_age' (for seconds), not 'expires_in'.
    #
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="none", 
        secure=settings.APP_ENV == "prod", 
        max_age=settings.JWT_EXPIRATION_MINUTES * 60, # <-- Changed 'expires_in' to 'max_age'
    )
    # --- END OF FIX ---


def clear_jwt_cookie(response: Response):
    """
    Clears the JWT cookie.
    """
    # This function is correct as-is
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite="none", 
        secure=settings.APP_ENV == "prod",
    )


def get_jwt_from_cookie(request: Request) -> str | None:
    """
    Extracts the JWT token from the request's cookies.
    """
    return request.cookies.get(settings.COOKIE_NAME)


def get_user_from_jwt(token: str, db: Session) -> (User, Membership):
    """
    Helper function to get user and membership from DB based on JWT payload.
    """
    try:
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        
        if not user_id or not org_id:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="User not found")
        
        membership = db.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.org_id == org_id
        ).first()

        if not membership:
             raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="User membership not found")

        return user, membership

    except HTTPException as e:
        # Re-raise HTTP exceptions from decode_jwt
        raise e
    except Exception as e:
        print(f"Unexpected error in get_user_from_jwt: {e}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")