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
        logger.error(f"❌ {sido}의 총 페이지 수를 가져오는 데 실패했습니다: {str(e)}")
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
        logger.error(f"❌ {sido}의 데이터를 가져오는 데 실패했습니다: {str(e)}")

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
        store_name = Session.query(LottoStore.name).filter_by(id=store_id).first()[0]
        Session.query(WinningInfo).filter_by(store_id=store_id).delete()
        logger.info(f"🗑️ 폐점한 판매점 {store_name} ({store_id})의 로또 당첨 정보를 삭제했습니다.")
    Session.commit()

# 폐점한 판매점 정보 삭제 함수
def delete_inactive_stores(inactive_store_ids):
    if inactive_store_ids:
        for store_id in inactive_store_ids:
            store_name = Session.query(LottoStore.name).filter_by(id=store_id).first()[0]
            Session.query(LottoStore).filter_by(id=store_id).delete()
            logger.info(f"🗑️ 폐점한 판매점 {store_name} ({store_id})를 삭제하였습니다.")
        Session.commit()
    else:
        logger.info("🔍 새로 폐점한 판매점이 존재하지 않습니다.")

# HTML 엔티티를 처리하는 함수
def decode_html_entities(text):
    if text is None:
        return ''
    text = text.replace("&#35;", "#")
    return html.unescape(text)

# 판매점 정보 업데이트 함수
def update_store_info(store_data):
    store_id = store_data['RTLRID']
    lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()
    
    if lotto_store:
        updated_fields = []
        
        # Unescape HTML entities in store_data
        firm_name = decode_html_entities(store_data.get('FIRMNM'))
        address = decode_html_entities(store_data.get('BPLCDORODTLADRES'))
        
        if lotto_store.name != firm_name:
            logger.info(f"🏷️ 로또판매점 이름이 {lotto_store.name}에서 {firm_name}으로 변경되었습니다.")
            lotto_store.name = firm_name
            updated_fields.append('name')
        
        if lotto_store.address != address:
            logger.info(f"🏷️ 로또판매점 {lotto_store.name} 의 주소가 {lotto_store.address}에서 {address}으로 변경되었습니다.")
            lotto_store.address = address
            updated_fields.append('address')
        
        if lotto_store.phone != store_data['RTLRSTRTELNO']:
            logger.info(f"📞 로또판매점 {lotto_store.name}의 전화번호가 {lotto_store.phone}에서 {store_data['RTLRSTRTELNO']}으로 변경되었습니다.")
            lotto_store.phone = store_data['RTLRSTRTELNO']
            updated_fields.append('phone')
        
        try:
            lotto_store_lat = float(lotto_store.lat)
            store_data_lat = float(store_data['LATITUDE'])
            if lotto_store_lat != store_data_lat:
                logger.info(f"🌐 로또판매점 {lotto_store.name}의 위도가 {lotto_store_lat}에서 {store_data_lat}으로 변경되었습니다.")
                lotto_store.lat = store_data_lat
                updated_fields.append('lat')
        except (ValueError, TypeError):
            logger.error(f"❌ 로또판매점 {lotto_store.name}의 {store_id}의 위도를 float로 변환하는 데 오류가 발생했습니다.")
        
        try:
            lotto_store_lon = float(lotto_store.lon)
            store_data_lon = float(store_data['LONGITUDE'])
            if lotto_store_lon != store_data_lon:
                logger.info(f"🌐 로또판매점 {lotto_store.name}의 경도가 {lotto_store_lon}에서 {store_data_lon}으로 변경되었습니다.")
                lotto_store.lon = store_data_lon
                updated_fields.append('lon')
        except (ValueError, TypeError):
            logger.error(f"❌ 로또판매점 {lotto_store.name}의 {store_id}의 경도를 float로 변환하는 데 오류가 발생했습니다.")
        
        if updated_fields:
            Session.commit()
    
    else:
        # 여기서 firm_name과 address를 미리 정의합니다.
        firm_name = decode_html_entities(store_data.get('FIRMNM', ''))
        address = decode_html_entities(store_data.get('BPLCDORODTLADRES', ''))

        try:
            lotto_store = LottoStore(
                id=store_id,
                name=firm_name,
                address=address,
                phone=store_data['RTLRSTRTELNO'],
                lat=float(store_data['LATITUDE']),
                lon=float(store_data['LONGITUDE']),
            )
            logger.info(f"🆕 새로운 판매점 추가: id: {store_id}, 이름: {firm_name}, 주소: {address}, 전화번호: {store_data['RTLRSTRTELNO']}, 위도: {store_data['LATITUDE']}, 경도: {store_data['LONGITUDE']}")
            Session.add(lotto_store)
            Session.commit()
        except (ValueError, TypeError):
            logger.error(f"❌ 유효하지 않은 위도 또는 경도로 인해 판매점 {firm_name}({store_id})을 생성하는 데 오류가 발생했습니다.")

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
            logger.info(f"📊 {sido}에서 수집된 총 로또 판매점 수: {len(all_store_data)}")

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

        # 판매점 정보 업데이트
        for store_data in all_store_data:
            update_store_info(store_data)
        return all_store_data  # 수집된 데이터 반환

    except Exception as e:
        logger.error(f"❌ 데이터 수집 중 오류 발생: {str(e)}")
    finally:
        Session.remove()

# 스케줄러용 함수
if __name__ == '__main__':
    collect_all_lotto_stores()
