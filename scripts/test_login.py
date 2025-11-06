import sys, os
# ensure the app package path is on sys.path
sys.path.insert(0, r"c:\Users\Haide\Downloads\StudyTrackerApp")
from app import app

with app.test_client() as client:
    # test a known user from the DB
    resp = client.post('/login', data={'username':'Haider','password':'Ebrahim'}, follow_redirects=False)
    print('POST /login ->', resp.status_code, resp.headers.get('Location'))
    print('Set-Cookie header:', resp.headers.get('Set-Cookie'))

    # Access /loading using the same client (cookies preserved)
    r2 = client.get('/loading')
    print('GET /loading ->', r2.status_code)
    print('Loading page contains:', b'Loading' in r2.data)

    # Access /dashboard (should work because session set)
    r3 = client.get('/dashboard')
    print('GET /dashboard ->', r3.status_code)
    if r3.status_code == 200:
        print('Dashboard page length:', len(r3.data))
    else:
        print('Dashboard redirected to:', r3.headers.get('Location'))
