from fastapi import APIRouter

from app.api.routes import login, users, orders, flight_tasks, routes, drones, clubs

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(orders.router)
api_router.include_router(flight_tasks.router)
# api_router.include_router(routes.router)
api_router.include_router(drones.router)
api_router.include_router(clubs.router)
