# classic-isekai: Automated Archive System

## 1. 프로젝트 개요

본 프로젝트는 저작권이 만료된 전 세계의 고전 명작들을 수집하고 관리하여, 현대적인 '이세계 판타지' 웹소설로 재창조하기 위한 기반을 마련하는 자동화 아카이브 시스템입니다.

다양한 온라인 라이브러리(Google Books, Internet Archive 등)에서 작품을 자동으로 탐색하고, SQLite 데이터베이스에 체계적으로 저장 및 관리하는 것을 목표로 합니다.

## 2. 시스템 아키텍처

이 시스템은 다음과 같은 모듈식 구조로 설계되었습니다.

- **`main.py`**: 사용자가 시스템과 상호작용하는 메인 CLI(명령어 인터페이스)입니다.
- **`archive.db`**: 모든 작품의 메타데이터가 저장되는 SQLite 데이터베이스입니다.
- **`connectors/`**: 각 온라인 라이브러리와 통신하여 데이터를 가져오는 커넥터 모듈들이 위치합니다.
- **`corpus/`**: 원문 텍스트 파일이 저장되는 폴더입니다.
- **`corpus_ko/`**: 번역된 텍스트 파일이 저장되는 폴더입니다.
- **`config.ini`**: 외부 API 키 등 민감한 설정 정보를 보관하는 파일입니다.
- **`world_setting/`**: 웹소설 세계관 설정 파일이 저장되는 폴더입니다.

## 3. 웹소설 세계관 설정

본 프로젝트는 D&D와 무협 세계관을 융합한 독창적인 웹소설 세계관을 구축하고 있습니다. 상세한 설정은 `world_setting/world_setting.md` 파일을 참조해주세요.

## 4. 설치 및 초기 설정

1.  **필요 라이브러리 설치:**
    ```bash
    pip install requests
    ```

2.  **API 키 설정:**
    - `config.ini` 파일을 열어 `YOUR_API_KEY_HERE` 부분을 본인의 Google Books API 키로 교체합니다.

3.  **데이터베이스 초기화:**
    - 프로젝트 폴더 내에서 다음 명령어를 실행하여 `archive.db` 파일을 생성합니다.
    ```bash
    python main.py init
    ```

## 4. 사용 방법

- **1. 작품 검색 및 아카이브 추가:**
  - Google Books에서 'Moby Dick'을 검색하여 데이터베이스에 '후보' 상태로 추가합니다.
  ```bash
  python main.py fetch --library google_books --query "Moby Dick"
  ```

- **2. 아카이브 검색:**
  - 데이터베이스에 저장된 작품들을 다양한 조건으로 검색합니다.
  ```bash
  # 저자 이름으로 검색
  python main.py search --author "Melville"

  # 제목으로 검색
  python main.py search --title "Moby Dick"

  # 작업 상태로 검색
  python main.py search --status "후보"
  ```

- **3. 작품 정보 업데이트:**
  - 작품의 작업 상태나 아이디어 메모를 수정합니다.
  ```bash
  # ID가 1인 작품의 상태를 '검토중'으로 변경
  python main.py update --id 1 --status "검토중"

  # ID가 1인 작품에 메모 추가
  python main.py update --id 1 --notes "주인공을 우주 비행사로 각색하는 아이디어"
  ```

## 5. 향후 계획

-   다양한 라이브러리(Internet Archive, Project Gutenberg 등) 커넥터 추가
-   작품 원문 다운로드 기능 구현
-   간단한 웹 인터페이스 개발