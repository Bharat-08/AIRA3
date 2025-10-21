# backend/app/routers/favorites.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.security.deps import require_user
from app.models.candidate import RankedCandidate, RankedCandidateFromResume

router = APIRouter(prefix="/favorites", tags=["Favorites"])


# ----------------------------
# Request Schema
# ----------------------------
class FavoriteToggleRequest(BaseModel):
    """
    Request body schema for toggling a candidate's favorite status.
    - candidate_id: UUID of the candidate (profile_id or resume_id)
    - source: Determines which table to update
    - favorite: New boolean value
    """
    candidate_id: str
    source: Literal["ranked_candidates", "ranked_candidates_from_resume"]
    favorite: bool


# ----------------------------
# Toggle Favorite Endpoint
# ----------------------------
@router.post("/toggle", status_code=status.HTTP_200_OK)
def toggle_favorite(
    body: FavoriteToggleRequest,
    db: Session = Depends(get_db),
    ctx: dict = Depends(require_user),
):
    """
    Toggle or update the favorite flag for a candidate in either
    ranked_candidates or ranked_candidates_from_resume table.
    """

    user = ctx.get("user")
    membership = ctx.get("membership")

    model = (
        RankedCandidate
        if body.source == "ranked_candidates"
        else RankedCandidateFromResume
    )

    filter_column = (
        model.profile_id if body.source == "ranked_candidates" else model.resume_id
    )

    try:
        candidate = db.query(model).filter(filter_column == body.candidate_id).first()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found in {body.source}.",
            )

        candidate.favorite = bool(body.favorite)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        return {
            "message": "Favorite status updated successfully.",
            "candidate_id": body.candidate_id,
            "favorite": candidate.favorite,
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while toggling favorite: {str(e)}",
        )


# ----------------------------
# Fetch Favorites for JD (Optional)
# ----------------------------
@router.get("/{jd_id}", status_code=status.HTTP_200_OK)
def get_favorited_candidates(
    jd_id: str,
    db: Session = Depends(get_db),
    ctx: dict = Depends(require_user),
):
    """
    Retrieve all candidates marked as favorite for a specific JD
    from both ranked tables.
    """

    user = ctx.get("user")

    try:
        favorites_from_search = (
            db.query(RankedCandidate)
            .filter(RankedCandidate.jd_id == jd_id, RankedCandidate.favorite.is_(True))
            .all()
        )

        favorites_from_resume = (
            db.query(RankedCandidateFromResume)
            .filter(
                RankedCandidateFromResume.jd_id == jd_id,
                RankedCandidateFromResume.favorite.is_(True),
            )
            .all()
        )

        return {
            "jd_id": jd_id,
            "favorites": {
                "search": favorites_from_search,
                "resume": favorites_from_resume,
            },
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching favorites: {str(e)}",
        )
