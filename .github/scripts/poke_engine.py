from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 브라우저 설정 (액션 서버 환경에 최적화)
options = Options()
options.add_argument("--headless") # 화면 없이 실행
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    # 1. 앱 접속 (데이비드님의 스트림릿 URL로 수정하세요)
    driver.get("https://your-app-url.streamlit.app/")
    
    # 2. 앱이 깨어날 때까지 대기 (최대 30초)
    # 인풋창이 나타날 때까지 기다립니다.
    wait = WebDriverWait(driver, 30)
    search_input = wait.until(EC.presence_of_element_located(
    (By.XPATH, f"//input[@placeholder='직무 키워드를 입력하세요.(예: 데이터기획, AI PM)']")
))
    
    # 3. 검색어 입력 (AI PM으로 검색하여 캐시 예열)
    # 기존 값이 있을 수 있으므로 Ctrl+A -> Backspace 후 입력
    search_input.send_keys(Keys.CONTROL + "a")
    search_input.send_keys(Keys.BACKSPACE)
    search_input.send_keys("AI PM")
    
    # 4. 엔터키 입력 (st.text_input은 엔터 시 바로 트리거됨)
    search_input.send_keys(Keys.ENTER)
    
    print("✅ 데이브 엔진: 검색 액션 수행 완료. 캐시 예열 중...")
    
    # 결과가 로딩될 때까지 잠시 대기
    time.sleep(10)
    print("✅ 엔진 상태 양호. 8시간 후 다시 깨우겠습니다.")

except Exception as e:
    print(f"❌ 에러 발생: {e}")

finally:
    driver.quit()