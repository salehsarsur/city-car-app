from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps
import os
import bcrypt

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key for session encryption
app.permanent_session_lifetime = timedelta(minutes=30)  # Session lasts 30 min
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ Models ------------------

class Car(db.Model):
    license_plate = db.Column(db.String(20), primary_key=True)
    color = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    owner = db.Column(db.String(100), nullable=False)

# ------------------ Utility ------------------

def get_passcode_hash():
    return os.getenv("PASSCODE_HASH", "")

def check_passcode(passcode):
    load_dotenv(override=True)  # 🔁 Reloads updated .env each time
    stored_hash = get_passcode_hash().encode()
    return bcrypt.checkpw(passcode.encode(), stored_hash)


def update_passcode(new_passcode):
    hashed = bcrypt.hashpw(new_passcode.encode(), bcrypt.gensalt())
    with open(".env", "w") as f:
        f.write(f"PASSCODE_HASH={hashed.decode()}")
        
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        load_dotenv(override=True)  # Make sure we get updated .env
        current_hash = get_passcode_hash()
        session_hash = session.get('passcode_hash')

        if not session.get('logged_in') or session_hash != current_hash:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ------------------ Routes ------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passcode = request.form['passcode']
        if check_passcode(passcode):
            session.permanent = True
            session['logged_in'] = True
            session['passcode_hash'] = get_passcode_hash()
            return redirect(url_for('home'))
        return render_template('invalid.html'), 403
    return render_template('login.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        color = request.form['color']
        type_ = request.form['type']
        owner = request.form['owner']
        if not all([license_plate, color, type_, owner]):
            return "All fields are required", 400
        car = Car(license_plate=license_plate, color=color, type=type_, owner=owner)
        try:
            db.session.add(car)
            db.session.commit()
            return redirect(url_for('home'))
        except:
            return "Car with that license plate already exists", 400
    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    results = []
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        color = request.form['color']
        type_ = request.form['type']
        owner = request.form['owner']

        query = Car.query
        if license_plate:
            query = query.filter_by(license_plate=license_plate)
        if color:
            query = query.filter_by(color=color)
        if type_:
            query = query.filter_by(type=type_)
        if owner:
            query = query.filter_by(owner=owner)

        results = query.all()
    return render_template('search.html', results=results)

@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        car = db.session.get(Car, license_plate)
        if car:
            db.session.delete(car)
            db.session.commit()
            return redirect(url_for('home'))
        message = "Car not found"
    return render_template('delete.html', message = message)

@app.route('/change', methods=['GET', 'POST'])
def change_passcode():
    if request.method == 'POST':
        new_passcode = request.form['new_passcode']
        update_passcode(new_passcode)
        return "Passcode updated successfully!"
    return '''
        <form method="post">
            <input type="password" name="new_passcode" placeholder="New Passcode" required>
            <input type="submit" value="Change Passcode">
        </form>
    '''

# ------------------ Run ------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
