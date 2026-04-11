import streamlit as st
import pandas as pd
import datetime
import uuid
import numpy as np
import time
import base64
from io import BytesIO
import random
import os
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_gsheets import GSheetsConnection
from PIL import Image, ImageDraw, ImageFont
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
import requests
import pytz
import threading
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="altair")

# 1. 페이지 및 세션 상태 설정
st.set_page_config(page_title="진짜 도는 런치룰렛", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    /* 1. 모든 상태 위젯(로딩바, 메시지) 강제 삭제 */
    [data-testid="stStatusWidget"], .stStatusWidget, div[class*="StatusWidget"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    /* 2. 스피너와 토스트 알림까지 차단 */
    .stSpinner {
        display: none !important;
    }
    /* 3. 로딩 중 화면이 반투명해지는 'Ghosting' 효과 제거 */
    .stApp { opacity: 1 !important; }
    </style>
""", unsafe_allow_html=True)


if 'winner' not in st.session_state:
    st.session_state.winner = None
if 'target_angle' not in st.session_state:
    st.session_state.target_angle = 0
if 'is_spinning' not in st.session_state:
    st.session_state.is_spinning = False
if 'user_id' not in st.session_state:
    # uuid를 사용해 중복되지 않는 고유 ID 생성
    st.session_state.user_id = str(uuid.uuid4())[:8] # 앞 8자리만 사용

# 1-1. 세션 식별자 (유지)
if 'user_real_ip' not in st.session_state:
    st.session_state.user_real_ip = "Unknown"

# 1-2. 구글 시트 연결 (Secrets 설정을 자동으로 읽어옴)
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 자바스크립트
# --- 앱 상단 ---
# 자바스크립트를 실행해서 IP를 가져오고, 그 결과를 바로 변수에 담습니다.
# 이 함수는 내부적으로 알아서 세션 관리를 해줍니다.
real_ip = streamlit_js_eval(
    js_expressions='fetch("https://api.ipify.org?format=json").then(response => response.json()).then(data => data.ip)',
    key='ip_address'
)


def save_log_to_sheets(items, result, current_ip, user_id, user_agent, accept_language, all_headers):
    try:
        # 1. 시트 읽기 (워크시트 이름을 명시하는 것이 가장 확실합니다)
        df = conn.read(worksheet="roulette_logs", ttl=0) 


        # # 모든 헤더를 문자열로 변환 (분석용)
        # all_headers = str(dict(st.context.headers))
        # user_agent = st.context.headers.get("User-Agent", "Unknown")
        # accept_language = st.context.headers.get("Accept-Language", "Unknown")

        # 한국 시간대 설정
        KST = pytz.timezone('Asia/Seoul')
        now_kst = datetime.datetime.now(KST) # 서버 시간이 아닌 한국 시간으로 가져오기
 
        # 2. 새 로그 데이터프레임 생성
        # 리스트 형태인 items를 문자열로 변환하여 저장합니다.
        new_row = pd.DataFrame([{
            "timestamp": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": str(user_id),
            "items": ", ".join(items),
            "result": str(result),
            "ip_address": str(current_ip), # 강제로 문자열 변환!
            "device_info": user_agent,      # 접속 기기 및 브라우저 정보
            "language": accept_language,    # 설정 언어
            "debug_headers": all_headers
        }])
        
        # 3. 기존 데이터와 합치기
        # 기존 시트가 비어있을 경우를 대비해 빈 데이터프레임 처리를 포함합니다.
        if df is not None and not df.empty:
            updated_df = pd.concat([df, new_row], ignore_index=True)
        else:
            updated_df = new_row
            
        # 4. 업데이트 실행
        conn.update(worksheet="roulette_logs", data=updated_df)
        
    except Exception as e:
        # 에러 발생 시 로그에 상세 내용을 찍습니다. (Streamlit Cloud 로그에서 확인 가능)
        print(f"Logging Error 상세: {e}")


# 2. 룰렛 이미지 생성 함수 (12시 방향 기준)
def create_roulette(items):
    size = (600, 600)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 서버(Linux)와 로컬(Windows) 경로를 모두 대응하도록 수정
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Streamlit 서버(Linux) 경로
        "C:/Windows/Fonts/malgun.ttf",                     # 윈도우 로컬 경로
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf" # 맥 로컬 경로
    ]
    
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 28)
                break
            except:
                continue
    
    # 만약 위 폰트들이 다 없다면 기본 폰트 사용
    if font is None:
        font = ImageFont.load_default()

    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#C2C2F0']
    n = len(items)
    angle_step = 360 / n
    
    for i in range(n):
        start_angle = i * angle_step - 90
        end_angle = (i + 1) * angle_step - 90
        draw.pieslice([10, 10, 590, 590], start=start_angle, end=end_angle, 
                      fill=colors[i % len(colors)], outline="white", width=3)
        
        mid_angle = np.radians(start_angle + angle_step / 2)
        tx = 300 + 190 * np.cos(mid_angle)
        ty = 300 + 190 * np.sin(mid_angle)
        draw.text((tx, ty), items[i], fill="black", anchor="mm", font=font) 
        
    return img

def img_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# 3. UI 구성
st.title("🍴 우리 뭐 먹지? 진짜 도는 런치룰렛")

img_base64 = ""
spin_class = "spinning-active" if st.session_state.get('is_spinning') else ""

# 메뉴 개수 세션 상태 초기화 (기본값 5)
if 'menu_count' not in st.session_state:
    st.session_state.menu_count = 5

default_list = ["돈가스", "부대찌개", "초밥", "쌀국수", "마라탕"]

if 'initialized' not in st.session_state:
    for i in range(10): # 최대 개수만큼 미리 생성
        key = f"m_{i}"
        if i < len(default_list):
            st.session_state[key] = default_list[i]
        else:
            st.session_state[key] = "" 
    st.session_state.initialized = True

#메뉴 입력
# [핵심 수정] 입력창 생성 및 데이터 수집
input_cols = st.columns(st.session_state.menu_count)
menus = []

for i in range(st.session_state.menu_count):
    key = f"m_{i}"
    
    # [수정] 위젯이 세션값을 직접 핸들링
    input_cols[i].text_input(f"메뉴 {i+1}", value=st.session_state.get(key, ""), key=key)
    
    # 실시간 데이터 수집
    val = st.session_state.get(key, "").strip()
    if val:
        menus.append(val)
    else:
        if i < len(default_list):
            menus.append(default_list[i])
        else:
            menus.append(f"메뉴 {i+1}")

# 메뉴 개수 조절 버튼 (UI 상단)
btn_cols = st.columns([2, 2, 2, 2, 2])
with btn_cols[0]:
    if st.button("➖ 메뉴 줄이기") and st.session_state.menu_count > 2:
        st.session_state.menu_count -= 1
        st.rerun()

with btn_cols[4]:
    if st.button("➕ 메뉴 늘리기") and st.session_state.menu_count < 10:
        # [해결] 에러 유발 코드 삭제
        st.session_state.menu_count += 1
        st.rerun()


# 룰렛 생성 및 출력 (이중 잠금 렌더링)
placeholder = st.empty()

try:
    target_angle = st.session_state.get('target_angle', 0)
    is_spinning = st.session_state.get('is_spinning', False)
    spin_class = "spinning-active" if is_spinning else ""
    
    roulette_img = create_roulette(menus)
    if roulette_img is not None:
        img_base64 = img_to_base64(roulette_img)
        

except Exception as e:
    st.error(f"룰렛 생성 중 오류: {e}")

# 4. CSS: 애니메이션 클래스 정의
st.markdown(f"""
<style>
    @keyframes spin-anim {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate({st.session_state.get('target_angle', 0)}deg); }}
    }}
    .roulette-container {{ display: flex; flex-direction: column; align-items: center; position: relative; padding: 20px; }}
    .arrow {{ width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 30px solid #FF4B4B; z-index: 10; margin-bottom: -20px; }}
    .spinning-active {{ animation: spin-anim 3s cubic-bezier(0.15, 0, 0.15, 1) forwards; }}
    .roulette-img {{ width: 400px; border-radius: 50%; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
    .result-box {{ text-align: center; padding: 30px; border-radius: 15px; background-color: #f0f2f6; border: 2px solid #FF4B4B; margin-top: 20px; }}

</style>
""", unsafe_allow_html=True)

# 5. 로직 실행
if st.session_state.winner and not st.session_state.is_spinning:
    # --- [결과 화면] ---
    placeholder.markdown(f"""
    <div class="roulette-container">
        <div class="arrow"></div>
        <img src="data:image/png;base64,{img_base64}" class="roulette-img" style="transform: rotate({st.session_state.target_angle}deg);" />
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="result-box">
            <h2 style="color: #555;">오늘의 추천 메뉴는?</h2>
            <h1 style="font-size: 85px; color: #FF4B4B; margin: 10px 0;">{st.session_state.winner}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📍 근처 식당 바로 찾기")
    
    # 지도 검색을 위한 컬럼 배치
    map_col1, map_col2 = st.columns(2)
    
    # 검색 키워드 생성 (예: "강남역 돈가스 맛집")
    # 특정 지역을 고정하고 싶다면 "내 주변" 혹은 "현재 위치"를 키워드에 추가하세요.
    search_keyword = f"주변 {st.session_state.winner} 맛집"
    
    with map_col1:
        # 네이버 지도 검색 URL
        naver_map_url = f"https://map.naver.com/v5/search/{search_keyword}"
        st.link_button("💚 네이버 지도에서 보기", naver_map_url, use_container_width=True)
        
    with map_col2:
        # 카카오 맵 검색 URL
        kakao_map_url = f"https://map.kakao.com/?q={search_keyword}"
        st.link_button("💛 카카오 맵에서 보기", kakao_map_url, use_container_width=True)

    if st.button("🔄 다시 돌리기", use_container_width=True):
        st.session_state.winner = None
        st.session_state.target_angle = 0
        st.rerun()

else:
    # --- [대기/회전 중 화면] ---
    # 회전 중일 때는 spinning-active 클래스를 붙여줌
    spin_class = "spinning-active" if st.session_state.is_spinning else ""
    rot_style = f"transform: rotate({st.session_state.target_angle}deg);" if not st.session_state.is_spinning else ""

    placeholder.markdown(f"""
    <div class="roulette-container">
        <div class="arrow"></div>
        <img src="data:image/png;base64,{img_base64}" class="roulette-img {spin_class}" style="{rot_style}" />
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔴 룰렛 돌리기 시작!", use_container_width=True):
        # 1. 당첨자 선정 및 각도 계산
        if not menus:
            st.error("메뉴를 입력해주세요!")
        else:
            current_menu_count = len(menus)
            win_idx = random.randint(0, current_menu_count - 1)
            # 당첨자 결정
            st.session_state.winner = menus[win_idx]
            angle_per_item = 360 / len(menus)
            # 화살표(상단) 위치에 맞게 각도 계산 (10바퀴 기본 회전)
            st.session_state.target_angle = 3600 - (win_idx * angle_per_item) - (angle_per_item / 2)

            # [핵심] 메인 스레드에서 정보를 미리 수집합니다.
            user_id = st.session_state.get('user_id', 'unknown')
            user_agent = st.context.headers.get("User-Agent", "Unknown")
            accept_language = st.context.headers.get("Accept-Language", "Unknown")
            all_headers = str(dict(st.context.headers))
            
            # 만약 IP를 가져오는 중이라면 'Checking'으로 표시
            user_ip = real_ip if real_ip else "Checking..."

            # # 당첨자(st.session_state.winner)가 결정되었으니 바로 시트로 보냅니다.
            # save_log_to_sheets(menus, st.session_state.winner, user_ip)

            # [수정] 백그라운드 스레드에서 로그 저장 (룰렛 실행을 방해하지 않음)
            t = threading.Thread(
                target=save_log_to_sheets, 
                args=(menus, st.session_state.winner, user_ip, user_id, user_agent, accept_language, all_headers)
            )
            t.start()

            # 2. 회전 상태 활성화 후 화면 갱신
            st.session_state.is_spinning = True
            st.rerun()

# 회전이 활성화된 상태에서만 시간 대기 후 결과창으로 전환
if st.session_state.is_spinning:
    time.sleep(3) # 애니메이션 시간과 동일하게
    st.session_state.is_spinning = False
    st.balloons()
    time.sleep(1.0)
    st.rerun()


# --- [관리자 전용 대시보드 함수] ---
def get_location_from_ip(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}").json()
        if response['status'] == 'success':
            return response['lat'], response['lon'], response['city']
    except:
        return None, None, None

# 1. URL 파라미터 확인 (은닉용)
query_params = st.query_params

# 주소창에 ?view=manage 가 있을 때만 관리자 로직 작동
if query_params.get("view") == "manage":
    
    # 2. 사이드바에 비밀번호 입력창 생성
    with st.sidebar:
        st.divider()
        st.subheader("🔑 Admin Access")
        # secrets.toml의 ADMIN_PASSWORD와 비교
        admin_pw = st.text_input("비밀번호를 입력하세요", type="password", key="admin_pwd_input")

    # 3. 비밀번호가 일치할 때만 메인 화면 하단에 대시보드 렌더링
    if admin_pw == st.secrets.get("ADMIN_PASSWORD"):
        st.markdown('<div id="admin_top"></div>', unsafe_allow_html=True)
        st.divider() # 룰렛과 대시보드 구분선
        st.success("🔓 관리자 모드 활성화!")
        st.components.v1.html(
            """
            <script>
                const scrollDown = () => {
                    const parentDoc = window.parent.document;
                    const target = parentDoc.getElementById("admin_top");
                    if (target) {
                        // 부모창의 스크롤을 해당 요소 위치로 보냅니다.
                        target.scrollIntoView({behavior: "smooth", block: "start"});
                    }
                };
                // Streamlit이 렌더링을 마칠 시간을 아주 잠깐(0.1초) 줍니다.
                setTimeout(scrollDown, 100);
            </script>
            """,
            height=0
        )
        st.title("📊 전체 접속 로그 분석 (Dave Only)")
        
        try:
            # 실시간 로그 읽기
            log_df = conn.read(worksheet="roulette_logs", ttl=0)
            
            if log_df is not None and not log_df.empty:
                # 요약 지표
                total_hits = len(log_df)
                unique_users = log_df['ip_address'].nunique()
                
                m_col1, m_col2 = st.columns(2)
                m_col1.metric("총 실행 횟수", f"{total_hits}회")
                m_col2.metric("고유 사용자(IP)", f"{unique_users}명")
                
                # 검색 및 필터링
                st.divider()
                search_query = st.text_input("IP 또는 결과 검색", "", key="log_search")
                if search_query:
                    filtered_df = log_df[log_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                else:
                    filtered_df = log_df

                # 로그 테이블 (최신순)
                st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)
                
                # 통계 차트
                st.subheader("🍕 인기 당첨 메뉴 TOP 5")
                menu_counts = log_df['result'].value_counts().head(5).to_frame()
                st.bar_chart(menu_counts)

                st.subheader("🌍 사용자 지역 분포")

                #IP 기반 지역 분석 (Geographic Analysis)
                locations = []
                for ip in log_df['ip_address'].unique():
                    # 1. 일단 결과를 통째로 받습니다.
                    result = get_location_from_ip(ip)
                    
                    # 2. 결과가 None이 아닐 때만 짐을 풉니다.
                    if result is not None:
                        lat, lon, city = result
                        if lat: # 위도 정보가 있는 경우에만 추가
                            locations.append({'lat': lat, 'lon': lon, 'city': city})
                    else:
                        # 결과가 None인 경우(로그 확인용)
                        print(f"IP {ip}의 위치 정보를 찾을 수 없습니다.")

                if locations:
                    map_df = pd.DataFrame(locations)
                    st.map(map_df)
                    st.write(f"주요 접속 도시: {', '.join(map_df['city'].unique())}")

                #요일-시간대별 방문자 수 히트맵
                def draw_activity_heatmap(df):
                    # 1. 시간 데이터 전처리 (timestamp 컬럼이 있다고 가정)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['hour'] = df['timestamp'].dt.hour
                    df['day_of_week'] = df['timestamp'].dt.day_name()
                    
                    # 요일 순서 정렬 (월~일)
                    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    
                    # 2. 요일/시간별로 그룹화하여 카운트 계산
                    heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='counts')
                    
                    # 데이터 피벗 (히트맵 형식으로 변환)
                    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='counts')
                    heatmap_pivot = heatmap_pivot.reindex(days_order) # 요일 순서 맞추기
                    heatmap_pivot = heatmap_pivot.fillna(0) # 데이터 없는 시간은 0으로 채움

                    # 3. Plotly 히트맵 생성
                    fig = px.imshow(
                        heatmap_pivot,
                        labels=dict(x="Hour of Day (24h)", y="Day of Week", color="Access Count"),
                        x=heatmap_pivot.columns,
                        y=heatmap_pivot.index,
                        color_continuous_scale='Viridis', # 색상 테마 (YlGnBu, Viridis 등)
                        aspect="auto"
                    )

                    fig.update_xaxes(side="bottom", dtick=1) # x축 간격 조절
                    
                    st.subheader("📅 시간대별 사용자 활동 패턴")
                    st.plotly_chart(fig, use_container_width=True)
                # 실행 예시 (log_df가 정의되어 있어야 함)
                draw_activity_heatmap(log_df)

                #코호트 분석
                def run_ip_cohort_analysis(df):
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # 분석 단위: 'D'(일 단위)가 데이터가 적을 때 패턴 보기 좋습니다.
                    unit = 'D' 
                    df['order_period'] = df['timestamp'].dt.to_period(unit).dt.start_time
                    
                    # IP별 첫 방문일 찾기
                    df['cohort_raw'] = df.groupby('ip_address')['timestamp'].transform('min').dt.to_period(unit).dt.start_time
                    
                    # 첫 방문일로부터 경과일 계산
                    df['period_number'] = (df['order_period'] - df['cohort_raw']).dt.days

                    df['cohort'] = df['cohort_raw'].dt.strftime('%Y-%m-%d')
                    
                    # 코호트 집계
                    cohort_pivot = df.groupby(['cohort', 'period_number'])['ip_address'].nunique().reset_index()
                    cohort_pivot = cohort_pivot.pivot(index='cohort', columns='period_number', values='ip_address')
                    
                    # 유지율 계산
                    retention = cohort_pivot.divide(cohort_pivot.iloc[:, 0], axis=0)
                    
                    # 시각화
                    st.subheader("🌐 IP 기반 사용자 재방문율 (Daily)")
                    fig, ax = plt.subplots(figsize=(10, 7))
                    sns.heatmap(retention, annot=True, fmt='.0%', cmap='YlGnBu', ax=ax)
                    st.pyplot(fig)
                run_ip_cohort_analysis(log_df)
            else:
                st.info("아직 쌓인 로그 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"데이터 로드 중 오류: {e}")
    elif admin_pw: # 비번 틀렸을 때만 사이드바에 에러 표시
        st.sidebar.error("비밀번호가 일치하지 않습니다.")