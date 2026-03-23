import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time
import base64
from io import BytesIO
import random

# 1. 페이지 및 세션 상태 설정
st.set_page_config(page_title="진짜 돌아가는 룰렛", layout="centered")

if 'winner' not in st.session_state:
    st.session_state.winner = None
if 'target_angle' not in st.session_state:
    st.session_state.target_angle = 0
if 'is_spinning' not in st.session_state:
    st.session_state.is_spinning = False

# 2. 룰렛 이미지 생성 함수 (12시 방향 기준)
def create_roulette(items):
    size = (600, 600)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Windows: r"C:\Windows\Fonts\malgun.ttf" / Mac: "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
        font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 28)
    except:
        font = None

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
st.title("🍴 이번엔 진짜 돈다! 점심 룰렛")

cols = st.columns(5)
menus = []
default_list = ["돈가스", "치킨", "초밥", "쌀국수", "마라탕"]
for i, col in enumerate(cols):
    m = col.text_input(f"메뉴 {i+1}", value=default_list[i], key=f"m_{i}")
    menus.append(m)

roulette_img = create_roulette(menus)
img_base64 = img_to_base64(roulette_img)

# 4. CSS: 애니메이션 클래스 정의
st.markdown(f"""
<style>
    @keyframes spin-anim {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate({st.session_state.target_angle}deg); }}
    }}
    .roulette-container {{ display: flex; flex-direction: column; align-items: center; position: relative; padding: 20px; }}
    .arrow {{ width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 30px solid #FF4B4B; z-index: 10; margin-bottom: -20px; }}
    .spinning-active {{ animation: spin-anim 3s cubic-bezier(0.15, 0, 0.15, 1) forwards; }}
    .roulette-img {{ width: 400px; border-radius: 50%; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
    .result-box {{ text-align: center; padding: 30px; border-radius: 15px; background-color: #f0f2f6; border: 2px solid #FF4B4B; margin-top: 20px; }}
</style>
""", unsafe_allow_html=True)

placeholder = st.empty()

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
        win_idx = random.randint(0, 4)
        st.session_state.winner = menus[win_idx]
        angle_per_item = 360 / len(menus)
        # 화살표(상단) 위치에 맞게 각도 계산 (10바퀴 기본 회전)
        st.session_state.target_angle = 3600 - (win_idx * angle_per_item) - (angle_per_item / 2)
        
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