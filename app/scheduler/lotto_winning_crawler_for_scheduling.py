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
        logging.FileHandler("winning_data_crawler.log", encoding='utf-8'),  # 파일에 로그를 기록
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

def collect_all_winning_data():
    driver = initialize_driver()  # 드라이버 초기화 위치 이동
    data = {"lotto_stores": []}  # 데이터 초기화


    try:
        # 크롤링할 페이지 접속
        driver.get('https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645')
        
        # 페이지 로드 대기
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'drwNo'))
        )
        time.sleep(2)  # 추가 대기
        
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

        # 최신 로또 당첨 회차가 이미 데이터베이스에 저장되어 있으면 추가 크롤링이 필요하지 않음
        if not drwNo_options:
            logger.info("📢 최신 로또 당첨 회차가 이미 데이터베이스에 저장되어 있습니다. 추가 크롤링이 필요하지 않습니다.")
            return

        for drwNo in drwNo_options:
            logger.info(f"🎯 [회차 {drwNo} 크롤링 중...]")
            data["lotto_stores"] = []  # 각 회차마다 초기화

            # 회차 선택
            drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))

            # 회차 선택 후 조회 버튼 클릭
            drwNo_select.select_by_value(drwNo)
            driver.find_element(By.ID, 'searchBtn').click()
            time.sleep(1)

            # 첫 페이지의 1등, 2등 배출점 크롤링
            crawl_table(driver, data, drwNo, "1", "//div[@class='group_content'][1]//table", True)
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")

            # 2번째 페이지부터 끝 페이지까지 순회하면서 2등 판매점 크롤링 함수
            crawl_second_tier_stores(driver, data, drwNo)

            # 크롤링한 데이터를 데이터베이스에 저장
            for store_data in data["lotto_stores"]:
                store_id = store_data["store_id"]

                logger.info(f"📌 신규 당첨점: {store_data['name']}, 주소: {store_data['address']}, 등수: {store_data['rank']}, 회차: {store_data['drwNo']}, 카테고리: {store_data.get('category')}")

                
                # LottoStores 테이블에서 store_id 확인
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
                    print(f"Skipping store_id {store_id} as it doesn't exist in LottoStores table.")

                Session.commit()

        # 데이터 수집 후 Materialized View 갱신
        refresh_materialized_view()
    except Exception as e:
        logger.error(f"❌ 데이터 수집 중 오류 발생: {str(e)}")
    finally:
        driver.quit()  # 드라이버 종료
        Session.remove()

# 테이블 크롤링 함수
def crawl_table(driver, data, drwNo, rank, xpath, include_category=False):
    try:

        # 테이블 로딩 대기
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        # 테이블 데이터 추출
        rows = table.find_elements(By.XPATH, ".//tbody/tr")

        # 테이블 데이터 순회
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
    # logger.info(f"📝 2등 배출점 크롤링할 총 페이지 수: {max_page_number}")
    while page_number <= max_page_number:
        try:
            page_link = driver.find_element(By.XPATH, f"//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit({page_number})')]")
            page_link.click()
            time.sleep(2)  # 페이지 로딩 대기
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            page_number += 1
        except (NoSuchElementException, TimeoutException):
            logger.error(f"❌ 페이지 {page_number}가 존재하지 않거나 로딩 시간이 초과되었습니다.")
            break

# Materialized View 갱신 함수 추가
def refresh_materialized_view():
    try:
        with engine.connect() as connection:
            connection.execute("REFRESH MATERIALIZED VIEW lotto_store_ranking;")
            logger.info("✅ REFRESH MATERIALIZED VIEW lotto_store_ranking 실행 완료.")
    except Exception as e:
        logger.error(f"❌ REFRESH MATERIALIZED VIEW 실행 중 오류 발생: {str(e)}")

if __name__ == '__main__':
    collect_all_winning_data()