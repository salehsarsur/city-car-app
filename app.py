from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import psycopg2
import bcrypt
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = 'super-secret-key'  # change this!
db_url = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(db_url)

@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect('/login')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_pass = request.form['passcode'].encode('utf-8')
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT passcode_hash FROM settings ORDER BY id DESC LIMIT 1")
        hashed = cur.fetchone()[0].encode('utf-8')
        conn.close()
        if bcrypt.checkpw(input_pass, hashed):
            session['authenticated'] = True
            return redirect('/')
        return "Invalid passcode", 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/add', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        color = request.form['color']
        type_ = request.form['type']
        owner_name = request.form['owner_name']

        if not all([license_plate, color, type_, owner_name]):
            return "All fields required", 400

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO cars VALUES (%s, %s, %s, %s)",
                        (license_plate, color, type_, owner_name))
            conn.commit()
        except:
            return "Car already exists", 400
        finally:
            conn.close()
        return redirect('/')
    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        filters = {
            "license_plate": request.form['license_plate'],
            "color": request.form['color'],
            "type": request.form['type'],
            "owner_name": request.form['owner_name']
        }
        conditions = []
        values = []

        for key, value in filters.items():
            if value:
                conditions.append(f"{key} ILIKE %s")
                values.append(f"%{value}%")

        sql = "SELECT * FROM cars"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, values)
        results = cur.fetchall()
        conn.close()
        return render_template('search.html', results=results)
    return render_template('search.html')

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        plate = request.form['license_plate']
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM cars WHERE license_plate = %s", (plate,))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('delete.html')

@app.route('/change_passcode', methods=['POST'])
def change_passcode():
    old = request.form['old_pass'].encode('utf-8')
    new = request.form['new_pass'].encode('utf-8')

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT passcode_hash FROM settings ORDER BY id DESC LIMIT 1")
    current_hash = cur.fetchone()[0].encode('utf-8')
    if not bcrypt.checkpw(old, current_hash):
        conn.close()
        return "Incorrect current passcode", 403

    new_hash = bcrypt.hashpw(new, bcrypt.gensalt()).decode('utf-8')
    cur.execute("INSERT INTO settings (passcode_hash) VALUES (%s)", (new_hash,))
    conn.commit()
    conn.close()
    return redirect('/')
