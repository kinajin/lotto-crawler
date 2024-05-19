# app/utilities/utils.py

from config.config import HEADERS
from config.logger import logger
import requests
import html
import time
from sqlalchemy.orm import Session
from app.models import LottoStore, WinningInfo
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from sqlalchemy.orm import scoped_session, sessionmaker



# 크롤링 페이지 접근 함수 추가
def access_crawling_page(driver, url):
    driver.get(url)
    time.sleep(2)


# 회차 번호 추출 함수 추가
def extract_draw_numbers(driver):
    drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
    drwNo_options = [option.get_attribute('value') for option in drwNo_select.options]
    return drwNo_options


# 회차 선택 함수 추가
def select_draw_number(driver, drwNo):
    drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
    drwNo_select.select_by_value(drwNo)



# 검색 버튼 클릭 함수 추가
def click_search_button(driver):
    driver.find_element(By.ID, 'searchBtn').click()

















# 지역별 크롤링할 페이지 수를 가져오는 함수
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
        response = requests.post(url, data=data, headers=HEADERS, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        if json_data['arr']:
            return json_data.get('totalPage')
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logger.error(f"❌ {sido}의 총 페이지 수를 가져오는 데 실패했습니다: {str(e)}")
        return None

# 데이터 가져오기 함수
def fetch_store_data(sido, gugun='', page=1, all_store_data=None, retries=3):
    url = "https://dhlottery.co.kr/store.do?method=sellerInfo645Result"
    data = {
        'searchType': 3,
        'nowPage': page,
        'sltSIDO2': sido,
        'sltGUGUN2': gugun,
        'rtlrSttus': '001'
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(url, data=data, headers=HEADERS, timeout=20)
            response.raise_for_status()
            json_data = response.json()
            all_store_data.extend(json_data['arr'])
            return
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            if attempt < retries - 1:
                logger.warning(f"⚠️ {sido}의 데이터를 가져오는 데 실패했습니다: {str(e)}. 재시도 중... ({attempt + 1}/{retries})")
                time.sleep(2)
            else:
                logger.error(f"❌ {sido}의 데이터를 가져오는 데 실패했습니다: {str(e)}")

# HTML 엔티티 디코딩 함수
def decode_html_entities(text):
    if text is None:
        return ''
    text = text.replace("&#35;", "#")
    return html.unescape(text)

# 판매점 데이터를 데이터베이스에 저장하는 함수
def get_all_store_ids(all_store_data):
    return [store_data['RTLRID'] for store_data in all_store_data]

# 기존 테이블에서 판매점 ID 가져오기 함수
def get_existing_store_ids(Session, LottoStore):
    existing_store_ids = Session.query(LottoStore.id).all()
    return [str(store_id[0]) for store_id in existing_store_ids]

# 폐점한 판매점 ID 가져오기 함수
def get_inactive_store_ids(existing_store_ids, all_store_ids):
    return set(existing_store_ids) - set(all_store_ids)

# 폐점한 판매점의 당첨 정보 삭제 함수
def delete_winning_info(Session, WinningInfo, inactive_store_ids):
    for store_id in inactive_store_ids:
        store_name = Session.query(WinningInfo.store_name).filter_by(id=store_id).first()[0]
        Session.query(WinningInfo).filter_by(store_id=store_id).delete()
        logger.info(f"🗑️ 폐점한 판매점 {store_name} ({store_id})의 로또 당첨 정보를 삭제했습니다.")
    Session.commit()


# 데이터베이스에 당첨정보 저장 함수
def save_winning_data(Session, data):
    for store_data in data["lotto_stores"]:
        store_id = store_data["store_id"]
        logger.info(f"📌 신규 당첨점: {store_data['name']}, 주소: {store_data['address']}, 등수: {store_data['rank']}, 회차: {store_data['drwNo']}, 카테고리: {store_data.get('category')}")

        # 판매점이 존재하는 경우에만 저장
        lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()
        
        if lotto_store:
            winning_info = WinningInfo(
                draw_no=store_data["drwNo"],
                rank=store_data["rank"],
                category=store_data.get("category"),
                store_id=store_id
            )
            
            Session.add(winning_info)
        else:
            logger.warning(f"Skipping store_id {store_id} as it doesn't exist in LottoStores table.")

        Session.commit()




# 폐점한 판매점 정보 삭제 함수
def delete_inactive_stores(Session, LottoStore, inactive_store_ids):
    if inactive_store_ids:
        for store_id in inactive_store_ids:
            store_name = Session.query(LottoStore.name).filter_by(id=store_id).first()[0]
            Session.query(LottoStore).filter_by(id=store_id).delete()
            logger.info(f"🗑️ 폐점한 판매점 {store_name} ({store_id})를 삭제하였습니다.")
        Session.commit()
    else:
        logger.info("🔍 새로 폐점한 판매점이 존재하지 않습니다.")

# 판매점 정보 업데이트 함수
def update_store_info(Session, store_data):
    store_id = store_data['RTLRID']
    lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()
    
    if lotto_store:
        updated_fields = []
        
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

# 테이블 크롤링 함수
def crawl_table(driver, data, drwNo, rank, xpath, include_category=False):
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        for row in rows:
            columns = row.find_elements(By.XPATH, ".//td")
            if "조회 결과가 없습니다." in row.text:
                logger.info(f"🔍 {rank}등 배출점 조회 결과가 없습니다.")
                continue
            name = columns[1].text
            category = columns[2].text if include_category else None
            address = columns[3].text if include_category else columns[2].text
            store_id = row.find_element(By.XPATH, ".//a[contains(@onclick, 'showMapPage')]").get_attribute("onclick")
            store_id = store_id.split("'")[1]
            store_data = {
                "drwNo": drwNo,
                "rank": rank,
                "name": name,
                "address": address,
                "store_id": store_id
            }
            if include_category:
                store_data["category"] = category
            data["lotto_stores"].append(store_data)
    except (NoSuchElementException, TimeoutException):
        logger.error(f"❌ {rank}등 배출점 테이블이 존재하지 않거나 로딩 시간이 초과되었습니다.")

# 마지막 페이지 번호 추정 함수
def estimate_last_page_number(driver):
    try:
        page_links = driver.find_elements(By.XPATH, "//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit')]")
        if len(page_links) > 0:
            page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]
            max_page_number = max(page_numbers)
            end_page_link = driver.find_elements(By.XPATH, "//div[@class='paginate_common']//a[contains(@class, 'go end')]")
            if end_page_link:
                end_page_number = int(end_page_link[0].get_attribute("onclick").split("(")[1].split(")")[0])
                max_page_number = max(max_page_number, end_page_number)
            return max_page_number
        else:
            return 1
    except NoSuchElementException:
        return 1

# 2번째 페이지부터 끝 페이지까지 순회하면서 2등 판매점 크롤링 함수
def crawl_second_tier_stores(driver, data, drwNo):
    page_number = 2
    max_page_number = estimate_last_page_number(driver)
    while page_number <= max_page_number:
        try:
            page_link = driver.find_element(By.XPATH, f"//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit({page_number})')]")
            page_link.click()
            time.sleep(2)
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            page_number += 1
        except (NoSuchElementException, TimeoutException):
            logger.error(f"❌ 페이지 {page_number}가 존재하지 않거나 로딩 시간이 초과되었습니다.")
            break

# Materialized View 갱신 함수 추가
def refresh_materialized_view(engine):
    try:
        with engine.connect() as connection:
            connection.execute("REFRESH MATERIALIZED VIEW lotto_store_ranking;")
            logger.info("✅ REFRESH MATERIALIZED VIEW lotto_store_ranking 실행 완료.")
    except Exception as e:
        logger.error(f"❌ REFRESH MATERIALIZED VIEW 실행 중 오류 발생: {str(e)}")


# 드라이버 초기화 함수 추가
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    driver_path = "/usr/local/bin/chromedriver"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


# # 크롤링 데이터 저장 함수 추가
# def save_crawled_data(Session, data):
#     for store_data in data["lotto_stores"]:
#         try:
#             store_id = int(store_data["store_id"])
#             lotto_store = Session.query(LottoStore).filter_by(id=store_id).first()

#             if lotto_store:
#                 winning_info = WinningInfo(
#                     draw_no=store_data["drwNo"],
#                     rank=store_data["rank"],
#                     category=store_data.get("category"),
#                     store_id=store_id
#                 )
#                 Session.add(winning_info)
#             else:
#                 logger.warning(f"Store {store_id} does not exist in LottoStores table. Skipping...")
#                 logger.debug(store_data)
#         except ValueError:
#             logger.warning(f"Invalid store_id: {store_data['store_id']}. Skipping...")

#     Session.commit()




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


# 세션 생성 함수 추가
def create_session(engine):
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)