import requests
from models import db, Book


def search_books(query, max_results = 20):
	"""Поиск книг в Google Books API"""
	url = "https://www.googleapis.com/books/v1/volumes"
	params = {
		'q': query,
		'maxResults': max_results,
		'langRestrict': 'ru'
	}

	try:
		response = requests.get(url, params = params)
		response.raise_for_status()
		data = response.json()

		books = []
		for item in data.get('items', []):
			volume_info = item.get('volumeInfo', {})
			book = {
				'google_id': item.get('id'),
				'title': volume_info.get('title', 'Без названия'),
				'authors': ', '.join(volume_info.get('authors', ['Автор не указан'])),
				'description': volume_info.get('description', 'Описание отсутствует'),
				'cover_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
				'published_year': volume_info.get('publishedDate', '')[:4]
			}
			books.append(book)

		return books

	except requests.exceptions.RequestException as e:
		print(f"Ошибка API: {e}")
		return []


def get_book_by_id(google_id):
	"""Получение информации об одной книге по её Google ID"""
	url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"

	try:
		response = requests.get(url)
		response.raise_for_status()
		item = response.json()

		volume_info = item.get('volumeInfo', {})
		book = {
			'google_id': item.get('id'),
			'title': volume_info.get('title', 'Без названия'),
			'authors': ', '.join(volume_info.get('authors', ['Автор не указан'])),
			'description': volume_info.get('description', 'Описание отсутствует'),
			'cover_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
			'published_year': volume_info.get('publishedDate', '')[:4],
			'page_count': volume_info.get('pageCount', 'Не указано'),
			'categories': ', '.join(volume_info.get('categories', ['Без категории']))
		}
		return book

	except requests.exceptions.RequestException as e:
		print(f"Ошибка API: {e}")
		return None


def save_book_to_db(book_data):
	"""Сохраняет книгу в базу данных, если её там ещё нет"""
	existing_book = Book.query.filter_by(google_books_id = book_data['google_id']).first()

	if existing_book:
		return existing_book

	new_book = Book(
		google_books_id = book_data['google_id'],
		title = book_data['title'],
		authors = book_data['authors'],
		description = book_data.get('description', ''),
		cover_url = book_data.get('cover_url', ''),
		published_year = book_data.get('published_year', '')
	)

	db.session.add(new_book)
	db.session.commit()

	return new_book