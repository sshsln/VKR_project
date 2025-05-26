from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.crud import get_all_clubs, get_club_by_id
from app.schemas import ClubBase, ClubResponse, Message, ClubUpdate, ClubAdmin

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("/", response_model=List[ClubResponse])
async def get_clubs(
    session: SessionDep,
    current_user: CurrentUser
):
    include_archived = current_user.is_superuser
    clubs = get_all_clubs(session, include_archived=include_archived)
    return clubs


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    club = get_club_by_id(session, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if not club.is_available and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Club is archived and not accessible")
    return club


@router.post("", response_model=ClubResponse, dependencies=[Depends(get_current_active_superuser)])
async def create_club(
    club_in: ClubBase,
    session: SessionDep
):
    club = crud.create_club(session, club_in)
    return club


@router.patch("/{club_id}", response_model=ClubAdmin, dependencies=[Depends(get_current_active_superuser)])
async def update_club(
    club_id: UUID,
    club_in: ClubUpdate,
    session: SessionDep
):
    club = crud.update_club(session, club_id, club_in)
    return club


@router.patch("/{club_id}/archive", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def archive_club(
    club_id: UUID,
    session: SessionDep
):
    crud.archive_club(session, club_id)
    return Message(message="Club archived successfully")


@router.patch("/{club_id}/activate", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def activate_club(
    club_id: UUID,
    session: SessionDep
):
    crud.activate_club(session, club_id)
    return Message(message="Club activated successfully")


@router.delete("/{club_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def delete_club(
    club_id: UUID,
    session: SessionDep
):
    crud.delete_club(session, club_id)
    return Message(message="Club deleted successfully")
