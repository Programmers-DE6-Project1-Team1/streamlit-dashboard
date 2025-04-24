# 📊 Streamlit CU 대시보드

CU 편의점 상품 데이터를 Django REST API로부터 가져와 시각화 및 검색을 지원하는 Streamlit 기반 대시보드입니다.

---

## 📁 파일 구조

```
streamlit-dashboard/
├── app.py          # 메인 진입점 (dashboard.py, slider.py 합치기)
├── dashboard.py    # CU 대시보드 뷰 (라벨별, 프로모션별 시각화 + 워드클라우드)
├── slider.py       # 상품 검색 & 필터(검색창, 슬라이더, 페이징)
├── requirements.txt
└── README.md
```

---

## 🚀 실행 방법

1. 가상환경 설정 및 패키지 설치
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate    # Windows
   pip install -r requirements.txt
   ```

2. Streamlit 앱 실행
   ```bash
   streamlit run app.py
   ```

3. 브라우저에서 접속
   ```
   http://localhost:8501
   ```

---

## 📦 사용 기술

- Streamlit  
- pandas  
- requests  
- altair  
- matplotlib  
- wordcloud

---

## 🔗 연결된 Django API

```
http://localhost:8000/api/products/
http://localhost:8000/api/products/all/
http://localhost:8000/api/tags/
http://localhost:8000/api/labels/
http://localhost:8000/api/promotion-tags/
```

---

## 🆕 주요 업데이트

1. **파일 분리 & 통합 진입점**  
   - `dashboard.py` (대시보드 뷰) / `slider.py` (상품검색 뷰) 분할  
   - `app.py`에서 두 뷰를 사이드바 네비게이션으로 전환

2. **사이드바 네비게이션**  
   - `st.sidebar.radio` → 라디오 버튼을 CSS로 "버튼형" 스타일 적용  
   - 보라색(#702CB7) 테두리/글자 → hover 및 선택 상태에서 보라 배경+흰 글씨 유지

3. **한글 폰트 자동 감지**  
   - Windows/macOS/Linux 환경에서 적절한 한글 폰트를 자동으로 찾아 워드클라우드에 적용

4. **예외 처리 강화**  
   - API 응답 `404` 시 "조건에 맞는 상품이 없습니다" 경고 후 함수 종료  
   - 기타 오류(`!resp.ok`) 시 `st.error` + `st.stop()` 처리

5. **워크플로우 개선**  
   - 첫 로드 시 가격(min/max) 자동 계산  
   - 가격 슬라이더, 페이지 네비게이션, 통계 요약 추가

---

## 📊 시각화 항목

| 항목                        | 설명                                |
|---------------------------|------------------------------------|
| 💵 라벨별 평균 가격        | "BEST", "NEW" 등 라벨별 평균가격 확인 |
| 🎯 프로모션별 상품 수      | "1+1", "2+1" 상품 개수 비교          |
| 🧩 Tag 키워드 워드클라우드 | 태그별 상위 100개 키워드 빈도 시각화   |
| 🔍 상품 검색 & 필터        | 검색창, 태그/라벨/프로모션 필터, 가격 슬라이더 |
| 📦 상품 목록 카드          | 썸네일, 라벨/태그/프로모션 배지, 가격/설명 표시|

---

## 🎒 향후 개선 사항

- Docker 컨테이너로 통합 배포  
- 인증/권한 관리 추가  
- 실시간 데이터 갱신 (WebSocket)  
- 차트 인터랙션(클릭/툴팁) 강화  


