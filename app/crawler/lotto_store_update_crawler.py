# app/scheduler/lotto_store_crawler_for_scheduling.py

import time
from sqlalchemy.orm import scoped_session, sessionmaker
from ..models import LottoStore, engine, WinningInfo
from config.config import SIDO_LIST
from config.logger import logger
from utilities.utils import get_page_number, fetch_store_data, get_all_store_ids, get_existing_store_ids, get_inactive_store_ids, delete_winning_info, delete_inactive_stores, update_store_info, create_session

Session = create_session(engine)

# 판매점 데이터 수집 함수
def update_all_lotto_stores():
    all_store_data = [] 
    try:
        for sido in SIDO_LIST:
            # 시/도별 페이지 수를 가져오기
            total_page = get_page_number(sido)
            if total_page:
                for page in range(1, total_page + 1):
                    # 페이지별 데이터 수집
                    fetch_store_data(sido, page=page, all_store_data=all_store_data)  
            logger.info(f"📊 {sido}까지 수집된 총 로또 판매점 수: {len(all_store_data)}")

        # 데이터베이스에서 기존 판매점 ID 가져오기
        all_store_ids = get_all_store_ids(all_store_data)

        # 기존 테이블에서 판매점 ID 가져오기
        existing_store_ids = get_existing_store_ids(Session, LottoStore)

        # 폐점한 판매점 ID 계산하기
        inactive_store_ids = get_inactive_store_ids(existing_store_ids, all_store_ids)

        # 폐점한 판매점의 당첨 정보 삭제
        delete_winning_info(Session, WinningInfo, inactive_store_ids)

        # 폐점한 판매점 정보 삭제
        delete_inactive_stores(Session, LottoStore, inactive_store_ids)

        for store_data in all_store_data:
            # 신규 로또판매점 정보 업데이트
            update_store_info(Session, store_data)
        return all_store_data

    except Exception as e:
        logger.error(f"❌ 데이터 수집 중 오류 발생: {str(e)}")
    finally:
        Session.remove()

if __name__ == '__main__':
    update_all_lotto_stores()
