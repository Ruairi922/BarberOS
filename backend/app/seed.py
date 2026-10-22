"""Local-demo seed data. Edit shop identity here; customize services/hours in dashboard.

Never overwrite existing shops or operational settings on restart.
Prices and hours below are DESIGN PLACEHOLDERS, not Aaron's confirmed business terms.
"""
from datetime import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Shop, Service, Barber, WeeklyHours

AARON_SLUG = 'aaron-binions'

def seed_aaron(db: Session) -> None:
    if db.scalar(select(Shop).where(Shop.slug == AARON_SLUG)):
        return
    shop = Shop(
        slug=AARON_SLUG,
        name='AB / Aaron Binions',
        tagline='Your cut. Your time. Your barber.',
        address='Monasterevin, Co. Kildare', # Area only. Home address stays private.
        timezone='Europe/Dublin',
    )
    db.add(shop)
    db.flush()
    db.add(Barber(shop_id=shop.id, name='Aaron Binions', role='Independent barber · 6+ years experience'))
    db.add_all([
        Service(shop_id=shop.id, name='Fresh Cut', description='A clean, considered cut and finish.', duration_min=30, price_cents=2500),
        Service(shop_id=shop.id, name='Skin Fade', description='Sharp fade, detailed finishing and styling.', duration_min=45, price_cents=3000),
        Service(shop_id=shop.id, name='Beard Tidy', description='Shape-up and beard detailing.', duration_min=20, price_cents=1500),
        Service(shop_id=shop.id, name='Cut + Beard', description='Your full refresh in one appointment.', duration_min=60, price_cents=4000),
    ])
    # PREVIEW hours only; Aaron will replace these in the admin panel.
    for weekday in range(7):
        db.add(WeeklyHours(shop_id=shop.id, weekday=weekday, enabled=weekday < 6, opens=time(10), closes=time(18)))
    db.commit()
