import sqlite3

# Connect to database (creates it if it doesn’t exist)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    goal INTEGER DEFAULT 10
)
''')

# Create study_sessions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    subject TEXT NOT NULL,
    duration INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (username) REFERENCES users (username)
)
''')

conn.commit()
conn.close()

print("✅ Database initialized successfully!")

