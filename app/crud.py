import json
from typing import Any, List, Tuple

from fastapi import HTTPException

from sqlmodel import Session, select
from uuid import UUID

from app.core.security import get_password_hash, verify_password
from app.models import User, Order, Club, Drone, Camera, Lens, FlightTask, Route
from app.schemas import UserCreate, UserUpdate, OrderStatus, OrderWithOperator, UserPublic, OrderResponse, RoutePoint, \
    ClubBase, DroneBase, FlightTaskCreate, DroneUpdate, DroneResponse, CameraBase, CameraResponse, CameraUpdate, \
    LensBase, LensResponse, LensUpdate, ClubResponse, ClubUpdate, OrderUpdate


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


def admin_update_order(session: Session, order_id: UUID, order_in: OrderUpdate) -> OrderResponse:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверка существования клуба, если club_id предоставлен
    club_id = order_in.club_id if order_in.club_id is not None else order.club_id
    club = session.get(Club, club_id)
    if not club or not club.is_available:
        raise HTTPException(status_code=404, detail="Club not found or archived")

    # Валидация перехода статуса, если status предоставлен
    if order_in.status is not None and order_in.status != order.status:
        allowed_transitions = {
            OrderStatus.new: [OrderStatus.in_processing, OrderStatus.cancelled],
            OrderStatus.in_processing: [OrderStatus.in_progress, OrderStatus.cancelled, OrderStatus.new],
            OrderStatus.in_progress: [OrderStatus.completed],
            OrderStatus.completed: [],
            OrderStatus.cancelled: []
        }
        if order_in.status not in allowed_transitions[order.status]:
            raise HTTPException(status_code=400,
                                detail=f"Invalid status transition from {order.status} to {order_in.status}")

    # Обновление только предоставленных полей
    if order_in.first_name is not None:
        order.first_name = order_in.first_name
    if order_in.last_name is not None:
        order.last_name = order_in.last_name
    if order_in.email is not None:
        order.email = order_in.email
    if order_in.order_date is not None:
        order.order_date = order_in.order_date
    if order_in.start_time is not None:
        order.start_time = order_in.start_time
    if order_in.end_time is not None:
        order.end_time = order_in.end_time
    if order_in.club_id is not None:
        order.club_id = order_in.club_id
    if order_in.status is not None:
        order.status = order_in.status

    return OrderResponse(
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
    )


def create_route(session: Session, club_id: UUID, points: List[RoutePoint]) -> Route:
    points_json = json.dumps([point.model_dump() for point in points])
    route = Route(club_id=club_id, points=points_json)
    session.add(route)
    session.commit()
    session.refresh(route)
    return route


def create_flight_task(session: Session, flight_task_in: FlightTaskCreate, operator_id: UUID) -> Tuple[FlightTask, Order, User, Route, Drone, Camera, Lens, Club]:
    # Проверяем, не существует ли уже flight_task для данного order_id
    existing_task = session.exec(
        select(FlightTask).where(FlightTask.order_id == flight_task_in.order_id)
    ).first()
    if existing_task:
        raise HTTPException(status_code=400, detail="A flight task already exists for this order")

    order = session.get(Order, flight_task_in.order_id)
    if not order or order.status != OrderStatus.new or order.operator_id is not None:
        raise HTTPException(status_code=400, detail="Order is not available")

    drone = session.get(Drone, flight_task_in.drone_id)
    if not drone or not drone.is_available or drone.club_id != order.club_id:
        raise HTTPException(status_code=400, detail="Drone not found, not available, or does not belong to the club")

    camera = session.get(Camera, flight_task_in.camera_id)
    if not camera or not camera.is_available or camera.club_id != order.club_id:
        raise HTTPException(status_code=400, detail="Camera not found, not available, or does not belong to the club")

    lens = None
    if flight_task_in.lens_id:
        lens = session.get(Lens, flight_task_in.lens_id)
        if not lens or not lens.is_available or lens.club_id != order.club_id:
            raise HTTPException(status_code=400, detail="Lens not found, not available, or does not belong to the club")

    club = session.get(Club, order.club_id)
    if not club or not club.is_available:
        raise HTTPException(status_code=400, detail="Club not found or not available")

    points_list = flight_task_in.points
    if len(points_list) < 2:
        raise HTTPException(status_code=400, detail="Route must have at least 2 points")
    if points_list[0].latitude != points_list[-1].latitude or points_list[0].longitude != points_list[-1].longitude:
        raise HTTPException(status_code=400, detail="First and last points must be the same")

    route = create_route(session, club_id=order.club_id, points=points_list)

    flight_task = FlightTask(
        order_id=flight_task_in.order_id,
        operator_id=operator_id,
        route_id=route.id,
        drone_id=flight_task_in.drone_id,
        camera_id=flight_task_in.camera_id,
        lens_id=flight_task_in.lens_id
    )
    session.add(flight_task)

    order.status = OrderStatus.in_processing
    order.operator_id = operator_id
    session.add(order)

    operator = session.get(User, operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    session.commit()
    session.refresh(flight_task)
    return flight_task, order, operator, route, drone, camera, lens, club


def get_all_flight_tasks(
        session: Session,
        user_id: UUID | None,
        is_superuser: bool,
        status_filter: OrderStatus | None = None
) -> List[dict]:
    statement = (
        select(FlightTask, Order, User, Route, Drone, Camera, Lens, Club)
        .join(Order, FlightTask.order_id == Order.id)
        .join(User, FlightTask.operator_id == User.id)
        .join(Route, FlightTask.route_id == Route.id)
        .join(Drone, FlightTask.drone_id == Drone.id)
        .join(Camera, FlightTask.camera_id == Camera.id)
        .join(Lens, FlightTask.lens_id == Lens.id)
        .join(Club, Order.club_id == Club.id)
    )
    if not is_superuser:
        statement = statement.where(FlightTask.operator_id == user_id)
    if status_filter:
        statement = statement.where(Order.status == status_filter)

    results = session.exec(statement).all()
    return [
        {
            "flight_task": task,
            "order": order,
            "operator": operator,
            "route": {
                "id": route.id,
                "club_id": route.club_id,
                "points": [RoutePoint(**point) for point in json.loads(route.points)]
            },
            "drone": drone,
            "camera": camera,
            "lens": lens,
            "club": club
        }
        for task, order, operator, route, drone, camera, lens, club in results
    ]


def get_flight_task_by_id(
        session: Session,
        flight_task_id: UUID,
        user_id: UUID,
        is_superuser: bool
) -> dict:
    statement = (
        select(FlightTask, Order, User, Route, Drone, Camera, Lens, Club)
        .join(Order, FlightTask.order_id == Order.id)
        .join(User, FlightTask.operator_id == User.id)
        .join(Route, FlightTask.route_id == Route.id)
        .join(Drone, FlightTask.drone_id == Drone.id)
        .join(Camera, FlightTask.camera_id == Camera.id)
        .join(Lens, FlightTask.lens_id == Lens.id)
        .join(Club, Order.club_id == Club.id)
        .where(FlightTask.id == flight_task_id)
    )
    if not is_superuser:
        statement = statement.where(FlightTask.operator_id == user_id)

    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Flight task not found or not authorized")

    task, order, operator, route, drone, camera, lens, club = result
    return {
        "flight_task": task,
        "order": order,
        "operator": operator,
        "route": {
            "id": route.id,
            "club_id": route.club_id,
            "points": [RoutePoint(**point) for point in json.loads(route.points)]
        },
        "drone": drone,
        "camera": camera,
        "lens": lens,
        "club": club
    }


def get_all_clubs(session: Session, include_archived: bool = False) -> List[Club]:
    statement = select(Club)
    if not include_archived:
        statement = statement.where(Club.is_available == True)
    return session.exec(statement).all()


def get_club_by_id(session: Session, club_id: UUID) -> Club | None:
    return session.get(Club, club_id)


def create_club(session: Session, club_in: ClubBase) -> ClubResponse:
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
    return ClubResponse(
        id=club.id,
        name=club.name,
        address=club.address,
        latitude=club.latitude,
        longitude=club.longitude
    )


def update_club(session: Session, club_id: UUID, club_in: ClubUpdate) -> ClubResponse:
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
    return ClubResponse(
        id=club.id,
        name=club.name,
        address=club.address,
        latitude=club.latitude,
        longitude=club.longitude
    )


def archive_club(session: Session, club_id: UUID) -> None:
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if not club.is_available:
        raise HTTPException(status_code=400, detail="Club is already archived")

    # Архивируем клуб
    club.is_available = False

    # Каскадное архивирование связанных дронов, камер и объективов
    session.query(Drone).filter(Drone.club_id == club_id).update({"is_available": False})
    session.query(Camera).filter(Camera.club_id == club_id).update({"is_available": False})
    session.query(Lens).filter(Lens.club_id == club_id).update({"is_available": False})

    session.add(club)
    session.commit()


def delete_club(session: Session, club_id: UUID) -> None:
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

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


def get_all_drones(session: Session, include_archived: bool = False, club_id: UUID | None = None) -> List[Drone]:
    statement = select(Drone).join(Club).where(Club.is_available == True)
    if not include_archived:
        statement = statement.where(Drone.is_available == True)
    if club_id:
        statement = statement.where(Drone.club_id == club_id)
    return session.exec(statement).all()


def get_drone_by_id(session: Session, drone_id: UUID) -> Drone | None:
    return session.get(Drone, drone_id)


def get_drones_by_club(session: Session, club_id: UUID, include_archived: bool = False) -> List[dict]:
    statement = (
        select(Drone)
        .join(Club)
        .where(Drone.club_id == club_id, Club.is_available == True)
    )
    if not include_archived:
        statement = statement.where(Drone.is_available == True)

    drones = session.exec(statement).all()
    return [{"drone": drone} for drone in drones]


def create_drone(session: Session, drone_in: DroneBase) -> DroneResponse:
    club = session.get(Club, drone_in.club_id)
    if not club or not club.is_available:
        raise HTTPException(status_code=404, detail="Club not found or archived")

    drone = Drone(
        model=drone_in.model,
        club_id=drone_in.club_id,
        battery_charge=drone_in.battery_charge,
        is_available=True
    )
    session.add(drone)
    session.commit()
    session.refresh(drone)
    return drone


def update_drone(session: Session, drone_id: UUID, drone_in: DroneUpdate) -> DroneResponse:
    drone = session.get(Drone, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    if drone_in.club_id:
        club = session.get(Club, drone_in.club_id)
        if not club or not club.is_available:
            raise HTTPException(status_code=404, detail="Club not found or archived")
        drone.club_id = drone_in.club_id

    if drone_in.model is not None:
        drone.model = drone_in.model
    if drone_in.battery_charge is not None:
        drone.battery_charge = drone_in.battery_charge

    session.add(drone)
    session.commit()
    session.refresh(drone)

    response = DroneResponse(
        id=drone.id,
        model=drone.model,
        club_id=drone.club_id,
        battery_charge=drone.battery_charge
    )
    print("Returning:", response)
    return response


def archive_drone(session: Session, drone_id: UUID) -> None:
    drone = session.get(Drone, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    if not drone.is_available:
        raise HTTPException(status_code=400, detail="Drone is already archived")

    active_tasks = session.query(FlightTask).filter(FlightTask.drone_id == drone_id).count()
    if active_tasks:
        raise HTTPException(status_code=400, detail="Cannot archive drone with flight tasks")

    drone.is_available = False
    session.add(drone)
    session.commit()


def delete_drone(session: Session, drone_id: UUID) -> None:
    drone = session.get(Drone, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    tasks = session.query(FlightTask).filter(FlightTask.drone_id == drone_id).count()
    if tasks:
        raise HTTPException(status_code=400, detail="Cannot delete drone with associated flight tasks")

    session.delete(drone)
    session.commit()


def get_all_cameras(session: Session, include_archived: bool = False, club_id: UUID | None = None) -> List[Camera]:
    statement = select(Camera).join(Club).where(Club.is_available == True)
    if not include_archived:
        statement = statement.where(Camera.is_available == True)
    if club_id:
        statement = statement.where(Camera.club_id == club_id)
    return session.exec(statement).all()


def get_camera_by_id(session: Session, camera_id: UUID) -> Camera | None:
    return session.get(Camera, camera_id)


def get_cameras_by_club(session: Session, club_id: UUID, include_archived: bool = False) -> List[dict]:
    statement = (
        select(Camera)
        .join(Club)
        .where(Camera.club_id == club_id, Club.is_available == True)
    )
    if not include_archived:
        statement = statement.where(Camera.is_available == True)

    cameras = session.exec(statement).all()
    return [{"camera": camera} for camera in cameras]


def create_camera(session: Session, camera_in: CameraBase) -> CameraResponse:
    club = session.get(Club, camera_in.club_id)
    if not club or not club.is_available:
        raise HTTPException(status_code=404, detail="Club not found or archived")

    camera = Camera(
        model=camera_in.model,
        width_px=camera_in.width_px,
        height_px=camera_in.height_px,
        fps=camera_in.fps,
        club_id=camera_in.club_id,
        is_available=True
    )
    session.add(camera)
    session.commit()
    session.refresh(camera)

    return CameraResponse(
        id=camera.id,
        model=camera.model,
        width_px=camera.width_px,
        height_px=camera.height_px,
        fps=camera.fps,
        club_id=camera.club_id
    )


def update_camera(session: Session, camera_id: UUID, camera_in: CameraUpdate) -> CameraResponse:
    camera = session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera_in.club_id:
        club = session.get(Club, camera_in.club_id)
        if not club or not club.is_available:
            raise HTTPException(status_code=404, detail="Club not found or archived")
        camera.club_id = camera_in.club_id

    if camera_in.model is not None:
        camera.model = camera_in.model
    if camera_in.width_px is not None:
        camera.width_px = camera_in.width_px
    if camera_in.height_px is not None:
        camera.height_px = camera_in.height_px
    if camera_in.fps is not None:
        camera.fps = camera_in.fps

    session.add(camera)
    session.commit()
    session.refresh(camera)

    return CameraResponse(
        id=camera.id,
        model=camera.model,
        width_px=camera.width_px,
        height_px=camera.height_px,
        fps=camera.fps,
        club_id=camera.club_id
    )


def archive_camera(session: Session, camera_id: UUID) -> None:
    camera = session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.is_available:
        raise HTTPException(status_code=400, detail="Camera is already archived")

    active_tasks = session.query(FlightTask).filter(FlightTask.camera_id == camera_id).count()
    if active_tasks:
        raise HTTPException(status_code=400, detail="Cannot archive camera with flight tasks")

    camera.is_available = False
    session.add(camera)
    session.commit()


def delete_camera(session: Session, camera_id: UUID) -> None:
    camera = session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    tasks = session.query(FlightTask).filter(FlightTask.camera_id == camera_id).count()
    if tasks:
        raise HTTPException(status_code=400, detail="Cannot delete camera with associated flight tasks")

    session.delete(camera)
    session.commit()


def get_all_lenses(session: Session, include_archived: bool = False, club_id: UUID | None = None) -> List[Lens]:
    statement = select(Lens).join(Club).where(Club.is_available == True)
    if not include_archived:
        statement = statement.where(Lens.is_available == True)
    if club_id:
        statement = statement.where(Lens.club_id == club_id)
    return session.exec(statement).all()


def get_lens_by_id(session: Session, lens_id: UUID) -> Lens | None:
    return session.get(Lens, lens_id)


def get_lenses_by_club(session: Session, club_id: UUID, include_archived: bool = False) -> List[dict]:
    statement = (
        select(Lens)
        .join(Club)
        .where(Lens.club_id == club_id, Club.is_available == True)
    )
    if not include_archived:
        statement = statement.where(Lens.is_available == True)

    lenses = session.exec(statement).all()
    return [{"lens": lens} for lens in lenses]


def create_lens(session: Session, lens_in: LensBase) -> LensResponse:
    club = session.get(Club, lens_in.club_id)
    if not club or not club.is_available:
        raise HTTPException(status_code=404, detail="Club not found or archived")

    lens = Lens(
        model=lens_in.model,
        min_focal_length=lens_in.min_focal_length,
        max_focal_length=lens_in.max_focal_length,
        zoom_ratio=lens_in.zoom_ratio,
        club_id=lens_in.club_id,
        is_available=True
    )
    session.add(lens)
    session.commit()
    session.refresh(lens)

    return LensResponse(
        id=lens.id,
        model=lens.model,
        min_focal_length=lens.min_focal_length,
        max_focal_length=lens.max_focal_length,
        zoom_ratio=lens.zoom_ratio,
        club_id=lens.club_id
    )


def update_lens(session: Session, lens_id: UUID, lens_in: LensUpdate) -> LensResponse:
    lens = session.get(Lens, lens_id)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")

    if lens_in.club_id:
        club = session.get(Club, lens_in.club_id)
        if not club or not club.is_available:
            raise HTTPException(status_code=404, detail="Club not found or archived")
        lens.club_id = lens_in.club_id

    if lens_in.model is not None:
        lens.model = lens_in.model
    if lens_in.min_focal_length is not None:
        lens.min_focal_length = lens_in.min_focal_length
    if lens_in.max_focal_length is not None:
        lens.max_focal_length = lens_in.max_focal_length
    if lens_in.zoom_ratio is not None:
        lens.zoom_ratio = lens_in.zoom_ratio

    session.add(lens)
    session.commit()
    session.refresh(lens)

    return LensResponse(
        id=lens.id,
        model=lens.model,
        min_focal_length=lens.min_focal_length,
        max_focal_length=lens.max_focal_length,
        zoom_ratio=lens.zoom_ratio,
        club_id=lens.club_id
    )


def archive_lens(session: Session, lens_id: UUID) -> None:
    lens = session.get(Lens, lens_id)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    if not lens.is_available:
        raise HTTPException(status_code=400, detail="Lens is already archived")

    active_tasks = session.query(FlightTask).filter(FlightTask.lens_id == lens_id).count()
    if active_tasks:
        raise HTTPException(status_code=400, detail="Cannot archive lens with flight tasks")

    lens.is_available = False
    session.add(lens)
    session.commit()


def delete_lens(session: Session, lens_id: UUID) -> None:
    lens = session.get(Lens, lens_id)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")

    tasks = session.query(FlightTask).filter(FlightTask.lens_id == lens_id).count()
    if tasks:
        raise HTTPException(status_code=400, detail="Cannot delete lens with associated flight tasks")

    session.delete(lens)
    session.commit()