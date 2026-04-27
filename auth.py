from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True, nullable = False)
	email = db.Column(db.String(120), unique = True, nullable = False)
	password = db.Column(db.String(200), nullable = False)


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


@app.route('/')
def index():
	if current_user.is_authenticated:
		return f'Привет, {current_user.username}! <a href="/logout">Выйти</a>'
	return 'Привет! <a href="/login">Войдите</a> или <a href="/register">зарегистрируйтесь</a>'


@app.route('/register', methods = ['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form['username']
		email = request.form['email']
		password = request.form['password']

		if User.query.filter_by(username = username).first():
			flash('Имя уже занято')
			return redirect(url_for('register'))

		if User.query.filter_by(email = email).first():
			flash('Email уже занят')
			return redirect(url_for('register'))

		user = User(username = username, email = email, password = password)
		db.session.add(user)
		db.session.commit()

		flash('Регистрация успешна! Теперь войдите.')
		return redirect(url_for('login'))

	return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']

		print(f"=== ПОПЫТКА ВХОДА ===")
		print(f"Email: {email}")
		print(f"Пароль: {password}")

		# Ищем пользователя
		user = User.query.filter_by(email = email).first()

		if user:
			print(f"Пользователь найден: {user.username}")
			print(f"Пароль в БД: {user.password}")
			print(f"Пароли совпадают? {user.password == password}")
		else:
			print("Пользователь НЕ найден!")

		if user and user.password == password:
			login_user(user)
			flash('Вход выполнен!')
			return redirect(url_for('index'))
		else:
			flash('Неверный email или пароль')
			print("=== ВХОД НЕ УДАЛСЯ ===")


	return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Вы вышли')
	return redirect(url_for('index'))


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug = True)