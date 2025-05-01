from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from uuid import UUID
from typing import List
from app.api.deps import SessionDep, CurrentUser
from app.models import Order, Route, FlightTask, Drone, OrderStatus, FlightTaskResponse, RoutePoint, RoutePointsData, \
    FlightTaskCreate, FlightTaskUpdate
from app.crud import get_flight_task_by_id, create_route, get_all_flight_tasks
import json

router = APIRouter(prefix="/flight-tasks", tags=["flight-tasks"])


@router.post("/", response_model=FlightTask)
async def create_flight_task(
    flight_task_in: FlightTaskCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    order = session.get(Order, flight_task_in.order_id)
    if not order or order.status != OrderStatus.new or order.operator_id is not None:
        raise HTTPException(status_code=400, detail="Order is not available")

    drone = session.get(Drone, flight_task_in.drone_id)
    if not drone or drone.club_id != order.club_id:
        raise HTTPException(status_code=400, detail="Drone does not belong to the club")

    points_list = flight_task_in.points
    if len(points_list) < 2:
        raise HTTPException(status_code=400, detail="Route must have at least 2 points")
    if points_list[0].latitude != points_list[-1].latitude or points_list[0].longitude != points_list[-1].longitude:
        raise HTTPException(status_code=400, detail="First and last points must be the same")

    route = create_route(session, club_id=order.club_id, points=points_list)

    flight_task = FlightTask(
        order_id=flight_task_in.order_id,
        operator_id=current_user.id,
        route_id=route.id,
        drone_id=flight_task_in.drone_id
    )
    session.add(flight_task)

    order.status = OrderStatus.in_processing
    order.operator_id = current_user.id
    session.add(order)

    session.commit()
    session.refresh(flight_task)
    return flight_task


router.get("/")
async def get_flight_tasks(session: SessionDep, current_user: CurrentUser):
    tasks = session.query(FlightTask).all()
    return [
        {
            "id": task.id,
            "order_id": task.order_id,
            "operator_id": task.operator_id,
            "route_id": task.route_id,
            "drone_id": task.drone_id
        }
        for task in tasks
    ]


@router.patch("/{flight_task_id}", response_model=FlightTask)
async def update_flight_task(
        flight_task_id: UUID,
        task_in: FlightTaskUpdate,
        session: SessionDep,
        current_user: CurrentUser
):
    # Находим полётное задание
    task = session.get(FlightTask, flight_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Flight task not found")

    # Проверяем права: только владелец или суперпользователь
    if not current_user.is_superuser and task.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this flight task")

    # Обновляем drone_id, если передан
    if task_in.drone_id:
        drone = session.get(Drone, task_in.drone_id)
        # Загружаем связанный заказ
        order = session.get(Order, task.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Associated order not found")
        if not drone or drone.club_id != order.club_id:
            raise HTTPException(status_code=400, detail="Drone does not belong to the club")
        task.drone_id = task_in.drone_id

    # Обновляем points в связанном маршруте, если переданы
    if task_in.points:
        if len(task_in.points) < 2:
            raise HTTPException(status_code=400, detail="Route must have at least 2 points")
        if task_in.points[0].latitude != task_in.points[-1].latitude or task_in.points[0].longitude != task_in.points[
            -1].longitude:
            raise HTTPException(status_code=400, detail="First and last points must be the same")

        # Находим связанный маршрут
        route = session.get(Route, task.route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Associated route not found")

        # Обновляем points в маршруте
        route.points = json.dumps([point.model_dump() for point in task_in.points])

        session.add(route)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{flight_task_id}")
async def delete_flight_task(flight_task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = session.get(FlightTask, flight_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Flight task not found")
    session.delete(task)
    session.commit()
    return {"message": "Flight task deleted"}


@router.get("/{id}", response_model=FlightTaskResponse)
async def get_flight_task(
        id: UUID,
        session: SessionDep,
        current_user: CurrentUser
):
    data = get_flight_task_by_id(
        session,
        flight_task_id=id,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )

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