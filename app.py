import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests  # 디스코드로 알림을 보내기 위해 필요한 파이썬 기본 부품

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(
    page_title="우리반 수행평가 & 시험 캘린더",
    page_icon="📅",
    layout="wide"
)

st.title("📅 우리반 수행평가 & 시험 디데이 캘린더")
st.markdown("동아리 프로젝트로 제작된 수행평가 일정 관리 서비스입니다. (구글 시트 및 디스코드 실시간 알림 연동)")
st.write("https://docs.google.com/spreadsheets/d/1jDPHmlhAcbe-Zdam5ghhX-bDgqjCXjz5qL4Po-cZFZg/edit?usp=sharing")

# 🔗 [필수 수정 1] 본인의 구글 시트 주소를 넣으세요.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1jDPHmlhAcbe-Zdam5ghhX-bDgqjCXjz5qL4Po-cZFZg/edit?usp=sharing"

# 🔗 [필수 수정 2] 방금 디스코드에서 복사한 웹훅 URL 주소를 넣으세요.
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1523567631850934383/31V09jK_uiBCBmeMT2c9mXD02P5vqoVSIguobGZioKc1h8SQyjiRRSdbeh5MVWMOXGkW"

# 2. 구글 시트 주소를 CSV 다운로드 주소로 변환하는 함수
def get_csv_url(url):
    try:
        if "/edit" in url:
            base_url = url.split("/edit")[0]
            return f"{base_url}/export?format=csv"
        return url
    except:
        return url

# 3. 구글 시트 데이터 로드 함수
@st.cache_data(ttl=3)
def load_data_from_sheets():
    try:
        csv_url = get_csv_url(GOOGLE_SHEET_URL)
        df = pd.read_csv(csv_url)
        if df.empty:
            return pd.DataFrame(columns=["과목", "구분", "내용", "마감일"])
        df["마감일"] = pd.to_datetime(df["마감일"]).dt.date
        return df
    except Exception as e:
        st.error(f"구글 시트 데이터를 읽어오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(columns=["과목", "구분", "내용", "마감일"])

# 🔔 4. 디스코드 알림 발송 함수
def send_discord_alert(subject, category, content, due_date):
    try:
        # 오늘 날짜 기준으로 남은 일수(디데이) 계산
        delta = (due_date - date.today()).days
        dday_str = f"⏳ D-{delta}" if delta > 0 else "🔥 D-Day" if delta == 0 else f"✅ 완료 (D+{abs(delta)})"
        
        # 디스코드에 보낼 예쁜 멘트 구성
        message = {
            "content": f"🚨 **[신규 일정 등록] 우리 반의 새로운 일정이 추가되었습니다!** 🚨\n"
                       f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                       f"📌 **과목명:** {subject}\n"
                       f"🏷️ **구 분:** {category}\n"
                       f"📝 **내 용:** {content}\n"
                       f"📅 **일 정:** {due_date.strftime('%Y년 %m월 %d일')} ({dday_str})\n"
                       f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                       f"💡 *지금 바로 캘린더 웹사이트에서 상세 내용을 확인해보세요!*"
        }
        
        # 인터넷을 통해 디스코드 서버로 데이터 전송 (POST 요청)
        response = requests.post(DISCORD_WEBHOOK_URL, json=message)
        
        if response.status_code == 204:
            return True
        else:
            return False
    except:
        return False

# 5. 데이터 동기화 관리
if "temp_events" not in st.session_state:
    st.session_state.temp_events = []

sheet_df = load_data_from_sheets()

if st.session_state.temp_events:
    temp_df = pd.DataFrame(st.session_state.temp_events)
    df_all = pd.concat([sheet_df, temp_df], ignore_index=True)
else:
    df_all = sheet_df

# 6. 사이드바: 새로운 일정 등록 기능
st.sidebar.header("➕ 새로운 일정 추가")
with st.sidebar.form(key="event_form", clear_on_submit=True):
    subject = st.text_input("과목명", placeholder="예: 국어, 화학I")
    category = st.selectbox("구분", ["수행평가", "지필평가", "동아리/기타"])
    content = st.text_area("상세 내용", placeholder="수행평가 주제 및 준비물 등")
    due_date = st.date_input("마감일 / 시험일", value=date.today())
    
    submit_button = st.form_submit_button(label="일정 등록하기")

if submit_button:
    if subject and content:
        # 1. 화면에 보여주기 위해 임시 세션 리스트에 추가
        st.session_state.temp_events.append({
            "과목": subject, "구분": category, "내용": content, "마감일": due_date
        })
        
        # 2. [핵심] 등록 성공 시 디스코드로 실시간 알림 쏘기!
        with st.spinner("디스코드로 알림을 전송하는 중..."):
            alert_success = send_discord_alert(subject, category, content, due_date)
            
        if alert_success:
            st.sidebar.success(f"🎉 {subject} 일정 등록 및 디스코드 알림 완료!")
        else:
            st.sidebar.warning(f"⚠️ 일정은 등록되었으나, 디스코드 알림 전송에 실패했습니다. URL을 확인하세요.")
            
        st.rerun()
    else:
        st.sidebar.error("❌ 과목명과 상세 내용을 입력해주세요.")

# 7. 메인 화면: 디데이 대시보드 및 일정 표 시각화
if not df_all.empty:
    today = date.today()
    
    def calculate_dday(target_date):
        delta = (target_date - today).days
        if delta == 0:
            return "🔥 D-Day"
        elif delta > 0:
            return f"⏳ D-{delta}"
        else:
            return f"✅ 완료 (D+{abs(delta)})"

    df_all["디데이"] = df_all["마감일"].apply(calculate_dday)
    df_all = df_all.sort_values(by="마감일")

    st.subheader("🚨 가장 가까운 주요 일정")
    upcoming_df = df_all[df_all["마감일"] >= today].head(3)
    
    if not upcoming_df.empty:
        cols = st.columns(len(upcoming_df))
        for idx, row in enumerate(upcoming_df.itertuples()):
            with cols[idx]:
                st.info(f"**[{row.구분}] {row.과목}**\n\n### {row.디데이}\n\n📅 {row.마감일}")
    else:
        st.success("🎉 다가오는 남은 일정이 없습니다! 여유를 즐기세요.")

    st.write("")
    st.subheader("📋 전체 일정 리스트")
    
    filter_category = st.multiselect("보기 설정 (구분 필터)", options=["수행평가", "지필평가", "동아리/기타"], default=["수행평가", "지필평가", "동아리/기타"])
    filtered_df = df_all[df_all["구분"].isin(filter_category)]
    
    display_df = filtered_df[["디데이", "과목", "구분", "내용", "마감일"]].reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("구글 시트에 데이터가 비어있거나 로딩 중입니다. 구글 시트 첫 줄에 데이터를 적어보세요!")
