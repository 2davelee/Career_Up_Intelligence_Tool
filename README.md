# CareerUp Intelligence Tool:
🚀[사람인 공고 x 잡플래닛 평점] 구직 의사결정 지원 도구 
- 채용 공고 정보와 기업 평점을 실시간으로 결합하여, 지원자가 기업의 내실을 한눈에 파악할 수 있도록 돕는 지능형 검색 엔진입니다.

🛠️ Logic & Tech Stack
Core Logic
1. Real-time Scraping: Requests와 BeautifulSoup을 사용하여 사람인의 최신 채용 공고 수집.
2. Score Matching Engine: 네이버 검색 API와 정규표현식(re)을 활용해 해당 기업의 잡플래닛 평점 및 리뷰 링크를 실시간으로 타겟팅.
3. Data Intelligence: 평점 필터링(Min Score) 및 중복/제외 공고 필터링을 통해 '클린 데이터' 추출.
4. Report Generation: 수집된 데이터를 하이퍼링크가 포함된 PDF 및 CSV 리포트로 즉시 변환.

Tech Stack
- Languages: Python, CSS3, HTML5
- Frontend: Streamlit (Dashboard UI)
- Data Processing: Pandas, Regular Expression
- Scraping: BeautifulSoup4, Requests
- Report: FPDF2 (Dynamic PDF Generation)
- Ops: GitHub Actions (Server Session Keep-alive via Selenium Poking), StreamlitCloud

✨ Key Features
- 통합 대시보드: 공고 제목과 잡플래닛 평점(⭐)을 한 화면에서 비교 분석.
- 평점 필터링: 사용자가 설정한 최소 평점(예: 3.0) 이상의 공고만 선별 노출.
- 실시간 상호작용: 관심 없는 기업/공고는 '🗑️ 제외' 버튼으로 즉시 리스트에서 제거.
- 리포트 다운로드:
    - PDF: 잡플래닛 링크와 공고 원문 링크가 삽입된 정제된 보고서 출력.
    - CSV: 엑셀 하이퍼링크(=HYPERLINK) 수식이 포함된 데이터 시트 제공.
    - URL 파라미터 공유: 현재 검색 설정(키워드, 필터 등)을 URL 링크 하나로 공유 가능.

🤖 Reliability (Zero-Downtime)
- Server Poking: Streamlit Cloud의 휴면 모드를 방지하기 위해 GitHub Actions를 통해 8시간 주기로 세션을 활성화합니다.
- Multithreading: 데이터 수집 시 UI 멈춤 현상을 방지하기 위해 threading을 적용하여 무중단 사용자 경험을 제공합니다.

👨‍💻 Developer: Dave
- Focus: 데이터 기반의 효율적인 구직 의사결정 프로세스 설계 및 자동화.
- Philosophy: "복잡한 정보의 결합을 통해 의사결정 비용을 최소화한다."

🚀 Usage
# 관련 라이브러리 설치
pip install -r requirements.txt

# 엔진 실행
streamlit run main.py