# 📊 Streamlit 대시보드

CU 상품 데이터를 Django API에서 불러와 시각화하는 Streamlit 기반의 대시보드입니다.

## 📦 사용 기술

- Streamlit
- pandas
- requests
- matplotlib
- wordcloud

## 🚀 실행 방법

### 1. 가상환경 및 패키지 설치

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> 필요한 패키지: `streamlit`, `requests`, `pandas`, `wordcloud`, `matplotlib`

### 2. 대시보드 실행

```bash
streamlit run dashboard.py
```

대시보드 접속: [http://localhost:8501](http://localhost:8501)

## 🔗 연결된 Django API

```
http://localhost:8000/api/products/
```

- JSON 응답 구조 기반으로 시각화 진행
- 가격/카테고리 기반 시각화만 사용 (`launch_date` 없음)

## 📊 시각화 항목

| 항목 | 설명 |
|------|------|
| 💵 가격 히스토그램 | 가격 분포 확인 |
| 🎚️ 가격 슬라이더 필터 | 원하는 가격 범위로 필터링 |
| 🏷️ Label 분포 | 증정, 1+1 등 프로모션 유형별 상품 수 |
| 🎯 Promotion Tag 빈도 | 가장 많이 등장하는 프로모션 유형 |
| 🧩 Tag 워드클라우드 | 태그 기반 트렌드 키워드 시각화 |


## 🎒 향후 개선 사항

- 검색창 필터 추가
- 상품 이미지 카드화
- Django 서버와 통합 배포 (Docker 등)
