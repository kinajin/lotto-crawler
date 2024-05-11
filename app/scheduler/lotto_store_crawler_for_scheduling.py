import time
import requests
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from ..models import LottoStore, engine, WinningInfo
from sqlalchemy.sql import func
import json

# 데이터 저장 함수
def save_to_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# 케이스:
# 1. 폐점된 케이스 ( 매주 크롤링 할 때 리스트 비교해서 삭제)
# 2. 새로운 판매점이 생긴 케이스 (매주 크롤링 할 때 리스트 비교해서 추가)
# 3. 기존 판매점이 업데이트 된 케이스 (매주 크롤링 할 때 리스트 비교해서 정보 업데이트)
# 4. 매주 새로운 당첨 내역이 신생 판매점에서 나온 케이스 (매주 크롤링할때 판매점 먼저 리스트 업데이트 하기 때문에 상관 없음)
# 5. 매주 새로운 당첨 내역이 폐점 판매점에서 나온 케이스?  ( 화요일에 당첨되었는데 토요일에 폐점하고 일요일에 크롤링할 경우? )


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
        print(f"Failed to get {sido} totalPage: {str(e)}")
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

        # 데이터 저장
        response.raise_for_status()
        json_data = response.json()
        all_store_data.extend(json_data['arr'])  # all_store_data에 데이터 추가

    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"Failed to get {sido} data: {str(e)}")



# 전체 판매점 ID 가져오기 함수
def get_all_store_ids(all_store_data):
    all_store_ids = [store_data['RTLRID'] for store_data in all_store_data]
    return all_store_ids


# 기존 테이블에서 판매점 ID 가져오기 함수
def get_existing_store_ids():
    existing_store_ids = Session.query(LottoStore.id).all()
    existing_store_ids = [str(store_id[0]) for store_id in existing_store_ids]
    return existing_store_ids


# 폐점한 판매점 ID 가져오기 함수
def get_inactive_store_ids(existing_store_ids, all_store_ids):
    inactive_store_ids = set(existing_store_ids) - set(all_store_ids)
    return inactive_store_ids


# 폐점한 판매점의 당첨 정보 삭제 함수
def delete_winning_info(inactive_store_ids):
    for store_id in inactive_store_ids:
        Session.query(WinningInfo).filter_by(store_id=store_id).delete()
        print("Deleted winning info for store:", store_id)
    Session.commit()


# 폐점한 판매점 정보 삭제 함수
def delete_inactive_stores(inactive_store_ids):
    if inactive_store_ids:
        Session.query(LottoStore).filter(LottoStore.id.in_(inactive_store_ids)).delete(synchronize_session=False)
        print("Deleted inactive stores:", inactive_store_ids)
        print("Deleted inactive stores names:", Session.query(LottoStore.name).filter(LottoStore.id.in_(inactive_store_ids)).all())        
        Session.commit()
    else:
        print("There is no inactive stores, 새로 폐점한 판매점이 존재하지 않습니다.")

# 판매점 정보 업데이트 함수
def update_store_info(store_data):
    store_id = store_data['RTLRID']
    lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()
    
    if lotto_store:
        updated_fields = []
        
        if lotto_store.name != store_data['FIRMNM']:
            print(f"Store name changed from {lotto_store.name} to {store_data['FIRMNM']}")
            lotto_store.name = store_data['FIRMNM']
            updated_fields.append('name')
        
        if lotto_store.address != store_data['BPLCDORODTLADRES']:
            print(f"Store address changed from {lotto_store.address} to {store_data['BPLCDORODTLADRES']}")
            lotto_store.address = store_data['BPLCDORODTLADRES']
            updated_fields.append('address')
        
        if lotto_store.phone != store_data['RTLRSTRTELNO']:
            print(f"Store phone number changed from {lotto_store.phone} to {store_data['RTLRSTRTELNO']}")
            lotto_store.phone = store_data['RTLRSTRTELNO']
            updated_fields.append('phone')
        
        try:
            lotto_store_lat = float(lotto_store.lat)
            store_data_lat = float(store_data['LATITUDE'])
            if lotto_store_lat != store_data_lat:
                print(f"Store latitude changed from {lotto_store_lat} to {store_data_lat}")
                lotto_store.lat = store_data_lat
                updated_fields.append('lat')
        except (ValueError, TypeError):
            print(f"Error converting LATITUDE to float for store {store_id}")
        
        try:
            lotto_store_lon = float(lotto_store.lon)
            store_data_lon = float(store_data['LONGITUDE'])
            if lotto_store_lon != store_data_lon:
                print(f"Store longitude changed from {lotto_store_lon} to {store_data_lon}")
                lotto_store.lon = store_data_lon
                updated_fields.append('lon')
        except (ValueError, TypeError):
            print(f"Error converting LONGITUDE to float for store {store_id}")
        
        if updated_fields:
            print(f"Updated store info for store {store_id}: {', '.join(updated_fields)}")
            Session.commit()

    
    else:
        try:
            lotto_store = LottoStore(
                id=store_id,
                name=store_data['FIRMNM'],
                address=store_data['BPLCDORODTLADRES'],
                phone=store_data['RTLRSTRTELNO'],
                lat=float(store_data['LATITUDE']),
                lon=float(store_data['LONGITUDE']),
            )
            print("Added new store:", store_id)
            Session.add(lotto_store)
            Session.commit()
        except (ValueError, TypeError):
            print(f"Error creating new store {store_id} due to invalid LATITUDE or LONGITUDE")



# 전체 판매점 데이터 수집 함수
def collect_all_lotto_stores():
    all_store_data = [] 
    try:
        # 데이터 수집 실행
        for sido in sido_list:
            total_page = get_page_number(sido)
            if total_page:
                print(f"Total pages for {sido}: {total_page}")
                for page in range(1, total_page + 1):

                    # 데이터 수집
                    fetch_data(sido, page=page, all_store_data=all_store_data)  
                    print(f"Data collection in progress: {sido} - page {page}")
                    print(f"Total data collected: {len(all_store_data)}")

        # 전체 판매점 ID 가져오기
        all_store_ids = get_all_store_ids(all_store_data)

        # 기존 테이블에서 판매점 ID 가져오기
        existing_store_ids = get_existing_store_ids()

        # 폐점한 판매점 ID 가져오기
        inactive_store_ids = get_inactive_store_ids(existing_store_ids, all_store_ids)

        # 폐점한 판매점 ID 저장 테스트용
        save_to_file(list(inactive_store_ids), 'inactive_store_ids.json')

        # 폐점한 판매점의 당첨 정보 삭제
        delete_winning_info(inactive_store_ids)

        # 폐점한 판매점 정보 삭제
        delete_inactive_stores(inactive_store_ids)

        for store_data in all_store_data:
            update_store_info(store_data)

        print("Lotto store data collection completed.")
        return all_store_data  # 수집된 데이터 반환

    except Exception as e:
        print(f"An error occurred during data collection: {str(e)}")
    finally:
        Session.remove()


# 스케줄러용 함수
if __name__ == '__main__':
    collect_all_lotto_stores()