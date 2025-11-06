# Scholarly

Scholarly is a web-based study tracker built with Flask. It helps students organize, log, and visualize their study sessions, manage study logs, and track progress over time. The app features dashboards, session management, PDF export, and more. 

**Note:** This app does not include user authentication or verification.

---

## Features
- Log and manage study sessions
- Dashboard for visualizing study progress
- Export study logs to PDF
- Edit and delete sessions
- Responsive user interface

---

## How to Run
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/scholarly.git
   cd scholarly
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python app.py
   ```
4. Open your browser and go to `http://localhost:5000`

---

## Technologies Used & What I Learned

### Python & Flask
- Built the backend logic, routing, and session management.
- Learned how to structure a Flask app, handle requests, and interact with SQLite databases.

### HTML
- Created the structure for all web pages (login, dashboard, study logs, etc.).
- Learned semantic HTML and how to organize templates for Flask.

### CSS
- Styled the app for a clean, modern look.
- Used custom styles and responsive layouts for usability.
- Learned about CSS selectors, flexbox, and grid.

### JavaScript
- Added interactivity to the dashboard and forms.
- Used JS for dynamic UI updates and client-side validation.
- Learned DOM manipulation and event handling.

### SQL (SQLite)
- Managed user and session data with SQLite.
- Learned SQL queries for CRUD operations and data analysis.

### Other Libraries
- Used FPDF for PDF export.
- Used Matplotlib for data visualization.
- Learned how to integrate third-party Python libraries into a Flask project.

---

## Folder Structure
- `app.py` - Main Flask application
- `init_db.py` - Database initialization script
- `database/` - SQLite database files
- `static/` - CSS, JS, and images
- `templates/` - HTML templates
- `scripts/` - Utility and test scripts

---

## License
MIT

---

## Author
Haide
