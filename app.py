import streamlit as st
import pandas as pd
from datetime import datetime, date

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(
    page_title="우리반 수행평가 & 시험 캘린더",
    page_icon="📅",
    layout="wide"
)

st.title("📅 우리반 수행평가 & 시험 디데이 캘린더")
st.markdown("동아리 프로젝트로 제작된 수행평가 일정 관리 서비스입니다. (구글 스프레드시트 최신 연동)")
st.write("---")

# 🔗 [중요!] 본인의 구글 시트 주소를 아래 큰따옴표 안에 붙여넣으세요!
# 링크 공유 설정은 그대로 '링크가 있는 모든 사용자 - 편집자' 상태여야 합니다.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1jDPHmlhAcbe-Zdam5ghhX-bDgqjCXjz5qL4Po-cZFZg/edit?usp=sharing"

# 2. 구글 시트 주소를 CSV 다운로드 주소로 변환하는 함수
def get_csv_url(url):
    try:
        # 구글 시트 주소 뒤의 /edit... 부분을 /export?format=csv로 바꿔서 직접 데이터를 다운로드하는 방식입니다.
        if "/edit" in url:
            base_url = url.split("/edit")[0]
            return f"{base_url}/export?format=csv"
        return url
    except:
        return url

# 3. 구글 시트 데이터 로드 함수
@st.cache_data(ttl=3) # 3초 캐싱
def load_data_from_sheets():
    try:
        csv_url = get_csv_url(GOOGLE_SHEET_URL)
        # 구글 시트의 데이터를 판다스(pandas)가 인터넷 주소에서 직접 긁어옵니다 (가장 안전하고 빠름)
        df = pd.read_csv(csv_url)
        
        # 만약 시트가 비어있다면 빈 데이터프레임 반환
        if df.empty:
            return pd.DataFrame(columns=["과목", "구분", "내용", "마감일"])
            
        # 구글 시트의 텍스트 날짜를 파이썬 날짜(date) 객체로 변환
        df["마감일"] = pd.to_datetime(df["마감일"]).dt.date
        return df
    except Exception as e:
        st.error(f"구글 시트 데이터를 읽어오는 중 오류가 발생했습니다. 주소가 정확한지 확인하세요. 에러내용: {e}")
        return pd.DataFrame(columns=["과목", "구분", "내용", "마감일"])

# 4. 데이터 동기화 관리
if "temp_events" not in st.session_state:
    st.session_state.temp_events = []

# 구글 시트에서 기본 데이터 읽어오기
sheet_df = load_data_from_sheets()

# 브라우저에서 새로 등록된 임시 데이터가 있다면 병합해줍니다.
if st.session_state.temp_events:
    temp_df = pd.DataFrame(st.session_state.temp_events)
    df_all = pd.concat([sheet_df, temp_df], ignore_index=True)
else:
    df_all = sheet_df

# 5. 사이드바: 새로운 일정 등록 기능
st.sidebar.header("➕ 새로운 일정 추가")
with st.sidebar.form(key="event_form", clear_on_submit=True):
    subject = st.text_input("과목명", placeholder="예: 국어, 화학I")
    category = st.selectbox("구분", ["수행평가", "지필평가", "동아리/기타"])
    content = st.text_area("상세 내용", placeholder="수행평가 주제 및 준비물 등")
    due_date = st.date_input("마감일 / 시험일", value=date.today())
    
    submit_button = st.form_submit_button(label="일정 등록하기")

if submit_button:
    if subject and content:
        # 화면 전용 세션 리스트에 임시 추가
        st.session_state.temp_events.append({
            "과목": subject, "구분": category, "내용": content, "마감일": due_date
        })
        st.sidebar.success(f"🎉 {subject} 일정이 화면에 등록되었습니다!")
        st.rerun()
    else:
        st.sidebar.error("❌ 과목명과 상세 내용을 입력해주세요.")

# 6. 메인 화면: 디데이 대시보드 및 일정 표 시각화
if not df_all.empty:
    today = date.today()
    
    # 디데이 계산 함수
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

    # 상단 카드: 마감일이 가장 가까운 3개 일정 하이라이트
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
    
    # 필터 기능
    filter_category = st.multiselect("보기 설정 (구분 필터)", options=["수행평가", "지필평가", "동아리/기타"], default=["수행평가", "지필평가", "동아리/기타"])
    filtered_df = df_all[df_all["구분"].isin(filter_category)]
    
    display_df = filtered_df[["디데이", "과목", "구분", "내용", "마감일"]].reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("구글 시트에 데이터가 비어있거나 로딩 중입니다. 구글 시트 첫 줄에 데이터를 적어보세요!")
