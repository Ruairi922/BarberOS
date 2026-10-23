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

# Single-studio pilot; replace with account-level auth before multi-tenant launch.
ADMIN_ENABLED = os.getenv("ADMIN_ENABLED", "false").lower() == "true"
ADMIN_LOGIN_USERNAME = os.getenv("ADMIN_LOGIN_USERNAME", "Aaron")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "")

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

import base64
import hashlib
import hmac
import json
import threading
import time as clock
from fastapi import Request

LOGIN_ATTEMPTS = {}
LOGIN_LOCK = threading.Lock()

class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)

def _configured():
    return bool(ADMIN_ENABLED and ADMIN_PASSWORD_HASH and len(ADMIN_SESSION_SECRET) >= 32)

def _password_ok(password: str) -> bool:
    try:
        algorithm, iterations, salt, digest = ADMIN_PASSWORD_HASH.split("$")
        if algorithm != "pbkdf2_sha256" or int(iterations) < 300000:
            return False
        attempt = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(attempt, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False

def _sign(raw: bytes) -> bytes:
    return hmac.new(ADMIN_SESSION_SECRET.encode(), raw, hashlib.sha256).digest()

def _enc(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

def _dec(encoded: str) -> bytes:
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))

def require_admin(request: Request):
    if not _configured():
        raise HTTPException(status_code=503, detail="Admin login unavailable")
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        raw_part, sig_part = authorization[7:].split(".", 1)
        raw = _dec(raw_part)
        if not hmac.compare_digest(_sign(raw), _dec(sig_part)):
            raise ValueError("Invalid signature")
        payload = json.loads(raw)
        if (payload.get("sub") != ADMIN_LOGIN_USERNAME
            or payload.get("shop") != "aaron-binions"
            or payload.get("version") != hashlib.sha256(ADMIN_PASSWORD_HASH.encode()).hexdigest()[:16]
            or int(payload.get("exp", 0)) <= int(clock.time())):
            raise ValueError("Expired or invalid")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/api/shops/{slug}/auth/login")
def login(slug: str, credentials: LoginPayload, request: Request):
    if slug != "aaron-binions":
        raise HTTPException(404, "Shop not found")
    if not _configured():
        raise HTTPException(status_code=503, detail="Admin login unavailable")
    # Pilot throttle, in-memory per instance; add shared rate limiting for production.
    client = request.client.host if request.client else "unknown"
    now = clock.monotonic()
    with LOGIN_LOCK:
        recent = [t for t in LOGIN_ATTEMPTS.get(client, []) if now - t < 900]
        LOGIN_ATTEMPTS[client] = recent
        if len(recent) >= 5:
            raise HTTPException(status_code=429, detail="Too many login attempts; try later")
    valid_user = hmac.compare_digest(credentials.username.casefold(), ADMIN_LOGIN_USERNAME.casefold())
    valid_password = _password_ok(credentials.password)
    if not (valid_user and valid_password):
        with LOGIN_LOCK:
            LOGIN_ATTEMPTS.setdefault(client, []).append(now)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS.pop(client, None)
    raw = json.dumps({
        "sub": ADMIN_LOGIN_USERNAME, "shop": slug,
        "exp": int(clock.time()) + 3600,
        "version": hashlib.sha256(ADMIN_PASSWORD_HASH.encode()).hexdigest()[:16]
    }, separators=(",", ":")).encode()
    return {"access_token": _enc(raw) + "." + _enc(_sign(raw)), "expires_in": 3600}

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
