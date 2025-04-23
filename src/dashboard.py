import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform
import pathlib

# ────────────────────────────── 페이지 설정
st.set_page_config(page_title="CU Dashboard", layout="wide")

API_URL = "http://127.0.0.1:8000/api/products/all"

# ────────────────────────────── OS별 한글 폰트 탐색
def find_korean_font() -> str | None:
    sys = platform.system()
    candidates = []
    if sys == "Windows":
        candidates = [r"C:\Windows\Fonts\malgun.ttf"]
    elif sys == "Darwin":
        candidates = ["/System/Library/Fonts/AppleSDGothicNeo.ttc",
                    "/System/Library/Fonts/AppleGothic.ttf"]
    else:
        candidates = ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                    "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf"]
    for p in candidates:
        if pathlib.Path(p).exists():
            return p
    return None

FONT_PATH = find_korean_font()

# ────────────────────────────── 데이터 로드 및 전처리
@st.cache_data(ttl=300)
def fetch_data() -> pd.DataFrame:
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data if isinstance(data, list) else data.get("results", [])
    df = pd.DataFrame(items)

    # labels, promotion_tags, tags 컬럼 평탄화
    def first_name(lst):
        if not isinstance(lst, list) or not lst:
            return "없음"
        first = lst[0]
        return first.get("name") if isinstance(first, dict) else str(first)

    if "labels" in df.columns:
        df["label"] = df["labels"].apply(first_name)
    if "promotion_tags" in df.columns:
        df["promotion_tag"] = df["promotion_tags"].apply(first_name)
    if "tags" in df.columns:
        df["tag"] = df["tags"].apply(first_name)

    # 원본 리스트 컬럼 삭제
    df.drop(columns=["labels", "promotion_tags", "tags"], inplace=True, errors="ignore")
    return df

# ────────────────────────────── 1) 데이터 준비
df = fetch_data()
filtered = df.copy()  # 사이드바 필터링용 복사본

# ────────────────────────────── 사이드바 (필터 예시)
st.sidebar.title("Filters")
# 예) 가격 필터
# min_p, max_p = int(df["price"].min()), int(df["price"].max())
# price_range = st.sidebar.slider("가격 범위", min_p, max_p, (min_p, max_p))
# filtered = filtered[(filtered["price"] >= price_range[0]) & (filtered["price"] <= price_range[1])]

# ────────────────────────────── 헤더
st.markdown(
    """
    <div style="background-color:#702CB7;padding:12px 20px;border-radius:8px;margin-bottom:20px;">
        <h1 style="color:#A8D032;font-weight:bold;margin:0;text-align:center;">
        📊 CU Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ────────────────────────────── 2개 컬럼: 라벨별 가격 & 프로모션별 개수
col1, col2 = st.columns(2)

with col1:
    st.subheader("라벨별 평균 가격")
    df_label = filtered.copy()
    df_label["label"] = df_label["label"].fillna("없음").replace("", "없음")
    lbl_df = (
        df_label.groupby("label")["price"]
        .mean()
        .reset_index(name="avg_price")
    )
    order = ["BEST", "NEW", "없음"]
    bar1 = (
        alt.Chart(lbl_df)
        .mark_bar()
        .encode(
            x=alt.X("label:N", sort=order, title="Label"),
            y=alt.Y("avg_price:Q", title="평균 가격"),
            tooltip=["label", "avg_price"],
        )
    )
    st.altair_chart(bar1, use_container_width=True)

with col2:
    st.subheader("1+1, 2+1 상품 개수")
    pt_df = (
        filtered
        .assign(promotion_tag=filtered["promotion_tag"].fillna("없음"))
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
            tooltip=["promotion_tag", "count"],
        )
    )
    st.altair_chart(bar2, use_container_width=True)

st.markdown("---")

# ────────────────────────────── 워드클라우드 두 개
col3, col4 = st.columns(2)

with col3:
    st.subheader("Tag 키워드 워드클라우드")
    tags_series = filtered.get("tag", pd.Series()).dropna().astype(str).str.strip()
    tags_series = tags_series[tags_series != ""]
    if tags_series.empty:
        st.write("표시할 태그 데이터가 없습니다.")
    else:
        tag_counts = tags_series.value_counts().head(100).to_dict()
        wc = WordCloud(
            font_path=FONT_PATH, width=400, height=200,
            background_color="white", max_words=100
        ).generate_from_frequencies(tag_counts)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

with col4:
    st.subheader("상품명 워드클라우드")
    names = filtered["product_name"].dropna().astype(str).str.strip()
    if names.empty:
        st.write("표시할 상품명 데이터가 없습니다.")
    else:
        name_counts = names.value_counts().head(100).to_dict()
        wc2 = WordCloud(
            font_path=FONT_PATH, width=400, height=200,
            background_color="white", max_words=100
        ).generate_from_frequencies(name_counts)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.imshow(wc2, interpolation="bilinear")
        ax2.axis("off")
        st.pyplot(fig2)

st.markdown("---")
