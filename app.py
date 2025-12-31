from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# Database Configuration
# Using SQLite for simplicity as requested
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-me' # Consider moving this to env as well for prod

db = SQLAlchemy(app)

# Credentials
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    games = db.relationship('Game', backref='user', lazy=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numbers = db.Column(db.String(50), nullable=False) # Storing as comma-separated string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
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

        # Create User
        new_user = User(full_name=full_name)
        db.session.add(new_user)
        db.session.flush() # Flush to get the new_user.id

        # Create Games
        count = 0
        for game_nums in games_data:
            if count >= 5:
                break # Hard limit
            
            # Basic validation
            if len(game_nums) != 6:
                continue
                
            # Sort and format numbers
            sorted_nums = sorted([int(n) for n in game_nums])
            nums_str = ",".join(map(str, sorted_nums))
            
            new_game = Game(numbers=nums_str, user_id=new_user.id)
            db.session.add(new_game)
            count += 1

        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('success')})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Credenciais inválidas.')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    # Simple admin view - fetch all users
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', users=users)

@app.route('/setup_db')
def setup_db():
    with app.app_context():
        db.create_all()
    return "Database created!"

if __name__ == '__main__':
    # Auto-create DB on first run if not exists
    if not os.path.exists('lottery.db'):
        with app.app_context():
            db.create_all()
            print("Database initialized.")
            
    app.run(debug=True)
