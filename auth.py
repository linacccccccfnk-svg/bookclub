from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods = ['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	if request.method == 'POST':
		username = request.form.get('username')
		email = request.form.get('email')
		password = request.form.get('password')
		confirm = request.form.get('confirm_password')

		# Проверки
		error = None
		if not username or not email or not password:
			error = 'Заполните все поля'
		elif password != confirm:
			error = 'Пароли не совпадают'
		elif User.query.filter_by(username = username).first():
			error = 'Имя пользователя уже занято'
		elif User.query.filter_by(email = email).first():
			error = 'Email уже зарегистрирован'

		if error:
			flash(error, 'danger')
		else:
			user = User(username = username, email = email)
			user.set_password(password)
			db.session.add(user)
			db.session.commit()
			flash('Регистрация успешна! Теперь войдите.', 'success')
			return redirect(url_for('auth.login'))

	return render_template('register.html')


@auth_bp.route('/login', methods = ['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')

		user = User.query.filter_by(email = email).first()
		if user and user.check_password(password):
			login_user(user)
			flash(f'Добро пожаловать, {user.username}!', 'success')
			return redirect(url_for('index'))
		else:
			flash('Неверный email или пароль', 'danger')

	return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Вы вышли из системы', 'info')
	return redirect(url_for('index'))