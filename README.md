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
- **`config.ini`**: 외부 API 키 등 민감한 설정 정보를 보관하는 파일입니다.

## 3. 설치 및 초기 설정

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

- **작품 검색 및 추가:**
  - Google Books에서 'Moby Dick'을 검색하여 데이터베이스에 추가합니다.
  ```bash
  python main.py fetch --library google_books --query "Moby Dick"
  ```

- **데이터베이스 검색 (구현 예정):**
  ```bash
  python main.py search --author "Herman Melville"
  ```

## 5. 향후 계획

-   다양한 라이브러리(Internet Archive, Project Gutenberg 등) 커넥터 추가
-   작품 원문 다운로드 기능 구현
-   데이터베이스 검색 및 관리 기능 고도화
-   간단한 웹 인터페이스 개발