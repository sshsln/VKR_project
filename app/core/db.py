from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
SQLModel.metadata.create_all(engine)


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            username=settings.FIRST_SUPERUSER_NAME,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
