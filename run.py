from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests, urllib

app = Flask(__name__)
app.secret_key = 'secret-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ---------- МОДЕЛИ ----------
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True, nullable = False)
	email = db.Column(db.String(120), unique = True, nullable = False)
	password_hash = db.Column(db.String(200), nullable = False)

	def set_password(self, pwd): self.password_hash = generate_password_hash(pwd)

	def check_password(self, pwd): return check_password_hash(self.password_hash, pwd)


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
def load_user(uid): return User.query.get(int(uid))


# ---------- API ----------
def search_books(query):
	url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=12"
	try:
		data = requests.get(url, timeout = 10).json()
		return [{
			'id': item.get('id'),
			'title': item.get('volumeInfo', {}).get('title', 'Нет названия'),
			'authors': ', '.join(item.get('volumeInfo', {}).get('authors', ['Неизвестен'])),
			'cover': item.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail', ''),
			'description': item.get('volumeInfo', {}).get('description', 'Нет описания')
		} for item in data.get('items', [])]
	except:
		return []


# ---------- МАРШРУТЫ ----------
@app.route('/')
def index(): return render_template('index.html')


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
			return redirect(url_for('index'))
		flash('Неверные данные', 'danger')
	return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/search')
def search():
	q = request.args.get('q', '')
	return render_template('search.html', query = q, books = search_books(q) if q else [])


@app.route('/book/<gid>')
def book_detail(gid):
	books = search_books(gid)
	book = books[0] if books else None
	ub = None
	if current_user.is_authenticated and book:
		ub = UserBook.query.filter_by(user_id = current_user.id, book_google_id = gid).first()
	return render_template('book.html', book = book, book_google_id = gid, user_book = ub)


@app.route('/add_to_library', methods = ['POST'])
@login_required
def add_to_library():
	ub = UserBook.query.filter_by(user_id = current_user.id, book_google_id = request.form['book_google_id']).first()
	if ub:
		ub.status = request.form['status']
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
		flash('Книга добавлена', 'success')
	db.session.commit()
	return redirect(url_for('profile'))


@app.route('/update_status/<int:bid>', methods = ['POST'])
@login_required
def update_status(bid):
	ub = UserBook.query.get_or_404(bid)
	if ub.user_id == current_user.id:
		ub.status = request.form['status']
		db.session.commit()
	return redirect(url_for('profile'))


@app.route('/add_review/<int:bid>', methods = ['POST'])
@login_required
def add_review(bid):
	ub = UserBook.query.get_or_404(bid)
	if ub.user_id == current_user.id:
		ub.rating = request.form.get('rating', type = int)
		ub.review = request.form.get('review', '')
		db.session.commit()
		flash('Оценка сохранена', 'success')
	return redirect(url_for('profile'))


@app.route('/delete_book/<int:bid>', methods = ['POST'])
@login_required
def delete_book(bid):
	ub = UserBook.query.get_or_404(bid)
	if ub.user_id == current_user.id:
		db.session.delete(ub)
		db.session.commit()
		flash('Книга удалена', 'success')
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