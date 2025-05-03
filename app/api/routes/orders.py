from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app import crud
from app.api.deps import SessionDep, CurrentUser, get_current_active_superuser, SuperUser
<<<<<<< HEAD
from app.crud import get_order_with_club_data
from app.models import Order, FlightTask, Club
from app.schemas import OrderWithOperator, OrderResponse, OrderUpdate, OrderStatus, OrderCreate, Message, \
    OrderStatusUpdate
=======
from app.crud import get_order_with_club_data, update_order_status
from app.models import Order, OrderWithOperator, OrderResponse, OrderStatusUpdate, OrderUpdate, OrderStatus, FlightTask
from app.scheduler import update_order_statuses
>>>>>>> 987c99b (добавлена логика изменения статусов)

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


@router.get("/statuses", response_model=List[str])
async def get_order_statuses(
    current_user: CurrentUser
):
    return [status.value for status in OrderStatus]


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
        "club": {
            "id": club.id,
            "name": club.name,
            "lat": club.latitude,
            "lon": club.longitude,
            "address": club.address
        }
    }


<<<<<<< HEAD
@router.patch("/{order_id}", response_model=Order)
async def update_order_status(
        order_id: UUID,
        order_in: OrderStatusUpdate,
=======
# @router.post("/status", response_model=Order)
# async def update_order_status(
#     status_update: OrderStatusUpdate,
#     session: SessionDep,
#     current_user: CurrentUser
# ):
#     order = update_order_status(
#         session,
#         order_id=status_update.order_id,
#         status=status_update.status,
#         user_id=current_user.id
#     )
#     return order


@router.patch("/{order_id}", response_model=Order)
async def update_order_status(
        order_id: UUID,
        order_in: OrderUpdate,
>>>>>>> 987c99b (добавлена логика изменения статусов)
        session: SessionDep,
        current_user: CurrentUser
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not current_user.is_superuser and order.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")

    if order_in.status:
        # Валидация перехода статуса
        allowed_transitions = {
            OrderStatus.new: [OrderStatus.in_processing, OrderStatus.cancelled],
            OrderStatus.in_processing: [OrderStatus.in_progress, OrderStatus.cancelled, OrderStatus.new],
            OrderStatus.in_progress: [OrderStatus.completed],
            OrderStatus.completed: [],
            OrderStatus.cancelled: []
        }
        if order_in.status not in allowed_transitions[order.status]:
            raise HTTPException(status_code=400,
                                detail=f"Invalid status transition from {order.status} to {order_in.status}")

        if order_in.status == OrderStatus.cancelled:
            order.status = OrderStatus.cancelled
        elif order_in.status == OrderStatus.new and order.status == OrderStatus.in_processing:
            order.status = OrderStatus.new
            order.operator_id = None
            # Удаляем связанное полётное задание
            flight_task = session.query(FlightTask).filter(FlightTask.order_id == order_id).first()
            if flight_task:
                session.delete(flight_task)
        else:
            raise HTTPException(status_code=400,
                                detail="Only cancellation or return to new is allowed via this endpoint")

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.post("", response_model=OrderResponse, dependencies=[Depends(get_current_active_superuser)])
async def create_order(
    order_in: OrderCreate,
    session: SessionDep
):
    # Проверка существования клуба
    club = session.get(Club, order_in.club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Создание заказа
    order = Order(
        first_name=order_in.first_name,
        last_name=order_in.last_name,
        email=order_in.email,
        order_date=order_in.order_date,
        start_time=order_in.start_time,
        end_time=order_in.end_time,
        club_id=order_in.club_id,
        status=OrderStatus.new,
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderResponse(
        id=order.id,
        first_name=order.first_name,
        last_name=order.last_name,
        email=order.email,
        order_date=order.order_date,
        start_time=order.start_time,
        end_time=order.end_time,
        club_id=order.club_id,
        status=order.status,
        club_name=club.name,
        club_address=club.address
    )


@router.patch("/admin/{order_id}", response_model=OrderResponse, dependencies=[Depends(get_current_active_superuser)])
async def admin_update_order(
    order_id: UUID,
    order_in: OrderUpdate,
    session: SessionDep
):
    return crud.admin_update_order(session=session, order_id=order_id, order_in=order_in)


@router.delete("/{order_id}", response_model=None, dependencies=[Depends(get_current_active_superuser)])
async def delete_order(
    order_id: UUID,
    session: SessionDep
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Удаление связанных полётных заданий
    session.query(FlightTask).filter(FlightTask.order_id == order_id).delete()
    session.delete(order)
    session.commit()

    return Message(message="Order deleted successfully")