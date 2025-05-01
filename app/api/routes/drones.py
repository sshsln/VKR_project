from uuid import UUID

from fastapi import APIRouter

from app.api.deps import SessionDep, CurrentUser
from app.crud import get_drones_by_club
from app.models import Drone

router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("/")
async def get_drones(
        club_id: UUID,
        session: SessionDep,
        current_user: CurrentUser
):
    drones_data = get_drones_by_club(session, club_id)
    return [
        {
            "id": data["drone"].id,
            "model": data["drone"].model,
            "club_id": data["drone"].club_id,
            "battery_charge": data["drone"].battery_charge,
            "camera": {
                "id": data["camera"].id,
                "model": data["camera"].model,
                "width_px": data["camera"].width_px,
                "height_px": data["camera"].height_px,
                "fps": data["camera"].fps
            },
            "lens": {
                "id": data["lens"].id,
                "model": data["lens"].model,
                "min_focal_length": data["lens"].min_focal_length,
                "max_focal_length": data["lens"].max_focal_length,
                "zoom_ratio": data["lens"].zoom_ratio
            }
        }
        for data in drones_data
    ]
