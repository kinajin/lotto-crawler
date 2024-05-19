# app/first_crawling/lotto_winning_crawler.py

from config.logger import logger
from app.models import WinningInfo, engine, LottoStore
from utilities.utils import (
    crawl_table, crawl_second_tier_stores, refresh_materialized_view, initialize_driver, 
    create_session, access_crawling_page, extract_draw_numbers, select_draw_number, click_search_button, save_winning_data
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

Session = create_session(engine)

# 당첨 데이터 수집 함수
def collect_all_winning_data():
    # 드라이버 초기화
    driver = initialize_driver()
    data = {"lotto_stores": []}

    try:
        url = 'https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645'
        access_crawling_page(driver, url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'drwNo'))
        )
        time.sleep(2)

        # 회차 번호 추출
        drwNo_options = extract_draw_numbers(driver)

        # 회차별 데이터 수집
        for drwNo in drwNo_options:
            logger.info(f"🎯 [회차 {drwNo} 크롤링 중...]")
            data["lotto_stores"] = []

            # 회차 선택 및 조회 버튼 클릭
            select_draw_number(driver, drwNo)
            click_search_button(driver)
            time.sleep(1)

            # 첫 페이지의 1등 2등 테이블 크롤링
            crawl_table(driver, data, drwNo, "1", "//div[@class='group_content'][1]//table", True)
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")

            # 두 번째 페이지부터 2등 테이블 크롤링
            crawl_second_tier_stores(driver, data, drwNo)

            # 데이터베이스에 저장
            save_winning_data(Session, data)

        # 데이터베이스 뷰 업데이트
        refresh_materialized_view(engine)
    except Exception as e:
        logger.error(f"❌ 데이터 수집 중 오류 발생: {str(e)}")
    finally:
        driver.quit()
        Session.remove()

if __name__ == '__main__':
    collect_all_winning_data()
