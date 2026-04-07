import streamlit as st
from streamlit_folium import st_folium
import folium
import requests

# 페이지 설정
st.set_page_config(page_title="백신고 주변 스터디카페 지도", layout="wide")

st.title("📍 우리 동네 스터디카페 실시간 지도")

# 1. API 키 로드 (로컬 환경과 클라우드 환경 모두 대응)
# 로컬 테스트 시에는 .streamlit/secrets.toml 파일이 필요합니다.
try:
    API_KEY = st.secrets["MY_API_KEY"]
except Exception:
    st.error("Secrets 설정에서 'MY_API_KEY'를 찾을 수 없습니다. '.streamlit/secrets.toml' 파일을 확인하세요.")
    st.stop()

# 2. 데이터 가져오기 함수 (구조 개선)
@st.cache_data(show_spinner="데이터를 불러오는 중...")
def get_study_cafe_data():
    endpoint = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
    params = {
        'serviceKey': API_KEY,
        'divId': 'adongCd',
        'key': '4128555000', # 마두1동
        'indsLclsCd': 'R',   # 예술·스포츠·여가
        'indsMclsCd': 'R01', # 여가 관련 서비스업
        'type': 'json',
        'numOfRows': '100'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 공공데이터 API 구조: body -> items -> item (리스트 형태)
            if 'body' in data and 'items' in data['body']:
                return data['body']['items']
        return []
    except Exception:
        return []

# 3. 지도 생성
v_lat, v_lon = 37.6433, 126.7871
m = folium.Map(location=[v_lat, v_lon], zoom_start=15)

# 학교 마커
folium.Marker(
    [v_lat, v_lon], 
    tooltip="백신고등학교", 
    icon=folium.Icon(color='red', icon='university', prefix='fa')
).add_to(m)

# 데이터 처리 및 마커 표시
items = get_study_cafe_data()

if items:
    count = 0
    for item in items:
        # 키값이 없는 경우를 대비해 .get() 사용
        name = item.get('bizesNm', '')
        lat = item.get('lat')
        lon = item.get('lon')
        
        if ('스터디' in name or '독서실' in name) and lat and lon:
            folium.Marker(
                location=[float(lat), float(lon)],
                popup=name,
                tooltip=name,
                icon=folium.Icon(color='blue', icon='book', prefix='fa')
            ).add_to(m)
            count += 1
    
    st_folium(m, width="100%", height=600)
    st.success(f"학교 주변에서 {count}개의 스터디카페/독서실을 찾았습니다!")
else:
    st_folium(m, width="100%", height=600)
    st.info("데이터가 없거나 API 연결에 실패했습니다.")
    # 데이터가 없을 경우 기본 지도라도 표시
    st_folium(m, width="100%", height=600)
    st.info("검색된 데이터가 없거나 API 연결 대기 중입니다.")
