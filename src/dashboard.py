import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# 페이지 설정
st.set_page_config(page_title="CU Dashboard", layout="wide")

API_URL = "http://127.0.0.1:8000/api/products/all"

# 데이터 로드 함수
@st.cache_data(ttl=300)
def fetch_data():
    resp = requests.get(API_URL)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("results", [])
    df = pd.DataFrame(items)

    # labels/promotion_tags 평탄화(필요하다면)
    # df['label'] = df['labels'].apply(lambda lst: lst[0]['name'] if lst else '없음')
    # df['promotion_tag'] = df['promotion_tags'].apply(lambda lst: lst[0]['name'] if lst else '없음')
    # return df.drop(columns=['labels','promotion_tags'], errors='ignore')

    return df

# 1) 데이터 불러오기
df = fetch_data()

# 2) 필터용 복사본 (지금은 전체 데이터 사용)
filtered = df.copy()

# --- 사이드바 필터 (예시)
st.sidebar.title("Filters")

# --- 대시보드 헤더
st.markdown(
    """
    <div style="
        background-color: #702CB7;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    ">
        <h1 style="
            color: #A8D032;
            font-weight: bold;
            margin: 0;
            text-align: center;
        ">
            📊 CU Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# --- 2개 컬럼: 라벨별 평균 가격 & 프로모션별 상품 개수
col1, col2 = st.columns(2)

with col1:
    st.subheader("라벨별 평균 가격")
    df_label = filtered.copy()
    df_label['label'] = df_label['label'].fillna('없음').replace('', '없음')
    lbl_df = (
        df_label
        .groupby("label")['price']
        .mean()
        .reset_index(name="avg_price")
    )
    order = ["BEST", "NEW", "없음"]
    bar1 = (
        alt.Chart(lbl_df)
        .mark_bar()
        .encode(
            x=alt.X("label:N", title="Label", sort=order),
            y=alt.Y("avg_price:Q", title="평균 가격"),
            tooltip=["label", "avg_price"]
        )
    )
    st.altair_chart(bar1, use_container_width=True)

with col2:
    st.subheader("1+1, 2+1 상품 개수")
    pt_df = (
        filtered
        .assign(promotion_tag=filtered['promotion_tag'].fillna("없음"))
        .groupby("promotion_tag")
        .size()
        .reset_index(name="count")
    )
    bar2 = (
        alt.Chart(pt_df)
        .mark_bar()
        .encode(
            x=alt.X("promotion_tag:N", title="Promotion Tag"),
            y=alt.Y("count:Q", title="상품 수"),
            tooltip=["promotion_tag", "count"]
        )
    )
    st.altair_chart(bar2, use_container_width=True)

st.markdown("---")

# --- 워드클라우드 두 개
font_path = "C:/Windows/Fonts/malgun.ttf"
col1, col2 = st.columns(2)

with col1:
    st.subheader("Tag 키워드 워드클라우드")
    tags = filtered['tag'].dropna().astype(str).str.strip()
    tags = tags[tags != ""]
    if tags.empty:
        st.write("표시할 태그 데이터가 없습니다.")
    else:
        tag_counts = tags.value_counts().head(100).to_dict()
        st.write(f"- 워드클라우드용 단어 개수: {len(tag_counts)}")
        wc = WordCloud(font_path=font_path, width=400, height=200,
                background_color="white", max_words=100
        ).generate_from_frequencies(tag_counts)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

with col2:
    st.subheader("상품명 워드클라우드")
    names = filtered['product_name'].dropna().astype(str).str.strip()
    if names.empty:
        st.write("표시할 상품명 데이터가 없습니다.")
    else:
        name_counts = names.value_counts().head(100).to_dict()
        st.write(f"- 워드클라우드용 단어 개수: {len(name_counts)}")
        wc2 = WordCloud(font_path=font_path, width=400, height=200,
                        background_color="white", max_words=100
        ).generate_from_frequencies(name_counts)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.imshow(wc2, interpolation="bilinear")
        ax2.axis("off")
        st.pyplot(fig2)

st.markdown("---")
