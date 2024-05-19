# 🍀 LottoMap Crawler 🍀

이 프로젝트는 로또 판매점과 당첨 정보를 크롤링하여 데이터베이스에 저장하는 시스템입니다. 매주 최신 로또 당첨 정보를 수집하고, 로또 판매점 정보를 주기적으로 업데이트합니다. 이 크롤러는 Amazon EC2에서 실행되며, 수집된 데이터는 AWS RDS PostgreSQL 데이터베이스에 저장됩니다.

## 🚀 Features

### 로또 판매점 정보

- 전국 로또 판매점 정보 수집
- 매주 새로 페업한 판매점 확인 및 데이터베이스에서 삭제
- 매주 새로 개업한 판매점 확인 및 데이터베이스에서 추가
- 매주 판매점 정보 변경 사항 업데이트 (상호명, 전화번호, 경도, 위도, 주소 )

### 로또 당첨 정보

- 로또 당첨 내역 수집
- 매주 자동으로 새로운 회차의 당첨 내역 업데이트

### 기타

- 데이터베이스 Materialized View 갱신
- 로깅을 통한 크롤링 과정 모니터링

## 📂 Project Structure

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── config
│   │   ├── config.py
│   │   └── logger.py
│   ├── crawler
│   │   ├── __init__.py
│   │   ├── lotto_store_crawler.py
│   │   ├── lotto_store_update_crawler.py
│   │   ├── lotto_winning_crawler.py
│   │   └── lotto_winning_update_crawler.py
│   ├── database.py
│   ├── models.py
│   ├── scheduler.py
│   └── utilities
│       ├── __init__.py
│       └── utils.py
├── lottomap-env
│   ├── bin
│   ├── include
│   ├── lib
│   └── pyvenv.cfg
└── requirements.txt
```

- `app` 폴더: 메인 애플리케이션 코드가 있는 폴더

  - `config` 폴더: 설정 파일들이 있는 폴더
    - `config.py`: 애플리케이션 설정을 포함하는 파일입니다.
    - `logger.py`: 로깅 설정을 포함하는 파일입니다.
  - `crawler` 폴더: 크롤링 관련 파일들이 있는 폴더
    - `lotto_store_crawler.py`: 처음 사용 시 로또 판매점 정보를 크롤링하는 스크립트입니다.
    - `lotto_store_update_crawler.py`: 주기적인 로또 판매점 정보 업데이트를 위한 크롤링 스크립트입니다.
    - `lotto_winning_crawler.py`: 처음 사용 시 로또 당첨 정보를 크롤링하는 스크립트입니다.
    - `lotto_winning_update_crawler.py`: 주기적인 로또 당첨 정보 업데이트를 위한 크롤링 스크립트입니다.
  - `utilities` 폴더: 유틸리티 함수들이 있는 폴더
    - `utils.py`: 크롤링에 사용되는 유틸리티 함수들을 포함하는 파일입니다.
  - `database.py`: 데이터베이스 연결 설정을 포함하는 파일입니다.
  - `models.py`: 데이터베이스 모델 정의를 포함하는 파일입니다.
  - `scheduler.py`: 크롤링 작업을 스케줄링하는 스크립트입니다.

- `lottomap-env` 폴더: 가상 환경 관련 파일들이 있는 폴더

  - `bin`, `include`, `lib` 폴더: 가상 환경의 실행 파일, 헤더 파일, 라이브러리 파일들이 있는 폴더입니다.
  - `pyvenv.cfg`: 가상 환경 설정 파일입니다.

- `Dockerfile`: 애플리케이션을 Docker 컨테이너로 빌드하기 위한 Dockerfile입니다.
- `requirements.txt`: 프로젝트에 필요한 Python 패키지 목록입니다.

이 프로젝트 구조는 크롤링 작업을 모듈화하고 분리하여 유지 관리와 확장이 용이하도록 설계되었습니다. 주요 기능은 `app` 폴더 내의 파일들로 구성되어 있으며, 설정과 유틸리티 함수들은 별도의 폴더로 분리되어 있습니다. 또한 `Dockerfile`을 통해 애플리케이션을 Docker 컨테이너로 쉽게 배포할 수 있습니다.

## 🛠️ 사용 기술

- 🐍 Python
- 🕸️ Selenium
- 🌐 Requests
- 🗄️ SQLAlchemy
- 🐘 PostgreSQL
- 🐳 Docker

## 🔧 Configuration

- .env 파일에 데이터베이스 URL을 설정합니다.

```
SQLALCHEMY_DATABASE_URL = "postgresql://username:password@host:port/database"
```

- app/config/config.py 파일에서 필요한 설정을 변경할 수 있습니다.

## 📅 Scheduling

- 크롤러는 app/scheduler.py에 정의된 스케줄에 따라 실행됩니다.
- 기본적으로 60분마다 크롤러가 실행되도록 설정되어 있습니다.
- 스케줄링 주기를 변경하려면 app/scheduler.py의 schedule.every(60).minutes.do(run_crawlers) 부분을 수정하세요.

## 🛠️ Installation

1. 프로젝트를 클론합니다.

   ```

   git clone https://github.com/your_username/lottomap-crawler.git

   ```

2. 프로젝트 디렉토리로 이동합니다.

   ```

   cd lottomap-crawler

   ```

3. Docker 이미지를 빌드합니다.

   ```

   docker build -t lottomap-crawler .

   ```

4. Docker 컨테이너를 실행합니다.

   ```

   docker run -d --name lottomap-crawler lottomap-crawler

   ```

## 🏃‍♂️ Usage

1. 초기 로또 판매점 정보를 수집하려면 app/crawler/lotto_store_crawler.py를 실행합니다.

   ```

   python app/crawler/lotto_store_crawler.py

   ```

2. 초기 로또 당첨 정보를 수집하려면 app/crawler/lotto_winning_crawler.py를 실행합니다.

   ```

   python app/crawler/lotto_winning_crawler.py

   ```

3. 주기적인 로또 판매점 정보 및 로또 당첨 정보 업데이트를 위해 스케줄링하려면 app/scheduler.py를 실행합니다.

   ```

   python app/scheduler.py

   ```

## 📝 Note

- 프로젝트를 실행하기 전에 .env 파일에 데이터베이스 연결 정보를 설정해야 합니다.

- 초기 크롤링 작업은 데이터베이스에 존재하지 않는 모든 로또 판매점과 당첨 정보를 수집합니다.

- 주기적인 업데이트 크롤링 작업은 이미 수집된 데이터를 기반으로 새로운 정보만 업데이트합니다.

- 크롤링 작업은 스케줄러에 의해 자동으로 실행되며, 스케줄링 주기는 app/scheduler.py에서 설정할 수 있습니다.

위의 설치 및 실행 과정은 프로젝트를 Docker 컨테이너로 배포하고 실행하는 방법을 설명합니다. 먼저 프로젝트를 클론하고 Docker 이미지를 빌드한 후, 컨테이너를 실행합니다. 그 후에는 각 크롤링 작업을 개별적으로 실행하거나 스케줄러를 통해 자동화할 수 있습니다. 프로젝트를 실행하기 전에는 데이터베이스 연결 정보를 설정해야 합니다.

## 🪵 Logging

- 크롤링 과정은 app/config/logger.py에 정의된 로거를 통해 모니터링됩니다.
- 로그는 콘솔과 crawler.log 파일에 출력됩니다.
- 로그 레벨과 포맷은 app/config/logger.py에서 설정할 수 있습니다.

## 📊 Database Models

- `LottoStore`: 로또 판매점 정보를 저장하는 모델입니다.
  - `id`: 판매점 고유 식별자 (Primary Key)
  - `name`: 판매점 이름
  - `address`: 판매점 주소
  - `phone`: 판매점 전화번호
  - `lat`: 판매점 위도
  - `lon`: 판매점 경도
  - `winning_infos`: 당첨 정보와의 관계 (One-to-Many)
- `WinningInfo`: 로또 당첨 정보를 저장하는 모델입니다.
  - `id`: 당첨 정보 고유 식별자 (Primary Key)
  - `store_id`: 판매점 식별자 (Foreign Key)
  - `draw_no`: 회차 번호
  - `rank`: 당첨 순위
  - `category`: 당첨 카테고리
  - `store`: 판매점과의 관계 (Many-to-One)

## 👨‍💻 작성자 정보

이메일: kinajin22@gmail.com
GitHub: https://github.com/kinajin/

## 📄 라이센스

이 프로젝트는 [MIT 라이센스](LICENSE)를 따릅니다.
