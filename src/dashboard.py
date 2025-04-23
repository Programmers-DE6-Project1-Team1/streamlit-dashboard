# dashboard.py
import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform, pathlib

# ────────────────────────────── 페이지 설정
st.set_page_config(page_title="CU Dashboard", layout="wide")

API_URL = "http://127.0.0.1:8000/api/products/all"      # 필요하면 /api/products/ 로 교체

# ────────────────────────────── OS별 한글 폰트 찾기
def find_korean_font() -> str | None:
    """
    실행 OS에 존재하는 한글 TrueType/OTF/Collection 폰트 경로를 반환.
    없으면 None (→ WordCloud 기본 폰트 사용, 한글은 깨질 수 있음)
    """
    sys = platform.system()
    candidates: list[str] = []

    if sys == "Windows":
        candidates = [
            r"C:\Windows\Fonts\malgun.ttf",             # 맑은고딕
        ]
    elif sys == "Darwin":                               # macOS
        candidates = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",   # 기본 한글
            "/System/Library/Fonts/AppleGothic.ttf",
        ]
    else:                                               # Linux
        candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        ]

    for p in candidates:
        if pathlib.Path(p).exists():
            return p
    return None

FONT_PATH = find_korean_font()

# ────────────────────────────── 데이터 로드
@st.cache_data(ttl=300)
def fetch_data() -> pd.DataFrame:
    data = requests.get(API_URL, timeout=10).json()

    # ① 페이지네이션 여부 감지
    items = data if isinstance(data, list) else data.get("results", [])

    df = pd.DataFrame(items)

    # ② 리스트 → 문자열 평탄화 ─ 첫 번째 name 사용
    def first_name(lst):
        if not lst:
            return None
        first = lst[0]
        return first["name"] if isinstance(first, dict) else str(first)

    if "labels" in df.columns:
        df["label"] = df["labels"].apply(first_name)
    if "promotion_tags" in df.columns:
        df["promotion_tag"] = df["promotion_tags"].apply(first_name)
    if "tags" in df.columns:
        df["tag"] = df["tags"].apply(first_name)

    # 불필요한 원본 컬럼 제거(선택)
    df.drop(columns=["labels", "promotion_tags", "tags"], inplace=True, errors="ignore")
    return df


# ────────────────────────────── 1) 데이터 불러오기
df       = fetch_data()
filtered = df.copy()          # 이후 사이드바 필터용

# ────────────────────────────── 사이드바(예시)
st.sidebar.title("Filters")
# (필터 로직 필요하면 여기서 작성)

# ────────────────────────────── 헤더
st.markdown(
    """
    <div style="background-color:#702CB7;padding:12px 20px;border-radius:8px;margin-bottom:20px;">
        <h1 style="color:#A8D032;font-weight:bold;margin:0;text-align:center;">
            📊 CU Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# ────────────────────────────── 라벨별 평균 가격
col1, col2 = st.columns(2)

with col1:
    st.subheader("라벨별 평균 가격")
    df_label = filtered.copy()
    df_label["label"] = df_label["label"].fillna("없음")
    lbl_df = (
        df_label.groupby("label")["price"].mean().reset_index(name="avg_price")
    )
    bar1 = (
        alt.Chart(lbl_df)
        .mark_bar()
        .encode(
            x=alt.X("label:N", sort=alt.SortField("avg_price", "descending"), title="Label"),
            y=alt.Y("avg_price:Q", title="평균 가격"),
            tooltip=["label", "avg_price"]
        )
    )
    st.altair_chart(bar1, use_container_width=True)

# ────────────────────────────── 프로모션 태그별 상품 수
with col2:
    st.subheader("1+1, 2+1 상품 개수")
    pt_df = (
        filtered.assign(promotion_tag=filtered["promotion_tag"].fillna("없음"))
        .groupby("promotion_tag").size().reset_index(name="count")
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

# ────────────────────────────── 워드클라우드 2종
col3, col4 = st.columns(2)

with col3:
    st.subheader("Tag 키워드 워드클라우드")
    tags_series = filtered["tag"].dropna().astype(str).str.strip()
    tags_series = tags_series[tags_series != ""]
    if tags_series.empty:
        st.write("표시할 태그 데이터가 없습니다.")
    else:
        tag_counts = tags_series.value_counts().head(100).to_dict()
        st.write(f"- 워드클라우드용 단어 개수: {len(tag_counts)}")
        wc = WordCloud(
            font_path=FONT_PATH,
            width=400, height=200,
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
        st.write(f"- 워드클라우드용 단어 개수: {len(name_counts)}")
        wc2 = WordCloud(
            font_path=FONT_PATH,
            width=400, height=200,
            background_color="white", max_words=100
        ).generate_from_frequencies(name_counts)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.imshow(wc2, interpolation="bilinear")
        ax2.axis("off")
        st.pyplot(fig2)

st.markdown("---")
