import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import quote
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import datetime
import pytz
from openai import OpenAI
from st_copy_to_clipboard import st_copy_to_clipboard
import logging
logging.getLogger("fpdf.fonts").setLevel(logging.ERROR)



def create_pdf(df):
    pdf = FPDF()
    pdf.alias_nb_pages()
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Nanum", style="", fname=font_path)
        pdf.add_font("Nanum", style="B", fname=font_path) 
        pdf.set_font("Nanum", size=12)
    else:
        return bytes(pdf.output())
    pdf.add_page()
    pdf.set_font("Nanum", size=12)

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
        if pdf.get_y() > 235:
            insert_watermark(pdf)
            pdf.add_page()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Nanum", size=12)
            pdf.ln(10)

        curr_y = pdf.get_y()

        # --- 데이터 추출 (이 부분이 확실해야 에러가 안 납니다) ---
        score = row.get('평점', 0.0) if row.get('평점', 0.0) > 0 else "N/A"
        
        # [핵심 수정] jp_link 변수를 확실하게 정의
        # 데이터프레임에 '잡플래닛링크' 컬럼이 없을 경우를 대비해 기본값 설정
        jp_link = row.get('잡플래닛링크', '')

        # --- 왼쪽 영역 ---
        pdf.set_font("Nanum", style="B", size=12)
        company_text = f"{idx+1}. {row['회사명']} ({row['플랫폼']})"
        pdf.text(15, curr_y + 5, company_text)
        
        pdf.set_font("Nanum", style="", size=10)
        qual_text = row.get('지원자격', row.get('경력', '상세 자격요건은 공고 참조'))
        
        pdf.set_xy(15, curr_y + 8)
        # [수정] txt -> text
        pdf.multi_cell(130, 6, text=f"Title: {row['공고제목']}")
        
        pdf.set_xy(15, pdf.get_y())
        pdf.set_text_color(80, 80, 80)
        # [수정] txt -> text
        pdf.multi_cell(130, 6, text=f"Qualification: {qual_text}")

        # --- 오른쪽 영역 ---
        score = row['평점'] if row['평점'] > 0 else "N/A"
        pdf.set_font("Nanum", style="B", size=11)
        pdf.set_text_color(200, 100, 0) 
        # [수정] Score 텍스트 자체에 잡플래닛 하이퍼링크 삽입
        pdf.set_xy(155, curr_y + 1)
        pdf.set_font("Nanum", style="B", size=11)
        pdf.set_text_color(255, 102, 0)
        # 텍스트에 밑줄 효과(BU)를 주어 클릭 가능함을 암시
        try: pdf.set_font("Nanum", style="BU", size=11)
        except: pdf.set_font("Nanum", style="B", size=11)

        pdf.cell(40, 8, text=f"기업 Score: {score}", link=jp_link, align='L')
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

    # 마지막 페이지 워터마크 삽입
    insert_watermark(pdf)
    return bytes(pdf.output())

def create_strategy_pdf(report_content, company_name):
    pdf = FPDF()
    pdf.alias_nb_pages()
    
    # 1. 폰트 설정 (이름 통일)
    font_name = "Nanum"
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font(font_name, style="", fname=font_path)
        pdf.add_font(font_name, style="B", fname=font_path)
        base_font = font_name
    else:
        return bytes(pdf.output())

    pdf.add_page()
    
    # --- [Header] ---
    pdf.set_fill_color(0, 77, 64) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(12)
    pdf.set_font(base_font, style="B", size=22)
    pdf.cell(0, 10, text="AI 채용 합격 전략 리포트", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font(base_font, style="", size=12)
    pdf.cell(0, 10, text=f"Target Company: {company_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(15) 

    # --- [Content Processing] ---
    pdf.set_text_color(40, 40, 40)
    lines = report_content.split('\n')
    
    for line in lines:
        if not line.strip():
            pdf.ln(4)
            continue
            
        if pdf.get_y() > 260:
            insert_watermark(pdf)
            pdf.add_page()
            pdf.ln(10)

        # 뎁스 파악
        indent_size = len(line) - len(line.lstrip())
        depth = indent_size // 2
        
        # 1. 대섹션 (###) - 기호 완벽 제거 및 디자인 복구
        if line.strip().startswith('###'):
            # ### 제거 및 앞뒤 공백 정리
            clean_title = line.replace('###', '').replace('**', '').strip()
            
            pdf.ln(5)
            pdf.set_fill_color(240, 248, 245)
            pdf.set_draw_color(0, 77, 64) # 테두리 진하게 복구
            pdf.set_line_width(0.6) # 테두리 두께 강화
            
            curr_y = pdf.get_y()
            pdf.rect(10, curr_y, 190, 12, 'FD')
            
            pdf.set_font(base_font, style="B", size=15) # 대제목 폰트 크기 및 진하게 복구
            pdf.set_text_color(0, 77, 64)
            pdf.set_xy(15, curr_y + 3)
            pdf.cell(0, 6, text=clean_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(7)
            continue

        # 2. 데이터 보존형 기호 정리 (숫자 보존)
        # 텍스트 내의 ** 제거
        text_only = line.replace('**', '').strip()
        # 문장 앞의 불렛 기호(*, -)만 제거하고 숫자는 남겨두는 정규식으로 수정
        display_text = re.sub(r'^[*\-\s]+', '', text_only) 

        # 3. 계층별 출력 로직
        if depth == 0:
            # 중간 제목: 불렛(•), 진하게, 13pt
            pdf.set_font(base_font, style="B", size=13)
            pdf.set_text_color(20, 60, 50)
            prefix = "• "
            base_x = 12
        else:
            # 상세 내용: 대시(-), 일반, 11pt
            pdf.set_font(base_font, style="", size=11)
            pdf.set_text_color(60, 60, 60)
            prefix = "- "
            base_x = 12 + (depth * 8)

        # 출력 위치 설정
        pdf.set_x(base_x)
        prefix_w = pdf.get_string_width(prefix)
        pdf.write(7, prefix)
        
        text_start_x = base_x + prefix_w
        pdf.set_xy(text_start_x, pdf.get_y())
        
        # 콜론(:) 기준 소제목 강조 (중간 제목용)
        if ":" in display_text and depth == 0:
            parts = display_text.split(":", 1)
            pdf.set_font(base_font, style="B", size=13)
            pdf.write(7, parts[0] + ":")
            pdf.set_font(base_font, style="", size=11)
            pdf.multi_cell(195 - (text_start_x + pdf.get_string_width(parts[0])), 7, text=parts[1])
        else:
            pdf.multi_cell(195 - text_start_x, 7, text=display_text)
            
        pdf.ln(1)

    insert_watermark(pdf)
    return bytes(pdf.output())


# 워터마크 삽입용 헬퍼 함수
def insert_watermark(pdf):
    # 현재 위치 저장
    current_x = pdf.get_x()
    current_y = pdf.get_y()
    
    # 오토 페이지 브레이크 일시 정지 (유령 페이지 방지)
    pdf.set_auto_page_break(False)
    
    # --- 위치 설정 (하단 여백 확보) ---
    pdf.set_y(-15) 
    
    # 1. [왼쪽 하단] 워터마크: Produced by Dave (연한 회색)
    pdf.set_x(15) # 왼쪽 마진 15mm 지점
    pdf.set_font("Nanum", style="", size=8)
    pdf.set_text_color(180, 180, 180) 
    pdf.cell(0, 10, text="Produced by Dave | CareerUp Intelligence Tool", align='L')
    
    # 2. [중앙] 페이지 번호 (검정색, 진하게)
    pdf.set_x(0) 
    pdf.set_font("Nanum", style="B", size=9) # 숫자는 조금 더 잘 보이게 Bold
    pdf.set_text_color(0, 0, 0) # 검은색
    
    page_no_text = f"- {pdf.page_no()} -"
    pdf.cell(0, 10, text=page_no_text, align='C')
    
    # --- 상태 복구 ---
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(current_x, current_y)


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
    # 가장 흔하게 나타나는 평점 패턴 3가지 (순서 중요)
    patterns = [
        r'(\d\.\d)\s?(?:점|/|5\.0)',    # 3.7점, 3.7/5.0
        r'(?:평점|별점|점수)\s?(\d\.\d)', # 평점 3.7
        r'(\d\.\d)'                     # 그냥 숫자 3.7
    ]
    
    # 텍스트 내에서 '잡플래닛' 단어 위치 찾기
    jp_index = text.find('잡플래닛')
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for m in matches:
            score = float(m.group(1))
            # [PM의 핵심 필터] 1.0~5.0 사이의 유효한 평점인지 확인
            if 1.0 <= score <= 5.0:
                # 만약 '잡플래닛' 단어 근처(앞뒤 30자 이내)에 있는 숫자라면 신뢰도 급상승
                if jp_index != -1 and abs(m.start() - jp_index) < 50:
                    return score
                # 근처가 아니더라도 일단 유효 범위면 후보군으로 유지 (나중에 리턴)
                last_valid_score = score
                
    try: return last_valid_score
    except: return 0.0

def get_jobplanet_info(company):
    search_name = clean_name(company)
    # [수정] 큰따옴표 제거! 네이버가 더 많은 결과를 주도록 유도함.
    query = quote(f"{search_name} 잡플래닛 평점") 
    url = f"https://search.naver.com/search.naver?query={query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.naver.com/'
    }
    
    score, link = 0.0, f"https://www.jobplanet.co.kr/search?query={quote(search_name)}"
    
    try:
        time.sleep(random.uniform(1.0, 2.0)) # 차단 안 당할 정도로만.
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # [핵심 로직] 특정 클래스(.bx)에 의존하지 않고 잡플래닛 링크가 포함된 모든 요소 탐색
        anchors = soup.find_all('a', href=re.compile(r'jobplanet\.co\.kr/companies'))
        
        for a in anchors:
            # 해당 링크가 포함된 가장 가까운 부모 컨테이너 추출
            parent = a.find_parent('li') or a.find_parent('div')
            if parent:
                parent_text = parent.get_text(separator=' ', strip=True)
                score = extract_score_from_text(parent_text)
                if score > 0:
                    link = a['href']
                    return score, link # 찾았으면 즉시 반환

        # [Fallback] 만약 위에서 못 찾았다면 페이지 전체 텍스트에서 '잡플래닛' 주변 훑기
        full_text = soup.get_text(separator=' ', strip=True)
        score = extract_score_from_text(full_text)
        
        return score, link
    except:
        return 0.0, link

# --- 2. 채용 데이터 수집 함수 ---
platform_map_to_id = {
    "전체 통합 검색": "all",
    "사람인 (Saramin)": "saramin",
    "원티드 (Wanted)": "wanted"
}
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

@st.cache_data(ttl=600, show_spinner=False)
def get_wanted_jobs(keyword, limit=20):
    """
    원티드 최신 API(v4/search)와 잡플래닛 평점 엔진을 결합한 통합 함수
    """
    if not keyword:
        return pd.DataFrame()

    encoded_keyword = quote(keyword)
    
    # 1. 원티드 최신 검색 엔드포인트 (v4/search)
    url = f"https://www.wanted.co.kr/api/v4/search?job_sort=job.latest_order&locations=all&years=-1&query={encoded_keyword}&country=kr"
    
    # 봇 차단 우회를 위한 정교한 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'https://www.wanted.co.kr/search?query={encoded_keyword}',
        'Origin': 'https://www.wanted.co.kr'
    }
    
    try:
        # 원티드 데이터 요청
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() 
        
        data = res.json()
        # v4/search API는 data -> jobs 구조를 가집니다.
        jobs = data.get('data', {}).get('jobs', [])
        
        if not jobs:
            return pd.DataFrame()
            
        job_list = []
        for item in jobs[:limit]:
            try:
                corp = item.get('company', {}).get('name', '미상')
                
                # --- [잡플래닛 연동 섹션] ---
                # 기존에 정의하신 get_jobplanet_info 함수를 호출합니다.
                score, jp_link = get_jobplanet_info(corp)
                # --------------------------
                
                job_list.append({
                    '플랫폼': '원티드',
                    '회사명': corp,
                    '평점': score,
                    '잡플래닛링크': jp_link,
                    '공고제목': item.get('position', '제목 없음'),
                    '지원자격': '상세 요건은 공고 참조',
                    '링크': f"https://www.wanted.co.kr/wd/{item.get('id')}"
                })
            except Exception: 
                continue
            
        return pd.DataFrame(job_list)
        
    except Exception as e:
        # 에러 발생 시 빈 데이터프레임을 반환하여 메인 루프가 끊기지 않게 방어
        print(f"⚠️ 원티드 통합 엔진 에러: {e}")
        return pd.DataFrame()

# @st.cache_data(ttl=600, show_spinner=False) # 테스트를 위해 일단 1분(60초)으로 줄이세요
# def get_wanted_jobs(keyword, limit=20):
#     if not keyword:
#         return pd.DataFrame()
    
#     # 1. job_ids를 제거하여 모든 직군 검색 가능하게 변경
#     # 2. keyword를 URL에 맞게 인코딩 (한글 깨짐 방지)
#     encoded_keyword = quote(keyword)
#     url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&job_sort=job.latest_order&locations=all&years=-1&keyword={encoded_keyword}&limit={limit}"
    
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#         'Referer': f'https://www.wanted.co.kr/search?query={encoded_keyword}'
#     }

#     try:
#         res = requests.get(url, headers=headers, timeout=10)
#         if res.status_code == 200:
#             data = res.json()
#             jobs = data.get('data', [])
            
#             if not jobs:
#                 return pd.DataFrame()
                
#             job_list = []
#             for job in jobs[:limit]:
#                 corp = job['company']['name']
#                 # 평점 수집 엔진 (기존 로직 유지)
#                 score, jp_link = get_jobplanet_info(corp)
                
#                 job_list.append({
#                     '플랫폼': '원티드',
#                     '회사명': corp,
#                     '평점': score,
#                     '잡플래닛링크': jp_link,
#                     '공고제목': job['position'],
#                     '지원자격': '상세내용은 원티드 공고 참조',
#                     '링크': f"https://www.wanted.co.kr/wd/{job['id']}"
#                 })
#             return pd.DataFrame(job_list)
#         return pd.DataFrame()
#     except Exception as e:
#         # 에러 발생 시 빈 데이터프레임 반환하여 전체 로직 유지
#         return pd.DataFrame()
    
# @st.cache_data(ttl=600, show_spinner=False)
# def get_wanted_jobs(keyword, limit=20):
#     st.write(f"DEBUG: 현재 원티드 검색어 -> {keyword}")
#     encoded_keyword = quote(keyword)
#     url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&job_sort=job.latest_order&locations=all&years=-1&keyword={encoded_keyword}"
#     try:
#         res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': f'https://www.wanted.co.kr/search?query={encoded_keyword}'}, timeout=10)
#         if res.status_code == 200:
#             jobs = res.json().get('data', [])
#             job_list = []
#             for job in jobs[:limit]:
#                 corp = job['company']['name']
#                 score, jp_link = get_jobplanet_info(corp)
#                 job_list.append({'플랫폼': '원티드', '회사명': corp, '평점': score, '잡플래닛링크': jp_link, '공고제목': job['position'], '지원자격': '상세공고 참조', '링크': f"https://www.wanted.co.kr/wd/{job['id']}"})
#             return pd.DataFrame(job_list)
#         return pd.DataFrame()
#     except: return pd.DataFrame()

def scrape_saramin_real_content(url, company_name):
    # 1. URL에서 공고 고유 번호(rec_idx) 추출
    match = re.search(r"rec_idx=(\d+)", url)
    if not match:
        return "❌ 공고 번호를 찾을 수 없는 URL입니다."
    
    rec_idx = match.group(1)
    
    # 2. 사람인의 '순수 본문 호출' 주소로 타겟팅 변경
    # 이 주소는 껍데기 없이 본문 내용만 반환하는 경우가 많습니다.
    target_url = f"https://www.saramin.co.kr/zf_user/jobs/relay/view-detail?rec_idx={rec_idx}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": url
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.encoding = 'utf-8' # 본문은 보통 utf-8
        soup = BeautifulSoup(response.text, 'html.parser')

        # 본문 영역 선택 (사람인 본문 전용 태그들)
        # 본문 전용 호출 페이지에서는 구조가 더 단순해집니다.
        content_section = soup.select_one(".user_content") or \
                          soup.select_one(".template_area") or \
                          soup.select_one(".jv_detail") or \
                          soup # 정 안되면 전체

        # 불필요한 UI 요소(닫기 버튼, 가이드 문구 등) 제거
        for s in content_section(['script', 'style', 'button', '.guide_area']):
            s.decompose()

        text = content_section.get_text(separator="\n")
        
        # 4. 정제: 아까 보신 '로그인', '메뉴' 같은 단어가 포함된 줄은 삭제
        lines = text.splitlines()
        garbage_keywords = ['로그인', '회원가입', '본문 바로가기', '검색어입력', '닫기', '개인정보']
        
        clean_lines = [f"### [회사명] {company_name} ###\n"]
        for line in lines:
            line = line.strip()
            # 쓰레기 키워드가 포함되지 않고, 실제 내용이 있는 줄만 선택
            if line and not any(kw in line for kw in garbage_keywords):
                clean_lines.append(line)
        
        return "\n".join(clean_lines)

    except Exception as e:
        return f"🚨 에러 발생: {e}"

def scrape_wanted_full_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.wanted.co.kr/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 기본 정보 추출 (회사명, 포지션)
        company_tag = soup.find('a', class_=re.compile(r'Company__Link'))
        company = company_tag.get('data-company-name') if company_tag else "정보없음"
        
        position_tag = soup.find('h1')
        position = position_tag.get_text(strip=True) if position_tag else "정보없음"

        # --- [추가 코드: 근무지 및 경력 추출] ---
        # JobHeader 영역에서 Info 클래스를 가진 모든 span을 찾음.
        info_tags = soup.find_all('span', class_=re.compile(r'JobHeader__Tools__Company__Info'))
        location = "정보없음"
        experience = "정보없음"
        
        if len(info_tags) >= 2:
            location = info_tags[0].get_text(strip=True)     # 첫 번째 span: 지역 (서울 강남구)
            experience = info_tags[1].get_text(strip=True)   # 두 번째 span: 경력 (경력 1-5년)
        # ---------------------------------------------

        # 2. 본문 내용 담을 딕셔너리
        content_data = {}

        # ---------------------------------------------------------
        # [A] 포지션 상세 (h2 태그 기반 추출)
        # ---------------------------------------------------------
        detail_header = soup.find('h2', string=lambda x: x and '포지션 상세' in x)
        if detail_header:
            # h2 태그와 같은 레벨 혹은 부모 안에 있는 상세 내용(span) 탐색
            parent_div = detail_header.find_parent('article') or detail_header.parent
            detail_content = parent_div.find('span', class_='wds-h4ga6o')
            if detail_content:
                content_data["포지션 상세"] = detail_content.get_text(separator="\n", strip=True)

        # ---------------------------------------------------------
        # [B] 주요업무, 자격요건, 우대사항 등 (h3 태그 기반 추출)
        # ---------------------------------------------------------
        sections = soup.find_all('div', class_=re.compile(r'JobDescription_JobDescription__paragraph'))
        for section in sections:
            header = section.find('h3')
            content = section.find('span', class_='wds-h4ga6o')
            
            if header and content:
                header_text = header.get_text(strip=True)
                content_text = content.get_text(separator="\n", strip=True)
                content_data[header_text] = content_text

        # 3. 결과 텍스트 조립
        if not content_data:
            return "❌ 데이터를 추출하지 못했습니다. 구조 확인이 필요합니다."

        result_lines = [f"### [{company}] {position} ###",
                f"지역: {location}",
                f"경력조건: {experience}\n"]
        
        # '포지션 상세'를 가장 먼저 배치하고 나머지를 순차적으로 추가
        priority_key = "포지션 상세"
        if priority_key in content_data:
            result_lines.append(f"[{priority_key}]\n{content_data[priority_key]}\n")
        
        for title, body in content_data.items():
            if title != priority_key: # 이미 넣은 건 제외
                result_lines.append(f"[{title}]\n{body}\n")
            
        return "\n".join(result_lines)

    except Exception as e:
        return f"🚨 에러 발생: {e}"

# Groq: OpenAI SDK
# secrets.toml에서 키 가져오기
try:
    groq_key = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
    st.stop()

# 클라이언트 설정
client = OpenAI(
    api_key=groq_key,
    base_url="https://api.groq.com/openai/v1"
)
def analyze_with_llama(crawled_result):
    analysis_prompt = f"""
    당신은 전략 컨설팅 펌 출신의 '수석 리쿠르팅 어드바이저'입니다. 
    제공된 [채용 공고]를 분석하여 객관적이고 논리적인 '지원 전략 보고서'를 작성하세요.

    ###1. 공고 기초 정보 
    - **공고 기초 정보:** 회사명, 공고 제목, 근무지, 주요 자격 요건, 제출 기한
    ### 2. 기업 분석 (Market & Biz Context)
    - **비즈니스 모델:** 이 회사가 무엇으로 돈을 벌고 있으며, 현재 어느 성장 단계(투자/확장/안정)에 있는지 요약하세요.
    - **채용 배경(추론):** 공고의 내용을 볼 때, 현재 이 팀이 해결해야 할 '가장 시급한 문제'는 무엇인가?

    ### 3. 직무 역량 우선순위 (Priority Matrix)
    - **필수 기술/스킬 (Must):** 실무에서 가장 높은 빈도로 사용될 핵심 역량 3가지를 선정하세요.
    - **차별화 포인트 (Nice-to-have):** 수많은 지원자 중 '최종 합격자'를 결정지을 결정적 한 끗(우대사항 기반)은 무엇인가?

    ### 4. 합격 필살기 가이드 (Action Plan)
    - **자소서 강조점:** 이 직무에서 가장 높게 평가할 '성과 지표'나 '경험의 키워드'를 제시하세요.
    - **면접 예상 질문:** 이 공고의 '자격요건'을 근거로 면접관이 던질 가장 날카로운 질문 하나를 뽑으세요.
    - **면접 예상 답변:** 위에서 뽑은 질문에 대해 구체적인 모범 답안을 문장형으로 답변하세요.

    ---
    [출력 규칙] 표 금지, 불렛포인트 사용, 한자(중국의 문자; 번체자, 간체자),일본어(일본의 문자; 히라가나, 카타카나) 일체 사용(표기)금지.
    ***"답변 시 공고문의 텍스트를 그대로 복사하지 말고, 수석 컨설턴트의 시각에서 '비즈니스 언어'로 재해석(Paraphrasing)해서 작성할 것. 특히 '필살기 가이드'에는 지원자가 면접관을 압도할 수 있는 구체적인 기술적 키워드(예: RAG 고도화, MLOps 등)를 추론해서 포함시켜라."***
    ***"단순 요약하지 말고, 공고에 없는 내용을 너의 지식을 바탕으로 창의적으로 추론해서 덧붙일 것."***
    ***"시간이 더 걸리더라도 독하게, 더 깊게 분석할 것."***
    ***"자연스러운 한국어 구어체(1번 항목의 기초정보에 한해서만 문장형이 아닌 깔끔히 표시)를 사용할 것"***
    ***"해당 업종만의 배경지식(업계 컨텍스트)을 활용해서 설명할 것."***
    ***"신입, 중간관리자, 시니어 등 각 자격요건(연차)에 맞게 강조점을 조정하여 맞춤형으로 제시할 것."***
    [채용 공고 데이터]
    {crawled_result}
    """

    try: response = client.chat.completions.create(
    # model="llama-3.3-70b-versatile", 
    model="meta-llama/llama-4-scout-17b-16e-instruct", 

    messages=[
        {"role": "system", "content": analysis_prompt},
        {"role": "user", "content": f"다음 공고를 분석해줘: {crawled_result}"}
    ],
    temperature=0.5 # 일관된 분석을 위해 약간 낮게 설정
    )
    except Exception as e:
        if "rate_limit_exceeded" in str(e).lower():
            st.warning("⚠️ AI 분석 요청이 너무 많습니다. 1분 후 다시 시도해주세요! (무료 API 할당량 제한)")
        else:
            st.error("AI 전략 도출 중 오류가 발생했습니다.")

    return response.choices[0].message.content

# --- 2. Streamlit UI 및 상태 관리 (상태 유지용) ---

st.set_page_config(page_title="Dave's Verified Hub", layout="wide")

# --- 메인 헤드라인 스타일 정의 ---
st.markdown("""
    <style>
    .title-link {
        text-decoration: none !important;
        color: #31333F !important; /* 스트림릿 기본 텍스트 색상 */
    }
    .title-link:hover {
        color: #FF4B4B !important; /* 마우스 올렸을 때 스트림릿 포인트 컬러(빨간색)로 변경 */
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화: 검색 데이터를 메모리에 유지
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()
if 'excluded_links' not in st.session_state:
    st.session_state.excluded_links = set()

st.markdown("""
<style>
    @keyframes starPulse { 0% { transform: scale(1); } 50% { transform: scale(1.3); text-shadow: 0 0 8px #FFD700; } 100% { transform: scale(1); } }
    .rating-link { text-decoration: none; color: #FFD700 !important; font-weight: bold; }
    .rating-link:hover .animated-star { animation: starPulse 0.8s infinite; display: inline-block; }
    .no-rating { color: #ccc; font-size: 0.85em; }
    .delete-btn { color: white; background-color: #ff4b4b; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<a href="/" target="_self" class="title-link"><h1>🚀 커리어UP 인텔리전스 채용 검색 엔진</h1></a>', unsafe_allow_html=True)
st.write("검색 후 **평점**⭐을 클릭하여 **잡플래닛 상세 리뷰**를 확인하세요.")

# [가장 먼저] 주소창에서 파라미터부터 낚아채기
# --- 1. 주소창 파라미터 낚아채기 (기존 위치) ---
params = st.query_params
get_kw = params.get("kw", "")
get_p_id = params.get("platform", "saramin")
id_map_to_platform = {
    "all": "전체 통합 검색",
    "saramin": "사람인 (Saramin)",
    "wanted": "원티드 (Wanted)"
}
get_platform = id_map_to_platform.get(get_p_id, "사람인 (Saramin)")

# --- 2. [수정] 무한 루프 방지 로직 ---
# 조건: 주소창에 키워드가 있고 + 아직 검색을 안 했거나 + 주소창 키워드가 이전 검색과 다를 때만 실행
auto_search = False
if get_kw:
    # 세션에 기록된 마지막 검색어와 주소창의 검색어가 다를 때만 '자동 검색' 활성화
    if st.session_state.get("last_kw") != get_kw:
        auto_search = True
# if get_kw:
#     if "last_kw" not in st.session_state or st.session_state.last_kw != get_kw:
#         auto_search = True

try:
    # 주소창에 'row'가 있으면 그 값을, 없으면 기본값 10를 가져옴
    get_row = int(params.get("row", 10))
except:
    get_row = 15

try:
    # 주소창에 'rate'가 있으면 그 값을, 없으면 기본값 2.5를 get_rate에 저장
    get_rate = float(params.get("rate", 2.5))
except:
    get_rate = 2.5

with st.sidebar:
    st.header("⚙️ 검색 & 필터 설정")
    platform_options = ("전체 통합 검색", "사람인 (Saramin)", "원티드 (Wanted)")
    
    p_index = platform_options.index(get_platform)

    if get_p_id in ["all", "saramin", "wanted"]:
    # 주소창 값이 있으면 그에 맞는 인덱스 설정 (공유 기능 유지)
        if get_p_id == "saramin": p_index = 1
        elif get_p_id == "wanted": p_index = 2
        else: p_index = 0
    else:
        # 2. 주소창에 아무 정보가 없는 '첫 접속'일 때만 사람인(1) 고정
        p_index = 1

    platform_choice = st.sidebar.radio("플랫폼 선택", platform_options, index=p_index)

    # platform_options = ("사람인 (Saramin)",)
    # p_index = 0
    # platform_choice = st.sidebar.radio("▶ 연결된 플랫폼", platform_options, index=p_index)

    row_count = st.slider("수집할 공고 개수 (플랫폼당)", 5, 50, value=get_row)
    
    st.markdown("---")
    # [핵심] 평점 필터 슬라이더 추가 (0.1단위)    
    min_rating = st.slider("최소 평점 필터 (⭐)", 0.0, 5.0, step=0.1, value=get_rate)
    st.caption(f"⭐ {min_rating}점 이상 공고만 표시 (검색화면 내 조절가능)")
    include_no_info = st.checkbox("정보없음(❓) 기업 포함하기", value=True)
    if st.sidebar.button("전체 초기화 (Clear All)"):
        # 1. 데이터 및 제외 목록 초기화
        st.session_state.raw_data = pd.DataFrame()
        st.session_state.excluded_links = set()
        
        # 2. 입력창 관련 세션도 초기화
        if 'last_kw' in st.session_state:
            st.session_state.last_kw = ""

        st.cache_data.clear()
        st.query_params.clear()
        st.rerun()

col1, col2 = st.columns([4, 1])

with col1:
    # label_visibility="collapsed"로 버튼과 수평 맟추기
    keyword = st.text_input(
        "직무 키워드 입력", 
        value=get_kw, 
        placeholder="직무 키워드를 입력하세요.(예: 데이터기획, AI PM)", 
        label_visibility="collapsed"
    )

with col2:
    # 폼 버튼 대신 일반 버튼 사용 (높이 조절용 여백 추가)
    search_submit = st.button("엔진 가동", use_container_width=True)

# with st.form(key='search_form'):
#     col1, col2 = st.columns([4, 1])
#     with col1:
#         # 라벨은 존재하지만 화면 공간을 차지하지 않음
#         keyword = st.text_input("직무 키워드 입력", value=get_kw, 
#                                placeholder="직무 키워드를 입력하세요.(예: 데이터기획, AI PM)", 
#                                label_visibility="collapsed")

#     with col2:
#         search_submit = st.form_submit_button("엔진 가동", use_container_width=True)


# 1. 데이터 수집 실행
if search_submit or (keyword and keyword != st.session_state.get('last_kw', '')) or auto_search:
    if keyword:
        # [추가 1] 검색 시작하자마자 현재 키워드를 '마지막 키워드'로 박제 (중복 실행 방지)
        st.session_state.last_kw = keyword
        
        with st.spinner(f"📡데이브 엔진이 **'{keyword}'** 공고를 정밀 스캔 중..."):
            if platform_choice == "사람인 (Saramin)":
                res_df = get_saramin_jobs(keyword, row_count)
            elif platform_choice == "원티드 (Wanted)":
                res_df = get_wanted_jobs(keyword, row_count)
            else:
                df_s = get_saramin_jobs(keyword, row_count)
                df_w = get_wanted_jobs(keyword, row_count)
                res_df = pd.concat([df_s, df_w], ignore_index=True)
            
            # 수집된 데이터를 세션 상태에 저장
            st.session_state.raw_data = res_df.reset_index(drop=True)

            # [추가 2] 검색이 끝났으니 auto_search 플래그 초기화
            if auto_search:
                auto_search = False
                
        # 성공적으로 끝났다면 화면을 한 번 리프레시
        st.rerun() 
    else:
        st.error("키워드를 입력해 주세요.")


# if search_submit or (keyword and keyword != st.session_state.get('last_kw', '')) or auto_search:
#     if keyword:
#         with st.spinner(f"데이브 엔진이 {keyword} 공고를 정밀 스캔 중..."):
#             if platform_choice == "사람인 (Saramin)":
#                 res_df = get_saramin_jobs(keyword, row_count)
#             elif platform_choice == "원티드 (Wanted)":
#                 res_df = get_wanted_jobs(keyword, row_count)
#             else:
#                 df_s = get_saramin_jobs(keyword, row_count)
#                 df_w = get_wanted_jobs(keyword, row_count)
#                 res_df = pd.concat([df_s, df_w], ignore_index=True)
            
#             # 수집된 데이터를 세션 상태에 저장 (인덱스 초기화 중요)
#             st.session_state.raw_data = res_df.reset_index(drop=True)
#     else:
#         st.error("키워드를 입력해 주세요.")


        # with st.spinner():
        #     try:
        #         # 플랫폼별 데이터 가져오기
        #         if platform_choice == "사람인 (Saramin)":
        #             res_df = get_saramin_jobs(keyword, row_count)
        #         # elif platform_choice == "원티드 (Wanted)":
        #         #     res_df = get_wanted_jobs(keyword, row_count)
        #         else:
        #             res_df = get_saramin_jobs(keyword, row_count)
        #             # df_s = get_saramin_jobs(keyword, row_count)
        #             # # df_w = get_wanted_jobs(keyword, row_count)
        #             # res_df = pd.concat([df_s, df_w], ignore_index=True)
                
            #     # 3. [가장 중요] 가져온 데이터를 '즉시' 세션에 박제
            #     if res_df is not None and not res_df.empty:
            #         # 인덱스 초기화까지 완벽하게 해서 저장
            #         st.session_state.raw_data = res_df.copy().reset_index(drop=True)
            #     else:
            #         st.session_state.raw_data = pd.DataFrame() # 결과 없으면 빈 통
            #         st.warning("결과가 없습니다. 키워드를 확인해 보세요.")

            # except Exception as e:
            #     st.error(f"엔진 가동 중 오류 발생: {e}")
            #     st.info("💡 팁: 잠시 후 다시 시도하거나 키워드를 변경해 보세요.")

        # 4. 🏁 수집이 '완전히' 끝난 후에만 리런!
        # auto_search 플래그는 여기서 꺼줍니다.

# 2. 데이터 전시 및 실시간 삭제 로직
placeholder = st.empty()
if (st.session_state.raw_data is None or st.session_state.raw_data.empty) and not search_submit:
    with placeholder.container():
        st.info("**사이드바**(**>>**)에서 **플랫폼 및 평점** 세부설정 후, 검색창에 키워드를 입력하고 [**엔진 가동**]\n\n💡 평점과 링크를 정밀 분석하느라 검색 시간이 조금 소요됩니다.")
        # st.caption("Produced by Dave | CareerUp Intelligence Tool (1st Edition)")

with placeholder.container():
    # [핵심] 세션이 완전히 비어있을 때는 절대 이전 루프를 타지 않도록 강제 차단
    if st.session_state.raw_data is None or st.session_state.raw_data.empty:
        if not search_submit:
            pass
    else:
        # 데이터가 있을 때만 필터링 및 전시 시작
        df = st.session_state.raw_data.copy()

        # 블랙리스트 필터링
        if 'excluded_links' in st.session_state and not df.empty:
            df = df[~df['링크'].isin(st.session_state.excluded_links)]
        
        # 🎯 [추가] 플랫폼 실시간 필터링 로직
        # 사이드바에서 선택한 platform_choice에 따라 '표시할 데이터'만 남기기
        if not df.empty:
            if "사람인 (Saramin)" in platform_choice:
                # 데이터프레임의 '플랫폼' 컬럼 값이 '사람인'인 것만 추출
                df = df[df['플랫폼'].str.contains("사람인", na=False)]
            elif "원티드 (Wanted)" in platform_choice:
                # 데이터프레임의 '플랫폼' 컬럼 값이 '원티드'인 것만 추출
                df = df[df['플랫폼'].str.contains("원티드", na=False)]
            # "전체 통합 검색"일 때는 필터링을 건너뛰어 전체를 보여줌

        # 평점 및 정보없음 필터링
        if not df.empty:
            if include_no_info:
                filtered_df = df[(df['평점'] >= min_rating) | (df['평점'] == 0.0)]
            else:
                filtered_df = df[df['평점'] >= min_rating]
            
            filtered_df = filtered_df.sort_values(by='평점', ascending=False)
        else:
            filtered_df = pd.DataFrame()

        # 최종 결과물이 있을 때만 UI 렌더링
        if not filtered_df.empty:
            st.subheader(f"✅ 현재 검색된 공고 ({len(filtered_df)}건)")
            st.info("🔗**상세링크**를 눌러 세부사항을 확인하고, 필요 없는 공고는 🗑️**제외**하세요.")

            # --- 헤더 출력 ---
            h_style = '<p style="font-size: 0.9rem; font-weight: 700; color: #31333F; margin-bottom: 0px;">'
            # h_style_center = '<p style="font-size: 0.9rem; font-weight: 700; color: #31333F; margin-bottom: 0px; text-align: center;">'
            h1, h2, h3, h4 = st.columns([1.5, 1, 4, 1.5])
            with h1: st.markdown(f"{h_style}🏢 회사명</p>", unsafe_allow_html=True)
            with h2: st.markdown(f"{h_style}⭐ 평점</p>", unsafe_allow_html=True)
            with h3: st.markdown(f"{h_style}📝 공고 제목 및 지원자격</p>", unsafe_allow_html=True)
            with h4: st.markdown(f"{h_style}⚙️ 상세링크 및 제외</p>", unsafe_allow_html=True)
            st.markdown('<hr style="border: 1px solid #31333F; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

            # 현재 시간 가져오기 (예: 2026-04-04 02:42:25)
            KST = pytz.timezone('Asia/Seoul')
            now_kst = datetime.datetime.now(KST) # 서버 시간이 아닌 한국 시간으로 가져오기
            now = now_kst.strftime("%Y%m%d_%H%M")
            # --- 리스트 출력 (for 루프) ---
            for idx, row in filtered_df.iterrows():
                unique_key = f"{keyword}_{idx}_{row['회사명']}"
                with st.container():
                    c1, c2, c3, c4 = st.columns([1.5, 1, 4, 1.5])
                    with c1:
                        st.markdown(f"**{row['회사명']}**")
                        st.caption(f"({row['플랫폼']})")
                    with c2:
                        if row['평점'] > 0:
                            st.markdown(f'<a href="{row["잡플래닛링크"]}" target="_blank" class="rating-link"><span class="animated-star">⭐</span> {row["평점"]}</a>', unsafe_allow_html=True)
                        else:
                            st.write("❓")
                    with c3:
                        st.markdown(f"{row['공고제목']}")
                        st.caption(row['지원자격'])
                        # --- [핵심] AI 전략 리포트 Expander ---
                        # 개별 공고마다 고유한 key가 필요하므로 idx를 활용
                        # 1. 각 공고마다 고유한 저장 키 생성 (중복 방지)
                        report_key = f"ai_report_{idx}"
                        with st.expander("✨ AI 합격 전략 리포트"):
                            # [조건] 버튼을 눌렀거나, 이미 이전에 분석해서 메모리(session_state)에 결과가 있는 경우
                            if st.button("AI 전략 도출 🚀", key=f"ai_btn_{idx}") or report_key in st.session_state:
                                
                                # 만약 메모리(session_state)에 데이터가 없다면 -> 처음 버튼을 누른 상태
                                if report_key not in st.session_state:
                                    with st.spinner("🔎 상세 공고 내용을 읽고 전략을 짜는 중입니다..."):
                                        # 크롤링 로직 시작
                                        if row['플랫폼'] == '사람인':
                                            crawled_result = scrape_saramin_real_content(row['링크'], row['회사명'])
                                        elif row['플랫폼'] == '원티드':
                                            crawled_result = scrape_wanted_full_content(row['링크'])
                                        # 2. 유효성 검사 (핵심 필터!)
                                        # 텍스트가 없거나 너무 짧으면(예: 100자 미만) 이미지 공고일 확률이 높음
                                        if not crawled_result or len(crawled_result.strip()) < 100:
                                            error_msg = "⚠️ 이 공고는 이미지로 구성되어 있어 내용을 읽을 수 없습니다. 상세 내용은 공고 링크를 직접 확인해 주세요!"
                                            st.session_state[report_key] = error_msg
                                        else:
                                            # 3. 데이터가 충분할 때만 AI 호출
                                            report_content = analyze_with_llama(crawled_result)
                                            st.session_state[report_key] = report_content.strip()

                                # 이제 메모리에 저장된 데이터를 가져옴 (AI 서버 안 돌림)
                                current_report = st.session_state[report_key]
                                
                                # 에러 메시지인 경우와 정상 리포트인 경우를 구분해서 출력
                                if current_report.startswith("⚠️"):
                                    st.warning(current_report)
                                else:
                                    # 3. 최종 출력
                                    st.success(current_report, icon=None)

                                    # 4. 다운로드 버튼 (메모리에 있는 데이터를 재활용)
                                    pdf_data = create_strategy_pdf(current_report, row['회사명'])
                                    st.download_button(
                                        label="📑 AI 전략 리포트 PDF 다운로드",
                                        data=bytes(pdf_data),
                                        file_name=f"AI_Strategy_{row['회사명']}_{now}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_btn_pdf{idx}",
                                        use_container_width=True
                                    )
                                    st.download_button(
                                        label="📝 텍스트(txt)파일로 저장",
                                        data=current_report.encode('utf-8-sig'), # 아이폰/윈도우 한글 깨짐 방지
                                        file_name=f"AI_Strategy_{row['회사명']}_{now}.txt",
                                        mime="text/plain",
                                        key=f"dl_btn_txt{idx}",
                                        use_container_width=True # 모바일에서도 시원하게 꽉 찬 버튼
                                    )

                        # with st.expander("✨ AI 합격 전략 리포트"):
                        #     # 1. 사용자가 버튼을 누르면
                        #     if st.button("AI 전략 도출 🚀", key=f"ai_btn_{idx}"):
                                
                        #         with st.spinner("🔎 상세 공고 내용을 읽고 전략을 짜는 중입니다..."):
                        #             # [선언 위치] 여기서 변수를 선언하고 크롤링 함수를 실행
                        #             if row['플랫폼'] == '사람인':
                        #                 crawled_result = scrape_saramin_real_content(row['링크'], row['회사명'])
                        #             elif row['플랫폼'] == '원티드':
                        #                 crawled_result = scrape_wanted_full_content(row['링크'])

                        #             else:
                        #                 crawled_result = "지원하지 않는 플랫폼입니다."

                        #             # 2. 수집된 데이터를 라마 분석 함수에 파라미터로 전달
                        #             if crawled_result and "실패" not in crawled_result:
                        #                 report_content = analyze_with_llama(crawled_result)
                                        
                        #                 # 3. 최종 출력
                        #                 st.success(report_content.strip(), icon=None)
                                        # st_copy_to_clipboard(report_content.strip(), before_copy_label="📋 리포트 전체 복사하기", after_copy_label="✅ 복사 완료!")

                            # else:
                            #     st.error("세부 내용을 가져오지 못했습니다. 상세공고 링크를 참고하세요.")
                    with c4:
                        b1, b2 = st.columns(2)
                        with b1:
                            st.link_button("🔗", row['링크'], help="상세 공고링크", use_container_width=True)
                            # show_detail = st.button("🔍", key=f"dt_{unique_key}", help="상세보기", use_container_width=True)
                        with b2:
                            if st.button("🗑️", key=f"del_{unique_key}", help="제외", use_container_width=True):
                                st.session_state.excluded_links.add(row['링크'])
                                # [수정] 원본 데이터에서 해당 인덱스 삭제 후 즉시 반영
                                st.session_state.raw_data = st.session_state.raw_data[st.session_state.raw_data.index != idx]
                                st.rerun()
                    
                    st.divider()    

            # UI 하단 액션 섹션
            # PDF 다운로드 (한글 폰트 세팅 전에는 깨질 수 있음)
            if not filtered_df.empty:
                pdf_data = create_pdf(filtered_df)
                st.download_button(
                    label="📄 검증 완료된 클린 PDF 다운로드",
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
            encoded_kw = quote(keyword)

            # p_id = "saramin"
            p_id = platform_map_to_id.get(platform_choice, "all")

            # 공유용 URL 생성
            share_url = f"https://careerup.streamlit.app/?kw={encoded_kw}&platform={p_id}&rate={min_rating}&row={row_count}"

            # (로컬용 주소)
            # share_url = f"http://localhost:8501/?kw={encoded_kw}&platform={p_id}&rate={min_rating}&row={row_count}"

            st.caption("🔗 공유 하기 (아래 링크 오른쪽 끝 클릭시 복사)")
            st.code(share_url, language=None)


        else:
            if not search_submit:
                st.info("사이드바에서 세부설정 후, 검색창에 검색어를 입력하고 [엔진 가동]\n\n💡 평점과 링크를 정밀 분석하느라 검색 시간이 조금 소요됩니다.")

st.caption("Produced by Dave | CareerUp Intelligence Tool (1st Edition)")