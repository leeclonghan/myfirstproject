import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="백신고 주변 스터디카페 지도", layout="wide")

st.title("📍 우리 동네 스터디카페 실시간 지도")
st.caption("공공데이터 API를 활용하여 실시간 정보를 가져옵니다.")

# --- 1. 보안: API 키 불러오기 ---
# Streamlit Cloud의 Settings > Secrets에 저장한 키를 사용합니다.
try:
    API_KEY = st.secrets["MY_API_KEY"]
except KeyError:
    st.error("Secrets 설정에서 'MY_API_KEY'를 찾을 수 없습니다.")
    st.stop()

# --- 2. 데이터 가져오기 함수 ---
@st.cache_data(show_spinner="데이터를 불러오는 중...")
def get_study_cafe_data():
    # 사진에서 확인한 Base URL과 호출 주소를 조합합니다.
    # 예시: 상권정보 업종별 점포 조회 API
    endpoint = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
    
    params = {
        'serviceKey': API_KEY,
        'divId': 'adongCd',
        'key': '4128555000', # 마두1동 법정동 코드
        'indsLclsCd': 'R',    # 예술·스포츠·여가
        'indsMclsCd': 'R01',  # 여가 관련 서비스업
        'type': 'json',
        'numOfRows': '100'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        return data['body']['items']
    except Exception as e:
        st.warning(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return []

# --- 3. 지도 생성 및 마커 표시 ---
# 백신고등학교 좌표
v_lat, v_lon = 37.6433, 126.7871

# 지도 객체 생성
m = folium.Map(location=[v_lat, v_lon], zoom_start=15)

# 중심점(백신고) 표시
folium.Marker(
    [v_lat, v_lon], 
    tooltip="백신고등학교", 
    popup="우리 학교",
    icon=folium.Icon(color='red', icon='university', prefix='fa')
).add_to(m)

# API 데이터 불러오기
items = get_study_cafe_data()

if items:
    count = 0
    for item in items:
        # 상호명에 '스터디' 또는 '독서실'이 포함된 경우만 표시
        name = item.get('bizesNm', '')
        if '스터디' in name or '독서실' in name:
            folium.Marker(
                location=[float(item['lat']), float(item['lon'])],
                popup=name,
                tooltip=name,
                icon=folium.Icon(color='blue', icon='book', prefix='fa')
            ).add_to(m)
            count += 1
    
    # 지도 출력
    st_folium(m, width="100%", height=600)
    st.success(f"학교 주변에서 {count}개의 스터디카페/독서실을 찾았습니다!")
else:
    # 데이터가 없을 경우 기본 지도라도 표시
    st_folium(m, width="100%", height=600)
    st.info("검색된 데이터가 없거나 API 연결 대기 중입니다.")
