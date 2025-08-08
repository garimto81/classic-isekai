import requests
from bs4 import BeautifulSoup
import os
from .base_connector import BaseConnector

class GutenbergConnector(BaseConnector):
    """Project Gutenberg에서 작품을 검색하고 다운로드하는 커넥터"""

    def __init__(self):
        super().__init__('Project Gutenberg')
        self.base_url = "https://www.gutenberg.org"
        self.search_url = f"{self.base_url}/ebooks/search/?query="
        self.download_base_url = f"{self.base_url}/files/"

    def search(self, query, max_results=10):
        search_query_url = f"{self.search_url}{query}"
        try:
            response = requests.get(search_query_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            results = []
            # 검색 결과는 'booklink' 클래스를 가진 div 안에 있습니다.
            for item in soup.find_all('li', class_='booklink'):
                title_tag = item.find('span', class_='title')
                author_tag = item.find('span', class_='subtitle')
                link_tag = item.find('a', href=True)

                title = title_tag.text.strip() if title_tag else 'N/A'
                author = author_tag.text.strip() if author_tag else 'N/A'
                source_url = f"{self.base_url}{link_tag['href']}" if link_tag else None

                # Project Gutenberg는 출판 연도를 직접 제공하지 않는 경우가 많으므로 None으로 설정
                publication_year = None 

                if source_url:
                    results.append({
                        'title': title,
                        'author': author,
                        'publication_year': publication_year,
                        'source_library': self.library_name,
                        'source_url': source_url,
                        'summary': '' # Project Gutenberg 검색 결과에서는 요약 제공 안 함
                    })
                if len(results) >= max_results:
                    break
            return results
        except requests.exceptions.RequestException as e:
            print(f"Project Gutenberg 검색 중 네트워크 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"Project Gutenberg 검색 중 오류 발생: {e}")
            return []

    def download(self, source_url, title, rank=None):
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '.', '_')]).rstrip()
        
        if rank is not None:
            file_name_prefix = f"rank{rank}-"
        else:
            file_name_prefix = ""

        try:
            # source_url에서 Project Gutenberg ID 추출
            gutenberg_id = source_url.split('/')[-1]
            if not gutenberg_id.isdigit():
                print(f"'{source_url}'에서 유효한 Project Gutenberg ID를 찾을 수 없습니다.")
                return None

            # 직접 다운로드 링크 구성 (Plain Text UTF-8)
            # Project Gutenberg는 ID를 기반으로 직접 파일에 접근할 수 있는 경우가 많습니다.
            # 예: https://www.gutenberg.org/files/11/11-0.txt
            download_link = f"{self.base_url}/files/{gutenberg_id}/{gutenberg_id}-0.txt"
            file_extension = '.txt'
            file_name = f"{file_name_prefix}{safe_title}{file_extension}"
            file_path = os.path.join("corpus", file_name)

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
