"""End-to-end API smoke test using a TEMP database. Does not touch your regular barberos.db.

Run from backend/: python scripts/smoke_test.py
"""
import os
import sys
import tempfile
from datetime import date,timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlencode

with tempfile.TemporaryDirectory(prefix='barberos-smoke-') as tmp:
    os.environ['DATABASE_URL'] = f"sqlite:///{Path(tmp) / 'test.db'}"
    os.environ['APP_ENV'] = 'local'
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        url = '/api/shops/aaron-binions'
        admin = {'X-Admin-Token':'local-demo-only'}
        response = client.get(url)
        assert response.status_code == 200, response.text
        shop = response.json()
        assert shop['shop']['address']=='Monasterevin, Co. Kildare'
        assert len(shop['barbers'])==1
        assert len(shop['services'])==4
        assert client.get(f'{url}/admin/services').status_code==401
        d=date.today()+timedelta(days=1)
        while d.weekday()==6:
            d+=timedelta(days=1)
        day=d.isoformat()
        service_id=shop['services'][0]['id']
        barber_id=shop['barbers'][0]['id']
        query=f'day={day}&service_id={service_id}&barber_id={barber_id}'
        a=client.get(f'{url}/availability?{query}')
        assert a.status_code==200
        slots=a.json()['slots']
        assert slots
        payload=dict(service_id=service_id,barber_id=barber_id,day=day,time=slots[0],customer_name='Local Test',customer_email='demo@example.com')
        booking=client.post(f'{url}/appointments',json=payload)
        assert booking.status_code==201, booking.text
        assert client.post(f'{url}/appointments',json=payload).status_code==409
        entries=client.get(f'{url}/appointments?day={day}',headers=admin)
        assert entries.status_code==200 and len(entries.json())==1
        assert client.put(f'{url}/appointments/{booking.json()["id"]}/cancel',headers=admin).status_code==200
        assert slots[0] in client.get(f'{url}/availability?{query}').json()['slots']
        assert client.put(f'{url}/exceptions',headers=admin,json={'day':day,'enabled':False}).status_code==200
        assert client.get(f'{url}/availability?{query}').json()['slots']==[]
        assert len(client.get(f'{url}/exceptions',headers=admin).json())==1
        assert client.delete(f'{url}/exceptions/{day}',headers=admin).status_code==200
        assert client.put(f'{url}/services/{service_id}',headers=admin,json=dict(name='Pilot Cut',description='demo',duration_min=30,price_cents=2700,active=False)).status_code==200
        assert len(client.get(url).json()['services'])==3
        assert len(client.get(f'{url}/admin/services',headers=admin).json())==4
        assert client.post(f'{url}/services',headers=admin,json=dict(name='Kids Cut',description='demo',duration_min=30,price_cents=2000,active=True)).status_code==201
        print('PASS: tenant seed, one barber, availability, booking, double-book prevention, admin guard, cancellation, exceptions, service edit/add')
