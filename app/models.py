import uuid
from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel, Relationship
from datetime import date as date_type, time as time_type
from enum import Enum
from typing import Optional, List


class ResolutionEnum(str, Enum):
    HD = '720p'
    FULL_HD = '1080p'
    UHD = '4K'
    UHD_8K = '8K'


class FrameRateEnum(int, Enum):
    FPS_24 = 24
    FPS_30 = 30
    FPS_60 = 60


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    flight_tasks: List["FlightTask"] = Relationship(back_populates="user")


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
    sub: uuid.UUID | None = None

    @field_validator("sub", mode="before")
    def validate_sub(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return uuid.UUID(value)
        return value


class FlightTask(SQLModel, table=True):
    __tablename__ = "flight_task"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    date: date_type
    start_time: time_type
    end_time: time_type
    resolution: ResolutionEnum | None = None
    frame_rate: FrameRateEnum | None = None

    user: "User" = Relationship(back_populates="flight_tasks")
    points: List["Point"] = Relationship(
        back_populates="flight_task",
        sa_relationship_kwargs={
            "foreign_keys": "Point.flight_task_id",
            "cascade": "all, delete-orphan"
        }
    )


class Point(SQLModel, table=True):
    __tablename__ = "point"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    flight_task_id: uuid.UUID = Field(foreign_key="flight_task.id", ondelete="CASCADE")
    waypoint_number: int
    latitude: float
    longitude: float
    altitude: float = 50.0

    flight_task: Optional["FlightTask"] = Relationship(
        back_populates="points",
        sa_relationship_kwargs={"foreign_keys": "Point.flight_task_id"}
    )


class PointCreate(SQLModel):
    waypoint_number: int
    latitude: float
    longitude: float
    altitude: float = 50.0

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError('Широта должна быть в диапазоне от -90 до 90 градусов')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180 градусов')
        return v

    @field_validator('altitude')
    def validate_altitude(cls, v):
        if not (20 <= v <= 150):
            raise ValueError('Высота должна быть в диапазоне от 20 до 150 метров')
        return v


class FlightTaskCreate(SQLModel):
    date: date_type
    start_time: time_type
    end_time: time_type
    resolution: ResolutionEnum | None = None
    frame_rate: FrameRateEnum | None = None
    points: List[PointCreate]

    @field_validator('date')
    def validate_date(cls, v):
        if v < date_type.today():
            raise ValueError('Дата должна быть сегодняшней или в будущем')
        return v

    @field_validator('end_time')
    def validate_times(cls, v, info):
        start_time = info.data.get('start_time')
        if start_time is not None and v <= start_time:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class FlightTaskUpdate(SQLModel):
    date: Optional[date_type] = None
    start_time: Optional[time_type] = None
    end_time: Optional[time_type] = None
    resolution: Optional[str] = None
    frame_rate: Optional[int] = None
    points: Optional[List[PointCreate]] = None

    @field_validator('date')
    def validate_date(cls, v):
        if v is not None and v < date_type.today():
            raise ValueError('Дата должна быть сегодняшней или в будущем')
        return v

    @field_validator('end_time')
    def validate_times(cls, v, info):
        start_time = info.data.get('start_time')
        if start_time is not None and v is not None and v <= start_time:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v
