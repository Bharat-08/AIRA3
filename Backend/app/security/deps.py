# In backend/app/security/deps.py

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.membership import Membership

# --- THIS IS THE FIX ---
# The function in jwt.py is named 'decode_jwt', not 'verify_jwt'.
from .jwt import decode_jwt
# --- END OF FIX ---

def get_current_session(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        # --- AND THIS IS THE CORRESPONDING CHANGE ---
        # Call 'decode_jwt' here
        claims = decode_jwt(token)
        # --- END OF CHANGE ---
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return claims

def require_user(claims=Depends(get_current_session), db: Session = Depends(get_db)):
    user = db.get(User, claims["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    membership = db.query(Membership).filter(
        Membership.user_id==claims["sub"], Membership.org_id==claims["org_id"]
    ).one_or_none()
    
    return {"claims": claims, "user": user, "membership": membership}

# --- NEW FUNCTION TO SOLVE THE IMPORT ERROR ---
def get_current_user(ctx=Depends(require_user)) -> User:
    """
    Depends on require_user and returns just the User model instance.
    This is what your API endpoints should use for type-hinting the current user.
    """
    return ctx["user"]

def require_admin(ctx=Depends(require_user)):
    if not ctx["membership"] or ctx["membership"].role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return ctx

def require_superadmin(ctx=Depends(require_user)):
    if not ctx["user"].is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return ctx