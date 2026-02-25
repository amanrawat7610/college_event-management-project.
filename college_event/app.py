from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "college_event_final_perfect_version"

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'college_event.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Fixed Master Key (Bina kisi space ke dalo: admin@786)
MASTER_KEY = "admin@786"

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)

with app.app_context():
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    db.create_all()

# --- Main Routes ---

@app.route('/')
def dashboard():
    all_events = Event.query.all()
    total = Student.query.count()
    return render_template('dashboard.html', events=all_events, total_reg=total)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.form.get('master_key').strip() != MASTER_KEY:
            flash("Invalid Master Key!", "danger")
            return redirect(url_for('signup'))
        
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        try:
            db.session.add(User(email=request.form.get('email').strip(), password=hashed_pw))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash("Email already registered!", "danger")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email').strip()).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials", "danger")
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        m_key = request.form.get('master_key').strip()
        u_email = request.form.get('email').strip()
        new_p = request.form.get('new_password').strip()

        if m_key != MASTER_KEY:
            flash("Wrong Master Key!", "danger")
            return redirect(url_for('forgot_password'))

        user = User.query.filter_by(email=u_email).first()
        if user:
            user.password = generate_password_hash(new_p, method='pbkdf2:sha256')
            db.session.commit()
            flash("Password Reset Successful! Please Login.", "success")
            return redirect(url_for('login'))
        flash("Email not found!", "danger")
    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Form data save karna
            new_s = Student(
                roll_no=request.form['roll_no'],
                name=request.form['name'],
                branch=request.form['branch'],
                year=request.form['year'], # Dropdown value yahan aayegi
                phone=request.form['phone'],
                event_name=request.form['event']
            )
            db.session.add(new_s)
            db.session.commit()
            flash("Registration Successful!", "success") # Green message ke liye
            return redirect(url_for('register'))
        except:
            db.session.rollback()
            flash("Error: Roll Number already exists!", "danger")
    return render_template('register.html')

@app.route('/add_event', methods=['POST'])
def add_event():
    if session.get('logged_in'):
        db.session.add(Event(name=request.form['event_name'], date=request.form['event_date']))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_event/<int:id>')
def delete_event(id):
    if session.get('logged_in'):
        event = Event.query.get(id)
        db.session.delete(event)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/students')
def view_students():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('view_students.html', students=Student.query.all())

@app.route('/logout')
def logout():
    session.clear()
    flash("Logout successfully!", "success") # Ye message 'success' category mein jayega
    return redirect(url_for('login'))

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if session.get('logged_in'):
        student = Student.query.get(id)
        if student:
            db.session.delete(student)
            db.session.commit()
            flash("Student record deleted!", "success")
    return redirect(url_for('view_students'))
@app.after_request
def add_header(response):
    # Ye headers browser ko page save karne se rokte hain
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)