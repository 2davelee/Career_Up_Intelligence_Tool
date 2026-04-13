from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# 유저 에이전트를 설정해 실제 브라우저처럼 보이게 합니다.
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

try:
    print("🚀 데이브 엔진 기상 시도...")
    driver.get("https://careerup.streamlit.app/") # URL 다시 확인!
    
    # 1. 페이지 로딩 대기
    time.sleep(30) 
    
    # 2. 스트림릿 메인 iframe이 있는지 확인하고 전환 (핵심!)
    # 스트림릿 클라우드는 앱 콘텐츠를 보통 iframe 내부에 둡니다.
    if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
        print("🌐 iframe 발견! 내부로 전환합니다.")
        driver.switch_to.frame(0)
    
    # 3. 인풋창 찾기 (가장 원시적이지만 확실한 방법)
    # placeholder고 뭐고 그냥 '첫 번째 나오는 input'을 잡습니다.
    wait = WebDriverWait(driver, 30)
    print("🔍 검색창 타겟팅 중...")
    
    # 모든 input 태그 중 첫 번째 요소를 기다림
    search_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
    
    # 4. 동작 수행
    search_input.click() # 일단 클릭해서 포커스
    search_input.send_keys("AI PM")
    search_input.send_keys(Keys.ENTER)
    
    print("✅ 성공: 엔진이 정상적으로 깨어났습니다!")
    time.sleep(5)

except Exception as e:
    print(f"❌ 실패 로그: {e}")
    # 실패 시 화면 스크린샷 대신 HTML 소스 일부 출력 (디버깅용)
    print("--- 현재 페이지 태그 요약 ---")
    tags = [tag.tag_name for tag in driver.find_elements(By.XPATH, "//*")[:20]]
    print(f"상위 태그 목록: {tags}")

finally:
    driver.quit()