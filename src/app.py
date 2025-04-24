import streamlit as st
from dashboard import view_dashboard
from slider import view_product_search

# ───────────────────────── 공통 설정
st.set_page_config(page_title="CU 통합 대시보드", layout="wide")


def render_sidebar():
    # 헤더
    st.sidebar.markdown("""
      <div style="padding:16px 0; text-align:center;">
        <h2 style="margin:0; color:#702CB7;">📊 CU 통합 대시보드</h2>
        <p style="margin:4px 0 0; font-size:14px; color:#555;">
          상품 데이터를 시각화하고 검색해 보세요.
        </p>
      </div>
      <hr/>
      <style>
        /* 버튼 공통 스타일 */
        button[kind="secondary"] {
          width:100% !important;
          padding:10px !important;
          margin:4px 0 !important;
          border:2px solid #702CB7 !important;
          border-radius:8px !important;
          background-color:#FFFFFF !important;
          color:#702CB7 !important;
          font-weight:600 !important;
        }
        /* hover */
        button[kind="secondary"]:hover {
          background-color:#702CB7 !important;
          color:#FFFFFF !important;
        }
        /* 클릭 후 활성화 상태 */
        button[kind="secondary"][aria-pressed="true"] {
          background-color:#702CB7 !important;
          color:#FFFFFF !important;
          border-color:#702CB7 !important;
        }
      </style>
    """, unsafe_allow_html=True)

    # 초기 state
    if "view" not in st.session_state:
        st.session_state.view = "CU 대시보드"

    # 버튼 렌더링
    if st.sidebar.button("CU 대시보드", key="btn-dashboard"):
        st.session_state.view = "CU 대시보드"
    if st.sidebar.button("상품검색", key="btn-search"):
        st.session_state.view = "상품검색"

    return st.session_state.view


def main():
    page = render_sidebar()
    if page == "CU 대시보드":
        view_dashboard()
    else:
        view_product_search()


if __name__ == "__main__":
    main()
