# 로또 판매점 및 당첨 정보 크롤링 시스템

이 프로젝트는 로또 판매점과 당첨 정보를 크롤링하여 데이터베이스에 저장하는 시스템입니다. 매주 최신 로또 당첨 정보를 수집하고, 로또 판매점 정보를 주기적으로 업데이트합니다.

## 프로젝트 구조

- `app` 폴더: 메인 애플리케이션 코드가 있는 폴더
  - `first_crawling` 폴더: 처음 크롤링을 위한 파일들이 있는 폴더
    - `lotto_store_crawler.py`: 로또 판매점 정보를 크롤링하는 스크립트입니다.
    - `lotto_winning_crawler.py`: 로또 당첨 정보를 크롤링하는 스크립트입니다.
  - `scheduler` 폴더: 스케줄링을 위한 파일들이 있는 폴더
    - `lotto_crawling_scheduler.py`: 크롤링 작업을 스케줄링하는 스크립트입니다.
    - `lotto_store_crawler_for_scheduling.py`: 주기적인 로또 판매점 정보 업데이트를 위한 크롤링 스크립트입니다.
    - `lotto_winning_crawler_for_scheduling.py`: 주기적인 로또 당첨 정보 업데이트를 위한 크롤링 스크립트입니다.
  - `database.py`: 데이터베이스 연결 설정을 포함하는 파일입니다.
  - `models.py`: 데이터베이스 모델 정의를 포함하는 파일입니다.
- `Dockerfile`: 애플리케이션을 Docker 컨테이너로 빌드하기 위한 Dockerfile입니다.
- `requirements.txt`: 프로젝트에 필요한 Python 패키지 목록입니다.

## 사용 기술

- Python
- Selenium
- Requests
- SQLAlchemy
- PostgreSQL
- Docker

## 설치 및 실행

1. 프로젝트를 클론하거나 다운로드합니다.
2. 필요한 종속성을 설치합니다: `pip install -r requirements.txt`
3. `app/database.py` 파일에서 데이터베이스 연결 설정을 구성합니다.
4. 데이터베이스를 생성하고 테이블을 초기화합니다: `python app/models.py`
5. 로또 판매점 정보를 수집하려면 `python app/first_crawling/lotto_store_crawler.py`를 실행합니다.
6. 로또 당첨 정보를 수집하려면 `python app/first_crawling/lotto_winning_crawler.py`를 실행합니다.
7. 크롤링 작업을 스케줄링하려면 `python app/scheduler/lotto_crawling_scheduler.py`를 실행합니다.

## 데이터베이스 모델

- `LottoStore`: 로또 판매점 정보를 저장하는 모델입니다.
  - `id`: 판매점 고유 식별자 (Primary Key)
  - `name`: 판매점 이름
  - `address`: 판매점 주소
  - `phone`: 판매점 전화번호
  - `lat`: 판매점 위도
  - `lon`: 판매점 경도
  - `first_prize`: 1등 당첨 횟수
  - `second_prize`: 2등 당첨 횟수
  - `score`: 판매점 점수
  - `winning_infos`: 당첨 정보와의 관계 (One-to-Many)
- `WinningInfo`: 로또 당첨 정보를 저장하는 모델입니다.
  - `id`: 당첨 정보 고유 식별자 (Primary Key)
  - `store_id`: 판매점 식별자 (Foreign Key)
  - `draw_no`: 회차 번호
  - `rank`: 당첨 순위
  - `category`: 당첨 카테고리
  - `store`: 판매점과의 관계 (Many-to-One)

## 작성자 정보

이메일: kinajin22@gmail.com
GitHub: https://github.com/kinajin/

## 라이센스

이 프로젝트는 [MIT 라이센스](LICENSE)를 따릅니다.
