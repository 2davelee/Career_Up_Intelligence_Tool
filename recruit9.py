import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import quote

# --- 1. 평점 추출 및 크롤링 엔진 (기존 골든 밸런스 로직) ---

def clean_name(name):
    cleaned = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', name)
    junk_words = ['주식회사', '유한회사', '농업회사법인', '합자회사', '사단법인', '(주)']
    for word in junk_words:
        cleaned = cleaned.replace(word, '')
    return re.sub(r'[^\w\s]', '', cleaned).strip()

def extract_score_from_text(text):
    if '잡플래닛' not in text and 'jobplanet' not in text.lower():
        return 0.0
    match = re.search(r'(?:평점|별점|점수)\s?[:]?\s?(\d\.\d)', text)
    if match:
        score = float(match.group(1))
        if 1.0 < score <= 5.0: return score
    match_alt = re.search(r'(\d\.\d)(?:점| / 5)', text)
    if match_alt:
        score = float(match_alt.group(1))
        if 1.0 < score <= 5.0: return score
    return 0.0

def get_jobplanet_info(company):
    search_name = clean_name(company)
    query = quote(f"{search_name} 잡플래닛 평점")
    url = f"https://search.naver.com/search.naver?query={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://www.naver.com/'}
    score, link = 0.0, f"https://www.jobplanet.co.kr/search?query={quote(search_name)}"
    try:
        time.sleep(random.uniform(0.5, 0.8))
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        full_text = soup.get_text(separator=' ', strip=True)
        score = extract_score_from_text(full_text)
        if score == 0.0:
            containers = soup.select(".total_group, .api_txt_lines, .txt_box")
            for container in containers:
                score = extract_score_from_text(container.text)
                if score > 0: break
        link_tag = soup.select_one('a[href*="jobplanet.co.kr/companies"]')
        if link_tag: link = link_tag['href']
        return score, link
    except: return 0.0, link

# --- 2. 채용 데이터 수집 함수 ---
def get_saramin_jobs(keyword, limit=20):
    encoded_keyword = quote(keyword)
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={encoded_keyword}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.select('.item_recruit')
        job_list = []
        for job in jobs[:limit]:
            try:
                corp = job.select_one('.corp_name a').text.strip()
                title = job.select_one('.job_tit a').text.strip()
                link = "https://www.saramin.co.kr" + job.select_one('.job_tit a')['href']
                condition = job.select_one('.job_condition').text.strip().replace('\n', ' ')
                score, jp_link = get_jobplanet_info(corp)
                job_list.append({'플랫폼': '사람인', '회사명': corp, '평점': score, '잡플래닛링크': jp_link, '공고제목': title, '지원자격': condition, '링크': link})
            except: continue
        return pd.DataFrame(job_list)
    except: return pd.DataFrame()

def get_wanted_jobs(keyword, limit=20):
    encoded_keyword = quote(keyword)
    url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&job_sort=job.latest_order&locations=all&years=-1&keyword={encoded_keyword}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': f'https://www.wanted.co.kr/search?query={encoded_keyword}'}, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get('data', [])
            job_list = []
            for job in jobs[:limit]:
                corp = job['company']['name']
                score, jp_link = get_jobplanet_info(corp)
                job_list.append({'플랫폼': '원티드', '회사명': corp, '평점': score, '잡플래닛링크': jp_link, '공고제목': job['position'], '지원자격': '상세공고 참조', '링크': f"https://www.wanted.co.kr/wd/{job['id']}"})
            return pd.DataFrame(job_list)
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. Streamlit UI 및 상태 관리 (상태 유지용) ---

st.set_page_config(page_title="Dave's Verified Hub", layout="wide")

# 세션 상태 초기화: 검색 데이터를 메모리에 유지
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()

st.markdown("""
<style>
    @keyframes starPulse { 0% { transform: scale(1); } 50% { transform: scale(1.3); text-shadow: 0 0 8px #FFD700; } 100% { transform: scale(1); } }
    .rating-link { text-decoration: none; color: #FFD700 !important; font-weight: bold; }
    .rating-link:hover .animated-star { animation: starPulse 0.8s infinite; display: inline-block; }
    .no-rating { color: #ccc; font-size: 0.85em; }
    .delete-btn { color: white; background-color: #ff4b4b; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 커리어UP 인텔리전스 채용 검색 엔진")
st.write("반짝이는 **평점 ⭐**을 클릭하여 **잡플래닛 상세 리뷰**를 확인하세요.")

with st.sidebar:
    st.header("⚙️ 검색 & 필터 설정")
    platform_choice = st.radio("플랫폼 선택", ("전체 통합 검색", "사람인 (Saramin)", "원티드 (Wanted)"))
    row_count = st.slider("수집할 공고 개수 (플랫폼당)", 5, 50, 15)
    
    st.markdown("---")
    # [핵심] 평점 필터 슬라이더 추가 (0.1단위)    
    min_rating = st.slider("최소 평점 필터 (⭐)", 0.0, 5.0, 3.0, step=0.1)
    st.caption(f"⭐ {min_rating}점 이상의 공고만 표시됩니다.")
    include_no_info = st.checkbox("정보없음(❓) 기업 포함하기", value=True)
    
with st.form(key='search_form'):
    col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
    with col1:
        keyword = st.text_input("직무 키워드 입력", placeholder="예: 데이터기획, AI PM")
    with col2:
        search_submit = st.form_submit_button("엔진 가동", use_container_width=True)

# 1. 데이터 수집 실행
if search_submit:
    if keyword:
        with st.spinner(f"데이비드 엔진이 {keyword} 공고를 정밀 스캔 중..."):
            if platform_choice == "사람인 (Saramin)":
                res_df = get_saramin_jobs(keyword, row_count)
            elif platform_choice == "원티드 (Wanted)":
                res_df = get_wanted_jobs(keyword, row_count)
            else:
                df_s = get_saramin_jobs(keyword, row_count)
                df_w = get_wanted_jobs(keyword, row_count)
                res_df = pd.concat([df_s, df_w], ignore_index=True)
            
            # 수집된 데이터를 세션 상태에 저장 (인덱스 초기화 중요)
            st.session_state.raw_data = res_df.reset_index(drop=True)
    else:
        st.error("키워드를 입력해 주세요.")

# 2. 데이터 전시 및 실시간 삭제 로직
if not st.session_state.raw_data.empty:
    # 필터링 적용
    df = st.session_state.raw_data.copy()
    if include_no_info:
        filtered_df = df[(df['평점'] >= min_rating) | (df['평점'] == 0.0)]
    else:
        filtered_df = df[df['평점'] >= min_rating]
    
    filtered_df = filtered_df.sort_values(by='평점', ascending=False)

    st.subheader(f"✅ 현재 검색된 공고 ({len(filtered_df)}건)")
    st.info("💡 각 공고의 **[상세보기]**를 눌러 자격요건을 확인하고, 필요 없는 공고는 **[제외]**하세요.")
    # 테이블 헤더 (자격요건 컬럼을 빼서 가로 폭 확보)
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([1, 1.2, 0.8, 5.5, 1.5])
    headers = ["플랫폼", "회사명", "평점", "공고제목", "상세보기 & 제외"]
    for col, title in zip([h_col1, h_col2, h_col3, h_col4, h_col5], headers):
        col.write(f"**{title}**")

    for idx, row in filtered_df.iterrows():
        # 메인 정보 줄
        c1, c2, c3, c4, c5 = st.columns([1, 1.2, 0.8, 5.5, 1.5])
        c1.write(row['플랫폼'])
        c2.write(row['회사명'])
        
        if row['평점'] > 0:
            c3.markdown(f'<a href="{row["잡플래닛링크"]}" target="_blank" class="rating-link"><span class="animated-star">⭐</span> {row["평점"]}</a>', unsafe_allow_html=True)
        else:
            c3.write("❓ 정보없음")
            
        c4.write(row['공고제목'])
        
        # 버튼 영역 (상세보기와 제외 버튼을 한 곳에)
        with c5:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                # 상세보기 버튼은 토글 역할을 함
                show_detail = st.button("📝", key=f"detail_{idx}", help="자격요건 보기")
            with btn_col2:
                if st.button("🗑️", key=f"del_{idx}", help="리스트에서 제외"):
                    st.session_state.raw_data = st.session_state.raw_data.drop(idx)
                    st.rerun()

        # [핵심] 상세보기 클릭 시 펼쳐지는 영역
        if show_detail:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px;">
                    <strong>📌 {row['회사명']} - 지원자격 및 상세내용</strong><br>
                    <p style="color: #333; margin-top: 10px;">{row['지원자격']}</p>
                    <a href="{row['링크']}" target="_blank" style="color: #ff4b4b; font-weight: bold;">[공고 원문 보러가기 🔗]</a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 3. 최종 클린 CSV 다운로드
    csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 검증 완료된 클린 CSV 다운로드",
        data=csv_data,
        file_name=f"Verified_{keyword}_List.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    if not search_submit:
        st.info("사이드바에서 세부설정 후, 검색창에 검색어를 입력하고 [엔진 가동]\n\n💡 평점과 링크를 정밀 분석하느라 검색 시간이 조금 소요됩니다.")

st.caption("Produced by Dave | Career Data Intelligence Tool (Final Verified Edition)")