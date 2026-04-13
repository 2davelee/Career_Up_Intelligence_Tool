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
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

try:
    print("🚀 데이브 엔진 기상 시도...")
    driver.get("https://your-app-url.streamlit.app/") 
    
    # 1. 초기 로딩 대기
    time.sleep(30) 
    
    # 2. iframe 전환
    if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
        print("🌐 iframe 내부로 진입합니다.")
        driver.switch_to.frame(0)
    
    # 3. 인풋창이 '상호작용 가능'할 때까지 대기 (핵심!)
    wait = WebDriverWait(driver, 30)
    print("🔍 검색창 활성화 대기 중...")
    
    # 단순히 존재하는 게 아니라, '클릭 가능'할 때까지 기다립니다.
    search_input = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "input")))
    
    # 4. 안전하게 입력 수행
    # 가끔 바로 입력하면 씹히는 경우가 있어 클릭 후 여유를 줍니다.
    search_input.click()
    time.sleep(1)
    
    # 기존 내용 지우고 입력
    search_input.send_keys(Keys.CONTROL + "a")
    search_input.send_keys(Keys.BACKSPACE)
    search_input.send_keys("AI PM")
    time.sleep(1)
    search_input.send_keys(Keys.ENTER)
    
    print("✅ 성공: 데이브 엔진이 힘차게 깨어났습니다!")
    time.sleep(5)

except Exception as e:
    print(f"❌ 에러 발생: {e}")

finally:
    driver.quit()