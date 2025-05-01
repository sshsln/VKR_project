from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser, SuperUser
from app.crud import get_order_with_club_data, update_order_status
from app.models import Order, OrderWithOperator, OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/new", response_model=List[OrderResponse])
def get_new_orders(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    orders = crud.get_new_orders(session=session, skip=skip, limit=limit)
    return orders


@router.get("/assigned", response_model=List[OrderResponse])
def get_assigned_orders(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    # if current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Administrators cannot view assigned orders"
    #     )
    orders = crud.get_assigned_orders(
        session=session, operator_id=current_user.id, skip=skip, limit=limit
    )
    return orders


@router.get("/all", response_model=List[OrderWithOperator])
def get_all_orders(
    session: SessionDep,
    current_user: SuperUser,
    skip: int = 0,
    limit: int = 100
):
    orders = crud.get_all_orders_with_operators(session=session, skip=skip, limit=limit)
    return orders


@router.get("/{order_id}")
async def get_order(
        order_id: UUID,
        session: SessionDep,
        current_user: CurrentUser
):
    data = get_order_with_club_data(session, order_id)
    if not data:
        raise HTTPException(status_code=404, detail="Order or Club not found")

    order = data["order"]
    club = data["club"]

    return {
        "id": order.id,
        "club_id": order.club_id,
        "status": order.status,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "email": order.email,
        "order_date": order.order_date,
        "start_time": order.start_time,
        "end_time": order.end_time,
        "creation_time": order.creation_time,
        "club": {
            "id": club.id,
            "name": club.name,
            "lat": club.latitude,
            "lon": club.longitude,
            "address": club.address
        }
    }


@router.post("/status", response_model=Order)
async def update_order_status(
    status_update: OrderStatusUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    order = update_order_status(
        session,
        order_id=status_update.order_id,
        status=status_update.status,
        user_id=current_user.id
    )
    return order
