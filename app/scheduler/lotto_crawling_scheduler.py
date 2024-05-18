import schedule
import time
import logging
import sys
import os
import pytz
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.scheduler.lotto_store_crawler_for_scheduling import collect_all_lotto_stores
from app.scheduler.lotto_winning_crawler_for_scheduling import collect_all_winning_data

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", encoding='utf-8'),  # 파일에 로그를 기록
        logging.StreamHandler()              # 콘솔에 로그를 출력
    ]
)
logger = logging.getLogger(__name__)

# 로또 판매점 데이터 수집 파트
def collect_lotto_stores():
    try:
        logger.info("🛠️ lotto_store_crawler 실행 중....")
        collect_all_lotto_stores()
        logger.info("✅ lotto_store_crawler 크롤링 완료.")
        logger.info("----------------------------------------")
    except Exception as e:
        logger.error(f"❌ Error running lotto_store_crawler: {str(e)}")


# 로또 당첨 데이터 수집 파트
def collect_winning_data():
    try:
        logger.info("🛠️ lotto_winning_store_crawler 실행 중....")
        collect_all_winning_data()
        logger.info("✅ lotto_winning_store_crawler 크롤링 완료.")
    except Exception as e:
        logger.error(f"❌ Error running lotto_winning_store_crawler: {str(e)}")

# 크롤러 실행
def run_crawlers():
    logger.info("============ 🏁 크롤링 시작 🏁 ============")
    collect_lotto_stores()
    collect_winning_data()
    logger.info("============ 🏁 크롤링 종료 🏁 ============")


# 특정 시간마다 크롤러 실행 예약
schedule.every(1).minutes.do(run_crawlers)


# 로그 설정
LOG_INTERVAL = timedelta(minutes=1) # 로그 출력 주기 설정
last_log_time = datetime.now()

while True:
    schedule.run_pending()
    time.sleep(1)
    now = datetime.now()
    current_time_str = now.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
    next_run = schedule.next_run().astimezone(KST).strftime("%Y-%m-%d %H:%M:%S") if schedule.next_run() else "No scheduled jobs"
    if now - last_log_time >= LOG_INTERVAL:
        logger.info(f"[ 🕦 현재시간: {current_time_str},  ⌛ 다음 스케쥴러 작동 시간: {next_run}]")
        last_log_time = now