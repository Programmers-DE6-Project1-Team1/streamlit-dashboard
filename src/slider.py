import streamlit as st
import requests

# ───────────────────────── 공통 설정
API_BASE = "http://localhost:8000/api"
PRODUCTS_URL = f"{API_BASE}/products/"
TAGS_URL = f"{API_BASE}/tags/"
LABELS_URL = f"{API_BASE}/labels/"
PROMOS_URL = f"{API_BASE}/promotion-tags/"


@st.cache_data
def load_filter_options():
    def go(url):
        r = requests.get(url, params={"page_size": 1000})
        data = r.json()
        arr = data.get("results", data) if isinstance(data, dict) else data
        return [x["name"] for x in arr if isinstance(x, dict) and "name" in x]

    return go(TAGS_URL), go(LABELS_URL), go(PROMOS_URL)


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

    fb = {
        "search": q,
        "tags__name": sel_tags,
        "labels__name": sel_labels,
        "promotion_tags__name": sel_promos
    }
    curr = (q, tuple(sel_tags), tuple(sel_labels), tuple(sel_promos))
    if curr != st.session_state.prev_filters:
        st.session_state.page = 1
        agg = requests.get(PRODUCTS_URL, params={**fb, "page": 1, "page_size": 1})
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
        pmin, pmax = st.slider("가격", min_value=lo, max_value=hi, value=(lo, hi), key="price_range")

    size = st.selectbox("페이지당 상품 수", [6, 12, 24], index=1, key="page_size")
    pg = st.session_state.page

    resp = requests.get(PRODUCTS_URL, params={**fb,
                                              "price_min": pmin, "price_max": pmax, "page": pg, "page_size": size})
    if resp.status_code == 404:
        st.warning("조건에 맞는 상품이 없습니다.")
        return
    if not resp.ok:
        st.error(f"API 오류: {resp.status_code}")
        st.stop()

    d = resp.json()
    cnt = d.get("count", 0)
    items = (d.get("results", {}).get("results", [])
             if isinstance(d.get("results"), dict) else d.get("results", []))
    maxp = (cnt - 1) // size + 1 if size else 1

    l, c, r = st.columns([2, 3, 2])
    with l:
        st.button("⬅️ 이전", disabled=pg <= 1,
                  on_click=lambda: st.session_state.__setitem__("page", max(pg - 1, 1)))
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
