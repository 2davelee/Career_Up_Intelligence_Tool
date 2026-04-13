from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

try:
    print("🚀 데이브 엔진 기상 시도...")
    driver.get("https://careerup.streamlit.app/") # URL 확인 필수!
    
    # 1. 1차 대기 (메인 프레임 로딩)
    time.sleep(30) 
    
    # 2. iframe 진입 시도
    if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
        driver.switch_to.frame(0)
        print("🌐 iframe 진입 성공")

    # 3. 인풋이 나타날 때까지 반복 확인 (최대 10회 시도)
    target_input = None
    for i in range(10):
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"🔄 [{i+1}차 시도] 발견된 input 개수: {len(inputs)}")
        
        if len(inputs) > 0:
            # placeholder 검사
            for inp in inputs:
                ph = inp.get_attribute("placeholder")
                if ph and "직무" in ph:
                    target_input = inp
                    break
            # placeholder로 못 찾았더라도 일단 인풋이 있으면 첫 번째꺼 선택
            if not target_input:
                target_input = inputs[0]
            
            if target_input:
                print(f"🎯 타겟 인풋 발견! (placeholder: {target_input.get_attribute('placeholder')})")
                break
        
        print("😴 아직 로딩 중... 10초 더 기다립니다.")
        time.sleep(10)

    # 4. 동작 수행
    if target_input:
        target_input.click()
        time.sleep(1)
        target_input.send_keys(Keys.CONTROL + "a")
        target_input.send_keys(Keys.BACKSPACE)
        target_input.send_keys("AI PM")
        time.sleep(1)
        target_input.send_keys(Keys.ENTER)
        print("✅ 성공: 데이브 엔진이 완전히 깨어났습니다!")
    else:
        print("❌ 실패: 2분간 기다렸으나 input 요소를 찾지 못했습니다.")

except Exception as e:
    print(f"❌ 에러 발생: {e}")

finally:
    driver.quit()