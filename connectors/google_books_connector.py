import requests
import configparser
import os
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class GoogleBooksConnector(BaseConnector):
    """Google Books API를 사용하여 작품을 검색하는 커넥터"""

    def __init__(self):
        super().__init__('Google Books')
        self.api_url = "https://www.googleapis.com/books/v1/volumes"
        self.api_key = self._load_api_key()

    def _load_api_key(self):
        config = configparser.ConfigParser()
        # Get the absolute path to the project's root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.ini')
        config.read(config_path)
        return config['API_KEYS'].get('GOOGLE_BOOKS_API_KEY')

    def search(self, query, max_results=10):
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            print("Google Books API 키가 설정되지 않았습니다. config.ini 파일을 확인해주세요.")
            return []

        params = {
            'q': query,
            'key': self.api_key,
            'maxResults': max_results
        }

        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()  # 오류가 발생하면 예외를 발생시킴
            data = response.json()

            results = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
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

    def download(self, source_url, title):
        # 파일명 생성 (특수문자 제거)
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '.', '_')]).rstrip()
        file_name = f"{safe_title}.pdf" # 또는 .epub
        file_path = os.path.join("corpus", file_name)

        try:
            # 1. source_url (infoLink)에서 HTML 콘텐츠 가져오기
            response = requests.get(source_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 2. 다운로드 링크 찾기 (예시: PDF 또는 EPUB 링크)
            # 이 부분은 Google Books 웹페이지의 HTML 구조에 따라 달라질 수 있습니다.
            # 실제로는 'Read' 또는 'Download' 버튼의 링크를 찾아야 합니다.
            # 여기서는 예시로 'pdf' 또는 'epub' 확장자를 포함하는 링크를 찾습니다.
            download_link = None
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href: # 또는 '.epub'
                    download_link = href
                    break
            
            if not download_link:
                print(f"'{title}'의 다운로드 링크를 찾을 수 없습니다. (Source URL: {source_url})")
                return None

            # 3. 파일 다운로드
            file_response = requests.get(download_link, stream=True)
            file_response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"'{title}' 원문이 '{file_path}'에 저장되었습니다.")
            return file_path

        except requests.exceptions.RequestException as e:
            print(f"다운로드 중 네트워크 오류 발생: {e}")
            return None
        except Exception as e:
            print(f"파일 다운로드 중 오류 발생: {e}")
            return None
