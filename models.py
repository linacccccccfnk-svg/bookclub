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
	__tablename__ = 'user_books'

	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
	book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable = False)
	status = db.Column(db.String(20), default = 'want')  # want, reading, read
	rating = db.Column(db.Integer, default = None)
	review = db.Column(db.Text, default = '')
	date_added = db.Column(db.DateTime, default = datetime.utcnow)

	__table_args__ = (db.UniqueConstraint('user_id', 'book_id', name = 'unique_user_book'),)