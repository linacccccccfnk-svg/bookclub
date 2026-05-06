from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

app = Flask(__name__)
app.secret_key = 'my-super-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_title = db.Column(db.String(200), nullable=False)
    book_author = db.Column(db.String(200))
    book_cover = db.Column(db.String(500))
    book_google_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='want')
    rating = db.Column(db.Integer)
    review = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    print(" Таблицы созданы")

def search_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=12"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        books = []
        for item in data.get('items', []):
            info = item.get('volumeInfo', {})
            books.append({
                'id': item.get('id'),
                'title': info.get('title', 'Нет названия'),
                'authors': ', '.join(info.get('authors', ['Неизвестен'])),
                'cover': info.get('imageLinks', {}).get('thumbnail', '').replace('http://', 'https://'),
                'description': info.get('description', 'Нет описания')
            })
        return books
    except Exception as e:
        print(f"Ошибка API: {e}")
        return []
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
            flash('Имя занято', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email занят', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
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
        flash('Неверные данные', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли', 'info')
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
    return render_template('book.html', book=book)

@app.route('/add_to_library', methods=['POST'])
@login_required
def add_to_library():
    book_google_id = request.form.get('book_google_id')
    book_title = request.form.get('book_title')
    book_author = request.form.get('book_author')
    book_cover = request.form.get('book_cover')
    status = request.form.get('status')
    
    existing = UserBook.query.filter_by(
        user_id=current_user.id,
        book_google_id=book_google_id
    ).first()
    
    if existing:
        existing.status = status
        flash('Статус обновлён', 'info')
    else:
        new_book = UserBook(
            user_id=current_user.id,
            book_title=book_title,
            book_author=book_author,
            book_cover=book_cover,
            book_google_id=book_google_id,
            status=status
        )
        db.session.add(new_book)
        flash('Книга добавлена!', 'success')
    
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    books = UserBook.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', books=books, user=current_user)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = UserBook.query.get_or_404(book_id)
    if book.user_id == current_user.id:
        db.session.delete(book)
        db.session.commit()
        flash('Книга удалена', 'success')
    return redirect(url_for('profile'))

@app.route('/update_status/<int:book_id>', methods=['POST'])
@login_required
def update_status(book_id):
    book = UserBook.query.get_or_404(book_id)
    if book.user_id == current_user.id:
        book.status = request.form.get('status')
        db.session.commit()
        flash('Статус обновлён', 'success')
    return redirect(url_for('profile'))
@app.route('/api/user/<username>/books')
def api_user_books(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return {'error': 'Пользователь не найден'}, 404
    
    books = UserBook.query.filter_by(user_id=user.id).all()
    return {
        'username': user.username,
        'books': [{
            'title': b.book_title,
            'author': b.book_author,
            'status': b.status,
            'rating': b.rating,
            'review': b.review
        } for b in books]
    }
@app.route('/add_review/<int:book_id>', methods=['POST'])
@login_required
def add_review(book_id):
    book = UserBook.query.get_or_404(book_id)
    if book.user_id == current_user.id:
        book.rating = request.form.get('rating', type=int)
        book.review = request.form.get('review', '')
        db.session.commit()
        flash('Оценка и рецензия сохранены!', 'success')
    return redirect(url_for('profile'))
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
