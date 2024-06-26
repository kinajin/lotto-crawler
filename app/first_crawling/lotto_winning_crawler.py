


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from app.models import engine, WinningInfo, LottoStore

# 세션 생성
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


# 드라이버 초기화 함수
def initialize_driver():
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    return driver


# 크롤링 페이지 접속 함수
def access_crawling_page(driver):
    driver.get('https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645')
    time.sleep(2)  # 2초 대기



# 회차 번호 추출 함수
def extract_draw_numbers(driver):
    drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
    drwNo_options = [option.get_attribute('value') for option in drwNo_select.options]
    return drwNo_options


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
                print(f"{rank}등 배출점 조회 결과가 없습니다.")
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
        print(f"{rank}등 배출점 테이블이 존재하지 않거나 로딩 시간이 초과되었습니다.")


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


# 2등 판매점 크롤링 함수
def crawl_second_tier_stores(driver, data, drwNo):
    page_number = 2
    max_page_number = estimate_last_page_number(driver)
    print(max_page_number)
    
    while page_number <= max_page_number:
        try:
            page_link = driver.find_element(By.XPATH, f"//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit({page_number})')]")
            page_link.click()
            time.sleep(2)  # 페이지 로딩 대기
            
            crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            
            page_number += 1
        
        except (NoSuchElementException, TimeoutException):
            print(f"페이지 {page_number}가 존재하지 않거나 로딩 시간이 초과되었습니다.")
            break

# 회차 선택 함수
def select_draw_number(driver, drwNo):
    drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
    drwNo_select.select_by_value(drwNo)

# 조회 버튼 클릭 함수
def click_search_button(driver):
    driver.find_element(By.ID, 'searchBtn').click()

# 첫 페이지 크롤링 함수
def crawl_first_page(driver, data, drwNo):
    crawl_table(driver, data, drwNo, "1", "//div[@class='group_content'][1]//table", True)
    crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")

# 크롤링 데이터 저장 함수
def save_crawled_data(data):
    for store_data in data["lotto_stores"]:
        try:
            store_id = int(store_data["store_id"])
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
                print(f"Store {store_id} does not exist in LottoStores table. Skipping...")
                print(store_data)
        except ValueError:
            print(f"Invalid store_id: {store_data['store_id']}. Skipping...")

    Session.commit()

# 크롤링 및 데이터 저장 함수
def crawl_and_save_data(driver, drwNo_options):
    for drwNo in drwNo_options:
        print("=====================================================================")
        print(f"[회차 {drwNo} 크롤링 중...]")
        data = {"lotto_stores": []}

        select_draw_number(driver, drwNo)
        click_search_button(driver)
        time.sleep(1)

        crawl_first_page(driver, data, drwNo)
        crawl_second_tier_stores(driver, data, drwNo)

        save_crawled_data(data)

# 메인 함수
def main():
    driver = initialize_driver()
    access_crawling_page(driver)
    drwNo_options = extract_draw_numbers(driver)

    crawl_and_save_data(driver, drwNo_options)

    driver.quit()
    Session.remove()

# 스크립트 실행
if __name__ == "__main__":
    main()





# from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import Select
# from selenium.common.exceptions import NoSuchElementException, TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager
# import time
# from sqlalchemy.orm import scoped_session
# from sqlalchemy.orm import sessionmaker

# import os
# import sys

# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# sys.path.append(project_root)

# from app.models import engine, WinningInfo, LottoStore



# # 세션 생성
# session_factory = sessionmaker(bind=engine)
# Session = scoped_session(session_factory)

# # ChromeDriverManager를 사용하여 Chrome Driver 경로 가져오기
# driver_path = ChromeDriverManager().install()
# service = Service(driver_path)
# driver = webdriver.Chrome(service=service)

# # 크롤링할 페이지 접속
# driver.get('https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645')
# time.sleep(2)  # 2초 대기

# # 회차 선택 옵션 추출
# drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
# drwNo_options = [option.get_attribute('value') for option in drwNo_select.options]


# # 테이블 크롤링 함수
# def crawl_table(driver, data, drwNo, rank, xpath, include_category=False):
#     try:
#         # 테이블이 나타날 때까지 최대 10초 동안 기다림
#         table = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, xpath))
#         )

#         # 테이블의 모든 행 추출
#         rows = table.find_elements(By.XPATH, ".//tbody/tr")

#         # 정보 출력
#         for row in rows:
#             columns = row.find_elements(By.XPATH, ".//td")
            
#             # 조회 결과가 없는 경우 건너뛰기
#             if "조회 결과가 없습니다." in row.text:
#                 print(f"{rank}등 배출점 조회 결과가 없습니다.")
#                 continue
            
#             # 행의 각 열에서 정보 추출
#             name = columns[1].text
#             category = columns[2].text if include_category else None
#             address = columns[3].text if include_category else columns[2].text
#             store_id = row.find_element(By.XPATH, ".//a[contains(@onclick, 'showMapPage')]").get_attribute("onclick")
#             store_id = store_id.split("'")[1]
            
#             # 크롤링한 데이터를 딕셔너리에 추가
#             store_data = {
#                 "drwNo": drwNo,
#                 "rank": rank,
#                 "name": name,
#                 "address": address,
#                 "store_id": store_id
#             }
#             if include_category:
#                 store_data["category"] = category
            
#             # 딕셔너리를 데이터 리스트에 추가
#             data["lotto_stores"].append(store_data)
    
#     except (NoSuchElementException, TimeoutException):
#         print(f"{rank}등 배출점 테이블이 존재하지 않거나 로딩 시간이 초과되었습니다.")


# # 마지막 페이지 번호 추정 함수
# def estimate_last_page_number(driver):
#     try:
#         # 페이지 번호 링크 요소들을 찾음
#         page_links = driver.find_elements(By.XPATH, "//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit')]")
        
#         if len(page_links) > 0:
#             # 페이지 번호 추출하여 정수로 변환
#             page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]
            
#             # 페이지 번호 중 최댓값 반환
#             max_page_number = max(page_numbers)
            
#             # "끝 페이지" 링크 확인
#             end_page_link = driver.find_elements(By.XPATH, "//div[@class='paginate_common']//a[contains(@class, 'go end')]")
#             if end_page_link:
#                 # "끝 페이지" 링크에서 페이지 번호 추출
#                 end_page_number = int(end_page_link[0].get_attribute("onclick").split("(")[1].split(")")[0])
#                 max_page_number = max(max_page_number, end_page_number)
            
#             return max_page_number
#         else:
#             # 페이지 번호 링크가 없는 경우 1 반환
#             return 1
    
#     except NoSuchElementException:
#         # 페이지 번호 링크가 없는 경우 1 반환
#         return 1



# # 2번째 페이지부터 끝 페이지까지 순회하면서 2등 판매점 크롤링 함수
# def crawl_second_tier_stores(driver, data, drwNo):
#     page_number = 2
#     max_page_number = estimate_last_page_number(driver)
#     print(max_page_number)
    
#     while page_number <= max_page_number:

#         try:
#             # 페이지 번호 클릭
#             page_link = driver.find_element(By.XPATH, f"//div[@class='paginate_common']//a[contains(@onclick, 'selfSubmit({page_number})')]")
#             page_link.click()
#             time.sleep(2)  # 페이지 로딩 대기
            
#             # 현재 페이지 크롤링
#             crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")
            
#             page_number += 1
        
#         except (NoSuchElementException, TimeoutException):
#             print(f"페이지 {page_number}가 존재하지 않거나 로딩 시간이 초과되었습니다.")
#             break






# # 각 회차별로 크롤링 수행
# for drwNo in drwNo_options:

#     print("=====================================================================")
#     print(f"[회차 {drwNo} 크롤링 중...]")

#     data = {"lotto_stores": []}

#     # 회차 선택
#     drwNo_select = Select(driver.find_element(By.ID, 'drwNo'))
#     drwNo_select.select_by_value(drwNo)

#     # 조회 버튼 클릭
#     driver.find_element(By.ID, 'searchBtn').click()

#     # 페이지 로딩 대기
#     time.sleep(1)

#     #첫 페이지 크롤링 1등 배출점 크롤링, 2등 배출점 크롤링
#     crawl_table(driver, data, drwNo, "1", "//div[@class='group_content'][1]//table", True)
#     crawl_table(driver, data, drwNo, "2", "//div[@class='group_content'][2]//table")

#     #2페이지 부터 끝 페이지까지 2등 배출점 크롤링
#     crawl_second_tier_stores(driver, data, drwNo)
    
#     # 크롤링한 데이터 저장
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
#                 print(f"Store {store_id} does not exist in LottoStores table. Skipping...")
#                 print(store_data)
#         except ValueError:
#             print(f"Invalid store_id: {store_data['store_id']}. Skipping...")

#     Session.commit()


# # 드라이버 종료
# driver.quit()
# Session.remove()
