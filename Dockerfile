# 기본 이미지로 Python 3.9 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 필요한 Python 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app ./app

# 크롤링 스케줄러 실행
CMD ["python", "app/scheduler/lotto_crawling_scheduler.py"]