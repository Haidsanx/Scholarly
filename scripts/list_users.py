import sqlite3
p = r"c:\Users\Haide\Downloads\StudyTrackerApp\users.db"
conn = sqlite3.connect(p)
cur = conn.cursor()
try:
    cur.execute('SELECT id, username, password FROM users')
    rows = cur.fetchall()
    print('FOUND', len(rows), 'users')
    for r in rows:
        print(r)
except Exception as e:
    print('ERROR', e)
finally:
    conn.close()
