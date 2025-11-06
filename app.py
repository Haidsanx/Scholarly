from fpdf import FPDF
import os
import sys
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
import json

from datetime import datetime, timedelta

# Define Flask app object
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Helper function to get study sessions for a user
def get_study_sessions_for_user(conn, user):
    """Return study sessions for a user.
    Handles two possible schemas:
    - study_sessions.user_id (int foreign key to users.id)
    - study_sessions.username (text username column)
    """
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(study_sessions)").fetchall()]
    except Exception:
        return []
    if 'user_id' in cols:
        return conn.execute('SELECT * FROM study_sessions WHERE user_id = ?', (user['id'],)).fetchall()
    elif 'username' in cols:
        return conn.execute('SELECT * FROM study_sessions WHERE username = ?', (user['username'],)).fetchall()
    else:
        return []
# Helper function for DB connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Define Flask app object



    


@app.route('/')
def home ():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        email = request.form['email'].strip()

        if not username or not password or not email:
            flash("Username, password, and email cannot be empty.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            flash("Username or email already exists. Please choose a different one.", "warning")
            conn.close()
            return render_template('register.html')

        code = generate_verification_code()
        try:
            send_verification_email(email, code)
        except Exception as e:
            flash(f'Error sending verification email: {e}', 'danger')
            conn.close()
            return render_template('register.html')

        conn.execute('INSERT INTO users (username, password, email, is_verified, verification_code) VALUES (?, ?, ?, ?, ?)', (username, password, email, 0, code))
        conn.commit()
        conn.close()
        session['pending_verification'] = email
        flash('Verification code sent! Please check your email.', 'info')
        return redirect(url_for('verify_email'))

    return render_template('register.html')

# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        remember_me = request.form.get('remember_me') == 'on'

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == password:
            session['user'] = user['username']
            resp = redirect(url_for('loading'))
            if remember_me:
                resp.set_cookie(f'remember_{username}', 'true', max_age=60*60*24*30)  # 30 days
            return resp
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/loading')
def loading():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    return render_template('loading.html')


# dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    # Fetch sessions using helper that handles multiple possible DB schemas
    all_sessions = get_study_sessions_for_user(conn, user)
    # Only show sessions from the last 7 days for homepage
    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_sessions = []
    for s in all_sessions:
        session_date = s['date'] if 'date' in s.keys() and s['date'] else (s['created_at'] if 'created_at' in s.keys() and s['created_at'] else None)
        if session_date and session_date >= seven_days_ago:
            recent_sessions.append(s)
    # compute simple aggregates for dashboard
    session_count = len(all_sessions) if all_sessions is not None else 0
    try:
        total_minutes = sum(int(s['duration']) for s in all_sessions) if all_sessions else 0
    except Exception:
        total_minutes = 0
    conn.close()

    return render_template('dashboard.html', user=user, sessions=recent_sessions, session_count=session_count, total_minutes=total_minutes)


# Export study sessions to CSV
@app.route('/export_sessions')
def export_sessions():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    sessions = get_study_sessions_for_user(conn, user)
    conn.close()
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    # Add summary stats at the top
    total_minutes = sum(int(s['duration']) for s in sessions if 'duration' in s.keys() and s['duration'])
    session_count = len(sessions)
    subject_counts = {}
    for s in sessions:
        subj = s['subject'] if 'subject' in s.keys() and s['subject'] else 'Unknown'
        subject_counts[subj] = subject_counts.get(subj, 0) + (int(s['duration']) if 'duration' in s.keys() and s['duration'] else 0)
    most_studied = max(subject_counts, key=subject_counts.get) if subject_counts else 'None'
    writer.writerow(['Summary'])
    writer.writerow(['Total Minutes', total_minutes])
    writer.writerow(['Session Count', session_count])
    writer.writerow(['Most Studied Subject', most_studied])
    writer.writerow([])
    writer.writerow(['Date', 'Subject', 'Duration', 'Notes'])
    for s in sessions:
        writer.writerow([
            s['date'] if 'date' in s.keys() else '-',
            s['subject'],
            s['duration'],
            s['notes']
        ])
    output = si.getvalue()
    from flask import Response
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=study_sessions.csv"})

@app.route('/export_sessions_pdf')
def export_sessions_pdf():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    sessions = get_study_sessions_for_user(conn, user)
    conn.close()
    import matplotlib.pyplot as plt
    import tempfile
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Study Sessions", ln=True, align='C')
    pdf.ln(10)
    # Summary stats
    total_minutes = sum(int(s['duration']) for s in sessions if 'duration' in s.keys() and s['duration'])
    session_count = len(sessions)
    subject_counts = {}
    for s in sessions:
        subj = s['subject'] if 'subject' in s.keys() and s['subject'] else 'Unknown'
        subject_counts[subj] = subject_counts.get(subj, 0) + (int(s['duration']) if 'duration' in s.keys() and s['duration'] else 0)
    most_studied = max(subject_counts, key=subject_counts.get) if subject_counts else 'None'
    pdf.cell(0, 10, f"Total Minutes: {total_minutes}", ln=True)
    pdf.cell(0, 10, f"Session Count: {session_count}", ln=True)
    pdf.cell(0, 10, f"Most Studied Subject: {most_studied}", ln=True)
    pdf.ln(5)
    # Line chart: Study time trend
    date_to_minutes = {}
    for s in sessions:
        session_date = s['date'] if 'date' in s.keys() else '-'
        try:
            date_to_minutes[session_date] = date_to_minutes.get(session_date, 0) + int(s['duration'])
        except Exception:
            pass
    if date_to_minutes:
        fig, ax = plt.subplots()
        ax.plot(list(date_to_minutes.keys()), list(date_to_minutes.values()), marker='o')
        ax.set_title('Study Time Trend')
        ax.set_xlabel('Date')
        ax.set_ylabel('Minutes')
        plt.xticks(rotation=45)
        fig.tight_layout()
        chart_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig.savefig(chart_img.name)
        plt.close(fig)
        pdf.image(chart_img.name, x=10, y=pdf.get_y(), w=180)
        pdf.ln(60)
    # Pie chart: Subject distribution
    if subject_counts:
        fig2, ax2 = plt.subplots()
        ax2.pie(list(subject_counts.values()), labels=list(subject_counts.keys()), autopct='%1.1f%%')
        ax2.set_title('Subject Distribution')
        chart_img2 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig2.savefig(chart_img2.name)
        plt.close(fig2)
        pdf.image(chart_img2.name, x=10, y=pdf.get_y(), w=120)
        pdf.ln(60)
    # Table of sessions
    pdf.ln(20)  # Add extra space after charts
    pdf.set_font("Arial", size=12)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Subject", 1)
    pdf.cell(30, 10, "Duration", 1)
    pdf.cell(80, 10, "Notes", 1)
    pdf.ln()
    for s in sessions:
        pdf.cell(40, 10, str(s['date'] if 'date' in s.keys() else '-'), 1)
        pdf.cell(40, 10, str(s['subject']), 1)
        pdf.cell(30, 10, str(s['duration']), 1)
        pdf.cell(80, 10, str(s['notes']), 1)
        pdf.ln()
        fig2, ax2 = plt.subplots()
        ax2.pie(list(subject_counts.values()), labels=list(subject_counts.keys()), autopct='%1.1f%%')
        ax2.set_title('Subject Distribution')
        fig2.tight_layout()
        pie_path = os.path.join(tempfile.gettempdir(), 'subject_pie.png')
        fig2.savefig(pie_path)
        plt.close(fig2)
        pdf.image(pie_path, x=10, y=100, w=100)
        pdf.ln(60)

    # --- Table: Study Sessions ---
    pdf.set_font("Arial", size=12)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Subject", 1)
    pdf.cell(30, 10, "Duration", 1)
    pdf.cell(80, 10, "Notes", 1)
    pdf.ln()
    for s in sessions:
        pdf.cell(40, 10, str(s['date'] if 'date' in s.keys() else '-'), 1)
        pdf.cell(40, 10, str(s['subject']), 1)
        pdf.cell(30, 10, str(s['duration']), 1)
        pdf.cell(80, 10, str(s['notes']), 1)
        pdf.ln()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    # Clean up chart images
    try:
        if os.path.exists(chart_path): os.remove(chart_path)
        if os.path.exists(pie_path): os.remove(pie_path)
    except Exception: pass
    return send_file(tmp.name, as_attachment=True, download_name="study_sessions.pdf", mimetype="application/pdf")
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Study Sessions", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Subject", 1)
    pdf.cell(30, 10, "Duration", 1)
    pdf.cell(80, 10, "Notes", 1)
    pdf.ln()
    for s in sessions:
        pdf.cell(40, 10, str(s['date'] if 'date' in s.keys() else '-'), 1)
        pdf.cell(40, 10, str(s['subject']), 1)
        pdf.cell(30, 10, str(s['duration']), 1)
        pdf.cell(80, 10, str(s['notes']), 1)
        pdf.ln()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name="study_sessions.pdf", mimetype="application/pdf")
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    sessions = get_study_sessions_for_user(conn, user)
    conn.close()
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Date', 'Subject', 'Duration', 'Notes'])
    for s in sessions:
        writer.writerow([
            s['date'] if 'date' in s.keys() else '-',
            s['subject'],
            s['duration'],
            s['notes']
        ])
    output = si.getvalue()
    from flask import Response
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=study_sessions.csv"})


@app.route('/profile')
def profile():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


@app.route('/account_settings', methods=['GET', 'POST'])
def account_settings():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if request.method == 'POST':
        # Allow changing the user's email, goal, and uploading a profile picture
        email = request.form.get('email', user['email'])
        try:
            goal = int(request.form.get('goal', user['goal']))
        except Exception:
            goal = user['goal']

        profile_pic = user['profile_pic'] if 'profile_pic' in user.keys() else None

        file = request.files.get('profile_pic')
        if file and file.filename:
            filename = secure_filename(file.filename)
            # prefix with username to avoid collisions
            _, ext = os.path.splitext(filename)
            filename = f"{user['username']}_{int(__import__('time').time())}{ext}"
            save_path = os.path.join('static', 'uploads', filename)
            # ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            profile_pic = save_path

        conn.execute('UPDATE users SET email = ?, goal = ?, profile_pic = ? WHERE id = ?', (email, goal, profile_pic, user['id']))
        conn.commit()
        flash('Account settings updated.', 'success')
        conn.close()
        return redirect(url_for('account_settings'))

    conn.close()
    return render_template('account_settings.html', user=user)


@app.route('/study_logs')
def study_logs():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    sessions = get_study_sessions_for_user(conn, user)

    # collect distinct subjects
    subjects = sorted({s['subject'] for s in sessions if 'subject' in s.keys()})
    # collect all unique session dates
    session_dates = sorted({(s['date'] if 'date' in s.keys() else (s['created_at'] if 'created_at' in s.keys() else None)) for s in sessions if ('date' in s.keys() or 'created_at' in s.keys())}, reverse=False)

    # get filters from query params
    filter_subject = request.args.get('subject') or None
    start_date = request.args.get('start_date') or None
    end_date = request.args.get('end_date') or None

    # filter sessions by subject and date range
    filtered_sessions = []
    for s in sessions:
        if filter_subject and (s['subject'] if 'subject' in s.keys() else None) != filter_subject:
            continue
        session_date = s['date'] if 'date' in s.keys() else (s['created_at'] if 'created_at' in s.keys() else None)
        if start_date and session_date and session_date < start_date:
            continue
        if end_date and session_date and session_date > end_date:
            continue
        filtered_sessions.append(s)

    # build chart labels and data from filtered_sessions (filtered or all)
    if not filter_subject and not start_date and not end_date:
        chart_sessions = sessions
    else:
        chart_sessions = filtered_sessions

    labels = []
    line_data = []
    date_to_minutes = {}
    if chart_sessions and len(chart_sessions) > 0:
        for s in chart_sessions:
            session_date = s['date'] if 'date' in s.keys() else (s['created_at'] if 'created_at' in s.keys() else None)
            if not session_date:
                continue
            try:
                date_to_minutes[session_date] = date_to_minutes.get(session_date, 0) + int(s['duration'])
            except Exception:
                pass
        for d in sorted(date_to_minutes.keys()):
            labels.append(d)
            line_data.append(date_to_minutes[d])
    else:
        labels = ["No Data"]
        line_data = [0]

    subject_counts = {}
    for s in chart_sessions:
        subj = s['subject'] if 'subject' in s.keys() and s['subject'] else 'Unknown'
        try:
            subject_counts[subj] = subject_counts.get(subj, 0) + (int(s['duration']) if 'duration' in s.keys() and s['duration'] else 0)
        except Exception:
            pass

    pie_labels = list(subject_counts.keys())
    pie_data = [subject_counts[k] for k in pie_labels]

    total_minutes = sum(int(s['duration']) for s in chart_sessions if 'duration' in s.keys() and s['duration'])

    # Remove unreachable/duplicate code and use chart_sessions for all chart calculations
    days_span = max(1, len(labels))
    goal_per_day = int(user['goal'] or 0)
    goal_total = goal_per_day * days_span
    progress_percent = int((total_minutes / goal_total * 100) if goal_total > 0 else 0)
    if progress_percent > 100:
        progress_percent = 100

    conn.close()

    return render_template('study_logs.html', user=user, sessions=filtered_sessions, subjects=subjects,
                           selected_subject=filter_subject, session_dates=session_dates,
                           selected_start_date=start_date, selected_end_date=end_date,
                           labels_json=json.dumps(labels), line_data_json=json.dumps(line_data),
                           pie_labels_json=json.dumps(pie_labels), pie_data_json=json.dumps(pie_data),
                           total_minutes=total_minutes, goal_total=goal_total, progress_percent=progress_percent)

    # (Removed unreachable duplicate chart code)
    progress_percent = int((total_minutes / goal_total * 100) if goal_total > 0 else 0)
    if progress_percent > 100:
        progress_percent = 100

    conn.close()

    return render_template('study_logs.html', user=user, sessions=filtered_sessions, subjects=subjects,
                           selected_subject=filter_subject, view_range=view_range,
                           labels_json=json.dumps(labels), line_data_json=json.dumps(line_data),
                           pie_labels_json=json.dumps(pie_labels), pie_data_json=json.dumps(pie_data),
                           total_minutes=total_minutes, goal_total=goal_total, progress_percent=progress_percent)


@app.route('/add_session', methods=['GET', 'POST'])
def add_session():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']

    if request.method == 'POST':
        subject = request.form['subject'].strip()
        duration = int(request.form['duration'])
        notes = request.form.get('notes', '')
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(study_sessions)").fetchall()]
        # Always record the date, even if the column is missing (for future-proofing)
        if 'user_id' in cols and 'date' in cols:
            conn.execute(
                'INSERT INTO study_sessions (user_id, subject, duration, notes, date) VALUES (?, ?, ?, ?, ?)',
                (user['id'], subject, duration, notes, today)
            )
        elif 'username' in cols and 'date' in cols:
            conn.execute(
                'INSERT INTO study_sessions (username, subject, duration, notes, date) VALUES (?, ?, ?, ?, ?)',
                (user['username'], subject, duration, notes, today)
            )
        elif 'user_id' in cols:
            conn.execute(
                'INSERT INTO study_sessions (user_id, subject, duration, notes) VALUES (?, ?, ?, ?)',
                (user['id'], subject, duration, notes)
            )
        elif 'username' in cols:
            conn.execute(
                'INSERT INTO study_sessions (username, subject, duration, notes) VALUES (?, ?, ?, ?)',
                (user['username'], subject, duration, notes)
            )
        else:
            # Fallback: insert without date
            if 'user_id' in cols:
                conn.execute(
                    'INSERT INTO study_sessions (user_id, subject, duration, notes) VALUES (?, ?, ?, ?)',
                    (user['id'], subject, duration, notes)
                )
            elif 'username' in cols:
                conn.execute(
                    'INSERT INTO study_sessions (username, subject, duration, notes) VALUES (?, ?, ?, ?)',
                    (user['username'], subject, duration, notes)
                )
        conn.commit()
        conn.close()

        flash("Study session added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_session.html')

@app.route('/logout') 
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))


# Edit session route
@app.route('/edit_session/<int:session_id>', methods=['GET', 'POST'])
def edit_session(session_id):
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    # Find session by id
    cols = [r[1] for r in conn.execute("PRAGMA table_info(study_sessions)").fetchall()]
    if 'user_id' in cols:
        session_row = conn.execute('SELECT * FROM study_sessions WHERE id = ? AND user_id = ?', (session_id, user['id'])).fetchone()
    elif 'username' in cols:
        session_row = conn.execute('SELECT * FROM study_sessions WHERE id = ? AND username = ?', (session_id, user['username'])).fetchone()
    else:
        session_row = None

    if not session_row:
        conn.close()
        flash('Session not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        subject = request.form['subject'].strip()
        duration = int(request.form['duration'])
        notes = request.form.get('notes', '')
        if 'date' in session_row.keys():
            if 'user_id' in cols:
                conn.execute('UPDATE study_sessions SET subject=?, duration=?, notes=? WHERE id=? AND user_id=?', (subject, duration, notes, session_id, user['id']))
            elif 'username' in cols:
                conn.execute('UPDATE study_sessions SET subject=?, duration=?, notes=? WHERE id=? AND username=?', (subject, duration, notes, session_id, user['username']))
        else:
            if 'user_id' in cols:
                conn.execute('UPDATE study_sessions SET subject=?, duration=?, notes=? WHERE id=? AND user_id=?', (subject, duration, notes, session_id, user['id']))
            elif 'username' in cols:
                conn.execute('UPDATE study_sessions SET subject=?, duration=?, notes=? WHERE id=? AND username=?', (subject, duration, notes, session_id, user['username']))
        conn.commit()
        conn.close()
        flash('Session updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_session.html', session=session_row)

# Delete session route
@app.route('/delete_session/<int:session_id>', methods=['GET', 'POST'])
def delete_session(session_id):
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(study_sessions)").fetchall()]
    if 'user_id' in cols:
        session_row = conn.execute('SELECT * FROM study_sessions WHERE id = ? AND user_id = ?', (session_id, user['id'])).fetchone()
    elif 'username' in cols:
        session_row = conn.execute('SELECT * FROM study_sessions WHERE id = ? AND username = ?', (session_id, user['username'])).fetchone()
    else:
        session_row = None

    if not session_row:
        conn.close()
        flash('Session not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if 'user_id' in cols:
            conn.execute('DELETE FROM study_sessions WHERE id = ? AND user_id = ?', (session_id, user['id']))
        elif 'username' in cols:
            conn.execute('DELETE FROM study_sessions WHERE id = ? AND username = ?', (session_id, user['username']))
        conn.commit()
        conn.close()
        flash('Session deleted successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('delete_session.html', session=session_row)


if __name__ == '__main__':
    app.run(debug=True)

