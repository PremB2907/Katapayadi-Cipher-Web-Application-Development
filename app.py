from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'katapayadi-microproject-2024-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///katapayadi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

# Database setup
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Katapayadi Encoding System
class Katapayadi:
    # Sanskrit consonants mapping to numbers
    CONSONANT_MAP = {
        'क': 1, 'ख': 2, 'ग': 3, 'घ': 4, 'ङ': 5,
        'च': 6, 'छ': 7, 'ज': 8, 'झ': 9, 'ञ': 0,
        'ट': 1, 'ठ': 2, 'ड': 3, 'ढ': 4, 'ण': 5,
        'त': 6, 'थ': 7, 'द': 8, 'ध': 9, 'न': 0,
        'प': 1, 'फ': 2, 'ब': 3, 'भ': 4, 'म': 5,
        'य': 1, 'र': 2, 'ल': 3, 'व': 4, 'श': 5,
        'ष': 6, 'स': 7, 'ह': 8, 'ळ': 9, 'क्ष': 0,
        'ज्ञ': 0
    }
    
    # Reverse mapping for decoding
    NUMBER_MAP = {
        0: ['ञ', 'न', 'क्ष', 'ज्ञ'],
        1: ['क', 'ट', 'प', 'य'],
        2: ['ख', 'ठ', 'फ', 'र'],
        3: ['ग', 'ड', 'ब', 'ल'],
        4: ['घ', 'ढ', 'भ', 'व'],
        5: ['ङ', 'ण', 'म', 'श'],
        6: ['च', 'त', 'ष'],
        7: ['छ', 'थ', 'स'],
        8: ['ज', 'द', 'ह'],
        9: ['झ', 'ध', 'ळ']
    }
    
    @staticmethod
    def encode(text, key=0):
        """Encode text using Katapayadi system"""
        result = []
        for char in text:
            if char in Katapayadi.CONSONANT_MAP:
                num = Katapayadi.CONSONANT_MAP[char]
                # Apply key transformation
                encoded_num = (num + key) % 10
                result.append(str(encoded_num))
            elif char.isdigit():
                result.append(char)
            elif char in 'अआइईउऊऋऌएऐओऔँंः':
                # Vowels and special marks - keep as separators
                result.append(' ')
            else:
                result.append(char)
        
        # Group numbers as per traditional Katapayadi (right to left)
        encoded_text = ''.join(result).strip()
        # Remove spaces between numbers
        encoded_text = re.sub(r'(\d)\s+(\d)', r'\1\2', encoded_text)
        return encoded_text
    
    @staticmethod
    def decode(numbers, key=0):
        """Decode numbers back to Sanskrit consonants"""
        if not numbers:
            return ""
        
        result = []
        for num_char in str(numbers):
            if num_char.isdigit():
                num = int(num_char)
                # Reverse key transformation
                original_num = (num - key) % 10
                if original_num in Katapayadi.NUMBER_MAP:
                    # Use first consonant for simplicity
                    result.append(Katapayadi.NUMBER_MAP[original_num][0])
                else:
                    result.append('?')
            else:
                result.append(num_char)
        
        return ''.join(result)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('index.html', show_login=True, page='login')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('home'))
    
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', show_dashboard=True, page='dashboard')

@app.route('/encode')
@login_required
def encode_page():
    return render_template('index.html', page='encode', show_dashboard=True)

@app.route('/api/encode', methods=['POST'])
@login_required
def encode_text():
    data = request.get_json()
    text = data.get('text', '')
    key = int(data.get('key', 0))
    
    encoded = Katapayadi.encode(text, key)
    return jsonify({
        'encoded': encoded,
        'original': text,
        'key': key
    })

@app.route('/decode')
@login_required
def decode_page():
    return render_template('index.html', page='decode', show_dashboard=True)

@app.route('/api/decode', methods=['POST'])
@login_required
def decode_text():
    data = request.get_json()
    numbers = data.get('numbers', '')
    key = int(data.get('key', 0))
    
    decoded = Katapayadi.decode(numbers, key)
    return jsonify({
        'decoded': decoded,
        'original': numbers,
        'key': key
    })

@app.route('/admin')
@login_required
def admin():
    if current_user.username != 'admin':
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('index.html', show_admin=True, page='admin', users=users)

@app.route('/about')
def about():
    return render_template('index.html', page='about')

@app.route('/system')
def system():
    return render_template('index.html', page='system')

# Initialize database
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin/admin123")

if __name__ == '__main__':
    app.run(debug=True, port=5000)