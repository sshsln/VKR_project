from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.crud import get_all_drones, get_drone_by_id
from app.schemas import DroneBase, DroneResponse, Message, DroneUpdate, DroneAdmin

router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("/", response_model=List[DroneResponse])
async def get_drones(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    club_id: UUID | None = None
):
    include_archived = current_user.is_superuser
    drones = get_all_drones(session, include_archived=include_archived, club_id=club_id)
    return drones[skip:skip + limit]


@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(
    drone_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    drone = get_drone_by_id(session, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    if not drone.is_available and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Drone is archived and not accessible")
    return drone


@router.post("", response_model=DroneResponse, dependencies=[Depends(get_current_active_superuser)])
async def create_drone(
    drone_in: DroneBase,
    session: SessionDep
):
    drone = crud.create_drone(session, drone_in)
    return drone


@router.patch("/{drone_id}", response_model=DroneAdmin, dependencies=[Depends(get_current_active_superuser)])
async def update_drone(
    drone_id: UUID,
    drone_in: DroneUpdate,
    session: SessionDep
):
    drone = crud.update_drone(session, drone_id, drone_in)
    return drone


@router.patch("/{drone_id}/archive", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def archive_drone(
    drone_id: UUID,
    session: SessionDep
):
    crud.archive_drone(session, drone_id)
    return Message(message="Drone archived successfully")


@router.patch("/{drone_id}/activate", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def activate_drone(
    drone_id: UUID,
    session: SessionDep
):
    crud.activate_drone(session, drone_id)
    return Message(message="Drone activated successfully")


@router.delete("/{drone_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def delete_drone(
    drone_id: UUID,
    session: SessionDep
):
    crud.delete_drone(session, drone_id)
    return Message(message="Drone deleted successfully")
