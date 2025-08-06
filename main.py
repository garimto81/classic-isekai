import sqlite3
import argparse
from connectors.google_books_connector import GoogleBooksConnector

DB_FILE = 'archive.db'

def get_connector(library_name):
    """라이브러리 이름에 맞는 커넥터 인스턴스를 반환합니다."""
    if library_name == 'google_books':
        return GoogleBooksConnector()
    # TODO: 다른 라이브러리 커넥터 추가
    else:
        print(f"'{library_name}'은(는) 지원하지 않는 라이브러리입니다.")
        return None

def initialize_database():
    """데이터베이스와 works 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        publication_year INTEGER,
        source_library TEXT,
        source_url TEXT UNIQUE,
        status TEXT DEFAULT '후보',
        summary TEXT,
        notes TEXT,
        local_path TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"데이터베이스 '{DB_FILE}'가 초기화되었습니다.")

def fetch_works(args):
    """선택한 라이브러리에서 작품을 검색하고 데이터베이스에 저장합니다."""
    connector = get_connector(args.library)
    if not connector:
        return

    print(f"'{connector.library_name}'에서 '{args.query}'(으)로 검색 중...")
    results = connector.search(args.query)

    if not results:
        print("검색 결과가 없습니다.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    new_works_count = 0
    for work in results:
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO works (title, author, publication_year, source_library, source_url, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                work.get('title'),
                work.get('author'),
                work.get('publication_year'),
                work.get('source_library'),
                work.get('source_url'),
                work.get('summary')
            ))
            if cursor.rowcount > 0:
                new_works_count += 1
        except sqlite3.IntegrityError:
            # source_url이 UNIQUE 제약 조건을 위반하는 경우 (이미 존재하는 경우)
            pass
            
    conn.commit()
    conn.close()
    
    print(f"총 {len(results)}개의 결과를 찾았습니다.")
    print(f"새롭게 추가된 작품: {new_works_count}개")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="고전 명작 아카이브 시스템")
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령어')

    # 초기화 명령어
    parser_init = subparsers.add_parser('init', help='데이터베이스를 초기화합니다.')
    parser_init.set_defaults(func=lambda args: initialize_database())

    # Fetch 명령어
    parser_fetch = subparsers.add_parser('fetch', help='외부 라이브러리에서 작품 정보를 가져옵니다.')
    parser_fetch.add_argument('--library', required=True, help='데이터를 가져올 라이브러리 이름 (e.g., google_books)')
    parser_fetch.add_argument('--query', required=True, help='검색할 키워드')
    parser_fetch.set_defaults(func=fetch_works)

    # TODO: search, download, update 명령어 추가 예정

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
