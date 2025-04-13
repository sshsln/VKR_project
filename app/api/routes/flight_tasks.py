import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app import crud
from app.api.deps import SessionDep, CurrentUser
from app.models import FlightTask, FlightTaskCreate, FlightTaskUpdate, Point

router = APIRouter(prefix="/flight-tasks", tags=["flight-tasks"])


@router.post("/", response_model=FlightTask)
def create_flight_task(
    flight_task_in: FlightTaskCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    flight_task = crud.create_flight_task(
        session=session, flight_task_in=flight_task_in, user_id=current_user.id
    )
    return flight_task


@router.get("/", response_model=list[FlightTask])
def read_flight_tasks(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    if current_user.is_superuser:
        statement = select(FlightTask).offset(skip).limit(limit)
    else:
        statement = select(FlightTask).where(FlightTask.user_id == current_user.id).offset(skip).limit(limit)
    return session.exec(statement).all()


@router.get("/{flight_task_id}", response_model=FlightTask)
def read_flight_task(
        flight_task_id: uuid.UUID,
        session: SessionDep,
        current_user: CurrentUser
):
    flight_task = session.get(FlightTask, flight_task_id)
    if not flight_task:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if not current_user.is_superuser and flight_task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра этой заявки")
    return flight_task


@router.patch("/{flight_task_id}", response_model=FlightTask)
def update_flight_task(
        flight_task_id: uuid.UUID,
        flight_task_in: FlightTaskUpdate,
        session: SessionDep,
        current_user: CurrentUser
):
    # Находим существующую заявку
    db_flight_task = session.get(FlightTask, flight_task_id)
    if not db_flight_task:
        raise HTTPException(status_code=404, detail="Flight task not found")
    if not current_user.is_superuser and db_flight_task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Обновляем поля заявки, исключая points
    update_dict = flight_task_in.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if key != "points":
            setattr(db_flight_task, key, value)

    # Обновляем точки, если они переданы
    if flight_task_in.points is not None:
        # Удаляем старые точки
        session.exec(
            Point.__table__.delete().where(Point.flight_task_id == flight_task_id)
        )
        # Добавляем новые точки
        for point_in in flight_task_in.points:
            db_point = Point(
                waypoint_number=point_in.waypoint_number,
                latitude=point_in.latitude,
                longitude=point_in.longitude,
                altitude=point_in.altitude,
                flight_task_id=flight_task_id
            )
            session.add(db_point)

    session.commit()
    session.refresh(db_flight_task)
    return db_flight_task


@router.delete("/{flight_task_id}")
def delete_flight_task(
        flight_task_id: uuid.UUID,
        session: SessionDep,
        current_user: CurrentUser
):
    db_flight_task = session.get(FlightTask, flight_task_id)
    if not db_flight_task:
        raise HTTPException(status_code=404, detail="Flight task not found")
    if db_flight_task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Явно удаляем связанные точки
    session.exec(
        Point.__table__.delete().where(Point.flight_task_id == flight_task_id)
    )

    # Удаляем заявку
    session.delete(db_flight_task)
    session.commit()
    return {"message": "Flight task deleted"}
