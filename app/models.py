import uuid
from datetime import date, time, datetime
from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, SQLModel
from uuid import UUID
from enum import Enum as PyEnum
import pytz


def moscow_now():
    return datetime.now(pytz.timezone('Europe/Moscow'))


class OrderStatus(str, PyEnum):
    new = "new"
    in_processing = "in_processing"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    is_superuser: bool = False
    username: str | None = Field(default=None, max_length=255)
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Club(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    address: str = Field(max_length=255)
    latitude: float
    longitude: float
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Camera(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    model: str = Field(max_length=255)
    width_px: int
    height_px: int
    fps: int
    club_id: UUID = Field(foreign_key="club.id")
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Lens(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    model: str = Field(max_length=255)
    min_focal_length: float
    max_focal_length: float
    zoom_ratio: Optional[float] = None
    club_id: UUID = Field(foreign_key="club.id")
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Drone(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    model: str = Field(max_length=255)
    club_id: UUID = Field(foreign_key="club.id")
    battery_charge: int
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Route(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    club_id: UUID = Field(foreign_key="club.id")
    points: str  # JSON-строка с координатами
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class Order(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    order_date: date
    start_time: time
    end_time: time
    club_id: UUID = Field(foreign_key="club.id")
    status: OrderStatus = OrderStatus.new
    operator_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None


class FlightTask(SQLModel, table=True):
    __tablename__ = "flight_task"
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="order.id")
    operator_id: UUID = Field(foreign_key="user.id")
    route_id: UUID = Field(foreign_key="route.id")
    drone_id: UUID = Field(foreign_key="drone.id")
    camera_id: UUID = Field(foreign_key="camera.id")
    lens_id: Optional[UUID] = Field(foreign_key="lens.id", default=None)
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = None