import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import quote
from fpdf import FPDF
import os
from datetime import datetime
import pytz
import logging
logging.getLogger("fpdf.fonts").setLevel(logging.ERROR)

def create_pdf(df):
    from fpdf import FPDF
    import os
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.add_page()
    
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Nanum", style="", fname=font_path)
        pdf.add_font("Nanum", style="B", fname=font_path) 
        pdf.set_font("Nanum", size=12)
    else:
        return bytes(pdf.output())

    # 1. 헤더 (txt -> text, ln -> new_x/y 로 전면 교체)
    pdf.set_fill_color(0, 51, 102) 
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Nanum", style="B", size=20)
    
    # [수정] txt -> text, ln=True -> new_x/y 방식으로 변경
    pdf.cell(0, 20, text="[CareerUp] 채용 데이터 분석 보고서", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)
    
    # 2. 데이터 본문
    pdf.set_text_color(0, 0, 0)
    for idx, (original_idx, row) in enumerate(df.head(20).iterrows()):
        if pdf.get_y() > 240:
            pdf.add_page()
            pdf.ln(10)

        curr_y = pdf.get_y()

        # --- 왼쪽 영역 ---
        pdf.set_font("Nanum", style="B", size=12)
        company_text = f"{idx+1}. {row['회사명']} ({row['플랫폼']})"
        pdf.text(15, curr_y + 5, company_text)
        
        pdf.set_font("Nanum", style="", size=10)
        qual_text = row.get('지원자격', row.get('경력', '상세 자격요건은 공고 참조'))
        
        pdf.set_xy(15, curr_y + 8)
        # [수정] txt -> text
        pdf.multi_cell(130, 6, text=f"TITLE: {row['공고제목']}")
        
        pdf.set_xy(15, pdf.get_y())
        pdf.set_text_color(80, 80, 80)
        # [수정] txt -> text
        pdf.multi_cell(130, 6, text=f"QUALIFICATION: {qual_text}")

        # --- 오른쪽 영역 ---
        score = row['평점'] if row['평점'] > 0 else "N/A"
        pdf.set_font("Nanum", style="B", size=11)
        pdf.set_text_color(200, 100, 0) 
        pdf.text(155, curr_y + 5, f"기업 Score: {score}")

        link = row.get('링크', row.get('url', ''))
        if link:
            pdf.set_xy(155, curr_y + 12)
            pdf.set_font("Nanum", style="", size=9)
            pdf.set_text_color(0, 0, 255)
            # [수정] txt -> text, ln 삭제 후 신규 문법 적용
            pdf.cell(
                40, 8, 
                text="상세 공고 >>", 
                border=1, 
                new_x=XPos.LMARGIN, 
                new_y=YPos.NEXT, 
                align='C', 
                link=link
            )
        
        # 하단 구분선
        pdf.ln(5)
        pdf.set_draw_color(230, 230, 230)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0) 

    return bytes(pdf.output())

def prepare_csv_data(df):
    # 원본 데이터 보호를 위해 복사본 사용
    csv_df = df.copy()

    # 1. 잡플래닛링크 컬럼 내용을 하이퍼링크 수식으로 완전 대체
    if '잡플래닛링크' in csv_df.columns:
        csv_df['잡플래닛링크'] = csv_df['잡플래닛링크'].apply(
            lambda x: f'=HYPERLINK("{x}", "리뷰확인")' if pd.notnull(x) and x != "" else "정보없음"
        )

    # 2. 채용 공고(링크/url) 컬럼 내용을 하이퍼링크 수식으로 완전 대체
    link_col = '링크' if '링크' in csv_df.columns else 'url'
    if link_col in csv_df.columns:
        csv_df[link_col] = csv_df[link_col].apply(
            lambda x: f'=HYPERLINK("{x}", "공고보기")' if pd.notnull(x) and x != "" else "링크없음"
        )

    # 한글 깨짐 방지를 위해 utf-8-sig 인코딩 적용하여 바이너리 반환
    return csv_df.to_csv(index=False).encode('utf-8-sig')

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
@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
    st.caption(f"⭐ {min_rating}점 이상 공고만 표시 (검색결과도 조절가능)")
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
        with st.spinner(f"데이브 엔진이 {keyword} 공고를 정밀 스캔 중..."):
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

# --- 3. 데이터 전시 (PC/모바일 하이브리드 최적화) ---

if not st.session_state.raw_data.empty:
    df = st.session_state.raw_data.copy()
    # 필터링 로직 (생략 - 기존과 동일)
    filtered_df = df[(df['평점'] >= min_rating) | (df['평점'] == 0.0)] if include_no_info else df[df['평점'] >= min_rating]
    filtered_df = filtered_df.sort_values(by='평점', ascending=False)

     # 💡 [핵심 교체] 폰트 크기를 키우고 가독성을 높인 커스텀 헤더
    h_style = '<p style="font-size: 0.9rem; font-weight: 700; color: #31333F; margin-bottom: 0px;">'

    h1, h2, h3, h4 = st.columns([1.5, 1, 4, 1.5])
    with h1: st.markdown(f"{h_style}🏢 회사명</p>", unsafe_allow_html=True)
    with h2: st.markdown(f"{h_style}⭐ 평점</p>", unsafe_allow_html=True)
    with h3: st.markdown(f"{h_style}📝 공고 제목</p>", unsafe_allow_html=True)
    with h4: st.markdown(f"{h_style}⚙️ 상세보기 및 제외</p>", unsafe_allow_html=True)
    
    # 헤더 하단 구분선을 조금 더 진하게
    st.markdown('<hr style="border: 1px solid #31333F; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

    for idx, row in filtered_df.iterrows():
        unique_key = row.get('id', f"idx_{idx}")
        
        # PC에서도 가독성이 좋은 1줄 구성 (Row 중심)
        with st.container():
            c1, c2, c3, c4 = st.columns([1.5, 1, 4, 1.5])
            
            # 1. 회사명 & 플랫폼
            with c1:
                st.markdown(f"**{row['회사명']}**")
                st.caption(f"({row['플랫폼']})")
            
            # 2. 평점 (클릭 시 잡플래닛)
            with c2:
                if row['평점'] > 0:
                    st.markdown(f'<a href="{row["잡플래닛링크"]}" target="_blank" class="rating-link"><span class="animated-star">⭐</span> {row["평점"]}</a>', unsafe_allow_html=True)
    
                else:
                    st.write("❓")

            # 3. 공고제목
            with c3:
                st.markdown(f"{row['공고제목']}")
            
            # 4. 버튼 (간결하게 아이콘 위주)
            with c4:
                b1, b2 = st.columns(2)
                with b1:
                    show_detail = st.button("🔍", key=f"dt_{unique_key}", help="상세보기", use_container_width=True)
                with b2:
                    if st.button("🗑️", key=f"del_{unique_key}", help="제외", use_container_width=True):
                        st.session_state.raw_data = st.session_state.raw_data.drop(idx)
                        st.rerun()
            
            # 상세보기 클릭 시 하단에 확장 (PC/모바일 공용)
            if show_detail:
                with st.expander("📄 상세 지원자격 및 공고 링크", expanded=True):
                    st.write(row['지원자격'])
                    st.link_button("공고 원문 페이지로 이동 🔗", row['링크'], use_container_width=True)
            
            st.divider()    

    # UI 하단 액션 섹션
    # 현재 시간 가져오기 (예: 2026-04-04 02:42:25)
    KST = pytz.timezone('Asia/Seoul')
    now_kst = datetime.datetime.now(KST) # 서버 시간이 아닌 한국 시간으로 가져오기
    now = now_kst.now().strftime("%Y%m%d_%H%M")
    
    # PDF 다운로드 (한글 폰트 세팅 전에는 깨질 수 있음)
    if not filtered_df.empty:
        pdf_data = create_pdf(filtered_df)
        st.download_button(
            label="📄 검증 완료된 클린 PDF 리포트 다운로드",
            data=bytes(pdf_data),
            file_name=f"CareerUp_Report_{keyword}_{now}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # CSV 다운로드
    csv_data = prepare_csv_data(filtered_df)

    st.download_button(
        label="📥 검증 완료된 클린 CSV 다운로드",
        data=csv_data,
        file_name=f"CareerUp_List_{keyword}_{now}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # URL 공유 링크 (st.code를 써서 클릭 시 복사되게 함)
    share_url = f"https://careerup.streamlit.app/?kw={quote(keyword)}&rate={min_rating}"
    st.caption("🔗 공유 링크 (클릭 시 복사)")
    st.code(share_url, language=None) 


else:
    if not search_submit:
        st.info("사이드바에서 세부설정 후, 검색창에 검색어를 입력하고 [엔진 가동]\n\n💡 평점과 링크를 정밀 분석하느라 검색 시간이 조금 소요됩니다.")

st.caption("Produced by Dave | Career Data Intelligence Tool (Final Verified Edition)")