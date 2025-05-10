from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.crud import get_all_lenses, get_lens_by_id
from app.schemas import LensBase, LensResponse, Message, LensUpdate

router = APIRouter(prefix="/lenses", tags=["lenses"])


@router.get("/", response_model=List[LensResponse])
async def get_lenses(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    club_id: UUID | None = None
):
    include_archived = current_user.is_superuser
    lenses = get_all_lenses(session, include_archived=include_archived, club_id=club_id)
    return lenses[skip:skip + limit]


@router.get("/{lens_id}", response_model=LensResponse)
async def get_lens(
    lens_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    lens = get_lens_by_id(session, lens_id)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    if not lens.is_available and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Lens is archived and not accessible")
    return lens


@router.post("/", response_model=LensResponse, dependencies=[Depends(get_current_active_superuser)])
async def create_lens(
    lens_in: LensBase,
    session: SessionDep
):
    lens = crud.create_lens(session, lens_in)
    return lens


@router.patch("/{lens_id}", response_model=LensResponse, dependencies=[Depends(get_current_active_superuser)])
async def update_lens(
    lens_id: UUID,
    lens_in: LensUpdate,
    session: SessionDep
):
    lens = crud.update_lens(session, lens_id, lens_in)
    return lens


@router.patch("/{lens_id}/archive", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def archive_lens(
    lens_id: UUID,
    session: SessionDep
):
    crud.archive_lens(session, lens_id)
    return Message(message="Lens archived successfully")


@router.delete("/{lens_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def delete_lens(
    lens_id: UUID,
    session: SessionDep
):
    crud.delete_lens(session, lens_id)
    return Message(message="Lens deleted successfully")
