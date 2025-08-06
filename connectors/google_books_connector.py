import requests
import configparser
from .base_connector import BaseConnector

class GoogleBooksConnector(BaseConnector):
    """Google Books API를 사용하여 작품을 검색하는 커넥터"""

    def __init__(self):
        super().__init__('Google Books')
        self.api_url = "https://www.googleapis.com/books/v1/volumes"
        self.api_key = self._load_api_key()

    def _load_api_key(self):
        config = configparser.ConfigParser()
        # config.ini 파일의 경로를 정확히 지정해야 합니다.
        config.read('C:/claude04/classic-isekai/config.ini')
        return config['API_KEYS'].get('GOOGLE_BOOKS_API_KEY')

    def search(self, query, max_results=10):
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            print("Google Books API 키가 설정되지 않았습니다. config.ini 파일을 확인해주세요.")
            return []

        params = {
            'q': query,
            'key': self.api_key,
            'maxResults': max_results,
            'filter': 'free-ebooks'  # 무료 전자책만 검색
        }

        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()  # 오류가 발생하면 예외를 발생시킴
            data = response.json()

            results = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                # 저작권이 명확히 공개된 자료만 필터링
                if volume_info.get('publicDomain', False):
                    results.append({
                        'title': volume_info.get('title', 'N/A'),
                        'author': ", ".join(volume_info.get('authors', [])),
                        'publication_year': int(volume_info.get('publishedDate', '0').split('-')[0]) if volume_info.get('publishedDate') else None,
                        'source_library': self.library_name,
                        'source_url': volume_info.get('infoLink'),
                        'summary': volume_info.get('description')
                    })
            return results
        except requests.exceptions.RequestException as e:
            print(f"Google Books API 요청 중 오류 발생: {e}")
            return []
