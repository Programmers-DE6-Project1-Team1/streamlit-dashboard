import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform, pathlib

# ───────────────────────── 공통 설정
API_BASE = "http://localhost:8000/api"
PRODUCTS_ALL = f"{API_BASE}/products/all/"


# ───────────────────────── OS별 한글 폰트 찾기
def find_korean_font() -> str | None:
    sys = platform.system()
    if sys == "Windows":
        candidates = [r"C:\Windows\Fonts\malgun.ttf"]
    elif sys == "Darwin":
        candidates = ["/System/Library/Fonts/AppleSDGothicNeo.ttc", "/System/Library/Fonts/AppleGothic.ttf"]
    else:
        candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        ]
    for p in candidates:
        if pathlib.Path(p).exists():
            return p
    return None


FONT_PATH = find_korean_font()


@st.cache_data(ttl=300)
def fetch_products_all() -> pd.DataFrame:
    raw = requests.get(PRODUCTS_ALL, timeout=30).json()
    items = raw if isinstance(raw, list) else raw.get("results", [])
    df = pd.DataFrame(items)

    def first_name(lst):
        if not lst: return None
        x = lst[0]
        return x["name"] if isinstance(x, dict) else str(x)

    for src, dst in [("labels", "label"), ("promotion_tags", "promotion_tag"), ("tags", "tag")]:
        if src in df.columns:
            df[dst] = df[src].apply(first_name)
    df.drop(columns=["labels", "promotion_tags", "tags"], errors="ignore", inplace=True)
    return df


def view_dashboard():
    df = fetch_products_all()
    st.markdown("""
      <div style="background-color:#702CB7;padding:12px 20px;border-radius:8px;margin-bottom:20px;">
        <h1 style="color:#A8D032;font-weight:bold;margin:0;text-align:center;">📊 CU Dashboard</h1>
      </div>""", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("라벨별 평균 가격")
        tmp = df.fillna({"label": "없음"}).groupby("label")["price"].mean().reset_index(name="avg_price")
        chart = (
            alt.Chart(tmp).mark_bar().encode(
                x=alt.X("label:N", sort=alt.SortField("avg_price", "descending")),
                y=alt.Y("avg_price:Q", title="평균 가격"),
                tooltip=["label", "avg_price"],
                color=alt.Color("avg_price:Q",
                                scale=alt.Scale(range=["#A8D032", "#006400"]),
                                legend=None)
            )
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.subheader("1+1, 2+1 상품 개수")
        pt = df.assign(promotion_tag=df["promotion_tag"].fillna("없음")) \
            .groupby("promotion_tag").size().reset_index(name="count")
        chart2 = (
            alt.Chart(pt).mark_bar().encode(
                x=alt.X("promotion_tag:N", title="Promotion Tag"),
                y=alt.Y("count:Q", title="상품 수"),
                tooltip=["promotion_tag", "count"],
                color=alt.Color("count:Q",
                                scale=alt.Scale(range=["#D6B3FF", "#5E00B3"]),
                                legend=None)
            )
        )
        st.altair_chart(chart2, use_container_width=True)
    st.markdown("---")

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Tag 키워드 워드클라우드")
        s = df["tag"].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            st.write("표시할 태그 데이터가 없습니다.")
        else:
            freqs = s.value_counts().head(100).to_dict()
            wc = WordCloud(font_path=FONT_PATH, width=400, height=200,
                           background_color="white", max_words=100) \
                .generate_from_frequencies(freqs)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wc, interpolation="bilinear");
            ax.axis("off")
            st.pyplot(fig)
    with c4:
        st.subheader("상품명 워드클라우드")
        s2 = df["product_name"].dropna().astype(str).str.strip()
        if s2.empty:
            st.write("표시할 상품명 데이터가 없습니다.")
        else:
            freqs2 = s2.value_counts().head(100).to_dict()
            wc2 = WordCloud(font_path=FONT_PATH, width=400, height=200,
                            background_color="white", max_words=100) \
                .generate_from_frequencies(freqs2)
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.imshow(wc2, interpolation="bilinear");
            ax2.axis("off")
            st.pyplot(fig2)
    st.markdown("---")
