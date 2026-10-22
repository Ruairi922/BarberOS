import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from .database import Base, engine, db_session
from .models import Shop, Service, Barber, WeeklyHours, HoursException, Appointment
from .scheduling import slots, effective_hours

# Demo only: replace shared admin token with authenticated membership/RBAC before deployment.
ADMIN_TOKEN = os.getenv('DEMO_ADMIN_TOKEN', 'local-demo-only')

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)  # MVP only; migrate to Alembic before production.
    from .seed import seed_aaron
    with next(db_session()) as db:
        seed_aaron(db)
    yield

app = FastAPI(title='BarberOS API', version='0.2.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','), allow_credentials=False, allow_methods=['GET','PUT','POST','DELETE'], allow_headers=['*'])

def get_shop(slug: str, db: Session):
    shop = db.scalar(select(Shop).where(Shop.slug == slug))
    if not shop: raise HTTPException(404, 'Shop not found')
    return shop

def require_admin(x_admin_token: str | None = Header(default=None)):
    if os.getenv('APP_ENV','local') != 'local' and ADMIN_TOKEN == 'local-demo-only':
        raise HTTPException(503, 'Demo token disabled outside local development')
    if x_admin_token != ADMIN_TOKEN: raise HTTPException(401, 'Admin access required')

class DayHours(BaseModel):
    weekday: int = Field(ge=0, le=6)
    enabled: bool
    opens: time
    closes: time

class HoursPayload(BaseModel):
    days: list[DayHours]

class ExceptionPayload(BaseModel):
    day: date
    enabled: bool
    opens: time | None = None
    closes: time | None = None

class ServicePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default='', max_length=250)
    duration_min: int = Field(ge=10, le=240)
    price_cents: int = Field(ge=0, le=100000)
    active: bool = True

class BookingPayload(BaseModel):
    service_id: int
    barber_id: int
    day: date
    time: str
    customer_name: str = Field(min_length=2, max_length=100)
    customer_email: str = Field(min_length=5, max_length=250)

@app.get('/api/health')
def health(): return {'ok': True}

@app.get('/api/shops/{slug}')
def get_public_shop(slug: str, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    services = db.scalars(select(Service).where(Service.shop_id == shop.id, Service.active == True).order_by(Service.id)).all()
    barbers = db.scalars(select(Barber).where(Barber.shop_id == shop.id, Barber.active == True).order_by(Barber.id)).all()
    hours = db.scalars(select(WeeklyHours).where(WeeklyHours.shop_id == shop.id).order_by(WeeklyHours.weekday)).all()
    return {'shop': {'id':shop.id,'name':shop.name,'slug':shop.slug,'tagline':shop.tagline,'address':shop.address,'timezone':shop.timezone},
            'services': [{'id':s.id,'name':s.name,'description':s.description,'duration_min':s.duration_min,'price_cents':s.price_cents} for s in services],
            'barbers': [{'id':b.id,'name':b.name,'role':b.role} for b in barbers],
            'hours': [{'weekday':h.weekday,'enabled':h.enabled,'opens':h.opens.strftime('%H:%M'),'closes':h.closes.strftime('%H:%M')} for h in hours]}

@app.get('/api/shops/{slug}/availability')
def availability(slug: str, day: date, service_id: int, barber_id: int, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    service = db.scalar(select(Service).where(Service.id == service_id, Service.shop_id == shop.id, Service.active == True))
    barber = db.scalar(select(Barber).where(Barber.id == barber_id, Barber.shop_id == shop.id, Barber.active == True))
    if not service or not barber: raise HTTPException(404, 'Service or barber not found')
    return {'slots': slots(db, shop, barber.id, day, service.duration_min)}

@app.post('/api/shops/{slug}/appointments', status_code=201)
def create_appointment(slug: str, payload: BookingPayload, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    service = db.scalar(select(Service).where(Service.id == payload.service_id, Service.shop_id == shop.id, Service.active == True))
    barber = db.scalar(select(Barber).where(Barber.id == payload.barber_id, Barber.shop_id == shop.id, Barber.active == True))
    if not service or not barber: raise HTTPException(404, 'Service or barber not found')
    try:
        requested_time = time.fromisoformat(payload.time)
    except ValueError:
        raise HTTPException(422, 'Invalid appointment time')
    if requested_time.strftime('%H:%M') != payload.time: raise HTTPException(422, 'Time must be HH:MM')
    # Postgres serializes bookings for the same barber by locking the barber row.
    # SQLite serializes writers; use Postgres for real multi-user deployment.
    if db.bind.dialect.name == 'postgresql':
        db.execute(select(Barber).where(Barber.id == barber.id).with_for_update()).scalar_one()
    if payload.time not in slots(db, shop, barber.id, payload.day, service.duration_min):
        raise HTTPException(409, 'That slot is no longer available')
    start = datetime.combine(payload.day, requested_time, tzinfo=ZoneInfo(shop.timezone)).astimezone(timezone.utc).replace(tzinfo=None)
    end = (datetime.combine(payload.day, requested_time, tzinfo=ZoneInfo(shop.timezone)) + timedelta(minutes=service.duration_min)).astimezone(timezone.utc).replace(tzinfo=None)
    appointment = Appointment(shop_id=shop.id, barber_id=barber.id, service_id=service.id, customer_name=payload.customer_name.strip(), customer_email=payload.customer_email.strip(), start_at=start, end_at=end)
    db.add(appointment); db.commit(); db.refresh(appointment)
    return {'id': appointment.id, 'status': 'confirmed'}

@app.get('/api/shops/{slug}/appointments', dependencies=[Depends(require_admin)])
def appointments(slug: str, day: date, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    tz = ZoneInfo(shop.timezone)
    start = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    records = db.scalars(select(Appointment).where(Appointment.shop_id == shop.id, Appointment.start_at >= start, Appointment.start_at < end).order_by(Appointment.start_at)).all()
    return [{'id':a.id,'customer_name':a.customer_name, 'barber_id':a.barber_id,'service_id':a.service_id,'time':a.start_at.replace(tzinfo=timezone.utc).astimezone(tz).strftime('%H:%M'),'status':a.status} for a in records]

@app.put('/api/shops/{slug}/hours', dependencies=[Depends(require_admin)])
def update_hours(slug: str, payload: HoursPayload, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    if len(payload.days) != 7 or {d.weekday for d in payload.days} != set(range(7)):
        raise HTTPException(422, 'Exactly seven unique weekdays required')
    if any(d.enabled and d.opens >= d.closes for d in payload.days):
        raise HTTPException(422, 'Opening time must precede closing time')
    old = {h.weekday:h for h in db.scalars(select(WeeklyHours).where(WeeklyHours.shop_id == shop.id)).all()}
    for item in payload.days:
        if item.weekday in old:
            h=old[item.weekday]; h.enabled=item.enabled; h.opens=item.opens; h.closes=item.closes
        else: db.add(WeeklyHours(shop_id=shop.id, **item.model_dump()))
    db.commit()
    return {'ok':True}

@app.put('/api/shops/{slug}/exceptions', dependencies=[Depends(require_admin)])
def update_exception(slug: str, payload: ExceptionPayload, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    if payload.enabled and (payload.opens is None or payload.closes is None or payload.opens >= payload.closes):
        raise HTTPException(422, 'Valid opening and closing times are required')
    existing = db.scalar(select(HoursException).where(HoursException.shop_id == shop.id, HoursException.day == payload.day))
    if existing:
        existing.enabled=payload.enabled; existing.opens=payload.opens; existing.closes=payload.closes
    else: db.add(HoursException(shop_id=shop.id, **payload.model_dump()))
    db.commit()
    return {'ok':True}


@app.get('/api/shops/{slug}/exceptions', dependencies=[Depends(require_admin)])
def list_exceptions(slug: str, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    records = db.scalars(select(HoursException).where(HoursException.shop_id == shop.id, HoursException.day >= date.today()).order_by(HoursException.day)).all()
    return [{'day':x.day.isoformat(),'enabled':x.enabled,'opens':x.opens.strftime('%H:%M') if x.opens else None,'closes':x.closes.strftime('%H:%M') if x.closes else None} for x in records]

@app.delete('/api/shops/{slug}/exceptions/{exception_day}', dependencies=[Depends(require_admin)])
def remove_exception(slug: str, exception_day: date, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    item = db.scalar(select(HoursException).where(HoursException.shop_id == shop.id, HoursException.day == exception_day))
    if not item:
        raise HTTPException(404, 'Special hours not found')
    db.delete(item)
    db.commit()
    return {'ok':True}

@app.post('/api/shops/{slug}/services', dependencies=[Depends(require_admin)], status_code=201)
def add_service(slug: str, payload: ServicePayload, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    service = Service(shop_id=shop.id, **payload.model_dump())
    db.add(service); db.commit(); db.refresh(service)
    return {'id':service.id,'ok':True}

@app.put('/api/shops/{slug}/services/{service_id}', dependencies=[Depends(require_admin)])
def update_service(slug: str, service_id: int, payload: ServicePayload, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    service = db.scalar(select(Service).where(Service.shop_id == shop.id, Service.id == service_id))
    if not service:
        raise HTTPException(404, 'Service not found')
    for key,value in payload.model_dump().items():
        setattr(service,key,value)
    db.commit()
    return {'ok':True}

@app.put('/api/shops/{slug}/appointments/{appointment_id}/cancel', dependencies=[Depends(require_admin)])
def cancel_appointment(slug: str, appointment_id: int, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    booking = db.scalar(select(Appointment).where(Appointment.shop_id == shop.id, Appointment.id == appointment_id))
    if not booking:
        raise HTTPException(404, 'Appointment not found')
    booking.status = 'cancelled'
    db.commit()
    return {'ok':True}


@app.get('/api/shops/{slug}/admin/services', dependencies=[Depends(require_admin)])
def admin_services(slug: str, db: Session = Depends(db_session)):
    shop = get_shop(slug, db)
    records = db.scalars(select(Service).where(Service.shop_id == shop.id).order_by(Service.id)).all()
    return [{'id':s.id,'name':s.name,'description':s.description,'duration_min':s.duration_min,'price_cents':s.price_cents,'active':s.active} for s in records]
