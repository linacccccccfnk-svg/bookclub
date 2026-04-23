from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from config import Config
from models import db, User, UserBook, Book
from books_api import search_books, get_book_by_id, save_book_to_db
from forms import ReviewForm

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация БД
db.init_app(app)
migrate = Migrate(app, db)

# Инициализация LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# Регистрация blueprint для авторизации
from auth import auth_bp

app.register_blueprint(auth_bp)


# ---------- ГЛАВНАЯ СТРАНИЦА ----------
@app.route('/')
def index():
	"""Главная страница"""
	return render_template('index.html')


# ---------- ПОИСК КНИГ ----------
@app.route('/search')
def search():
	"""Поиск книг через Google Books API"""
	query = request.args.get('q', '')
	books = []

	if query:
		books = search_books(query)

	return render_template('search.html', query = query, books = books)


# ---------- СТРАНИЦА КНИГИ ----------
@app.route('/book/<google_id>')
def book_detail(google_id):
	"""Страница с подробной информацией о книге"""
	# Получаем данные книги из Google API
	book = get_book_by_id(google_id)
	if not book:
		return "Книга не найдена", 404

	# Проверяем, есть ли эта книга в библиотеке текущего пользователя
	user_book = None
	if current_user.is_authenticated:
		# Сначала находим книгу в нашей БД
		db_book = Book.query.filter_by(google_books_id = google_id).first()
		if db_book:
			# Затем находим связь пользователя с этой книгой
			user_book = UserBook.query.filter_by(
				user_id = current_user.id,
				book_id = db_book.id
			).first()

	# Создаём форму для оценки и рецензии
	form = ReviewForm()

	# Если книга уже в библиотеке, заполняем форму текущими значениями
	if user_book:
		form.rating.data = user_book.rating
		form.review.data = user_book.review
		form.status.data = user_book.status

	return render_template('book.html',
	                       book = book,
	                       user_book = user_book,
	                       form = form)


# ---------- ДОБАВЛЕНИЕ КНИГИ В БИБЛИОТЕКУ ----------
@app.route('/add_book/<google_id>', methods = ['POST'])
@login_required
def add_book(google_id):
	"""Добавляет книгу в библиотеку пользователя"""
	# Получаем статус из формы (want/reading/read)
	status = request.form.get('status', 'want')

	# Получаем данные книги из Google API
	book_data = get_book_by_id(google_id)
	if not book_data:
		return "Книга не найдена", 404

	# Сохраняем книгу в БД (если её там ещё нет)
	book = save_book_to_db(book_data)

	# Проверяем, не добавлял ли пользователь уже эту книгу
	existing_entry = UserBook.query.filter_by(
		user_id = current_user.id,
		book_id = book.id
	).first()

	if existing_entry:
		# Если уже есть, просто обновляем статус
		existing_entry.status = status
		flash(f'Статус книги "{book.title}" обновлён!', 'info')
	else:
		# Создаём новую запись в user_books
		user_book = UserBook(
			user_id = current_user.id,
			book_id = book.id,
			status = status
		)
		db.session.add(user_book)
		flash(f'Книга "{book.title}" добавлена в библиотеку!', 'success')

	db.session.commit()
	return redirect(url_for('book_detail', google_id = google_id))


# ---------- ОБНОВЛЕНИЕ ОЦЕНКИ И РЕЦЕНЗИИ ----------
@app.route('/update_review/<google_id>', methods = ['POST'])
@login_required
def update_review(google_id):
	"""Обновляет оценку и рецензию на книгу"""
	form = ReviewForm()

	if form.validate_on_submit():
		# Получаем данные книги из Google API
		book_data = get_book_by_id(google_id)
		if not book_data:
			return "Книга не найдена", 404

		# Сохраняем книгу в БД
		book = save_book_to_db(book_data)

		# Находим запись о книге в библиотеке пользователя
		user_book = UserBook.query.filter_by(
			user_id = current_user.id,
			book_id = book.id
		).first()

		if user_book:
			# Обновляем поля
			user_book.rating = form.rating.data
			user_book.review = form.review.data
			if form.status.data:
				user_book.status = form.status.data
			db.session.commit()
			flash('Оценка и рецензия сохранены!', 'success')
		else:
			flash('Сначала добавьте книгу в библиотеку', 'warning')

	return redirect(url_for('book_detail', google_id = google_id))


# ---------- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ----------
@app.route('/profile')
@login_required
def profile():
	"""Страница профиля пользователя с его библиотекой"""
	# Получаем книги пользователя с разными статусами
	want_books = UserBook.query.filter_by(user_id = current_user.id, status = 'want').all()
	reading_books = UserBook.query.filter_by(user_id = current_user.id, status = 'reading').all()
	read_books = UserBook.query.filter_by(user_id = current_user.id, status = 'read').all()

	return render_template('profile.html',
	                       user = current_user,
	                       want_books = want_books,
	                       reading_books = reading_books,
	                       read_books = read_books)


# ---------- ЗАПУСК ПРИЛОЖЕНИЯ ----------
if __name__ == '__main__':
	app.run(debug = True)