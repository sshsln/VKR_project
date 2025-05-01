from datetime import date, time, datetime
from typing import Optional, List
from pydantic import EmailStr, field_validator, BaseModel, validator
from sqlmodel import SQLModel, Field
from uuid import UUID
from enum import Enum as PyEnum


class OrderStatus(str, PyEnum):
    new = "new"
    in_processing = "in_processing"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class UserBase(SQLModel):
    email: EmailStr = Field(max_length=255)
    is_superuser: bool = False
    username: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    username: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    username: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UserPublic(UserBase):
    id: UUID


class UserAdmin(UserPublic):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int


class UsersAdmin(SQLModel):
    data: List[UserAdmin]
    count: int


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    refresh_token: str
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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ClubBase(SQLModel):
    name: str = Field(max_length=255)
    address: str = Field(max_length=255)
    latitude: float
    longitude: float


class ClubUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ClubResponse(ClubBase):
    id: UUID


class ClubAdmin(ClubResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class OrderBase(SQLModel):
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    order_date: date
    start_time: time
    end_time: time
    club_id: UUID
    status: OrderStatus = OrderStatus.new


class OrderUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    order_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    club_id: Optional[UUID] = None
    status: Optional[OrderStatus] = None


class OrderCreate(SQLModel):
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    order_date: date
    start_time: time
    end_time: time
    club_id: UUID


class OrderResponse(OrderBase):
    id: UUID
    club_name: str
    club_address: str


class OrderWithOperator(OrderResponse):
    operator: Optional[UserPublic]


class OrderStatusUpdate(BaseModel):
    status: Optional[OrderStatus] = None

    @validator("status")
    def validate_status_transition(cls, v, values):
        if not v:
            return v
        current_status = values.get("current_status")
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


class OrderAdmin(OrderResponse):
    # operator_id: Optional[UUID]
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


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


class RouteBase(SQLModel):
    club_id: UUID
    points: str


class RouteResponse(RouteBase):
    id: UUID
    points: List[RoutePoint]


class RouteAdmin(RouteResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class RouteUpdate(BaseModel):
    points: str


class RoutePointsData(BaseModel):
    points: List[RoutePoint]


class CameraBase(SQLModel):
    model: str = Field(max_length=255)
    width_px: int
    height_px: int
    fps: int
    club_id: UUID


class CameraUpdate(SQLModel):
    model: Optional[str] = Field(default=None, max_length=255)
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    fps: Optional[int] = None
    club_id: Optional[UUID] = None


class CameraResponse(CameraBase):
    id: UUID


class CameraAdmin(CameraResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class LensBase(SQLModel):
    model: str = Field(max_length=255)
    min_focal_length: float
    max_focal_length: float
    zoom_ratio: Optional[float] = None
    club_id: UUID


class LensUpdate(SQLModel):
    model: Optional[str] = Field(default=None, max_length=255)
    min_focal_length: Optional[float] = None
    max_focal_length: Optional[float] = None
    club_id: Optional[UUID] = None


class LensResponse(LensBase):
    id: UUID


class LensAdmin(LensResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class DroneBase(SQLModel):
    model: str = Field(max_length=255)
    club_id: UUID
    battery_charge: int


class DroneUpdate(SQLModel):
    model: Optional[str] = Field(default=None, max_length=255)
    club_id: Optional[UUID] = None
    battery_charge: Optional[int] = None


class DroneResponse(DroneBase):
    id: UUID


class DroneAdmin(DroneResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class FlightTaskBase(SQLModel):
    order_id: UUID
    operator_id: UUID
    route_id: UUID
    drone_id: UUID
    camera_id: UUID
    lens_id: UUID


class FlightTaskCreate(BaseModel):
    order_id: UUID
    drone_id: UUID
    camera_id: UUID
    lens_id: Optional[UUID] = None
    points: List[RoutePoint]


class FlightTaskUpdate(BaseModel):
    drone_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    lens_id: Optional[UUID] = None
    points: Optional[List[RoutePoint]] = None


class FlightTaskResponse(BaseModel):
    id: UUID
    order: OrderResponse
    operator: UserPublic
    route: RouteResponse
    drone: DroneResponse
    camera: CameraResponse
    lens: Optional[LensResponse]


class FlightTaskAdmin(FlightTaskResponse):
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]