from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime, time
from .database import Base

class Shop(Base):
    __tablename__ = 'shops'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(90), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    tagline: Mapped[str] = mapped_column(String(220), default='Precision in every detail.')
    address: Mapped[str] = mapped_column(String(250), default='Dublin, Ireland')
    timezone: Mapped[str] = mapped_column(String(60), default='Europe/Dublin')

class Service(Base):
    __tablename__ = 'services'
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(250), default='')
    duration_min: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Barber(Base):
    __tablename__ = 'barbers'
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120), default='Senior Barber')
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class WeeklyHours(Base):
    __tablename__ = 'weekly_hours'
    __table_args__ = (UniqueConstraint('shop_id', 'weekday'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'), index=True)
    weekday: Mapped[int] = mapped_column(Integer) # Mon 0 .. Sun 6
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    opens: Mapped[time] = mapped_column(Time)
    closes: Mapped[time] = mapped_column(Time)

class HoursException(Base):
    __tablename__ = 'hours_exceptions'
    __table_args__ = (UniqueConstraint('shop_id', 'day'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'), index=True)
    day: Mapped[date] = mapped_column(Date)
    enabled: Mapped[bool] = mapped_column(Boolean)
    opens: Mapped[time | None] = mapped_column(Time, nullable=True)
    closes: Mapped[time | None] = mapped_column(Time, nullable=True)

class Appointment(Base):
    __tablename__ = 'appointments'
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'), index=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey('barbers.id'), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id'))
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_email: Mapped[str] = mapped_column(String(250))
    start_at: Mapped[datetime] = mapped_column(DateTime, index=True) # naive UTC
    end_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default='confirmed')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
