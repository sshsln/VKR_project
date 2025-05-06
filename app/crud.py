import json
from typing import Any, List, Optional

from fastapi import HTTPException

from sqlmodel import Session, select
from uuid import UUID

from app.core.security import get_password_hash, verify_password
from app.models import User, Order, Club, Drone, Camera, Lens, FlightTask, Route
from app.schemas import UserCreate, UserUpdate, OrderStatus, OrderWithOperator, UserPublic, OrderResponse, RoutePoint, \
    ClubBase


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def get_new_orders(
    session: Session, skip: int = 0, limit: int = 100
) -> List[OrderResponse]:
    statement = (
        select(Order, Club.name, Club.address)
        .join(Club, Order.club_id == Club.id)
        .where(Order.status == OrderStatus.new, Order.operator_id == None)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement).all()

    return [
        OrderResponse(
            **order.dict(),
            club_name=club_name,
            club_address=club_address
        )
        for order, club_name, club_address in results
    ]


def get_assigned_orders(
    session: Session, operator_id: UUID, skip: int = 0, limit: int = 100
) -> List[OrderResponse]:
    statement = (
        select(Order, Club.name, Club.address)
        .join(Club, Order.club_id == Club.id)
        .where(Order.operator_id == operator_id)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement).all()

    return [
        OrderResponse(
            **order.dict(),
            club_name=club_name,
            club_address=club_address
        )
        for order, club_name, club_address in results
    ]


def get_all_orders_with_operators(
    session: Session, skip: int = 0, limit: int = 100
) -> List[OrderWithOperator]:
    statement = (
        select(Order, User, Club.name, Club.address)
        .outerjoin(User, Order.operator_id == User.id)
        .join(Club, Order.club_id == Club.id)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement).all()

    return [
        OrderWithOperator(
            **order.dict(),
            club_name=club_name,
            club_address=club_address,
            operator=UserPublic.from_orm(user) if user else None
        )
        for order, user, club_name, club_address in results
    ]


def get_order_with_club_data(session: Session, order_id: UUID) -> dict | None:
    # Выполняем JOIN между Order и Club
    statement = (
        select(Order, Club)
        .where(Order.id == order_id)
        .join(Club, Order.club_id == Club.id)
    )
    result = session.exec(statement).first()

    if not result:
        return None

    order, club = result
    return {
        "order": order,
        "club": club
    }


def get_drones_by_club(session: Session, club_id: UUID) -> List[dict]:
    # Выполняем JOIN между drone, camera и lens
    statement = (
        select(Drone, Camera, Lens)
        .where(Drone.club_id == club_id)
        .join(Camera, Drone.camera_id == Camera.id)
        .join(Lens, Drone.lens_id == Lens.id)
    )
    results = session.exec(statement).all()

    # Формируем список словарей с данными
    drones_data = []
    for drone, camera, lens in results:
        drones_data.append({
            "drone": drone,
            "camera": camera,
            "lens": lens
        })

    return drones_data


def get_all_clubs(session: Session, include_archived: bool = False) -> List[Club]:
    statement = select(Club)
    if not include_archived:
        statement = statement.where(Club.is_available == True)
    return session.exec(statement).all()


def get_club_by_id(session: Session, club_id: UUID) -> Club | None:
    return session.get(Club, club_id)


def create_club(session: Session, club_in: ClubBase) -> Club:
    club = Club(
        name=club_in.name,
        address=club_in.address,
        latitude=club_in.latitude,
        longitude=club_in.longitude,
        is_available=True
    )
    session.add(club)
    session.commit()
    session.refresh(club)
    return club


def update_club(session: Session, club_id: UUID, club_in: ClubBase) -> Club:
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    club.name = club_in.name
    club.address = club_in.address
    club.latitude = club_in.latitude
    club.longitude = club_in.longitude

    session.add(club)
    session.commit()
    session.refresh(club)
    return club


def archive_club(session: Session, club_id: UUID) -> None:
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if not club.is_available:
        raise HTTPException(status_code=400, detail="Club is already archived")

    club.is_available = False
    session.add(club)
    session.commit()


def delete_club(session: Session, club_id: UUID) -> None:
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Проверка связанных данных
    related_orders = session.query(Order).filter(Order.club_id == club_id).count()
    related_drones = session.query(Drone).filter(Drone.club_id == club_id).count()
    related_cameras = session.query(Camera).filter(Camera.club_id == club_id).count()
    related_lenses = session.query(Lens).filter(Lens.club_id == club_id).count()
    related_routes = session.query(Route).filter(Route.club_id == club_id).count()

    if any([related_orders, related_drones, related_cameras, related_lenses, related_routes]):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete club with associated orders, drones, cameras, lenses, or routes"
        )

    session.delete(club)
    session.commit()


def update_order_status(session: Session, order_id: UUID, status: OrderStatus, user_id: UUID) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверка прав: пользователь может обновить статус, только если он оператор заявки или заявка не назначена
    if order.operator_id is not None and order.operator_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied: this order is assigned to another operator"
        )

    order.status = status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def create_route(session: Session, club_id: UUID, points: List[RoutePoint]) -> Route:
    # Преобразуем points в JSON-строку
    points_json = json.dumps([point.model_dump() for point in points])
    route = Route(club_id=club_id, points=points_json)
    session.add(route)
    session.commit()
    session.refresh(route)
    return route


def get_flight_task_by_id(session: Session, flight_task_id: UUID, user_id: UUID, is_superuser: bool) -> dict:
    statement = (
        select(FlightTask, Order, User, Route, Drone, Club)
        .join(Order, FlightTask.order_id == Order.id)
        .join(User, FlightTask.operator_id == User.id)
        .join(Route, FlightTask.route_id == Route.id)
        .join(Drone, FlightTask.drone_id == Drone.id)
        .join(Club, Order.club_id == Club.id)
        .where(FlightTask.id == flight_task_id)
    )

    result = session.exec(statement).first()

    if not result:
        raise HTTPException(status_code=404, detail="Flight task not found")

    flight_task, order, user, route, drone, club = result

    if not is_superuser and flight_task.operator_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view flight tasks assigned to you."
        )

    points = [RoutePoint(**point) for point in json.loads(route.points)]

    return {
        "flight_task": flight_task,
        "order": order,
        "operator": user,
        "route": {"id": route.id, "club_id": route.club_id, "points": points},
        "drone": drone,
        "club": club
    }


def get_all_flight_tasks(
    session: Session,
    user_id: UUID,
    is_superuser: bool,
    status_filter: Optional[OrderStatus] = None
) -> List[dict]:
    query = (
        session.query(FlightTask, Order, User, Route, Drone, Club)
        .join(Order, FlightTask.order_id == Order.id)
        .join(User, FlightTask.operator_id == User.id)
        .join(Route, FlightTask.route_id == Route.id)
        .join(Drone, FlightTask.drone_id == Drone.id)
        .join(Club, Order.club_id == Club.id)
    )

    if not is_superuser:
        query = query.filter(FlightTask.operator_id == user_id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    results = query.all()

    return [
        {
            "flight_task": flight_task,
            "order": order,
            "operator": operator,
            "route": {
                "id": route.id,
                "club_id": route.club_id,
                "points": json.loads(route.points)
            },
            "drone": drone,
            "club": club
        }
        for flight_task, order, operator, route, drone, club in results
    ]

