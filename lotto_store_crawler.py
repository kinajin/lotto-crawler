

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import json
import os

# ChromeDriverManager를 사용하여 Chrome Driver 경로 가져오기
driver_path = ChromeDriverManager().install()

# Service 객체 생성
service = Service(driver_path)

# 크롬 드라이버 옵션
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')  # 헤드리스 모드 설정

# 셀레니움 웹드라이버 초기화
driver = webdriver.Chrome(service=service, options=chrome_options)

# 시/도 리스트
sido_list = ['서울', '경기', '부산', '대구', '인천', '대전', '울산', '강원', '충북', '충남', '광주', '전북', '전남', '경북', '경남', '제주', '세종']

# 헤더 설정
headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}



# 데이터 수집 함수
def getPageNumber(sido, gugun=''):
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': 1,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    response = requests.post(url, data=data, headers=headers)
    
    # 응답 상태 확인 및 데이터 처리
    if response.status_code == 200:
        try:
            json_data = response.json()
            if json_data['arr']:
                return json_data.get('totalPage')
        except:
            print(f"Failed to get {sido} totalPage")
    else:
        print(f"Request failed with status {response.status_code} for {sido} {gugun} page {page}")




# 데이터 수집 함수
def fetch_and_save_data(sido, gugun='', page=1):
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': page,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    response = requests.post(url, data=data, headers=headers)
    
    # 응답 상태 확인 및 데이터 처리
    if response.status_code == 200:

        try:
            json_data = response.json()

            if json_data['arr']:

                # data 폴더 경로 생성
                data_folder = "lotto_store_data"

                # data 폴더가 없으면 생성
                os.makedirs(data_folder, exist_ok=True)
    
                # 파일 경로 생성
                file_name = os.path.join(data_folder, f"lotto_stores_{sido}_{gugun if gugun else '전체'}_{page}.json")    
                with open(file_name, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)


        except json.JSONDecodeError:
            print(f"Failed to decode JSON from response for {sido} {gugun} page {page}")
    else:
        print(f"Request failed with status {response.status_code} for {sido} {gugun} page {page}")





# 데이터 수집 실행
for sido in sido_list:

    # 페이지 번호 추출
    total_page = getPageNumber(sido)
    print (f"Total page for {sido}: {total_page}")

    # 페이지별로 데이터 수집
    for page in range(1, total_page+1):
        fetch_and_save_data(sido, page=page)










