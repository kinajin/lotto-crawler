import time
import requests
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from ..models import LottoStore, engine, WinningInfo
from sqlalchemy.sql import func
import json
import html
import logging

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("lotto_store_crawler.log"),  # 파일에 로그를 기록
        logging.StreamHandler()  # 콘솔에 로그를 출력
    ]
)
logger = logging.getLogger(__name__)

# 세션 생성
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# 시/도 리스트
sido_list = ['서울', '경기', '부산', '대구', '인천', '대전', '울산', '강원', '충북', '충남', '광주', '전북', '전남', '경북', '경남', '제주', '세종']

# 헤더 설정
headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# 수집할 페이지 번호 가져오기 함수
def get_page_number(sido, gugun=''):
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': 1,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        if json_data['arr']:
            return json_data.get('totalPage')
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logger.error(f"Failed to get {sido} totalPage: {str(e)}")
        return None

# 데이터 가져오기 함수
def fetch_data(sido, gugun='', page=1, all_store_data=None):
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': page,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    try:
        # 데이터 수집
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        all_store_data.extend(json_data['arr'])  # all_store_data에 데이터 추가
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logger.error(f"Failed to get {sido} data: {str(e)}")

# 전체 판매점 ID 가져오기 함수
def get_all_store_ids(all_store_data):
    return [store_data['RTLRID'] for store_data in all_store_data]

# 기존 테이블에서 판매점 ID 가져오기 함수
def get_existing_store_ids():
    existing_store_ids = Session.query(LottoStore.id).all()
    return [str(store_id[0]) for store_id in existing_store_ids]

# 폐점한 판매점 ID 가져오기 함수
def get_inactive_store_ids(existing_store_ids, all_store_ids):
    return set(existing_store_ids) - set(all_store_ids)

# 폐점한 판매점의 당첨 정보 삭제 함수
def delete_winning_info(inactive_store_ids):
    for store_id in inactive_store_ids:
        Session.query(WinningInfo).filter_by(store_id=store_id).delete()
        logger.info(f"Deleted winning info for store: {store_id}")
    Session.commit()

# 폐점한 판매점 정보 삭제 함수
def delete_inactive_stores(inactive_store_ids):
    if inactive_store_ids:
        Session.query(LottoStore).filter(LottoStore.id.in_(inactive_store_ids)).delete(synchronize_session=False)
        logger.info(f"Deleted inactive stores: {inactive_store_ids}")
        logger.info(f"Deleted inactive stores names: {Session.query(LottoStore.name).filter(LottoStore.id.in_(inactive_store_ids)).all()}")
        Session.commit()
    else:
        logger.info("There are no inactive stores, 새로 폐점한 판매점이 존재하지 않습니다.")

# HTML 엔티티를 처리하는 함수
def decode_html_entities(text):
    text = text.replace("&#35;", "#")
    return html.unescape(text)

# 판매점 정보 업데이트 함수
def update_store_info(store_data):
    store_id = store_data['RTLRID']
    lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()
    
    if lotto_store:
        updated_fields = []
        
        # Unescape HTML entities in store_data
        firm_name = decode_html_entities(store_data['FIRMNM'])
        address = decode_html_entities(store_data['BPLCDORODTLADRES'])
        
        if lotto_store.name != firm_name:
            logger.info(f"Store name changed from {lotto_store.name} to {firm_name}")
            lotto_store.name = firm_name
            updated_fields.append('name')
        
        if lotto_store.address != address:
            logger.info(f"Store address changed from {lotto_store.address} to {address}")
            lotto_store.address = address
            updated_fields.append('address')
        
        if lotto_store.phone != store_data['RTLRSTRTELNO']:
            logger.info(f"Store phone number changed from {lotto_store.phone} to {store_data['RTLRSTRTELNO']}")
            lotto_store.phone = store_data['RTLRSTRTELNO']
            updated_fields.append('phone')
        
        try:
            lotto_store_lat = float(lotto_store.lat)
            store_data_lat = float(store_data['LATITUDE'])
            if lotto_store_lat != store_data_lat:
                logger.info(f"Store latitude changed from {lotto_store_lat} to {store_data_lat}")
                lotto_store.lat = store_data_lat
                updated_fields.append('lat')
        except (ValueError, TypeError):
            logger.error(f"Error converting LATITUDE to float for store {store_id}")
        
        try:
            lotto_store_lon = float(lotto_store.lon)
            store_data_lon = float(store_data['LONGITUDE'])
            if lotto_store_lon != store_data_lon:
                logger.info(f"Store longitude changed from {lotto_store_lon} to {store_data_lon}")
                lotto_store.lon = store_data_lon
                updated_fields.append('lon')
        except (ValueError, TypeError):
            logger.error(f"Error converting LONGITUDE to float for store {store_id}")
        
        if updated_fields:
            logger.info(f"Updated store info for store {store_id}: {', '.join(updated_fields)}")
            Session.commit()
    
    else:
        try:
            lotto_store = LottoStore(
                id=store_id,
                name=firm_name,
                address=address,
                phone=store_data['RTLRSTRTELNO'],
                lat=float(store_data['LATITUDE']),
                lon=float(store_data['LONGITUDE']),
            )
            logger.info(f"Added new store: {store_id}")
            Session.add(lotto_store)
            Session.commit()
        except (ValueError, TypeError):
            logger.error(f"Error creating new store {store_id} due to invalid LATITUDE or LONGITUDE")

# 전체 판매점 데이터 수집 함수
def collect_all_lotto_stores():
    all_store_data = [] 
    try:
        # 데이터 수집 실행
        for sido in sido_list:
            total_page = get_page_number(sido)
            if total_page:
                for page in range(1, total_page + 1):
                    # 데이터 수집
                    fetch_data(sido, page=page, all_store_data=all_store_data)  
                    # logger.info(f"Data collection in progress: {sido} - page {page}")
            logger.info(f"Total data collected: {len(all_store_data)} for {sido}")

        # 전체 판매점 ID 가져오기
        all_store_ids = get_all_store_ids(all_store_data)

        # 기존 테이블에서 판매점 ID 가져오기
        existing_store_ids = get_existing_store_ids()

        # 폐점한 판매점 ID 가져오기
        inactive_store_ids = get_inactive_store_ids(existing_store_ids, all_store_ids)

        # 폐점한 판매점의 당첨 정보 삭제
        delete_winning_info(inactive_store_ids)

        # 폐점한 판매점 정보 삭제
        delete_inactive_stores(inactive_store_ids)

        for store_data in all_store_data:
            update_store_info(store_data)

        logger.info("Lotto store data collection completed.")
        return all_store_data  # 수집된 데이터 반환

    except Exception as e:
        logger.error(f"An error occurred during data collection: {str(e)}")
    finally:
        Session.remove()

# 스케줄러용 함수
if __name__ == '__main__':
    collect_all_lotto_stores()
