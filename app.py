import streamlit as st
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="백신고 주변 지도", layout="wide")

st.title("📍 백신고등학교 주변 (반경 5km)")

# 1. 백신고등학교 좌표 설정
# 주소: 경기도 고양시 일산동구 마두동
v_lat, v_lon = 37.6433, 126.7871

# 2. 지도 객체 생성
m = folium.Map(location=[v_lat, v_lon], zoom_start=13)

# 3. 백신고등학교 마커 추가
folium.Marker(
    [v_lat, v_lon],
    popup="백신고등학교",
    tooltip="백신고등학교",
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

# 4. 반경 5km 원(Circle) 추가
folium.Circle(
    location=[v_lat, v_lon],
    radius=5000, # 단위: 미터(m)
    color='blue',
    fill=True,
    fill_color='blue',
    fill_opacity=0.1,
    popup="반경 5km 영역"
).add_to(m)

# 5. Streamlit에 지도 출력
st_folium(m, width=1000, height=600)

st.info("💡 지도를 확대/축소하거나 마커를 클릭해 보세요.")
