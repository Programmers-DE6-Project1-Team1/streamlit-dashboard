# app.py   ──  Streamlit 단일 파일(멀티-뷰)

import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform, pathlib

# ────────────────────────────── 공통 설정
st.set_page_config(page_title="CU 통합 대시보드", layout="wide")
API_BASE      = "http://localhost:8000/api"
PRODUCTS_URL  = f"{API_BASE}/products/"
PRODUCTS_ALL  = f"{API_BASE}/products/all/"
TAGS_URL      = f"{API_BASE}/tags/"
LABELS_URL    = f"{API_BASE}/labels/"
PROMOS_URL    = f"{API_BASE}/promotion-tags/"

# ────────────────────────────── OS별 한글 폰트 찾기
def find_korean_font() -> str | None:
    sys = platform.system()
    candidates = (
        [r"C:\Windows\Fonts\malgun.ttf"]
        if sys == "Windows" else
        ["/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/AppleGothic.ttf"]
        if sys == "Darwin" else
        ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf"]
    )
    for p in candidates:
        if pathlib.Path(p).exists():
            return p
    return None

FONT_PATH = find_korean_font()

# ────────────────────────────── 유틸
@st.cache_data(ttl=300)
def fetch_products_all() -> pd.DataFrame:
    data = requests.get(PRODUCTS_ALL, timeout=40).json()
    items = data if isinstance(data, list) else data.get("results", [])
    df = pd.DataFrame(items)

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

    df.drop(columns=["labels", "promotion_tags", "tags"], inplace=True, errors="ignore")
    return df


@st.cache_data
def load_filter_options():
    def fetch_all(url):
        res = requests.get(url, params={"page_size": 1000}).json()
        items = res.get("results", res) if isinstance(res, dict) else res
        return [x.get("name") for x in items if isinstance(x, dict) and "name" in x]
    return fetch_all(TAGS_URL), fetch_all(LABELS_URL), fetch_all(PROMOS_URL)


# ────────────────────────────── ① CU 대쉬보드
def view_dashboard():
    df = fetch_products_all()
    filtered = df.copy()

    # 헤더
    st.markdown(
        """
        <div style="background-color:#702CB7;padding:12px 20px;border-radius:8px;margin-bottom:20px;">
            <h1 style="color:#A8D032;font-weight:bold;margin:0;text-align:center;">
                📊 CU Dashboard
            </h1>
        </div>""",
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2 = st.columns(2)

    # ── 라벨별 평균가 (좌측, 초록 그라데이션)
    with col1:
        st.subheader("라벨별 평균 가격")
        df_l = filtered.copy()
        df_l["label"] = df_l["label"].fillna("없음")
        lbl_df = df_l.groupby("label")["price"].mean().reset_index(name="avg_price")

        bar1 = (
            alt.Chart(lbl_df)
            .mark_bar()
            .encode(
                x=alt.X("label:N", sort=alt.SortField("avg_price", "descending")),
                y=alt.Y("avg_price:Q", title="평균 가격"),
                tooltip=["label", "avg_price"],
                color=alt.Color(
                    "avg_price:Q",
                    scale=alt.Scale(
                        domain=[lbl_df["avg_price"].min(), lbl_df["avg_price"].max()],
                        range=["#A8D032", "#006400"]  # 연두 → 짙은 초록
                    ),
                    legend=None
                ),
            )
        )
        st.altair_chart(bar1, use_container_width=True)

    # ── 프로모션 태그별 개수 (우측, 보라 그라데이션)
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
                color=alt.Color(
                    "count:Q",
                    scale=alt.Scale(
                        domain=[pt_df["count"].min(), pt_df["count"].max()],
                        range=["#D6B3FF", "#5E00B3"]  # 연보라 → 진한 보라
                    ),
                    legend=None
                ),
            )
        )
        st.altair_chart(bar2, use_container_width=True)

    st.markdown("---")

    # ── 워드클라우드 2종
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Tag 키워드 워드클라우드")
        tags_series = filtered["tag"].dropna().astype(str).str.strip()
        tags_series = tags_series[tags_series!=""]
        if tags_series.empty:
            st.write("표시할 태그 데이터가 없습니다.")
        else:
            tag_counts = tags_series.value_counts().head(100).to_dict()
            wc = WordCloud(font_path=FONT_PATH,width=400,height=200,
                        background_color="white",max_words=100
                        ).generate_from_frequencies(tag_counts)
            fig, ax = plt.subplots(figsize=(8,4))
            ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
            st.pyplot(fig)

    with col4:
        st.subheader("상품명 워드클라우드")
        names = filtered["product_name"].dropna().astype(str).str.strip()
        if names.empty:
            st.write("표시할 상품명 데이터가 없습니다.")
        else:
            name_counts = names.value_counts().head(100).to_dict()
            wc2 = WordCloud(font_path=FONT_PATH,width=400,height=200,
                            background_color="white",max_words=100
                        ).generate_from_frequencies(name_counts)
            fig2, ax2 = plt.subplots(figsize=(8,4))
            ax2.imshow(wc2, interpolation="bilinear"); ax2.axis("off")
            st.pyplot(fig2)

    st.markdown("---")


# ────────────────────────────── ② 상품 검색
def view_product_search():
    st.title("📦 CU 상품 대시보드")

    tags_all, labels_all, promos_all = load_filter_options()

    # 세션 초기값
    st.session_state.setdefault("page", 1)
    st.session_state.setdefault("prev_filters", {})

    # ── 필터 UI
    st.subheader("🔍 상품 검색 및 필터")
    search = st.text_input("상품명·설명 검색", key="search")
    with st.expander("🧩 카테고리·프로모션", expanded=False):
        sel_tags   = st.multiselect("Tag", tags_all,   key="tags")
        sel_labels = st.multiselect("Label", labels_all, key="labels")
        sel_promos = st.multiselect("Promotion", promos_all, key="promos")

    filter_base = {
        "search": search,
        "tags__name": sel_tags,
        "labels__name": sel_labels,
        "promotion_tags__name": sel_promos,
    }

    # ── 필터 변경 시 가격 범위 재계산
    curr_filters = (search, tuple(sel_tags), tuple(sel_labels), tuple(sel_promos))
    if curr_filters != st.session_state.prev_filters:
        st.session_state.page = 1
        r = requests.get(PRODUCTS_URL, params={**filter_base, "page":1, "page_size":1})
        if r.ok:
            agg = r.json().get("results", {})
            st.session_state.min_price = agg.get("min_price", 0)
            st.session_state.max_price = agg.get("max_price", 0)
        else:
            st.session_state.min_price = st.session_state.max_price = 0
        st.session_state.prev_filters = curr_filters

    # ── 가격 슬라이더
    st.subheader("💰 가격 범위")
    min_p = st.session_state.get("min_price", 0)
    max_p = st.session_state.get("max_price", 0)
    if min_p == max_p:
        st.info(f"가격: ₩{min_p:,} (모든 상품 동일)")
        price_min, price_max = min_p, max_p
    else:
        price_min, price_max = st.slider(
            "가격", min_value=min_p, max_value=max_p,
            value=(min_p, max_p), key="price_range"
        )

    # ── 페이지당 수
    page_size = st.selectbox("페이지당 상품 수", [6,12,24], index=1, key="page_size")

    # ── 상품 호출
    page = st.session_state.page
    params = {
        **filter_base,
        "price_min": price_min, "price_max": price_max,
        "page": page, "page_size": page_size,
    }
    resp = requests.get(PRODUCTS_URL, params=params)
    if not resp.ok:
        st.error(f"API 오류: {resp.status_code}")
        st.stop()
    res   = resp.json()
    count = res.get("count", 0)
    items = res.get("results", {}).get("results", []) if isinstance(res.get("results"), dict) else []
    max_page = (count - 1)//page_size + 1 if page_size else 1

    # ── 네비게이션
    nav_l, nav_c, nav_r = st.columns([2,3,2])
    with nav_l:
        st.button("⬅️ 이전", disabled=page<=1, on_click=lambda: st.session_state.__setitem__("page", max(page-1,1)))
    with nav_c:
        st.markdown(f"<div style='text-align:center;font-size:18px;font-weight:600;line-height:38px;'>페이지 {page} / {max_page}</div>", unsafe_allow_html=True)
    with nav_r:
        st.button("다음 ➡️", disabled=page>=max_page, on_click=lambda: st.session_state.__setitem__("page", min(page+1,max_page)))

    # ── 통계
    stats_l, stats_r = st.columns(2)
    stats_l.markdown(f"✅ **총 {count:,}개**")
    stats_r.markdown(f"페이지당 **{page_size}개**")

    # ── 상품 카드
    if not items:
        st.warning("🚨 조건에 맞는 상품이 없습니다.")
    else:
        st.subheader("🖼️ 상품 목록")
        cols = st.columns(3)
        for idx, it in enumerate(items):
            with cols[idx % 3]:
                badges = "".join(
                    f"<span style='border:1px solid #ccc;padding:4px;border-radius:8px;margin:2px;font-size:12px;'>{sym} {v['name']}</span>"
                    for sym, key in [("🏷️","labels"),("🧩","tags"),("🎯","promotion_tags")]
                    for v in it.get(key, [])
                )
                st.markdown(
                    f"""
                    <div style='border:1px solid #e0e0e0;border-radius:12px;padding:12px;margin:6px;'>
                        <img src='{it['image_url']}' style='width:100%;height:180px;object-fit:cover;border-radius:8px;' />
                        <div style='margin:8px 0;display:flex;flex-wrap:wrap;justify-content:center;'>{badges}</div>
                        <div style='font-weight:600;'>{it['product_name']}</div>
                        <div style='color:#E74C3C;margin-bottom:4px;'>₩{it['price']:,}</div>
                        <div style='font-size:13px;color:#555;'>{it['product_description']}</div>
                    </div>""",
                    unsafe_allow_html=True
                )


# ────────────────────────────── 사이드바 네비게이션
page_choice = st.sidebar.radio(
    "📂 메뉴", ("CU 대쉬보드", "상품검색"), index=0
)

if page_choice == "CU 대쉬보드":
    view_dashboard()
else:
    view_product_search()
