from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime
import pytz
from app.api.deps import get_db
from app.models import Order, OrderStatus

scheduler = AsyncIOScheduler()


def update_order_statuses():
    session: Session = next(get_db())
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        orders = session.query(Order).all()

        for order in orders:
            # Комбинируем order_date и start_time/end_time в datetime
            try:
                start_datetime = datetime(
                    order.order_date.year,
                    order.order_date.month,
                    order.order_date.day,
                    order.start_time.hour,
                    order.start_time.minute,
                    tzinfo=moscow_tz
                )
                end_datetime = datetime(
                    order.order_date.year,
                    order.order_date.month,
                    order.order_date.day,
                    order.end_time.hour,
                    order.end_time.minute,
                    tzinfo=moscow_tz
                )
            except Exception as e:
                continue
            # Автоматическая отмена для new
            if order.status == OrderStatus.new and now >= start_datetime:
                order.status = OrderStatus.cancelled
                session.add(order)

            # Переход в in_progress
            if order.status == OrderStatus.in_processing and now >= start_datetime:
                order.status = OrderStatus.in_progress
                session.add(order)

            # Переход в completed
            if order.status == OrderStatus.in_progress and now >= end_datetime:
                order.status = OrderStatus.completed
                session.add(order)

        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()


def start_scheduler():
    scheduler.add_job(update_order_statuses, "interval", minutes=5)
<<<<<<< HEAD
    scheduler.start()
=======
    scheduler.start()
>>>>>>> 987c99b (добавлена логика изменения статусов)
