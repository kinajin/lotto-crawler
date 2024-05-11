import schedule
import time
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.scheduler.lotto_store_crawler_for_scheduling import collect_all_lotto_stores
from app.scheduler.lotto_winning_crawler_for_scheduling import collect_all_winning_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 로또 판매점 데이터 수집
def collect_lotto_stores():
    try:
        print("Running lotto_store_crawler...")
        collect_all_lotto_stores()
        print("lotto_store_crawler finished successfully.")
    except Exception as e:
        print(f"Error running lotto_store_crawler: {str(e)}")

# 로또 당첨 데이터 수집
def collect_winning_data():
    try:
        print("Running lotto_winning_store_crawler...")
        collect_all_winning_data()
        print("lotto_winning_store_crawler finished successfully.")
    except Exception as e:
        print(f"Error running lotto_winning_store_crawler: {str(e)}")

def run_crawlers():
    collect_lotto_stores()
    collect_winning_data()




run_crawlers()  # 스케줄러 시작 시 크롤러 실행




print("Scheduler started.")  # 스케줄러 시작 메시지 출력

# # 매주 목요일 11:25에 크롤러 실행 예약
# schedule.every().saturday.at("01:09").do(run_crawlers)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
#     current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#     print(f"Scheduler is running at {current_time}, next job at {schedule.next_run()}")  # 프린트 문으로 변경