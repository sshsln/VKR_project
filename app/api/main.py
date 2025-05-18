from fastapi import APIRouter

from app.api.routes import login, users, orders, flight_tasks, drones, clubs, cameras, lenses

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(orders.router)
api_router.include_router(flight_tasks.router)
api_router.include_router(clubs.router)
api_router.include_router(drones.router)
api_router.include_router(cameras.router)
api_router.include_router(lenses.router)