# app/first_crawling/lotto_store_crawler.py

import time
from config.config import SIDO_LIST
from config.logger import logger
from app.models import engine, LottoStore
from utilities.utils import get_page_number, fetch_store_data, save_store_data, create_session


Session = create_session(engine)

# 판매점 데이터를 수집하는 함수
def collect_store_data():

    try: 
        for sido in SIDO_LIST:
            # 시/도별 페이지 수를 가져오기
            total_page = get_page_number(sido)

            if total_page:
                for page in range(1, total_page + 1):

                    # 페이지별 데이터 수집
                    store_data_list = fetch_store_data(sido, page=page)

                    # 데이터 저장
                    save_store_data(Session, store_data_list)
            logger.info(f"📊 {sido}까지 수집된 총 로또 판매점 수: {len(store_data_list)}")

    except Exception as e:
        logger.error(f"❌ 데이터 수집 중 오류 발생: {str(e)}")
    finally:
        Session.remove()

# 메인 함수
def main():
    collect_store_data()
    Session.remove()

if __name__ == "__main__":
    main()
