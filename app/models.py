import uuid
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import EmailStr, field_validator, BaseModel, validator, json
from sqlmodel import Field, SQLModel
from uuid import UUID
from enum import Enum as PyEnum


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = False
    username: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    username: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    username: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: UUID | None = None

    @field_validator("sub", mode="before")
    def validate_sub(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return UUID(value)
        return value


class ClubBase(SQLModel):
    name: str = Field(max_length=255)
    address: str = Field(max_length=255)
    latitude: float
    longitude: float


class Club(ClubBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class ClubResponse(SQLModel):
    id: UUID
    name: str
    address: str
    latitude: float
    longitude: float


class OrderStatus(str, PyEnum):
    new = "new"
    in_processing = "in_processing"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class OrderBase(SQLModel):
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    order_date: date
    start_time: time
    end_time: time
    club_id: uuid.UUID
    status: OrderStatus


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
    __tablename__ = "flight_task"
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


# class FlightTaskCreate(BaseModel):
#     order_id: UUID
#     drone_id: UUID
#     points: str  # JSON-строка с координатами [{"lat": float, "lon": float, "alt": float}, ...]


class RoutePoint(BaseModel):
    sequence_number: int
    latitude: float
    longitude: float
    altitude: float
    color: str

    @validator("sequence_number")
    def check_sequence_number(cls, v):
        if v < 1:
            raise ValueError("sequence_number must be positive")
        return v


class FlightTaskCreate(BaseModel):
    order_id: UUID
    drone_id: UUID
    points: List[RoutePoint]


class RouteResponse(BaseModel):
    id: UUID
    club_id: UUID
    points: List[RoutePoint]


# class FlightTaskCreate(BaseModel):
#     order_id: UUID
#     drone_id: UUID
#     points: str
#
#     @validator("points")
#     def validate_points(cls, value):
#         try:
#             data = json.loads(value)
#             # Валидируем как массив объектов
#             RoutePointsData(points=data)
#             return value
#         except (json.JSONDecodeError, ValueError) as e:
#             raise ValueError(f"Invalid points JSON: {str(e)}")
#
#
# class RouteResponse(BaseModel):
#     id: UUID
#     club_id: UUID
#     points: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: Optional[str]


class FlightTaskUpdate(BaseModel):
    drone_id: Optional[UUID] = None
    points: Optional[List[RoutePoint]] = None


class DroneResponse(BaseModel):
    id: UUID
    model: str
    club_id: UUID
    battery_charge: int


class FlightTaskResponse(BaseModel):
    id: UUID
    order: OrderResponse
    operator: UserResponse
    route: RouteResponse
    drone: DroneResponse


# class RoutePoint(BaseModel):
#     sequence_number: int
#     latitude: float
#     longitude: float
#     altitude: float
#     color: str


class RoutePointsData(BaseModel):
    points: List[RoutePoint]
