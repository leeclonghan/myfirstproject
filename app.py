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
st.write("---")

# 2. 데이터 초기화 (세션 상태를 활용해 브라우저가 열려 있는 동안 유지)
if "events" not in st.session_state:
    st.session_state.events = [
        {"과목": "수학I", "구분": "수행평가", "내용": "삼각함수 탐구 보고서 제출", "마감일": date(2026, 7, 10)},
        {"과목": "영어 독해와 작문", "구분": "수행평가", "내용": "영작문 에세이 발표", "마감일": date(2026, 7, 14)},
        {"과목": "통합과학", "구분": "지필평가", "내용": "2학기 1회 고사", "마감일": date(2026, 9, 25)},
    ]

# 3. 사이드바: 새로운 일정 등록 기능
st.sidebar.header("➕ 새로운 일정 추가")
with st.sidebar.form(key="event_form", clear_on_submit=True):
    subject = st.text_input("과목명", placeholder="예: 국어, 화학I")
    category = st.selectbox("구분", ["수행평가", "지필평가", "동아리/기타"])
    content = st.text_area("상세 내용", placeholder="수행평가 주제 및 준비물 등")
    due_date = st.date_input("마감일 / 시험일", value=date.today())
    
    submit_button = st.form_submit_button(label="일정 등록하기")

if submit_button:
    if subject and content:
        # 새로운 일정을 세션 상태 데이터에 추가
        new_event = {
            "과목": subject,
            "구분": category,
            "내용": content,
            "마감일": due_date
        }
        st.session_state.events.append(new_event)
        st.sidebar.success(f"🎉 {subject} 일정이 등록되었습니다!")
    else:
        st.sidebar.error("❌ 과목명과 상세 내용을 입력해주세요.")

# 4. 메인 화면: 디데이 대시보드 및 일정 표 시각화
if st.session_state.events:
    # 딕셔너리 리스트를 데이터프레임으로 변환
    df = pd.DataFrame(st.session_state.events)
    today = date.today()
    
    # 디데이 계산 함수
    def calculate_dday(target_date):
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        delta = (target_date - today).days
        if delta == 0:
            return "🔥 D-Day"
        elif delta > 0:
            return f"⏳ D-{delta}"
        else:
            return f"✅ 완료 (D+{abs(delta)})"

    df["디데이"] = df["마감일"].apply(calculate_dday)
    df = df.sort_values(by="마감일") # 오타가 났던 정렬 영역을 깔끔하게 '마감일' 기준으로 단일 정렬하도록 수정 완료!

    # 상단 카드: 마감일이 가장 가까운 3개 일정 하이라이트
    st.subheader("🚨 가장 가까운 주요 일정")
    upcoming_df = df[df["마감일"] >= today].head(3)
    
    if not upcoming_df.empty:
        cols = st.columns(len(upcoming_df))
        for idx, row in enumerate(upcoming_df.itertuples()):
            with cols[idx]:
                st.info(f"**[{row.구분}] {row.과목}**\n\n### {row.디데이}\n\n📅 {row.마감일}")
    else:
        st.success("🎉 다가오는 남은 일정이 없습니다! 여유를 즐기세요.")

    st.write("")
    st.subheader("📋 전체 일정 리스트")
    
    # 사용자가 원하는 구분만 필터링해서 볼 수 있는 기능
    filter_category = st.multiselect("보기 설정 (구분 필터)", options=["수행평가", "지필평가", "동아리/기타"], default=["수행평가", "지필평가", "동아리/기타"])
    filtered_df = df[df["구분"].isin(filter_category)]
    
    # 열 순서 이쁘게 정리해서 테이블로 출력
    display_df = filtered_df[["디데이", "과목", "구분", "내용", "마감일"]].reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("등록된 일정이 없습니다. 왼쪽 사이드바에서 첫 일정을 등록해 보세요!")
