import sys
sys.path.insert(0, r"c:\Users\Haide\Downloads\StudyTrackerApp")
from app import app
with app.test_client() as client:
    client.post('/login', data={'username':'Haider','password':'Ebrahim'}, follow_redirects=True)
    r = client.get('/dashboard')
    print('GET /dashboard', r.status_code)
    data = r.get_data(as_text=True)
    print('Contains Recent Sessions?', 'Recent Sessions' in data)
    print('Contains Sessions count', 'Sessions' in data)
