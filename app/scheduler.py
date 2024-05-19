import schedule
import time
import sys
import os
import pytz
from datetime import datetime, timedelta
from config.logger import logger  # 기존 로그 설정 사용


# 프로젝트 루트 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)


from app.crawler.lotto_store_update_crawler import update_all_lotto_stores
from app.crawler.lotto_winning_update_crawler import update_all_winning_data


# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 로또 판매점 데이터 수집 함수
def collect_lotto_stores():
    try:
        logger.info("🛠️ lotto_store_crawler 실행 중....")
        update_all_lotto_stores()
        logger.info("✅ lotto_store_crawler 크롤링 완료.")
        logger.info("----------------------------------------")
    except Exception as e:
        logger.error(f"❌ Error running lotto_store_crawler: {str(e)}")

# 로또 당첨 데이터 수집 함수
def collect_winning_data():
    try:
        logger.info("🛠️ lotto_winning_store_crawler 실행 중....")
        update_all_winning_data()
        logger.info("✅ lotto_winning_store_crawler 크롤링 완료.")
    except Exception as e:
        logger.error(f"❌ Error running lotto_winning_store_crawler: {str(e)}")

# 크롤러 실행 함수
def run_crawlers():
    logger.info("============ 🏁 크롤링 시작 🏁 ============")
    collect_lotto_stores()
    collect_winning_data()
    logger.info("============ 🏁 크롤링 종료 🏁 ============")

# 스케줄러 실행 함수
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 스케줄러를 일정 시간마다 실행
schedule.every(60).minutes.do(run_crawlers)

# 로그 출력 주기 설정
LOG_INTERVAL = timedelta(minutes=1)  # 로그 출력 주기 설정
last_log_time = datetime.now()

# 주기적으로 로그를 출력하는 함수
def log_scheduler_status():
    global last_log_time
    now = datetime.now()
    current_time_str = now.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
    next_run = schedule.next_run().astimezone(KST).strftime("%Y-%m-%d %H:%M:%S") if schedule.next_run() else "No scheduled jobs"
    if now - last_log_time >= LOG_INTERVAL:
        logger.info(f"[ 🕦 현재시간: {current_time_str},  ⌛ 다음 스케쥴러 작동 시간: {next_run}]")
        last_log_time = now

# 로그 출력 주기 스케줄링
schedule.every(LOG_INTERVAL.total_seconds()).seconds.do(log_scheduler_status)

if __name__ == "__main__":
    run_scheduler()
