import requests


def search_books(query, max_results = 12):
	#Поиск книг через Google Books API

	if not query:
		return []

	url = "https://www.googleapis.com/books/v1/volumes"
	params = {
		'q': query,
		'maxResults': max_results,
		'langRestrict': 'ru',
		'printType': 'books'
	}

	try:
		response = requests.get(url, params = params, timeout = 10)
		data = response.json()

		books = []

		for item in data.get('items', []):
			volume_info = item.get('volumeInfo', {})
			book = {
				'google_id': item.get('id'),
				'title': volume_info.get('title', 'Название не указано'),
				'authors': ', '.join(volume_info.get('authors', ['Автор не указан'])),
				'description': volume_info.get('description', 'Описание отсутствует'),
				'cover_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
				'published_year': volume_info.get('publishedDate', '')[:4],
				'page_count': volume_info.get('pageCount', ''),
				'categories': ', '.join(volume_info.get('categories', ['Без категории']))
			}
			books.append(book)

		return books

	except Exception as e:
		print(f"Ошибка API: {e}")
		return []


def get_book_by_id(google_id):
	#Получение информации о конкретной книге по ID

	url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"

	try:
		response = requests.get(url, timeout = 10)
		item = response.json()

		volume_info = item.get('volumeInfo', {})

		book = {
			'google_id': item.get('id'),
			'title': volume_info.get('title', 'Название не указано'),
			'authors': ', '.join(volume_info.get('authors', ['Автор не указан'])),
			'description': volume_info.get('description', 'Описание отсутствует'),
			'cover_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
			'published_year': volume_info.get('publishedDate', '')[:4],
			'page_count': volume_info.get('pageCount', 'Не указано'),
			'categories': ', '.join(volume_info.get('categories', ['Без категории']))
		}
		return book

	except Exception as e:
		print(f"Ошибка получения книги: {e}")
		return None