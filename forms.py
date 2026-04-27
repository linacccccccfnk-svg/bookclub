from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from models import User


class RegistrationForm(FlaskForm):
	username = StringField('Имя пользователя',
	                       validators = [DataRequired(), Length(min = 3, max = 80)])
	email = StringField('Email',
	                    validators = [DataRequired(), Email()])
	password = PasswordField('Пароль',
	                         validators = [DataRequired(), Length(min = 6)])
	confirm_password = PasswordField('Подтвердите пароль',
	                                 validators = [DataRequired(), EqualTo('password')])
	submit = SubmitField('Зарегистрироваться')

	def validate_username(self, username):
		user = User.query.filter_by(username = username.data).first()
		if user:
			raise ValidationError('Это имя уже занято. Выберите другое.')

	def validate_email(self, email):
		user = User.query.filter_by(email = email.data).first()
		if user:
			raise ValidationError('Этот email уже зарегистрирован.')


class LoginForm(FlaskForm):
	email = StringField('Email', validators = [DataRequired(), Email()])
	password = PasswordField('Пароль', validators = [DataRequired()])
	submit = SubmitField('Войти')


class ReviewForm(FlaskForm):
	rating = IntegerField('Оценка (1-5)',
	                      validators = [NumberRange(min = 1, max = 5)],
	                      default = None)
	review = TextAreaField('Рецензия', validators = [Length(max = 1000)])
	status = StringField('Статус')
	submit = SubmitField('Сохранить')