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


def search_works(args):
    """데이터베이스에서 작품을 검색하고 결과를 출력합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = "SELECT id, title, author, publication_year, status FROM works WHERE 1=1"
    params = []

    if args.title:
        query += " AND title LIKE ?"
        params.append(f"%{args.title}%")
    if args.author:
        query += " AND author LIKE ?"
        params.append(f"%{args.author}%")
    if args.status:
        query += " AND status = ?"
        params.append(args.status)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        print("검색 결과가 없습니다.")
        return

    # 결과 출력
    print(f"\n--- 검색 결과 ({len(results)}개) ---")
    for row in results:
        print(f"ID: {row[0]}, 제목: {row[1]}, 저자: {row[2]}, 출판년도: {row[3]}, 상태: {row[4]}")
    print("------------------------\n")


def update_work(args):
    """데이터베이스의 작품 정보를 수정합니다."""
    if not args.status and not args.notes:
        print("오류: --status 또는 --notes 중 하나는 반드시 제공되어야 합니다.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    set_clauses = []
    params = []

    if args.status:
        set_clauses.append("status = ?")
        params.append(args.status)
    if args.notes:
        set_clauses.append("notes = ?")
        params.append(args.notes)

    params.append(args.id)

    query = f"UPDATE works SET {', '.join(set_clauses)} WHERE id = ?"

    cursor.execute(query, params)
    
    if cursor.rowcount == 0:
        print(f"ID가 {args.id}인 작품을 찾을 수 없습니다.")
    else:
        print(f"ID {args.id}인 작품의 정보가 성공적으로 업데이트되었습니다.")
        # 변경된 내용 확인
        cursor.execute("SELECT id, title, status, notes FROM works WHERE id = ?", (args.id,))
        updated_work = cursor.fetchone()
        print(f"  -> ID: {updated_work[0]}, 제목: {updated_work[1]}, 상태: {updated_work[2]}, 메모: {updated_work[3]}")


    conn.commit()
    conn.close()


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

    # Search 명령어
    parser_search = subparsers.add_parser('search', help='데이터베이스에서 작품을 검색합니다.')
    parser_search.add_argument('--title', help='검색할 작품 제목')
    parser_search.add_argument('--author', help='검색할 저자')
    parser_search.add_argument('--status', help='검색할 작업 상태 (e.g., 후보, 검토중)')
    parser_search.set_defaults(func=search_works)

    # Update 명령어
    parser_update = subparsers.add_parser('update', help='데이터베이스의 작품 정보를 수정합니다.')
    parser_update.add_argument('--id', type=int, required=True, help='수정할 작품의 ID')
    parser_update.add_argument('--status', help='새로운 작업 상태 (e.g., 검토중, 각색중)')
    parser_update.add_argument('--notes', help='작품에 대한 아이디어 메모')
    parser_update.set_defaults(func=update_work)

    # TODO: download 명령어 추가 예정

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
