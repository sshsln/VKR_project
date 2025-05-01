from fastapi import FastAPI
from sqlmodel import Session
from app.core.db import engine, init_db
from app.api.main import api_router
from app.scheduler import start_scheduler

app = FastAPI()

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    start_scheduler()
    with Session(engine) as session:
        init_db(session)