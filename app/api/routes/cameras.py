from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.crud import get_all_cameras, get_camera_by_id
from app.schemas import CameraBase, CameraResponse, Message, CameraUpdate, CameraAdmin

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/", response_model=List[CameraResponse])
async def get_cameras(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    club_id: UUID | None = None
):
    include_archived = current_user.is_superuser
    cameras = get_all_cameras(session, include_archived=include_archived, club_id=club_id)
    return cameras[skip:skip + limit]


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    camera = get_camera_by_id(session, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.is_available and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Camera is archived and not accessible")
    return camera


@router.post("/", response_model=CameraResponse, dependencies=[Depends(get_current_active_superuser)])
async def create_camera(
    camera_in: CameraBase,
    session: SessionDep
):
    camera = crud.create_camera(session, camera_in)
    return camera


@router.patch("/{camera_id}", response_model=CameraAdmin, dependencies=[Depends(get_current_active_superuser)])
async def update_camera(
    camera_id: UUID,
    camera_in: CameraUpdate,
    session: SessionDep
):
    camera = crud.update_camera(session, camera_id, camera_in)
    return camera


@router.patch("/{camera_id}/archive", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def archive_camera(
    camera_id: UUID,
    session: SessionDep
):
    crud.archive_camera(session, camera_id)
    return Message(message="Camera archived successfully")


@router.patch("/{camera_id}/activate", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def activate_camera(
    camera_id: UUID,
    session: SessionDep
):
    crud.activate_camera(session, camera_id)
    return Message(message="Camera archived successfully")


@router.delete("/{camera_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def delete_camera(
    camera_id: UUID,
    session: SessionDep
):
    crud.delete_camera(session, camera_id)
    return Message(message="Camera deleted successfully")
