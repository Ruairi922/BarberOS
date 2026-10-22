"""Shop-local business rules, conversion to UTC, and server-authoritative slots."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Shop, WeeklyHours, HoursException, Appointment

SLOT_STEP_MIN = 15

def effective_hours(db: Session, shop: Shop, day: date):
    exception = db.scalar(select(HoursException).where(HoursException.shop_id == shop.id, HoursException.day == day))
    if exception is not None:
        return (exception.opens, exception.closes) if exception.enabled else None
    weekly = db.scalar(select(WeeklyHours).where(WeeklyHours.shop_id == shop.id, WeeklyHours.weekday == day.weekday()))
    return (weekly.opens, weekly.closes) if weekly and weekly.enabled else None

def intervals(db: Session, shop: Shop, barber_id: int, day: date):
    start = datetime.combine(day, datetime.min.time(), tzinfo=ZoneInfo(shop.timezone)).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(shop.timezone)).astimezone(timezone.utc).replace(tzinfo=None)
    return db.scalars(select(Appointment).where(Appointment.shop_id == shop.id, Appointment.barber_id == barber_id, Appointment.start_at < end, Appointment.end_at > start, Appointment.status == 'confirmed')).all()

def slots(db: Session, shop: Shop, barber_id: int, day: date, duration_min: int):
    hours = effective_hours(db, shop, day)
    if not hours or not all(hours):
        return []
    tz = ZoneInfo(shop.timezone)
    open_time, close_time = hours
    current = datetime.combine(day, open_time)
    boundary = datetime.combine(day, close_time)
    busy = intervals(db, shop, barber_id, day)
    now = datetime.now(timezone.utc)
    result = []
    while current + timedelta(minutes=duration_min) <= boundary:
        local_start = current.replace(tzinfo=tz)
        utc_start = local_start.astimezone(timezone.utc)
        # Reject non-existent local times around DST jumps.
        if utc_start.astimezone(tz).replace(tzinfo=None) == current and utc_start > now:
            utc_end = (local_start + timedelta(minutes=duration_min)).astimezone(timezone.utc)
            if utc_end > utc_start and not any(utc_start.replace(tzinfo=None) < b.end_at and utc_end.replace(tzinfo=None) > b.start_at for b in busy):
                result.append(current.strftime('%H:%M'))
        current += timedelta(minutes=SLOT_STEP_MIN)
    return result
