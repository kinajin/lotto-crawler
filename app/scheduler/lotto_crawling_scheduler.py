import schedule
import time
import logging
import sys
import os
import pytz
from datetime import datetime, timedelta

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
        logging.FileHandler("crawler.log"),  # 파일에 로그를 기록
        logging.StreamHandler()              # 콘솔에 로그를 출력
    ]
)
logger = logging.getLogger(__name__)

# 로또 판매점 데이터 수집
def collect_lotto_stores():
    try:
        logger.info("Running lotto_store_crawler...")
        collect_all_lotto_stores()
        logger.info("lotto_store_crawler finished successfully.")
    except Exception as e:
        logger.error(f"Error running lotto_store_crawler: {str(e)}")

# 로또 당첨 데이터 수집
def collect_winning_data():
    try:
        logger.info("Running lotto_winning_store_crawler...")
        collect_all_winning_data()
        logger.info("lotto_winning_store_crawler finished successfully.")
    except Exception as e:
        logger.error(f"Error running lotto_winning_store_crawler: {str(e)}")

def run_crawlers():
    logger.info("Crawler started.")
    collect_lotto_stores()
    collect_winning_data()
    logger.info("Crawler finished.")

# 5분마다 크롤러 실행 예약
schedule.every(5).minutes.do(run_crawlers)

last_log_time = datetime.now()

while True:
    schedule.run_pending()
    time.sleep(1)
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    next_run = schedule.next_run().astimezone(KST).strftime("%Y-%m-%d %H:%M:%S") if schedule.next_run() else "No scheduled jobs"
    
    # 1분마다 로그 출력
    if datetime.now() - last_log_time >= timedelta(minutes=1):
        logger.info(f"Scheduler is running at {current_time}, next job at {next_run}")
        last_log_time = datetime.now()

# # 매주 목요일 11:25에 크롤러 실행 예약 버전 
# schedule.every().saturday.at("01:09").do(run_crawlers)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
#     current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#     print(f"Scheduler is running at {current_time}, next job at {schedule.next_run()}")  # 프린트 문으로 변경
