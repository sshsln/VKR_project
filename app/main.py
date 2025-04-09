from fastapi import FastAPI
from sqlmodel import Session
from app.core.db import engine, init_db
from app.api.main import api_router

app = FastAPI()

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    with Session(engine) as session:
        init_db(session)
