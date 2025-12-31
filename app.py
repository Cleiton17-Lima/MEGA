from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# ==============================
# DATABASE CONFIG (LOCAL + RENDER)
# ==============================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL')

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # Corrige prefixo antigo
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # Fallback local (somente para DEV)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(DB_DIR, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(DB_DIR, 'lottery.db')}"


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

db = SQLAlchemy(app)

# ==============================
# MODELS
# ==============================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    games = db.relationship('Game', backref='user', lazy=True, cascade="all, delete-orphan")


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numbers = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ==============================
# CREATE DATABASE
# ==============================

with app.app_context():
    db.create_all()

# ==============================
# ADMIN CREDENTIALS
# ==============================

ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

# ==============================
# ROUTES
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        full_name = data.get('fullName')
        games_data = data.get('games')

        if not full_name or not games_data:
            return jsonify({'success': False, 'message': 'Missing data'}), 400

        # Enforce exact 5 games
        if len(games_data) != 5:
            return jsonify({'success': False, 'message': 'É obrigatório fazer exatamente 5 jogos.'}), 400

        new_user = User(full_name=full_name)
        db.session.add(new_user)
        db.session.flush()

        for game_nums in games_data:
            if len(game_nums) != 6:
                continue

            sorted_nums = sorted(map(int, game_nums))
            nums_str = ",".join(map(str, sorted_nums))

            db.session.add(Game(numbers=nums_str, user_id=new_user.id))

        db.session.commit()
        
        # Calculate total for redirect
        total_val = len(games_data) * 6
        return jsonify({'success': True, 'redirect': url_for('success', val=total_val)})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/success')
def success():
    val = request.args.get('val', 0)
    try:
        val = float(val)
    except:
        val = 0
    return render_template('success.html', total=val)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash('Credenciais inválidas')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', users=users)


# ==============================
# RUN
# ==============================

if __name__ == '__main__':
    app.run(debug=True)
