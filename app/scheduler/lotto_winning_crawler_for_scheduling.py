from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from sqlalchemy.orm import scoped_session, sessionmaker
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time
from app.models import WinningInfo, engine, LottoStore

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("winning_data_crawler.log"),  # 파일에 로그를 기록
        logging.StreamHandler()  # 콘솔에 로그를 출력
    ]
)
logger = logging.getLogger(__name__)

# 세션 생성
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Chrome Driver 설정 함수
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless 모드
    chrome_options.add_argument("--no-sandbox")  # 리눅스에서 실행 시 필요
    chrome_options.add_argument("--disable-dev-shm-usage")  # 리눅스에서 실행 시 필요
    chrome_options.add_argument("--disable-gpu")  # GPU 비활성화
    chrome_options.add_argument("--window-size=1920x1080")  # 화면 사이즈 설정
    
    driver_path = "/usr/local/bin/chromedriver"  # 크롬 드라이버 경로 직접 지정
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

# 드라이버 초기화
driver = initialize_driver()

# 크롤링할 페이지 접속
driver.get('https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645')
time.sleep(2)  # 2초 대기

# 회차 선택 옵션 추출
drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
drwNo_options = [option.get_attribute('value') for option in drwNo_select.options]

# 데이터베이스에서 가장 최근에 저장된 회차 번호 가져오기
latest_drwNo = WinningInfo.get_latest_drwNo(Session)

# 크롤링할 회차 범위 설정
if latest_drwNo:
    drwNo_options = [drwNo for drwNo in drwNo_options if int(drwNo) > latest_drwNo]
else:
    pass

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
                logger.info(f"{rank}등 배출점 조회 결과가 없습니다.")
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
        logger.error(f"{rank}등 배출점 테이블이 존재하지 않거나 로딩 시간이 초과되었습니다.")

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
    logger.info(f"Total pages to crawl for 2등: {max_page_number}")
    while page_number <= max_page_number:
        try:
            page_link = driver.find_element(By.XPATH, f"//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit({page_number})')]")
            page_link.click()
            time.sleep(2)  # 페이지 로딩 대기
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            page_number += 1
        except (NoSuchElementException, TimeoutException):
            logger.error(f"페이지 {page_number}가 존재하지 않거나 로딩 시간이 초과되었습니다.")
            break

def collect_all_winning_data():
    driver = initialize_driver()  # 드라이버 초기화 위치 이동
    data = {"lotto_stores": []}  # 초기화 위치 변경
    try:
        for drwNo in drwNo_options:
            logger.info("=====================================================================")
            logger.info(f"[회차 {drwNo} 크롤링 중...]")
            data["lotto_stores"] = []  # 각 회차마다 초기화
            drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
            drwNo_select.select_by_value(drwNo)
            driver.find_element(By.ID, 'searchBtn').click()
            time.sleep(1)
            crawl_table(driver, data, drwNo, "1", "//div[@class='group_content'][1]//table", True)
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            crawl_second_tier_stores(driver, data, drwNo)
            for store_data in data["lotto_stores"]:
                store_id = store_data["store_id"]
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
                    logger.info(f"Skipping store_id {store_id} as it doesn't exist in LottoStores table.")
            Session.commit()
    except Exception as e:
        logger.error(f"An error occurred during data collection: {str(e)}")
    finally:
        driver.quit()  # 드라이버 종료
        Session.remove()


if __name__ == '__main__':
    collect_all_winning_data()
