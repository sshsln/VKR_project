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


<<<<<<< HEAD
class FlightTask(SQLModel, table=True):
=======
class Order(OrderBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    operator_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    creation_time: datetime


class OrderResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    order_date: date
    start_time: time
    end_time: time
    club_id: UUID
    status: OrderStatus
    creation_time: datetime
    club_name: str
    club_address: str

    class Config:
        from_attributes = True


class OrderWithOperator(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    order_date: date
    start_time: time
    end_time: time
    club_id: UUID
    status: OrderStatus
    creation_time: datetime
    club_name: str
    club_address: str
    operator: Optional[UserPublic]

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    order_id: UUID
    status: OrderStatus


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

    @validator("status")
    def validate_status_transition(cls, v, values):
        if not v:
            return v
        # Предполагаем, что текущий статус будет передан в эндпоинте
        current_status = values.get("current_status", None)
        allowed_transitions = {
            OrderStatus.new: [OrderStatus.in_processing, OrderStatus.cancelled],
            OrderStatus.in_processing: [OrderStatus.in_progress, OrderStatus.cancelled, OrderStatus.new],
            OrderStatus.in_progress: [OrderStatus.completed],
            OrderStatus.completed: [],
            OrderStatus.cancelled: []
        }
        if current_status and v not in allowed_transitions[current_status]:
            raise ValueError(f"Invalid status transition from {current_status} to {v}")
        return v


class RouteBase(SQLModel):
    club_id: uuid.UUID
    points: str  # JSON-строка с координатами


class DroneBase(SQLModel):
    model: str = Field(max_length=255)
    club_id: uuid.UUID
    battery_charge: int
    camera_id: uuid.UUID
    lens_id: uuid.UUID


class CameraBase(SQLModel):
    model: str = Field(max_length=255)
    width_px: int
    height_px: int
    fps: int


class LensBase(SQLModel):
    model: str = Field(max_length=255)
    min_focal_length: float
    max_focal_length: float


class Drone(DroneBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class Camera(CameraBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class Lens(LensBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    zoom_ratio: Optional[float] = Field(default=None)  # Генерируется в БД


class Route(RouteBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class RouteUpdate(BaseModel):
    points: str


class FlightTaskBase(SQLModel):
    order_id: uuid.UUID
    operator_id: uuid.UUID
    route_id: uuid.UUID
    drone_id: uuid.UUID


class FlightTask(FlightTaskBase, table=True):
>>>>>>> 987c99b (добавлена логика изменения статусов)
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