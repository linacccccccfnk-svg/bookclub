from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True, nullable = False)
	email = db.Column(db.String(120), unique = True, nullable = False)
	password_hash = db.Column(db.String(200), nullable = False)
	avatar = db.Column(db.String(200), default = 'default.jpg')
	bio = db.Column(db.Text, default = '')
	created_at = db.Column(db.DateTime, default = datetime.utcnow)

	books = db.relationship('UserBook', backref = 'user', lazy = True)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return f'<User {self.username}>'


class Book(db.Model):
	__tablename__ = 'books'

	id = db.Column(db.Integer, primary_key = True)
	google_books_id = db.Column(db.String(100), unique = True, nullable = False)
	title = db.Column(db.String(200), nullable = False)
	authors = db.Column(db.String(500), default = '')
	description = db.Column(db.Text, default = '')
	cover_url = db.Column(db.String(500), default = '')
	published_year = db.Column(db.String(20), default = '')

	users = db.relationship('UserBook', backref = 'book', lazy = True)

	def __repr__(self):
		return f'<Book {self.title}>'


class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_title = db.Column(db.String(200))
    book_author = db.Column(db.String(200))
    book_cover = db.Column(db.String(500))
    book_google_id = db.Column(db.String(100))  # ← ЭТО ПОЛЕ ДОЛЖНО БЫТЬ!
    status = db.Column(db.String(20), default='want')
    rating = db.Column(db.Integer)
    review = db.Column(db.Text)
