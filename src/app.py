import streamlit as st
import pandas as pd
import requests
import altair as alt
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform, pathlib

# ───────────────────────── 공통 설정
st.set_page_config(page_title="CU 통합 대시보드", layout="wide")
API_BASE = "http://localhost:8000/api"
PRODUCTS_URL = f"{API_BASE}/products/"
PRODUCTS_ALL = f"{API_BASE}/products/all/"
TAGS_URL = f"{API_BASE}/tags/"
LABELS_URL = f"{API_BASE}/labels/"
PROMOS_URL = f"{API_BASE}/promotion-tags/"


# ───────────────────────── OS별 한글 폰트 찾기
def find_korean_font() -> str | None:
    sys = platform.system()
    if sys == "Windows":
        candidates = [r"C:\Windows\Fonts\malgun.ttf"]
    elif sys == "Darwin":
        candidates = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/AppleGothic.ttf",
        ]
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


# ───────────────────────── 데이터 로드 유틸
@st.cache_data(ttl=300)
def fetch_products_all() -> pd.DataFrame:
    data = requests.get(PRODUCTS_ALL, timeout=30).json()
    items = data if isinstance(data, list) else data.get("results", [])
    df = pd.DataFrame(items)

    def first_name(lst):
        if not lst:
            return None
        first = lst[0]
        return first["name"] if isinstance(first, dict) else str(first)

    for col, key in [("labels", "label"), ("promotion_tags", "promotion_tag"), ("tags", "tag")]:
        if col in df.columns:
            df[key] = df[col].apply(first_name)
    df.drop(columns=["labels", "promotion_tags", "tags"], errors="ignore", inplace=True)
    return df


@st.cache_data
def load_filter_options():
    def fetch_all(url):
        r = requests.get(url, params={"page_size": 1000})
        d = r.json()
        items = d.get("results", d) if isinstance(d, dict) else d
        return [x["name"] for x in items if isinstance(x, dict) and "name" in x]

    return fetch_all(TAGS_URL), fetch_all(LABELS_URL), fetch_all(PROMOS_URL)


# ───────────────────────── ① CU 대시보드 뷰
def view_dashboard():
    df = fetch_products_all()
    filtered = df.copy()
    st.markdown("""
      <div style="background-color:#702CB7;padding:12px 20px;border-radius:8px;margin-bottom:20px;">
        <h1 style="color:#A8D032;font-weight:bold;margin:0;text-align:center;">📊 CU Dashboard</h1>
      </div>""", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("라벨별 평균 가격")
        df_l = filtered.copy()
        df_l["label"] = df_l["label"].fillna("없음")
        lbl_df = df_l.groupby("label")["price"].mean().reset_index(name="avg_price")
        chart = (
            alt.Chart(lbl_df).mark_bar().encode(
                x=alt.X("label:N", sort=alt.SortField("avg_price", "descending")),
                y=alt.Y("avg_price:Q", title="평균 가격"),
                tooltip=["label", "avg_price"],
                color=alt.Color("avg_price:Q",
                                scale=alt.Scale(
                                    domain=[lbl_df["avg_price"].min(), lbl_df["avg_price"].max()],
                                    range=["#A8D032", "#006400"]),
                                legend=None)
            )
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.subheader("1+1, 2+1 상품 개수")
        pt_df = (
            filtered.assign(promotion_tag=filtered["promotion_tag"].fillna("없음"))
            .groupby("promotion_tag")
            .size()
            .reset_index(name="count")
        )
        chart2 = (
            alt.Chart(pt_df).mark_bar().encode(
                x=alt.X("promotion_tag:N", title="Promotion Tag"),
                y=alt.Y("count:Q", title="상품 수"),
                tooltip=["promotion_tag", "count"],
                color=alt.Color("count:Q",
                                scale=alt.Scale(
                                    domain=[pt_df["count"].min(), pt_df["count"].max()],
                                    range=["#D6B3FF", "#5E00B3"]),
                                legend=None)
            )
        )
        st.altair_chart(chart2, use_container_width=True)
    st.markdown("---")

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Tag 키워드 워드클라우드")
        s = filtered["tag"].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            st.write("표시할 태그 데이터가 없습니다.")
        else:
            freqs = s.value_counts().head(100).to_dict()
            wc = WordCloud(font_path=FONT_PATH, width=400, height=200,
                           background_color="white", max_words=100
                           ).generate_from_frequencies(freqs)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
    with c4:
        st.subheader("상품명 워드클라우드")
        s2 = filtered["product_name"].dropna().astype(str).str.strip()
        if s2.empty:
            st.write("표시할 상품명 데이터가 없습니다.")
        else:
            freqs2 = s2.value_counts().head(100).to_dict()
            wc2 = WordCloud(font_path=FONT_PATH, width=400, height=200,
                            background_color="white", max_words=100
                            ).generate_from_frequencies(freqs2)
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.imshow(wc2, interpolation="bilinear")
            ax2.axis("off")
            st.pyplot(fig2)
    st.markdown("---")


# ───────────────────────── ② 상품 검색 뷰
def view_product_search():
    st.title("📦 CU 상품 대시보드")
    tags, labels, promos = load_filter_options()
    st.session_state.setdefault("page", 1)
    st.session_state.setdefault("prev_filters", ())

    st.subheader("🔍 상품 검색 및 필터")
    q = st.text_input("상품명·설명 검색", key="search")
    with st.expander("태그 · 라벨 · 프로모션 필터"):
        sel_tags = st.multiselect("🧩 Tag", tags, key="tags")
        sel_labels = st.multiselect("🏷 Label", labels, key="labels")
        sel_promos = st.multiselect("🎯 Promotion", promos, key="promos")
    fb = {"search": q,
          "tags__name": sel_tags,
          "labels__name": sel_labels,
          "promotion_tags__name": sel_promos}

    curr = (q, tuple(sel_tags), tuple(sel_labels), tuple(sel_promos))
    if curr != st.session_state.prev_filters:
        st.session_state.page = 1
        agg = requests.get(PRODUCTS_URL,
                           params={**fb, "page": 1, "page_size": 1})
        if agg.status_code == 404:
            st.warning("조건에 맞는 상품이 없습니다.")
            return
        elif not agg.ok:
            st.error(f"API 오류(agg): {agg.status_code}")
            st.stop()
        data = agg.json().get("results", {})
        st.session_state.min_price = data.get("min_price", 0)
        st.session_state.max_price = data.get("max_price", 0)
        st.session_state.prev_filters = curr

    st.subheader("💰 가격 범위")
    lo, hi = st.session_state.min_price, st.session_state.max_price
    if lo == hi:
        st.info(f"가격: ₩{lo:,} (모두 동일)")
        pmin, pmax = lo, hi
    else:
        pmin, pmax = st.slider("가격",
                               min_value=lo, max_value=hi,
                               value=(lo, hi),
                               key="price_range")

    size = st.selectbox("페이지당 상품 수", [6, 12, 24], index=1, key="page_size")
    pg = st.session_state.page

    resp = requests.get(PRODUCTS_URL,
                        params={**fb,
                                "price_min": pmin,
                                "price_max": pmax,
                                "page": pg,
                                "page_size": size})
    if resp.status_code == 404:
        st.warning("조건에 맞는 상품이 없습니다.")
        return
    if not resp.ok:
        st.error(f"API 오류: {resp.status_code}")
        st.stop()

    d = resp.json()
    cnt = d.get("count", 0)
    items = (d.get("results", {}).get("results", [])
             if isinstance(d.get("results"), dict)
             else d.get("results", []))
    maxp = (cnt - 1) // size + 1 if size else 1

    l, c, r = st.columns([2, 3, 2])
    with l:
        st.button("⬅️ 이전", disabled=pg <= 1, on_click=lambda: st.session_state.__setitem__("page", max(pg - 1, 1)))
    with c:
        st.markdown(f"<div style='text-align:center;font-size:18px;font-weight:600;'>페이지 {pg} / {maxp}</div>",
                    unsafe_allow_html=True)
    with r:
        st.button("다음 ➡️", disabled=pg >= maxp,
                  on_click=lambda: st.session_state.__setitem__("page", min(pg + 1, maxp)))
    a, b = st.columns(2)
    a.markdown(f"✅ **총 {cnt:,}개**")
    b.markdown(f"페이지당 **{size}개**")
    if not items:
        st.warning("조건에 맞는 상품이 없습니다.")
    else:
        st.subheader("🖼️ 상품 목록")
        cols = st.columns(3)
        for i, it in enumerate(items):
            with cols[i % 3]:
                badges = "".join(
                    f"<span style='border:1px solid #ccc; padding:4px; border-radius:8px; margin:2px; font-size:12px;'>{sym} {v['name']}</span>"
                    for sym, key in [("🏷️", "labels"), ("🧩", "tags"), ("🎯", "promotion_tags")]
                    for v in it.get(key, [])
                )
                st.markdown(f"""
                    <div style='border:1px solid #e0e0e0; border-radius:12px; padding:12px; margin:6px;'>
                      <img src='{it['image_url']}' style='width:100%; height:180px; object-fit:cover; border-radius:8px;'/>
                      <div style='display:flex; flex-wrap:wrap; justify-content:center; margin:8px 0;'>{badges}</div>
                      <div style='font-weight:600;'>{it['product_name']}</div>
                      <div style='color:#E74C3C; margin-bottom:4px;'>₩{it['price']:,}</div>
                      <div style='font-size:13px; color:#555;'>{it['product_description']}</div>
                    </div>""", unsafe_allow_html=True)


# ───────────────────────── 사이드바 네비게이션 (버튼형, 세션 스테이트 유지)
def render_sidebar():
    st.sidebar.markdown("""
      <div style="padding:16px 0; text-align:center;">
        <h2 style="margin:0; color:#702CB7;">📊 CU 통합 대시보드</h2>
        <p style="margin:4px 0 0; font-size:14px; color:#555;">
          상품 데이터를 시각화하고 검색해 보세요.
        </p>
      </div>
      <hr/>
      <style>
        /* 기본 버튼 스타일 */
        button[kind="secondary"] {
          width: 100% !important;
          padding: 8px 12px !important;
          margin: 4px 0 !important;
          border: 2px solid #702CB7 !important;
          border-radius: 8px !important;
          background-color: #FFFFFF !important;
          color: #702CB7 !important;
          font-weight: 600 !important;
          text-align: center !important;
        }
        /* hover 상태 */
        button[kind="secondary"]:hover {
          background-color: #702CB7 !important;
          color: #FFFFFF !important;
        }
        /* 활성화 상태 (클릭 후 선택된 상태) */
        button[kind="secondary"].active,
        button[kind="secondary"][aria-pressed="true"] {
          background-color: #702CB7 !important;
          color: #FFFFFF !important;
          border: 2px solid #702CB7 !important;
        }
      </style>
    """, unsafe_allow_html=True)

    MENU = ["CU 대시보드", "상품검색"]
    if "view" not in st.session_state:
        st.session_state.view = MENU[0]
    if "active_button" not in st.session_state:
        st.session_state.active_button = MENU[0]

    # 버튼 생성 및 클릭 시 상태 업데이트
    for idx, name in enumerate(MENU):
        button_key = f"btn-{name}"
        if st.sidebar.button(name, key=button_key):
            st.session_state.view = name
            st.session_state.active_button = name

    # JavaScript로 active 클래스 동적 추가
    active_button = st.session_state.active_button
    st.sidebar.markdown(f"""
      <script>
        function updateActiveButton() {{
          // 모든 버튼 선택
          const buttons = document.querySelectorAll('button[kind="secondary"]');
          buttons.forEach(button => {{
            // 클래스 초기화
            button.classList.remove("active");
            // 버튼의 aria-label에서 텍스트 추출
            const label = button.getAttribute("aria-label") || "";
            const buttonText = label.split(" ").slice(0, -2).join(" ").trim();
            // 현재 active_button과 비교하여 active 클래스 추가
            if (buttonText === "{active_button}") {{
              button.classList.add("active");
            }}
          }});
        }}

        // 초기 로드 시 실행
        setTimeout(updateActiveButton, 100);

        // 리렌더링 시 실행
        const observer = new MutationObserver(() => {{
          setTimeout(updateActiveButton, 100);
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});
      </script>
    """, unsafe_allow_html=True)


# ───────────────────────── 메인
def main():
    render_sidebar()
    if st.session_state.view == "CU 대시보드":
        view_dashboard()
    else:
        view_product_search()


if __name__ == "__main__":
    main()
