import uuid

from typing import Any

from sqlmodel import Session, select


from app.core.security import get_password_hash, verify_password
from app.models import User, UserCreate, UserUpdate, FlightTask, Point, FlightTaskCreate


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


def create_flight_task(
        *, session: Session, flight_task_in: FlightTaskCreate, user_id: uuid.UUID
) -> FlightTask:
    # Создаём объект FlightTask без поля points
    db_flight_task = FlightTask(
        date=flight_task_in.date,
        start_time=flight_task_in.start_time,
        end_time=flight_task_in.end_time,
        resolution=flight_task_in.resolution,
        frame_rate=flight_task_in.frame_rate,
        user_id=user_id
    )
    session.add(db_flight_task)
    session.commit()
    session.refresh(db_flight_task)

    # Создаём объекты Point и связываем их с FlightTask
    for point_in in flight_task_in.points:
        db_point = Point(
            waypoint_number=point_in.waypoint_number,
            latitude=point_in.latitude,
            longitude=point_in.longitude,
            altitude=point_in.altitude,
            flight_task_id=db_flight_task.id
        )
        session.add(db_point)
    session.commit()
    session.refresh(db_flight_task)
    return db_flight_task
