import schedule
import time
import subprocess

def run_lotto_store_crawler():
    try:
        print("Running lotto_store_crawler.py...")
        subprocess.run(["python", "lotto_store_crawler.py"], check=True)
        print("lotto_store_crawler.py finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running lotto_store_crawler.py: {str(e)}")

def run_lotto_winning_store_crawler():
    try:
        print("Running lotto_winning_store_crawler.py...")
        subprocess.run(["python", "lotto_winning_store_crawler.py"], check=True)
        print("lotto_winning_store_crawler.py finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running lotto_winning_store_crawler.py: {str(e)}")

def run_crawlers():
    run_lotto_store_crawler()
    run_lotto_winning_store_crawler()

# 매주 일요일 12:00에 크롤러 실행
schedule.every().sunday.at("12:00").do(run_crawlers)

while True:
    schedule.run_pending()
    time.sleep(1)