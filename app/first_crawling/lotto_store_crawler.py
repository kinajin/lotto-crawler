import time
import requests
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import sys
from app.models import LottoStore, engine

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




    # 지역별 페이지 수를 가져오는 함수

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





def fetch_store_data(sido, gugun='', page=1):
    """
    판매점 데이터를 가져오는 함수
    """
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': page,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        if json_data['arr']:
            return json_data['arr']
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"Failed to fetch data for {sido} {gugun} page {page}: {str(e)}")
        return []




# 판매점 데이터를 데이터베이스에 저장하는 함수
def save_store_data(store_data_list):
    lotto_stores = [LottoStore(
        id=store_data['RTLRID'],
        name=store_data['FIRMNM'],
        address=store_data['BPLCDORODTLADRES'],
        phone=store_data['RTLRSTRTELNO'],
        lat=store_data['LATITUDE'],
        lon=store_data['LONGITUDE']
    ) for store_data in store_data_list]
    
    Session.bulk_save_objects(lotto_stores)
    Session.commit()


#  판매점 데이터를 수집하는 함수
def collect_store_data():
    for sido in sido_list:
        total_page = get_page_number(sido)
        if total_page:
            print(f"Total pages for {sido}: {total_page}")
            for page in range(1, total_page + 1):
                store_data_list = fetch_store_data(sido, page=page)
                save_store_data(store_data_list)
                print(f"Data saved for {sido} page {page}")
                time.sleep(1)  # 요청 간 1초 지연



# 
def main():
    collect_store_data()
    Session.remove()

if __name__ == "__main__":
    # 프로젝트 루트 디렉토리를 sys.path에 추가
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.append(project_root)
    
    main()