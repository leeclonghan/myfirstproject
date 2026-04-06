import streamlit as st
import pandas as pd
import numpy as np

st.title("Streamlit 기본 지도")

# 샘플 데이터 생성 (서울 인근)
df = pd.DataFrame(
    np.random.randn(100, 2) / [50, 50] + [37.56, 126.97],
    columns=['lat', 'lon']
)

st.map(df)
