import streamlit as st
import requests

# API 엔드포인트
API_BASE = "http://localhost:8000/api"
PRODUCTS_URL = f"{API_BASE}/products/"
TAGS_URL = f"{API_BASE}/tags/"
LABELS_URL = f"{API_BASE}/labels/"
PROMOS_URL = f"{API_BASE}/promotion-tags/"

st.title("📦 CU 상품 대시보드")

# 1. 옵션 로드
@st.cache_data
def load_options():
    def fetch_all(url):
        r = requests.get(url, params={"page_size": 1000})
        data = r.json()
        items = data.get("results", data) if isinstance(data, dict) else data
        return [x.get("name") for x in items if isinstance(x, dict) and "name" in x]
    return fetch_all(TAGS_URL), fetch_all(LABELS_URL), fetch_all(PROMOS_URL)

tags_all, labels_all, promos_all = load_options()

# 2. 세션 초기값
st.session_state.setdefault("page", 1)
st.session_state.setdefault("prev_filters", {})

# 3. 필터 UI
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

# 4. 필터 변경 → 가격 범위 재계산
curr_filters = (search, tuple(sel_tags), tuple(sel_labels), tuple(sel_promos))
if curr_filters != st.session_state.prev_filters:
    st.session_state.page = 1
    r = requests.get(PRODUCTS_URL, params={**filter_base, "page": 1, "page_size": 1})
    if r.ok:
        agg = r.json().get("results", {})
        st.session_state.min_price = agg.get("min_price", 0)
        st.session_state.max_price = agg.get("max_price", 0)
    else:
        st.session_state.min_price = st.session_state.max_price = 0
    st.session_state.prev_filters = curr_filters

# 5. 가격 슬라이더
st.subheader("💰 가격 범위")
min_p = st.session_state.get("min_price", 0)
max_p = st.session_state.get("max_price", 0)
if min_p == max_p:
    st.info(f"가격: ₩{min_p:,} (모든 상품 동일)")
    price_min, price_max = min_p, max_p
else:
    price_min, price_max = st.slider(
        "가격",
        min_value=min_p,
        max_value=max_p,
        value=(min_p, max_p),
        key="price_range",
    )

# 6. 페이지당 수
page_size = st.selectbox("페이지당 상품 수", [6, 12, 24], index=1, key="page_size")

# 7. 상품 호출
page = st.session_state.page
params = {
    **filter_base,
    "price_min": price_min,
    "price_max": price_max,
    "page": page,
    "page_size": page_size,
}
resp = requests.get(PRODUCTS_URL, params=params)
if not resp.ok:
    st.error(f"API 오류: {resp.status_code}")
    st.stop()
res = resp.json()
count = res.get("count", 0)
items = res.get("results", {}).get("results", []) if isinstance(res.get("results"), dict) else []
max_page = (count - 1) // page_size + 1 if page_size else 1

# 8. 네비게이션 ---------------------------------
nav_l, nav_c, nav_r = st.columns([2, 3, 2])

def prev():
    st.session_state.page = max(page - 1, 1)

def nxt():
    st.session_state.page = min(page + 1, max_page)

with nav_l:
    st.button("⬅️ 이전", disabled=page <= 1, on_click=prev)
with nav_c:
    st.markdown(
        f"<div style='text-align:center; font-size:18px; font-weight:600; line-height:38px;'>페이지 {page} / {max_page}</div>",
        unsafe_allow_html=True,
    )
with nav_r:
    st.button("다음 ➡️", disabled=page >= max_page, on_click=nxt)

# 9. 통계
stats_l, stats_r = st.columns([1, 1])
with stats_l:
    st.markdown(f"✅ **총 {count:,}개**")
with stats_r:
    st.markdown(f"페이지당 **{page_size}개**")

# 10. 상품 목록 ---------------------------------
if not items:
    st.warning("🚨 조건에 맞는 상품이 없습니다.")
else:
    st.subheader("🖼️ 상품 목록")
    cols = st.columns(3)
    for idx, it in enumerate(items):
        with cols[idx % 3]:
            badges = "".join(
                f"<span style='border:1px solid #ccc; padding:4px; border-radius:8px; margin:2px; font-size:12px;'>{sym} {v['name']}</span>"
                for sym, key in [("🏷️", "labels"), ("🧩", "tags"), ("🎯", "promotion_tags")]
                for v in it.get(key, [])
            )
            st.markdown(
                f"""
                <div style='border:1px solid #e0e0e0; border-radius:12px; padding:12px; margin:6px;'>
                    <img src='{it['image_url']}' style='width:100%; height:180px; object-fit:cover; border-radius:8px;' />
                    <div style='margin:8px 0; display:flex; flex-wrap:wrap; justify-content:center;'>{badges}</div>
                    <div style='font-weight:600;'>{it['product_name']}</div>
                    <div style='color:#E74C3C; margin-bottom:4px;'>₩{it['price']:,}</div>
                    <div style='font-size:13px; color:#555;'>{it['product_description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
