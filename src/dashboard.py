import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(page_title="CU Dashboard", layout="wide")

API_URL = "http://127.0.0.1:8000/api/products/"

@st.cache_data(ttl=300)
def fetch_data():
    resp = requests.get(API_URL)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    return df

df = fetch_data()

# --- 사이드바 필터
st.sidebar.title("Filters")
search = st.sidebar.text_input("상품명 검색")
min_price, max_price = st.sidebar.slider(
    "가격 범위",
    int(df.price.min()), int(df.price.max()),
    (int(df.price.min()), int(df.price.max())),
    step=100
)

mask = (df.price >= min_price) & (df.price <= max_price)
if search:
    mask &= df.product_name.str.contains(search, case=False, na=False)
filtered = df[mask]

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

# --- 이미지 카드
st.subheader("오늘의 CU 음식")
cols = st.columns(4)
for i, (_, row) in enumerate(filtered.head(4).iterrows()):
    cols[i].image(row.image_url, width=150)
    cols[i].caption(f"{row.product_name}\n{row.price}원")

st.markdown("---")

# --- 상세 표
st.subheader("슬라이더 필터 + 상세 표")
st.write(f"선택된 가격: {min_price}원 ~ {max_price}원  |  검색어: '{search}'")
st.dataframe(filtered.reset_index(drop=True))

st.markdown("---")

# --- 2개 컬럼: Label별 & Promotion Tag별 통계
col1, col2 = st.columns(2)

with col1:
    st.subheader("라벨별 평균 가격")

    # 1) 빈 값 처리해서 '없음'으로 통일
    df_label = filtered.copy()
    df_label['label'] = (
        df_label['label']
        .fillna('없음')         # NaN → '없음'
        .replace('', '없음')    # ''  → '없음'
    )

    # 2) 그룹화 & 평균 가격 계산
    lbl_df = (
        df_label
        .groupby("label")
        .price
        .mean()
        .reset_index(name="avg_price")
    )

    # 3) x축 순서 지정
    order = ["BEST", "NEW", "없음"]

    # 4) 차트
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
    st.subheader("1+1, 2+1 상품개수")
    # fillna 후 groupby.size() → reset_index(name="count") 로
    pt_df = (
        filtered
        .assign(promotion_tag=filtered.promotion_tag.fillna("없음"))
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
            tooltip=["promotion_tag","count"]
        )
    )
    st.altair_chart(bar2, use_container_width=True)

st.markdown("---")

# --- 워드클라우드 두 개
font_path = "C:/Windows/Fonts/malgun.ttf"

col1, col2 = st.columns(2)

with col1:
    st.subheader("Tag 키워드 워드클라우드")

    # 1) 태그 시리즈 정제
    tags = (
        filtered['tag']
        .dropna()
        .astype(str)
        .str.strip()
    )
    tags = tags[tags != ""]

    if tags.empty:
        st.write("표시할 태그 데이터가 없습니다.")
    else:
        # 2) 상위 100개 태그 빈도 계산
        tag_counts = tags.value_counts().head(100).to_dict()
        st.write(f"- 워드클라우드용 단어 개수: {len(tag_counts)}")

        try:
            wc = WordCloud(
                font_path=font_path,
                width=400,
                height=200,
                background_color="white",
                max_words=100
            ).generate_from_frequencies(tag_counts)

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"❌ 워드클라우드 생성 중 오류: {e}")

with col2:
    st.subheader("상품명 워드클라우드 & 이미지 검색")

    # 1) 상품명 시리즈 정제
    names = (
        filtered['product_name']
        .dropna()
        .astype(str)
        .str.strip()
    )

    if names.empty:
        st.write("표시할 상품명 데이터가 없습니다.")
    else:
        # 2) 상위 100개 상품명 빈도 계산
        name_counts = names.value_counts().head(100).to_dict()
        st.write(f"- 상품명 워드클라우드용 단어 개수: {len(name_counts)}")

        try:
            wc2 = WordCloud(
                font_path=font_path,
                width=400,
                height=200,
                background_color="white",
                max_words=100
            ).generate_from_frequencies(name_counts)

            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.imshow(wc2, interpolation="bilinear")
            ax2.axis("off")
            st.pyplot(fig2)
        except Exception as e:
            st.error(f"❌ 상품명 워드클라우드 생성 중 오류: {e}")

    # 3) 키워드 필터 + 이미지 카드
    keyword = st.text_input("워드클라우드 키워드로 필터", key="wc_filter")
    if keyword:
        sel = filtered[filtered.product_name.str.contains(keyword, case=False, na=False)]
        st.write(f"'{keyword}' 포함 상품 {len(sel)}개")
        cols2 = st.columns(4)
        for i, (_, row) in enumerate(sel.head(4).iterrows()):
            cols2[i].image(row.image_url, width=150)
            cols2[i].caption(f"{row.product_name}\n{row.price}원")

st.markdown("---")
