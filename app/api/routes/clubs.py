from fastapi import APIRouter
from app.api.deps import SessionDep, SuperUser
from app.crud import get_all_clubs
from app.models import ClubResponse
from typing import List

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("/", response_model=List[ClubResponse])
async def get_clubs(
    session: SessionDep,
    current_user: SuperUser
):
    clubs = get_all_clubs(session)
    return clubs
