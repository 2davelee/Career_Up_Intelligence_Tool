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
    driver.get("https://your-app-url.streamlit.app/") # URL 꼭 확인!
    
    # 1. 충분한 초기 로딩 (스트림릿은 깨어나는 데 시간이 꽤 걸립니다)
    time.sleep(45) 
    
    # 2. iframe 전환 (발견될 때까지 대기)
    try:
        wait = WebDriverWait(driver, 20)
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)
        print("🌐 iframe 내부 진입 성공")
    except:
        print("⚠️ iframe을 찾지 못했습니다. 메인 컨텐츠에서 계속 진행합니다.")

    # 3. 인풋창 탐색 (저인망 전략)
    print("🔍 검색창 타겟팅 중...")
    
    # 모든 input 태그를 다 가져옵니다.
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"📦 발견된 input 개수: {len(inputs)}")

    target_input = None
    for idx, i in enumerate(inputs):
        placeholder = i.get_attribute("placeholder")
        print(f"   [{idx}] placeholder: {placeholder}")
        # 우리가 설정한 placeholder 키워드가 포함되어 있다면 그놈입니다.
        if placeholder and "직무" in placeholder:
            target_input = i
            break
    
    # 만약 placeholder로 못 찾았다면 첫 번째 인풋을 강제로 사용
    if not target_input and len(inputs) > 0:
        target_input = inputs[0]
        print("⚠️ placeholder로 못 찾아 첫 번째 input을 강제 선택했습니다.")

    if target_input:
        # 4. 동작 수행 (클릭 -> 지우기 -> 입력)
        driver.execute_script("arguments[0].scrollIntoView();", target_input) # 스크롤 이동
        time.sleep(1)
        target_input.click()
        target_input.send_keys(Keys.CONTROL + "a")
        target_input.send_keys(Keys.BACKSPACE)
        target_input.send_keys("AI PM")
        time.sleep(1)
        target_input.send_keys(Keys.ENTER)
        print("✅ 성공: 데이브 엔진 기상 완료!")
    else:
        print("❌ 실패: 사용 가능한 input 요소를 찾지 못했습니다.")

except Exception as e:
    print(f"❌ 에러 발생: {e}")
    # 디버깅을 위해 현재 페이지의 텍스트 일부 출력
    print(driver.find_element(By.TAG_NAME, "body").text[:500])

finally:
    driver.quit()