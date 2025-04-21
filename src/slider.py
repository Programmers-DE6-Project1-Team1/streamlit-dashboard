import streamlit as st
import pandas as pd
import requests

# API 주소
API_URL = "http://localhost:8000/api/products/"

st.title("📦 CU 상품 대시보드")

# 1. 데이터 불러오기
response = requests.get(API_URL)
if response.status_code != 200:
    st.error("❌ API 요청 실패")
    st.stop()
df = pd.DataFrame(response.json())

# 2. 검색창 필터
st.subheader("🔍 상품명으로 검색")
query = st.text_input("상품명 입력")
if query:
    df = df[df["product_name"].str.contains(query, case=False, na=False)]

# 3. 이미지 카드 목록
st.subheader("🖼️ 상품 이미지 카드")

# 카드 출력 (3개씩 가로 배치)
cols = st.columns(3)
for i, (_, row) in enumerate(df.iterrows()):
    with cols[i % 3]:
        st.image(row["image_url"], use_container_width=True)
        st.markdown(f"**{row['product_name']}**")
        st.markdown(f"💰 {row['price']}원")
        if pd.notna(row["label"]):
            st.markdown(f"🏷️ {row['label']}")
        if pd.notna(row["promotion_tag"]):
            st.markdown(f"🎯 {row['promotion_tag']}")
