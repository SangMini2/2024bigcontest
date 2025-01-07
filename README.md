# 2024bigcontest
생성형 AI분야(제주도 맛집 추천)

![image](https://github.com/user-attachments/assets/7812eda1-fbc8-4ade-bc00-bca6914e3380)

## 설명
- 제주도 내 핫플레이스 맛집을 추천하는 대화형 AI 모델 개발
- LLM을 활용해 개발한 AI 모형에 기반해야 하며, 사용자가 입력하는 자연어(한국어)에 알맞은 맛집을 추천
- 추천 대상 가맹점은 신한카드에 등록된 가맹점 중 매출 상위 9,252개 요식업종(음식점, 카페 등) 가맹점으로 제한

## 데이터
- 신한 카드 데이터(요식업종 가맹점)
- 크롤링 데이터
    - Naver Place의 정보

## 사용한 Tools
- Gemini 1.5 flash
- Naver Maps
    - Geocodings
    - Directions5
- Streamlit

## 추천에 사용한 정보
- 사용자의 현재 위치 기반, 특정 거리 및 시간 내 가게 추천
- Naver Place
    - 편의 시설
    - 메뉴
    - 사용자 리뷰


정성 평가 시연 동영상: https://youtu.be/K6GdK2e5FTk
