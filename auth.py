from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User
from forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods = ['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(
			username = form.username.data,
			email = form.email.data
		)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Регистрация успешна! Теперь вы можете войти.', 'success')
		return redirect(url_for('auth.login'))

	return render_template('register.html', form = form)


@auth_bp.route('/login', methods = ['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user and user.check_password(form.password.data):
			login_user(user)
			flash(f'Добро пожаловать, {user.username}!', 'success')
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('index'))
		else:
			flash('Неверный email или пароль', 'danger')

	return render_template('login.html', form = form)


@auth_bp.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Вы вышли из системы', 'info')
	return redirect(url_for('index'))