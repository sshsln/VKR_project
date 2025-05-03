from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.models import Order, Route, FlightTask, Drone, OrderStatus, Camera, Lens, User, Club
from app.schemas import FlightTaskResponse, RoutePoint, FlightTaskCreate, FlightTaskUpdate, OrderResponse, \
     UserPublic, RouteResponse, DroneResponse, CameraResponse, LensResponse, Message
from app.crud import get_flight_task_by_id, get_all_flight_tasks
import json

router = APIRouter(prefix="/flight-tasks", tags=["flight-tasks"])


@router.post("/", response_model=FlightTaskResponse)
async def create_flight_task(
        flight_task_in: FlightTaskCreate,
        session: SessionDep,
        current_user: CurrentUser
):
    flight_task, order, operator, route, drone, camera, lens, club = crud.create_flight_task(session, flight_task_in, operator_id=current_user.id)
    return FlightTaskResponse(
        id=flight_task.id,
        order=OrderResponse(
            id=order.id,
            club_id=order.club_id,
            status=order.status,
            operator_id=order.operator_id,
            first_name=order.first_name,
            last_name=order.last_name,
            email=order.email,
            order_date=order.order_date,
            start_time=order.start_time,
            end_time=order.end_time,
            club_name=club.name,
            club_address=club.address
        ),
        operator=UserPublic(
            id=operator.id,
            username=operator.username,
            email=operator.email
        ),
        route=RouteResponse(
            id=route.id,
            club_id=route.club_id,
            points=[RoutePoint(**point) for point in json.loads(route.points)]
        ),
        drone=DroneResponse(
            id=drone.id,
            model=drone.model,
            club_id=drone.club_id,
            battery_charge=drone.battery_charge
        ),
        camera=CameraResponse(
            id=camera.id,
            model=camera.model,
            width_px=camera.width_px,
            height_px=camera.height_px,
            fps=camera.fps,
            club_id=camera.club_id
        ),
        lens=LensResponse(
            id=lens.id,
            model=lens.model,
            min_focal_length=lens.min_focal_length,
            max_focal_length=lens.max_focal_length,
            zoom_ratio=lens.zoom_ratio,
            club_id=lens.club_id
        )
    )


@router.get("/", response_model=List[FlightTaskResponse])
async def get_flight_tasks(
    session: SessionDep,
    current_user: CurrentUser
):
    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
    return [
        FlightTaskResponse(
            id=data["flight_task"].id,
            order=OrderResponse(
                id=data["order"].id,
                first_name=data["order"].first_name,
                last_name=data["order"].last_name,
                email=data["order"].email,
                order_date=data["order"].order_date,
                start_time=data["order"].start_time,
                end_time=data["order"].end_time,
                club_id=data["order"].club_id,
                status=data["order"].status,
                club_name=data["club"].name,
                club_address=data["club"].address
            ),
            operator=UserPublic(
                id=data["operator"].id,
                email=data["operator"].email,
                username=data["operator"].username,
                is_superuser=data["operator"].is_superuser
            ),
            route=RouteResponse(
                id=data["route"]["id"],
                club_id=data["route"]["club_id"],
                points=data["route"]["points"]
            ),
            drone=DroneResponse(
                id=data["drone"].id,
                model=data["drone"].model,
                club_id=data["drone"].club_id,
                battery_charge=data["drone"].battery_charge
            ),
            camera=CameraResponse(
                id=data["camera"].id,
                model=data["camera"].model,
                width_px=data["camera"].width_px,
                height_px=data["camera"].height_px,
                fps=data["camera"].fps,
                club_id=data["camera"].club_id
            ),
            lens=LensResponse(
                id=data["lens"].id,
                model=data["lens"].model,
                min_focal_length=data["lens"].min_focal_length,
                max_focal_length=data["lens"].max_focal_length,
                zoom_ratio=data["lens"].zoom_ratio,
                club_id=data["lens"].club_id
            )
        )
        for data in flight_tasks_data
    ]


@router.patch("/{flight_task_id}", response_model=FlightTaskResponse)
async def update_flight_task(
    flight_task_id: UUID,
    task_in: FlightTaskUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    task = session.get(FlightTask, flight_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Flight task not found")

    if not current_user.is_superuser and task.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this flight task")

    order = session.get(Order, task.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Associated order not found")

    if order.status != OrderStatus.in_processing:
        raise HTTPException(status_code=400, detail="Flight task can only be edited when order is in_processing")

    if task_in.drone_id:
        drone = session.get(Drone, task_in.drone_id)
        if not drone or drone.club_id != order.club_id:
            raise HTTPException(status_code=400, detail="Drone does not belong to the club")
        task.drone_id = task_in.drone_id

<<<<<<< HEAD
    if task_in.camera_id:
        camera = session.get(Camera, task_in.camera_id)
        if not camera or camera.club_id != order.club_id:
            raise HTTPException(status_code=400, detail="Camera does not belong to the club")
        task.camera_id = task_in.camera_id

    if task_in.lens_id:
        lens = session.get(Lens, task_in.lens_id)
        if not lens or lens.club_id != order.club_id:
            raise HTTPException(status_code=400, detail="Lens does not belong to the club")
        task.lens_id = task_in.lens_id

=======
>>>>>>> 987c99b (добавлена логика изменения статусов)
    if task_in.points:
        if len(task_in.points) < 2:
            raise HTTPException(status_code=400, detail="Route must have at least 2 points")
        if task_in.points[0].latitude != task_in.points[-1].latitude or task_in.points[0].longitude != task_in.points[-1].longitude:
            raise HTTPException(status_code=400, detail="First and last points must be the same")

        route = session.get(Route, task.route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Associated route not found")

        route.points = json.dumps([point.model_dump() for point in task_in.points])
        session.add(route)

    session.add(task)
    session.commit()
    session.refresh(task)

    order = session.get(Order, task.order_id)
    operator = session.get(User, task.operator_id)
    route = session.get(Route, task.route_id)
    drone = session.get(Drone, task.drone_id)
    camera = session.get(Camera, task.camera_id)
    lens = session.get(Lens, task.lens_id)
    club = session.get(Club, order.club_id)

    return FlightTaskResponse(
        id=task.id,
        order=OrderResponse(
            id=order.id,
            first_name=order.first_name,
            last_name=order.last_name,
            email=order.email,
            order_date=order.order_date,
            start_time=order.start_time,
            end_time=order.end_time,
            club_id=order.club_id,
            status=order.status,
            club_name=club.name,
            club_address=club.address
        ),
        operator=UserPublic(
            id=operator.id,
            email=operator.email,
            username=operator.username,
            is_superuser=operator.is_superuser
        ),
        route=RouteResponse(
            id=route.id,
            club_id=route.club_id,
            points=[RoutePoint(**point) for point in json.loads(route.points)]
        ),
        drone=DroneResponse(
            id=drone.id,
            model=drone.model,
            club_id=drone.club_id,
            battery_charge=drone.battery_charge
        ),
        camera=CameraResponse(
            id=camera.id,
            model=camera.model,
            width_px=camera.width_px,
            height_px=camera.height_px,
            fps=camera.fps,
            club_id=camera.club_id
        ),
        lens=LensResponse(
            id=lens.id,
            model=lens.model,
            min_focal_length=lens.min_focal_length,
            max_focal_length=lens.max_focal_length,
            zoom_ratio=lens.zoom_ratio,
            club_id=lens.club_id
        )
    )


@router.delete("/{flight_task_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
async def delete_flight_task(
    flight_task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    task = session.get(FlightTask, flight_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Flight task not found")

    if not current_user.is_superuser and task.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this flight task")

    order = session.get(Order, task.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Associated order not found")

    if order.status != OrderStatus.in_processing:
        raise HTTPException(status_code=400, detail="Flight task can only be deleted when order is in_processing")

    route = session.get(Route, task.route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Associated route not found")

    session.delete(route)
    order.status = OrderStatus.cancelled
    session.add(order)
    session.delete(task)

    session.commit()
    return Message(message="Flight task and associated route deleted successfully")


@router.get("/active", response_model=List[FlightTaskResponse])
async def get_active_flight_tasks(
    session: SessionDep,
    current_user: CurrentUser
):
    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        status_filter=OrderStatus.in_processing
    )
    return [
        FlightTaskResponse(
            id=data["flight_task"].id,
            order=OrderResponse(
                id=data["order"].id,
                first_name=data["order"].first_name,
                last_name=data["order"].last_name,
                email=data["order"].email,
                order_date=data["order"].order_date,
                start_time=data["order"].start_time,
                end_time=data["order"].end_time,
                club_id=data["order"].club_id,
                status=data["order"].status,
                club_name=data["club"].name,
                club_address=data["club"].address
            ),
            operator=UserPublic(
                id=data["operator"].id,
                email=data["operator"].email,
                username=data["operator"].username,
                is_superuser=data["operator"].is_superuser
            ),
            route=RouteResponse(
                id=data["route"]["id"],
                club_id=data["route"]["club_id"],
                points=data["route"]["points"]
            ),
            drone=DroneResponse(
                id=data["drone"].id,
                model=data["drone"].model,
                club_id=data["drone"].club_id,
                battery_charge=data["drone"].battery_charge
            ),
            camera=CameraResponse(
                id=data["camera"].id,
                model=data["camera"].model,
                width_px=data["camera"].width_px,
                height_px=data["camera"].height_px,
                fps=data["camera"].fps,
                club_id=data["camera"].club_id
            ),
            lens=LensResponse(
                id=data["lens"].id,
                model=data["lens"].model,
                min_focal_length=data["lens"].min_focal_length,
                max_focal_length=data["lens"].max_focal_length,
                zoom_ratio=data["lens"].zoom_ratio,
                club_id=data["lens"].club_id
            )
        )
        for data in flight_tasks_data
    ]


@router.get("/history", response_model=List[FlightTaskResponse])
async def get_completed_flight_tasks(
    session: SessionDep,
    current_user: CurrentUser
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can access flight tasks history")

    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=None,
        is_superuser=True,
        status_filter=OrderStatus.completed
    )
    return [
        FlightTaskResponse(
            id=data["flight_task"].id,
            order=OrderResponse(
                id=data["order"].id,
                first_name=data["order"].first_name,
                last_name=data["order"].last_name,
                email=data["order"].email,
                order_date=data["order"].order_date,
                start_time=data["order"].start_time,
                end_time=data["order"].end_time,
                club_id=data["order"].club_id,
                status=data["order"].status,
                club_name=data["club"].name,
                club_address=data["club"].address
            ),
            operator=UserPublic(
                id=data["operator"].id,
                email=data["operator"].email,
                username=data["operator"].username,
                is_superuser=data["operator"].is_superuser
            ),
            route=RouteResponse(
                id=data["route"]["id"],
                club_id=data["route"]["club_id"],
                points=data["route"]["points"]
            ),
            drone=DroneResponse(
                id=data["drone"].id,
                model=data["drone"].model,
                club_id=data["drone"].club_id,
                battery_charge=data["drone"].battery_charge
            ),
            camera=CameraResponse(
                id=data["camera"].id,
                model=data["camera"].model,
                width_px=data["camera"].width_px,
                height_px=data["camera"].height_px,
                fps=data["camera"].fps,
                club_id=data["camera"].club_id
            ),
            lens=LensResponse(
                id=data["lens"].id,
                model=data["lens"].model,
                min_focal_length=data["lens"].min_focal_length,
                max_focal_length=data["lens"].max_focal_length,
                zoom_ratio=data["lens"].zoom_ratio,
                club_id=data["lens"].club_id
            )
        )
        for data in flight_tasks_data
    ]


<<<<<<< HEAD
@router.get("/{id}", response_model=FlightTaskResponse)
async def get_flight_task(
    id: UUID,
    session: SessionDep,
    current_user: CurrentUser
):
=======
@router.get("/", response_model=List[FlightTaskResponse])
async def get_flight_tasks(
        session: SessionDep,
        current_user: CurrentUser
):
    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )

    if not flight_tasks_data:
        return []

    return [
        {
            "id": data["flight_task"].id,
            "order": {
                "id": data["order"].id,
                "first_name": data["order"].first_name,
                "last_name": data["order"].last_name,
                "email": data["order"].email,
                "order_date": data["order"].order_date,
                "start_time": data["order"].start_time,
                "end_time": data["order"].end_time,
                "club_id": data["order"].club_id,
                "status": data["order"].status,
                "operator_id": data["order"].operator_id,
                "creation_time": data["order"].creation_time,
                "club_name": data["club"].name,
                "club_address": data["club"].address
            },
            "operator": {
                "id": data["operator"].id,
                "email": data["operator"].email,
                "username": data["operator"].username
            },
            "route": {
                "id": data["route"]["id"],
                "club_id": data["route"]["club_id"],
                "points": data["route"]["points"]
            },
            "drone": {
                "id": data["drone"].id,
                "model": data["drone"].model,
                "club_id": data["drone"].club_id,
                "battery_charge": data["drone"].battery_charge
            }
        }
        for data in flight_tasks_data
    ]


@router.get("/active", response_model=List[FlightTaskResponse])
async def get_active_flight_tasks(
    session: SessionDep,
    current_user: CurrentUser
):
    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        status_filter=OrderStatus.in_processing
    )

    if not flight_tasks_data:
        return []

    return [
        {
            "id": data["flight_task"].id,
            "order": {
                "id": data["order"].id,
                "first_name": data["order"].first_name,
                "last_name": data["order"].last_name,
                "email": data["order"].email,
                "order_date": data["order"].order_date,
                "start_time": data["order"].start_time,
                "end_time": data["order"].end_time,
                "club_id": data["order"].club_id,
                "status": data["order"].status,
                "operator_id": data["order"].operator_id,
                "creation_time": data["order"].creation_time,
                "club_name": data["club"].name,
                "club_address": data["club"].address
            },
            "operator": {
                "id": data["operator"].id,
                "email": data["operator"].email,
                "username": data["operator"].username
            },
            "route": {
                "id": data["route"]["id"],
                "club_id": data["route"]["club_id"],
                "points": data["route"]["points"]
            },
            "drone": {
                "id": data["drone"].id,
                "model": data["drone"].model,
                "club_id": data["drone"].club_id,
                "battery_charge": data["drone"].battery_charge
            }
        }
        for data in flight_tasks_data
    ]

@router.get("/history", response_model=List[FlightTaskResponse])
async def get_completed_flight_tasks(
    session: SessionDep,
    current_user: CurrentUser
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can access flight tasks history")

    flight_tasks_data = get_all_flight_tasks(
        session,
        user_id=None,  # No user filter for superuser
        is_superuser=True,
        status_filter=OrderStatus.completed
    )

    if not flight_tasks_data:
        return []

    return [
        {
            "id": data["flight_task"].id,
            "order": {
                "id": data["order"].id,
                "first_name": data["order"].first_name,
                "last_name": data["order"].last_name,
                "email": data["order"].email,
                "order_date": data["order"].order_date,
                "start_time": data["order"].start_time,
                "end_time": data["order"].end_time,
                "club_id": data["order"].club_id,
                "status": data["order"].status,
                "operator_id": data["order"].operator_id,
                "creation_time": data["order"].creation_time,
                "club_name": data["club"].name,
                "club_address": data["club"].address
            },
            "operator": {
                "id": data["operator"].id,
                "email": data["operator"].email,
                "username": data["operator"].username
            },
            "route": {
                "id": data["route"]["id"],
                "club_id": data["route"]["club_id"],
                "points": data["route"]["points"]
            },
            "drone": {
                "id": data["drone"].id,
                "model": data["drone"].model,
                "club_id": data["drone"].club_id,
                "battery_charge": data["drone"].battery_charge
            }
        }
        for data in flight_tasks_data
    ]


@router.get("/{id}", response_model=FlightTaskResponse)
async def get_flight_task(
        id: UUID,
        session: SessionDep,
        current_user: CurrentUser
):
>>>>>>> 987c99b (добавлена логика изменения статусов)
    data = get_flight_task_by_id(
        session,
        flight_task_id=id,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
<<<<<<< HEAD
    return FlightTaskResponse(
        id=data["flight_task"].id,
        order=OrderResponse(
            id=data["order"].id,
            first_name=data["order"].first_name,
            last_name=data["order"].last_name,
            email=data["order"].email,
            order_date=data["order"].order_date,
            start_time=data["order"].start_time,
            end_time=data["order"].end_time,
            club_id=data["order"].club_id,
            status=data["order"].status,
            club_name=data["club"].name,
            club_address=data["club"].address
        ),
        operator=UserPublic(
            id=data["operator"].id,
            email=data["operator"].email,
            username=data["operator"].username,
            is_superuser=data["operator"].is_superuser
        ),
        route=RouteResponse(
            id=data["route"]["id"],
            club_id=data["route"]["club_id"],
            points=data["route"]["points"]
        ),
        drone=DroneResponse(
            id=data["drone"].id,
            model=data["drone"].model,
            club_id=data["drone"].club_id,
            battery_charge=data["drone"].battery_charge
        ),
        camera=CameraResponse(
            id=data["camera"].id,
            model=data["camera"].model,
            width_px=data["camera"].width_px,
            height_px=data["camera"].height_px,
            fps=data["camera"].fps,
            club_id=data["camera"].club_id
        ),
        lens=LensResponse(
            id=data["lens"].id,
            model=data["lens"].model,
            min_focal_length=data["lens"].min_focal_length,
            max_focal_length=data["lens"].max_focal_length,
            zoom_ratio=data["lens"].zoom_ratio,
            club_id=data["lens"].club_id
        )
    )
=======

    return {
        "id": data["flight_task"].id,
        "order": {
            "id": data["order"].id,
            "first_name": data["order"].first_name,
            "last_name": data["order"].last_name,
            "email": data["order"].email,
            "order_date": data["order"].order_date,
            "start_time": data["order"].start_time,
            "end_time": data["order"].end_time,
            "club_id": data["order"].club_id,
            "status": data["order"].status,
            "operator_id": data["order"].operator_id,
            "creation_time": data["order"].creation_time,
            "club_name": data["club"].name,
            "club_address": data["club"].address
        },
        "operator": {
            "id": data["operator"].id,
            "email": data["operator"].email,
            "username": data["operator"].username
        },
        "route": {
            "id": data["route"]["id"],
            "club_id": data["route"]["club_id"],
            "points": data["route"]["points"]
        },
        "drone": {
            "id": data["drone"].id,
            "model": data["drone"].model,
            "club_id": data["drone"].club_id,
            "battery_charge": data["drone"].battery_charge
        }
    }
>>>>>>> 987c99b (добавлена логика изменения статусов)
