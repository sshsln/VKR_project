# from uuid import UUID
#
# from fastapi import APIRouter, HTTPException
#
# from app.api.deps import SessionDep, CurrentUser
# from app.models import Route, RouteUpdate
#
# router = APIRouter(prefix="/routes", tags=["routes"])
#
# @router.get("/")
# async def get_routes(session: SessionDep, current_user: CurrentUser):
#     routes = session.query(Route).all()
#     return [{"id": route.id, "club_id": route.club_id, "points": route.points} for route in routes]
#
#
# @router.patch("/{route_id}")
# async def update_route(route_id: UUID, route_in: RouteUpdate, session: SessionDep, current_user: CurrentUser):
#     route = session.get(Route, route_id)
#     if not route:
#         raise HTTPException(status_code=404, detail="Route not found")
#     route.points = route_in.points
#     session.add(route)
#     session.commit()
#     session.refresh(route)
#     return route
#
#
# @router.delete("/{route_id}")
# async def delete_route(route_id: UUID, session: SessionDep, current_user: CurrentUser):
#     route = session.get(Route, route_id)
#     if not route:
#         raise HTTPException(status_code=404, detail="Route not found")
#     session.delete(route)
#     session.commit()
#     return {"message": "Route deleted"}
