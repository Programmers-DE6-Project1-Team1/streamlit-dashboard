import streamlit as st
import pandas as pd
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Django API 주소
API_URL = "http://localhost:8000/api/products/"

st.set_page_config(page_title="CU 상품 대시보드", layout="wide")
st.title("📊 CU 신상품 데이터 시각화")

# --- 1. 데이터 불러오기 ---
response = requests.get(API_URL)
if response.status_code != 200:
    st.error("❌ API 응답 실패: 데이터를 불러올 수 없습니다.")
    st.stop()

df = pd.DataFrame(response.json())

# --- 2. 가격 슬라이더 + 필터 ---
st.subheader("💰 가격 필터링")

min_price = int(df["price"].min())
max_price = int(df["price"].max())
selected_range = st.slider("가격 범위 선택", min_price, max_price, (min_price, max_price))

filtered_df = df[(df["price"] >= selected_range[0]) & (df["price"] <= selected_range[1])]
st.write(f"선택된 상품 수: {len(filtered_df)}개")
st.dataframe(filtered_df[['product_name', 'price', 'label', 'promotion_tag']])

# --- 3. 가격 분포 히스토그램 ---
st.subheader("📈 전체 가격 분포")
st.hist_chart(df["price"])

# --- 4. Label별 상품 수 ---
st.subheader("🏷️ 프로모션 라벨별 상품 수")
label_counts = df['label'].fillna('없음').value_counts()
st.bar_chart(label_counts)

# --- 5. Promotion Tag 빈도수 (상위 10개) ---
st.subheader("🎯 Promotion Tag 상위 10개")
tag_counts = df['promotion_tag'].fillna('없음').value_counts().head(10)
st.bar_chart(tag_counts)

# --- 6. Tag 워드클라우드 (선택 사항) ---
if "tag" in df.columns:
    st.subheader("🧩 태그 워드클라우드")
    all_tags = " ".join(df['tag'].dropna().astype(str))
    if all_tags.strip():
        wc = WordCloud(width=800, height=400, background_color="white").generate(all_tags)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.write("태그 데이터가 부족합니다.")
