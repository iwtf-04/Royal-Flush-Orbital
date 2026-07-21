import json
import urllib.request

payload = {
    'brand': 'Toyota',
    'name': 'Toyota Corolla Altis 1.6A',
    'registration_date': '2019-05-20',
    'mileage': 65000,
    'owners': 1,
    'depreciation': 11500,
}

req = urllib.request.Request(
    'http://127.0.0.1:8001/api/predict-price',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(resp.status)
        print(resp.read().decode())
except Exception as exc:
    print(type(exc).__name__)
    print(exc)
