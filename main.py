import sqlite3
import argparse
import sys
import io
import os
from connectors.google_books_connector import GoogleBooksConnector
from connectors.gutenberg_connector import GutenbergConnector
from translators.google_translator import GoogleTranslator

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'archive.db'

def get_connector(library_name):
    """라이브러리 이름에 맞는 커넥터 인스턴스를 반환합니다."""
    if library_name == 'google_books' or library_name == 'Google Books':
        return GoogleBooksConnector()
    elif library_name == 'gutenberg' or library_name == 'Project Gutenberg':
        return GutenbergConnector()
    # TODO: 다른 라이브러리 커넥터 추가
    else:
        print(f"'{library_name}'은(는) 지원하지 않는 라이브러리입니다.")
        return None

def initialize_database():
    """데이터베이스와 works 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS works;')
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
        local_path TEXT,
        views INTEGER DEFAULT 0
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

    query = "SELECT id, title, author, publication_year, status, views FROM works WHERE 1=1"
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
        print(f"ID: {row[0]}, 제목: {row[1]}, 저자: {row[2]}, 출판년도: {row[3]}, 상태: {row[4]}, 조회수: {row[5]}")
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

def download_work(args, rank=None):
    """데이터베이스에 저장된 작품의 원문을 다운로드합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, source_library, source_url FROM works WHERE id = ?", (args.id,))
    work = cursor.fetchone()
    conn.close()

    if not work:
        print(f"ID가 {args.id}인 작품을 찾을 수 없습니다.")
        return

    work_id, title, source_library, source_url = work

    connector = get_connector(source_library)
    if not connector:
        print(f"'{source_library}' 라이브러리에 대한 커넥터를 찾을 수 없습니다.")
        return

    print(f"'{title}' (ID: {work_id}) 원문 다운로드 중...")
    local_path = connector.download(source_url, title, rank)

    if local_path:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE works SET local_path = ?, views = views + 1 WHERE id = ?", (local_path, work_id))
        conn.commit()
        conn.close()
        print(f"'{title}' 원문이 '{local_path}'에 저장되었습니다.")
    else:
        print(f"'{title}' 원문 다운로드에 실패했습니다.")


def download_all_ranked_works(args):
    """조회수가 가장 높은 작품부터 순위를 매겨 모든 작품을 다운로드합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 모든 작품을 조회수가 높은 순으로 정렬하여 가져옵니다.
    cursor.execute("SELECT id, title, source_library, source_url FROM works ORDER BY views DESC")
    all_works = cursor.fetchall()
    conn.close()

    if not all_works:
        print("다운로드할 작품이 없습니다. 검색 결과가 없습니다.")
        return

    print(f"총 {len(all_works)}개 작품 다운로드를 시작합니다. (조회수 순)")
    for rank, (work_id, title, source_library, source_url) in enumerate(all_works, 1):
        # download_work 함수를 직접 호출하는 대신, 로직을 재사용합니다.
        # download_work는 args 객체를 기대하므로, 임시 args 객체를 생성합니다.
        temp_args = argparse.Namespace(id=work_id)
        download_work(temp_args, rank=rank)

def translate_work(args):
    """지정된 작품을 번역합니다."""
    translator = GoogleTranslator()
    
    # rank1 문서만 번역
    if args.rank == 1:
        # corpus 폴더에 있는 rank1 문서의 정확한 파일 이름을 찾아야 합니다.
        # 여기서는 rank1-Moby Dick Or The Whale.txt 와 같은 패턴을 가정합니다.
        corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
        rank1_files = [f for f in os.listdir(corpus_dir) if f.startswith("rank1-")]

        if not rank1_files:
            print("rank1 문서가 corpus 폴더에 없습니다.")
            return
        
        # 첫 번째 rank1 문서만 처리
        file_name = rank1_files[0]
        file_path = os.path.join(corpus_dir, file_name)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"'{file_name}' 번역 시작...")
            translated_content = translator.translate_text(content, target_language='ko')

            # 번역된 내용을 새로운 파일로 저장
            translated_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus_ko")
            os.makedirs(translated_dir, exist_ok=True)
            translated_file_name = f"{os.path.splitext(file_name)[0]}_ko{os.path.splitext(file_name)[1]}"
            translated_file_path = os.path.join(translated_dir, translated_file_name)

            with open(translated_file_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            print(f"'{file_name}'이(가) '{translated_file_path}'로 번역되어 저장되었습니다.")

        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            print(f"번역 중 오류 발생: {e}")
    else:
        print("현재는 rank1 문서만 번역할 수 있습니다.")

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

    # Download 명령어
    parser_download = subparsers.add_parser('download', help='데이터베이스에 저장된 작품의 원문을 다운로드합니다.')
    parser_download.add_argument('--id', type=int, required=True, help='다운로드할 작품의 ID')
    parser_download.set_defaults(func=download_work)

    # Download Top Views 명령어 (이전)
    # parser_download_top = subparsers.add_parser('download-top', help='조회수가 가장 높은 작품부터 다운로드합니다.')
    # parser_download_top.add_argument('--count', type=int, default=1, help='다운로드할 작품의 개수 (기본값: 1)')
    # parser_download_top.set_defaults(func=download_top_views)

    # Download All Ranked Works 명령어
    parser_download_all_ranked = subparsers.add_parser('download-all-ranked', help='조회수 순으로 모든 작품을 다운로드합니다.')
    parser_download_all_ranked.set_defaults(func=download_all_ranked_works)

    # Translate 명령어
    parser_translate = subparsers.add_parser('translate', help='지정된 작품을 번역합니다.')
    parser_translate.add_argument('--rank', type=int, required=True, help='번역할 작품의 순위 (현재는 1만 지원)')
    parser_translate.set_defaults(func=translate_work)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
