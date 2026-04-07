import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="백신고 주변 스터디카페 지도", layout="wide")

st.title("📍 우리 동네 스터디카페 실시간 지도")
st.caption("공공데이터 API를 활용하여 실시간 정보를 가져옵니다.")

# 2. API 키 불러오기
try:
    # 서비스키가 이미 인코딩되어 있을 경우를 대비해 처리
    raw_key = st.secrets["MY_API_KEY"]
    # 공공데이터 API는 키에 특수문자가 많아 인코딩/디코딩 관리가 중요합니다.
    API_KEY = urllib.parse.unquote(raw_key) 
except KeyError:
    st.error("Secrets 설정에서 'MY_API_KEY'를 찾을 수 없습니다.")
    st.stop()

# 3. 데이터 가져오기 함수
@st.cache_data(show_spinner="데이터를 불러오는 중...")
def get_study_cafe_data():
    endpoint = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
    
    # ⚠️ 중요: params 대신 URL 스트링을 직접 구성하여 인코딩 중복 방지
    params = {
        "serviceKey": API_KEY,
        "divId": "adongCd",
        "key": "4128555000", # 마두1동 행정동 코드
        "indsLclsCd": "R",    # 예술·스포츠·여가
        "indsMclsCd": "R01",  # 여가 관련 서비스업
        "type": "json",
        "numOfRows": "100"
    }
    
    try:
        # verify=False는 SSL 인증서 에러 방지용 (필요시)
        response = requests.get(endpoint, params=params, timeout=15)
        
        # 에러 디버깅을 위해 응답 텍스트 확인 (문제가 생기면 이 부분을 st.write로 출력)
        if response.status_code != 200:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            return []

        # JSON 파싱 전 내용이 비어있는지 확인
        if not response.text.strip():
            st.warning("API 응답이 비어있습니다.")
            return []
            
        data = response.json()
        
        # 데이터 구조 탐색: body -> items (리스트)
        items = data.get('body', {}).get('items', [])
        return items
        
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return []

# 4. 지도 생성 및 마커 표시
# 백신고등학교 좌표
v_lat, v_lon = 37.6433, 126.7871
m = folium.Map(location=[v_lat, v_lon], zoom_start=15)

# 백신고 마커
folium.Marker(
    [v_lat, v_lon], 
    tooltip="백신고등학교", 
    popup="우리 학교",
    icon=folium.Icon(color='red', icon='university', prefix='fa')
).add_to(m)

# API 데이터 불러오기
items = get_study_cafe_data()

# 지도에 데이터 표시
count = 0
if items:
    for item in items:
        name = item.get('bizesNm', '')
        # 이름에 '스터디' 또는 '독서실'이 포함된 경우만 필터링
        if '스터디' in name or '독서실' in name:
            lat = item.get('lat')
            lon = item.get('lon')
            if lat and lon:
                folium.Marker(
                    location=[float(lat), float(lon)],
                    popup=name,
                    tooltip=name,
                    icon=folium.Icon(color='blue', icon='book', prefix='fa')
                ).add_to(m)
                count += 1

# 지도 출력
st_folium(m, width="100%", height=600)

# 결과 메시지
if count > 0:
    st.success(f"학교 주변에서 {count}개의 스터디카페를 찾았습니다!")
elif not items:
    st.info("API로부터 데이터를 받지 못했습니다. 잠시 후 다시 시도하거나 API 키를 확인해 주세요.")
else:
    st.warning("해당 구역에 검색 조건에 맞는 스터디카페가 없습니다.")
