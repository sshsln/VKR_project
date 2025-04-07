####################
# Файл main.py

from fastapi import FastAPI, Depends, HTTPException, status
from app.db import schemas, crud
from app.api import auth
from app.db.session import SessionLocal, engine
from sqlalchemy.orm import Session
from app.db.session import Base

app = FastAPI(
    title="Drone Video Service",
    version="1.0",
    description="API для сервиса автоматизированной видеосъёмки"
)

# Создаём таблицы в БД (для теста)
Base.metadata.create_all(bind=engine)  # Теперь работает!

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", tags=["Регистрация"], summary="Зарегистрироваться", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login", tags=["Вход"], summary="Авторизоваться", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, user.email, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
def read_current_user(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user
