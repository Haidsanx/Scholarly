import sys
sys.path.insert(0, r"c:\Users\Haide\Downloads\StudyTrackerApp")
from app import app
with app.test_client() as client:
    client.post('/login', data={'username':'Haider','password':'Ebrahim'}, follow_redirects=True)
    print('/profile', client.get('/profile').status_code)
    print('/account_settings', client.get('/account_settings').status_code)
    print('/study_logs', client.get('/study_logs').status_code)
