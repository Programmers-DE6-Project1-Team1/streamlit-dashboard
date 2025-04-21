import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8000/api/products/"

st.title("📦 CU 상품 대시보드")

# 1. 데이터 불러오기
@st.cache_data
def fetch_data():
    response = requests.get(API_URL)
    if response.status_code != 200:
        st.error("❌ API 요청 실패")
        return pd.DataFrame()
    return pd.DataFrame(response.json())

df = fetch_data()

# 2. 텍스트 검색 필터
st.subheader("🔍 텍스트 검색")
keywords = st.text_input("검색 키워드 입력 (예: 햄버거 단호박)").strip().split()
if keywords:
    for keyword in keywords:
        df = df[
            df["product_name"].str.contains(keyword, case=False, na=False) |
            df["product_description"].str.contains(keyword, case=False, na=False)
        ]

# 3. 카테고리 필터
st.subheader("🎯 카테고리 필터")
with st.expander("🧩 필터 열기 / 닫기", expanded=True):
    tags = pd.Series(sum(df["tags"], [])).dropna().unique().tolist()
    promos = pd.Series(sum(df["promotion_tags"], [])).dropna().unique().tolist()
    labels = pd.Series(sum(df["labels"], [])).dropna().unique().tolist()

    c1, c2 = st.columns(2)
    with c1:
        selected_tags = st.multiselect("🧩 Tag", tags)
        selected_labels = st.multiselect("🏷️ Label", labels)
    with c2:
        selected_promos = st.multiselect("🎯 Promotion Tag", promos)

    if selected_tags:
        df = df[df["tags"].apply(lambda lst: any(t in selected_tags for t in lst))]
    if selected_promos:
        df = df[df["promotion_tags"].apply(lambda lst: any(p in selected_promos for p in lst))]
    if selected_labels:
        df = df[df["labels"].apply(lambda lst: any(l in selected_labels for l in lst))]

# 4. 가격 필터
st.subheader("💰 가격 필터")
if df.empty:
    st.warning("조건에 맞는 상품이 없습니다.")
    st.stop()
if df["price"].nunique() > 1:
    lo, hi = int(df["price"].min()), int(df["price"].max())
    lo, hi = st.slider("가격 범위", lo, hi, (lo, hi))
    df = df[(df["price"] >= lo) & (df["price"] <= hi)]
else:
    st.info(f"모든 상품 가격이 {df['price'].iloc[0]}원입니다.")

# 5. 결과 개수
tot = len(df)
st.markdown(f"✅ 총 {tot}개의 상품이 검색되었습니다.")
if tot == 0:
    st.warning("조건에 맞는 상품이 없습니다.")
    st.stop()

# 6. 페이지네이션
st.subheader("📄 페이지네이션")
pg_size = st.selectbox("페이지당 상품 수", [6, 12, 24], index=1)
pages = (tot - 1) // pg_size + 1
if "page" not in st.session_state:
    st.session_state.page = 1
if st.session_state.page > pages:
    st.session_state.page = 1
cur = st.session_state.page
cp = None
if pages <= 5:
    s, e = 1, pages
elif cur <= 3:
    s, e = 1, 5
elif cur >= pages - 2:
    s, e = pages - 4, pages
else:
    s, e = cur - 2, cur + 2
s, e = max(1, s), min(pages, e)
pr = range(s, e + 1)
nav = st.columns(len(pr) + 2)
with nav[0]:
    if cur > 1 and st.button("⬅️", key="prev"):
        cp = max(cur - 5, 1)
for i, p in enumerate(pr):
    with nav[i + 1]:
        if st.button(str(p), key=f"pg_{p}", disabled=(p == cur)):
            cp = p
with nav[-1]:
    if cur < pages and st.button("➡️", key="next"):
        cp = min(cur + 5, pages)
if cp and cp != cur:
    st.session_state.page = cp
    st.rerun()
page = st.session_state.page
slice_df = df.iloc[(page - 1) * pg_size : page * pg_size]

# 7. 상품 목록 출력
st.subheader("🖼️ 상품 목록")
cols = st.columns(3)
for i, (_, r) in enumerate(slice_df.iterrows()):
    with cols[i % 3]:
        # 뱃지 생성
        lab = ''.join([f"<span style='border:1px solid #e0c7a3; background:#ffe4b5; padding:4px 8px; border-radius:12px; margin:2px;'>🏷️ {x}</span>" for x in r.get('labels', [])])
        tag = ''.join([f"<span style='border:1px solid #a7d7c5; background:#d4f7dc; padding:4px 8px; border-radius:12px; margin:2px;'>🧩 {x}</span>" for x in r.get('tags', [])])
        pro = ''.join([f"<span style='border:1px solid #ecb7b7; background:#f9d4d4; padding:4px 8px; border-radius:12px; margin:2px;'>🎯 {x}</span>" for x in r.get('promotion_tags', [])])
        badges = lab + tag + pro
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:15px;'>
            <div style='text-align:center;'>
                <img src='{r['image_url']}' style='height:180px; object-fit:contain; border-radius:8px;' />
                <div style='margin-top:10px; display:flex; justify-content:center; flex-wrap:wrap;'>{badges}</div>
            </div>
            <div style='margin-top:15px;'>
                <div style='font-size:18px; font-weight:bold; margin-bottom:8px;'>{r['product_name']}</div>
                <div style='margin-bottom:6px;'>💰 {r['price']}원</div>
                <div style='margin-bottom:6px; white-space:normal; word-break:break-word;'>📝 {r['product_description']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
