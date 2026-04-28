from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import urllib.parse

app = Flask(__name__)
app.secret_key = 'secret-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True, nullable = False)
	email = db.Column(db.String(120), unique = True, nullable = False)
	password_hash = db.Column(db.String(200), nullable = False)

	def set_password(self, pwd):
		self.password_hash = generate_password_hash(pwd)

	def check_password(self, pwd):
		return check_password_hash(self.password_hash, pwd)


class UserBook(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	book_title = db.Column(db.String(200))
	book_author = db.Column(db.String(200))
	book_cover = db.Column(db.String(500))
	book_google_id = db.Column(db.String(100))
	status = db.Column(db.String(20), default = 'want')
	rating = db.Column(db.Integer)
	review = db.Column(db.Text)


@login_manager.user_loader
def load_user(uid):
	return User.query.get(int(uid))


def search_books(query):
	# Поиск книг через Open Library API
	if not query:
		return []

	encoded_query = urllib.parse.quote(query)
	url = f"https://openlibrary.org/search.json?q={encoded_query}&limit=12"

	print(f"Запрос к Open Library: {url}")

	try:
		response = requests.get(url, timeout = 10)
		print(f"Статус: {response.status_code}")

		if response.status_code != 200:
			print(f"Ошибка: статус {response.status_code}")
			return []

		data = response.json()
		books = []

		for doc in data.get('docs', []):
			# Получаем ID обложки
			cover_id = doc.get('cover_i')
			cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

			# Получаем описание
			description = doc.get('first_sentence', ['Нет описания'])[0]
			if not description or description == 'Нет описания':
				description = f"Книга {doc.get('title', '')} автора {', '.join(doc.get('author_name', ['неизвестного']))}"

			book = {
				'id': doc.get('key', '').replace('/works/', ''),
				'title': doc.get('title', 'Нет названия'),
				'authors': ', '.join(doc.get('author_name', ['Неизвестен'])),
				'cover': cover_url,
				'description': description[:300]
			}
			books.append(book)
			print(f"Добавлена: {book['title'][:50]}")

		print(f"Найдено книг: {len(books)}")
		return books

	except Exception as e:
		print(f"Ошибка: {e}")
		return []


def get_book_details(book_id):
	# Получение деталей книги из Open Library
	url = f"https://openlibrary.org/works/{book_id}.json"

	try:
		response = requests.get(url, timeout = 10)
		data = response.json()

		cover_id = data.get('covers', [None])[0]
		cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else ""

		description = data.get('description', 'Нет описания')
		if isinstance(description, dict):
			description = description.get('value', 'Нет описания')

		return {
			'id': book_id,
			'title': data.get('title', 'Нет названия'),
			'authors': data.get('authors', [{}])[0].get('name', 'Автор не указан') if data.get(
				'authors') else 'Автор не указан',
			'cover': cover_url,
			'description': description
		}
	except Exception as e:
		print(f"Ошибка получения деталей: {e}")
		return None


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/register', methods = ['GET', 'POST'])
def register():
	if request.method == 'POST':
		if User.query.filter_by(username = request.form['username']).first():
			flash('Имя занято', 'danger')
		elif User.query.filter_by(email = request.form['email']).first():
			flash('Email занят', 'danger')
		else:
			user = User(username = request.form['username'], email = request.form['email'])
			user.set_password(request.form['password'])
			db.session.add(user)
			db.session.commit()
			flash('Регистрация успешна!', 'success')
			return redirect(url_for('login'))
	return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		user = User.query.filter_by(username = request.form['username']).first()
		if user and user.check_password(request.form['password']):
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


@app.route('/search', methods = ['GET'])
def search():
	query = request.args.get('q', '')
	books = search_books(query) if query else []
	return render_template('search.html', query = query, books = books)


@app.route('/book/<book_id>')
def book_detail(book_id):
	book = get_book_details(book_id)

	if not book:
		flash('Книга не найдена', 'danger')
		return redirect(url_for('search'))

	user_book = None
	if current_user.is_authenticated:
		user_book = UserBook.query.filter_by(
			user_id = current_user.id,
			book_google_id = book_id
		).first()

	return render_template('book.html', book = book, book_google_id = book_id, user_book = user_book)


@app.route('/add_to_library', methods = ['POST'])
@login_required
def add_to_library():
	user_book = UserBook.query.filter_by(
		user_id = current_user.id,
		book_google_id = request.form['book_google_id']
	).first()

	if user_book:
		user_book.status = request.form['status']
		flash('Статус обновлён', 'success')
	else:
		db.session.add(UserBook(
			user_id = current_user.id,
			book_title = request.form['book_title'],
			book_author = request.form['book_author'],
			book_cover = request.form['book_cover'],
			book_google_id = request.form['book_google_id'],
			status = request.form['status']
		))
		flash('Книга добавлена в библиотеку!', 'success')

	db.session.commit()
	return redirect(url_for('profile'))


@app.route('/update_status/<int:bid>', methods = ['POST'])
@login_required
def update_status(bid):
	user_book = UserBook.query.get_or_404(bid)
	if user_book.user_id == current_user.id:
		user_book.status = request.form['status']
		db.session.commit()
		flash('Статус обновлён', 'success')
	return redirect(url_for('profile'))


@app.route('/add_review/<int:bid>', methods = ['POST'])
@login_required
def add_review(bid):
	user_book = UserBook.query.get_or_404(bid)
	if user_book.user_id == current_user.id:
		rating = request.form.get('rating')
		user_book.rating = int(rating) if rating else None
		user_book.review = request.form.get('review', '')
		db.session.commit()
		flash('Оценка и рецензия сохранены!', 'success')
	return redirect(url_for('profile'))


@app.route('/delete_book/<int:bid>', methods = ['POST'])
@login_required
def delete_book(bid):
	user_book = UserBook.query.get_or_404(bid)
	if user_book.user_id == current_user.id:
		db.session.delete(user_book)
		db.session.commit()
		flash('Книга удалена из библиотеки', 'success')
	return redirect(url_for('profile'))


@app.route('/profile')
@login_required
def profile():
	books = UserBook.query.filter_by(user_id = current_user.id).all()
	return render_template('profile.html',
	                       want = [b for b in books if b.status == 'want'],
	                       reading = [b for b in books if b.status == 'reading'],
	                       read = [b for b in books if b.status == 'read'])


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug = True)
