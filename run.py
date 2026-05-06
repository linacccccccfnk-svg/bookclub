from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'my-super-secret-key-for-local-dev-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# СОЗДАНИЕ ТАБЛИЦ — ЭТО САМОЕ ВАЖНОЕ!
with app.app_context():
    db.create_all()
    print("✅ База данных и таблицы созданы!")

# Поиск книг через API
def search_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
    try:
        response = requests.get(url)
        data = response.json()
        books = []
        for item in data.get('items', []):
            info = item.get('volumeInfo', {})
            books.append({
                'id': item.get('id'),
                'title': info.get('title', 'Нет названия'),
                'authors': ', '.join(info.get('authors', ['Неизвестен'])),
                'cover': info.get('imageLinks', {}).get('thumbnail', ''),
                'description': info.get('description', 'Нет описания')
            })
        return books
    except:
        return []

# Маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    books = search_books(query) if query else []
    return render_template('search.html', query=query, books=books)

@app.route('/book/<book_id>')
def book_detail(book_id):
    books = search_books(book_id)
    book = books[0] if books else None
    return render_template('book.html', book=book, book_google_id=book_id)

@app.route('/add_to_library', methods=['POST'])
@login_required
def add_to_library():
    # Здесь будет логика добавления в библиотеку
    flash('Книга добавлена в библиотеку!', 'success')
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)
@app.route('/api/user/<username>/books')
def api_user_books(username):
    """REST API: возвращает список книг пользователя в JSON"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return {"error": "Пользователь не найден"}, 404
    
    books = UserBook.query.filter_by(user_id=user.id).all()
    
    result = {
        "username": user.username,
        "books": [
            {
                "title": b.book_title,
                "author": b.book_author,
                "status": b.status,
                "rating": b.rating,
                "review": b.review
            } for b in books
        ]
    }
    
    return result
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
