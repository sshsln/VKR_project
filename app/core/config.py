import secrets

from pydantic import EmailStr

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///./vkr.db'
    FIRST_SUPERUSER: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "arminpassword"


settings = Settings()
