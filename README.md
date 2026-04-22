# CareerUp Intelligence Tool:
🚀[사람인 & 원티드 공고 x 잡플래닛 평점 x AI 합격 전략] 구직 의사결정 지원 도구 
- 분산된 멀티 플랫폼 채용 공고 정보와 기업 평점을 실시간으로 결합하고, **LLM 기반의 맞춤형 합격 전략**을 제시하여 지원자의 의사결정 비용을 혁신적으로 낮추는 지능형 분석 엔진입니다.

🛠️ Logic & Tech Stack
Core Logic
1. **Real-time Scraping**: 'Request'와 'BeautifulSoup'을 사용하여 사람인과 원티드의 최신 채용 공고 수집.
2. **AI Strategy Agent**: 추출된 공고 원문을 **Llama-3.3-70b-versatile(Groq)** 모델에 전달하여 기업 및 직무에 최적화된 '합격 필살기' 도출.
3. **Score Matching Engine**: 'Pandas'를 통한 사람인/원티드 공고와 해당 기업의 잡플래닛 평점 실시간 매칭. 
4. **Data Intelligence**: 최소 평점 필터링 및 세션 기반 리스트 관리를 통한 데이터의 신뢰도와 가치 보존.
5. **Report Generation**: 유저에 의해 최종 선별된 공고 리스트를 PDF 및 CSV로 다운 받는 '편리성'.

🛰 Tech Stack
- **AI/LLM**: Llama-3.3-70b-versatile (via Groq API), Prompt Engineering
    - 70B 파라미터급 대형 언어 모델을 활용한 고도로 정교한 공고 텍스트 추론 및 전략 도출. 
- **Languages**: Python, CSS3, HTML5
- **Frontend**: Streamlit (Dashboard UI & Session State Management)
- **Data Processing**: Pandas, Regular Expression
- **Scraping**: BeautifulSoup4, Requests
- **Report**: FPDF2 (Dynamic PDF Generation)
- **Ops**: GitHub Actions (Server Session Keep-alive), StreamlitCloud

✨ Key Features
- **AI 합격 전략 도출**: 개별 공고의 텍스트를 심층 분석하여 해당 기업 지원 시 강조해야 할 역량과 예상 질문 가이드 제공.
- **통합 대시보드**: 공고 제목과 잡플래닛 평점(⭐)을 한 화면에서 비교 분석.
- **평점 필터링**: 사용자가 설정한 최소 평점(예: 3.0) 이상의 공고만 선별 노출.
- **실시간 상호작용**: 관심 없는 기업/공고는 '🗑️ 제외' 버튼으로 즉시 제거하여 개인화된 리스트 구축.
- **리포트 다운로드**:
    - PDF: 잡플래닛 링크와 공고 원문 링크가 삽입된 정제된 보고서 출력.
    - CSV: 엑셀 하이퍼링크(=HYPERLINK) 수식이 포함된 데이터 시트 제공.
    - URL 파라미터 공유: 현재 검색 설정(키워드, 필터 등)을 URL 링크 하나로 공유 가능.

🤖 Reliability (Zero-Downtime)
- **Server Poking**: Streamlit Cloud의 휴면 모드를 방지하기 위해 GitHub Actions를 통해 8시간 주기로 세션을 활성화.

👨‍💻 Developer: Dave
- **Focus**: 데이터 수집부터 AI 기반 요약까지, 의사결정 비용을 획기적으로 줄이는 시스템을 설계합니다.
- **Philosophy**: “파편화된 정보를 연결해, 사용자의 이해와 판단 과정을 단축합니다.”

🚀 Usage
# 관련 라이브러리 설치
pip install -r requirements.txt

# 엔진 실행
streamlit run recruit9.py
