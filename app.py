import streamlit as st
import time
from game_logic_v2 import (
    init_game_state, get_elapsed_time, get_game_time_str,
    check_win_condition, generate_customer, add_item_to_counter,
    scan_item, complete_payment, update_customer_patience,
    finish_customer, check_game_over, ITEMS, calculate_total_price
)

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="야간 편돌이",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────
# CSS 스타일
# ─────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: #1a1a2e;
    color: #e0e0e0;
}

.title {
    text-align: center;
    font-size: 3rem;
    color: #ff0088;
    text-shadow: 2px 2px 4px #000;
    margin-bottom: 1rem;
}

.counter-area {
    background: #2a2a3e;
    border: 3px solid #4a4a8a;
    border-radius: 10px;
    padding: 20px;
    min-height: 400px;
}

.customer-info {
    background: #3a3a4e;
    border: 2px solid #666;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
}

.item-card {
    background: white;
    color: black;
    border-radius: 8px;
    padding: 12px;
    margin: 8px;
    text-align: center;
    cursor: pointer;
    border: 2px solid #ddd;
    transition: all 0.2s;
}

.item-card:hover {
    border-color: #ff0088;
    transform: scale(1.05);
}

.item-card.scanned {
    background: #90EE90;
    opacity: 0.6;
}

.pos-display {
    background: #000;
    color: #0f0;
    border: 3px solid #666;
    border-radius: 8px;
    padding: 20px;
    font-family: monospace;
    font-size: 1.2rem;
    margin: 15px 0;
}

.stress-bar {
    width: 100%;
    height: 30px;
    background: #333;
    border-radius: 15px;
    overflow: hidden;
    border: 2px solid #fff;
    margin: 10px 0;
}

.stress-fill {
    height: 100%;
    transition: width 0.3s ease;
}

.button-group {
    display: flex;
    gap: 10px;
    margin: 15px 0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────
if "gs" not in st.session_state:
    st.session_state.gs = init_game_state()
    st.session_state.last_item_spawn = time.time()
    st.session_state.next_customer_time = time.time() + 3

def gs():
    return st.session_state.gs

# ─────────────────────────────────────────
# 메인 게임 화면
# ─────────────────────────────────────────
def render_game():
    g = gs()
    
    # 상단 상태바
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.markdown(f"### ⏰ {get_game_time_str(g)}")
    with col2:
        st.markdown(f"### 💰 {g['money']:,}원")
    with col3:
        st.markdown(f"### 👤 {g['customers_served']}명")
    with col4:
        st.markdown(f"### ⏱️ {get_elapsed_time(g)}초")
    
    st.divider()
    
    # 게임 루프 처리
    current_time = time.time()
    
    # 새 손님 스폰
    if g["current_customer"] is None and current_time >= st.session_state.next_customer_time:
        g["current_customer"] = generate_customer()
        g["phase"] = "waiting"
        st.session_state.last_item_spawn = current_time
        st.session_state.next_customer_time = current_time + 5
    
    # 손님이 물건을 계산대에 올려놓음 (자동 스폰)
    if g["current_customer"] and len(g["items_on_counter"]) < len(g["current_customer"]["items"]):
        if current_time - st.session_state.last_item_spawn > 1:  # 1초마다 물건 추가
            add_item_to_counter(g)
            st.session_state.last_item_spawn = current_time
    
    # 손님 인내심 업데이트
    if not update_customer_patience(g):
        st.warning("😡 손님이 화가 나서 나갔습니다!")
        st.rerun()
    
    # 게임 오버 확인 (스트레스 시스템 제거됨)
    
    # 승리 조건 확인
    check_win_condition(g)
    if g["game_won"]:
        st.balloons()
        st.success("🌅 퇴근 성공! 축하합니다!")
        g["game_won"] = True
    
    # ─────────────────────────────────────────
    # 메인 게임 영역
    # ─────────────────────────────────────────
    
    if g["current_customer"] is None:
        st.markdown("<div style='text-align:center; padding:100px;'><h2>손님을 기다리는 중...</h2></div>", unsafe_allow_html=True)
    else:
        customer = g["current_customer"]
        
        # 손님 정보
        st.markdown(f"""
        <div class="customer-info">
            <h3>{customer['name']}님이 계산대에 왔습니다!</h3>
            <p>인내심: {'❤️' * max(1, int(g['patience_left'] / 10))} ({int(g['patience_left'])}%)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 계산대 (물건 표시)
        st.markdown("### 📦 계산대 (물건을 클릭해서 스캔하세요!)")
        
        if g["items_on_counter"]:
            cols = st.columns(4)
            for i, item_key in enumerate(g["items_on_counter"]):
                with cols[i % 4]:
                    item = ITEMS[item_key]
                    if st.button(f"{item['emoji']}\n{item['name']}\n{item['price']}원", key=f"item_{i}_{item_key}"):
                        scan_item(g, item_key)
                        st.rerun()
        else:
            st.info("물건을 기다리는 중...")
        
        st.divider()
        
        # POS 화면
        st.markdown("### 🖥️ POS 화면")
        st.markdown(f"""
        <div class="pos-display">
        ═══════════════════════════════════<br>
        스캔된 물건: {len(g['scanned_items'])}개<br>
        ═══════════════════════════════════<br>
        <span style="color: #ffff00; font-size: 1.5rem;">
        총액: {g['total_price']:,}원
        </span><br>
        ═══════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        
        # 결제 방식 선택
        if g["total_price"] > 0 and len(g["items_on_counter"]) == 0:
            st.markdown("### 💳 결제 방식 선택")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💵 현금 결제", use_container_width=True):
                    success, msg = complete_payment(g, "cash", g["total_price"])
                    if success:
                        st.success(f"✅ 결제 완료! {msg}")
                        finish_customer(g)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col2:
                if st.button("💳 카드 결제", use_container_width=True):
                    success, msg = complete_payment(g, "card", g["total_price"])
                    if success:
                        st.success(f"✅ 결제 완료! {msg}")
                        finish_customer(g)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
    
    # 자동 새로고침
    time.sleep(0.5)
    st.rerun()


def render_title():
    st.markdown("<h1 class='title'>🏪 야간 편돌이</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;'><h3>슈의 라면가게 스타일 편의점 계산 시뮬레이션</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🌙 영업 시작!", use_container_width=True, key="start_game"):
            st.session_state.gs = init_game_state()
            st.session_state.game_started = True
            st.rerun()


def render_game_over():
    g = gs()
    if g["game_won"]:
        st.balloons()
        st.markdown("<h1 style='text-align:center; color:#00ff88;'>🌅 퇴근 성공!</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align:center; color:#ff0000;'>😱 멘탈 붕괴</h1>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='text-align:center; font-size:1.5rem;'>
        <p>최종 매출: <span style='color:#ffff00;'>{g['money']:,}원</span></p>
        <p>처리한 손님: <span style='color:#00ff88;'>{g['customers_served']}명</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("다시 도전하기", use_container_width=True):
        st.session_state.gs = init_game_state()
        st.session_state.game_started = False
        st.rerun()


# ─────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────
if __name__ == "__main__":
    if not st.session_state.get("game_started", False):
        render_title()
    elif gs()["game_over"] or gs()["game_won"]:
        render_game_over()
    else:
        render_game()
