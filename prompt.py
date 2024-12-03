DISTINGUISH_PROMPT = '''
너는 질문이 정성 평가에 대한 질문인지, 정량 평가에 대한 질문인지 구분해야해.
각 평가에 대한 특징을 알려줄게.

정량 평가) 대체로 질문의 형태가 의문형. 조건들에 맞는 특정 가게를 찾아내야 하는 목적. 사용하는 데이터는 오직 신한 카드 데이터만 사용해.
정성 평가) 대체로 질문의 형태가 요청형. 현재 상황 또는 제한 사항에 맞는 가게들을 추천해줘야 하는 목적. 사용하는 데이터는 네이버 맵 데이터와 신한 카드 데이터를 사용할 수 있어.

평점 얘기가 나오면 '정성 평가'야.
만약 너가 질문이 정량 평가라고 판단한다면 '정량' 만 return 해줘.
만약 정성 평가라고 판단단했을 때 '정성' 만 return 해줘.
다른 표현은 생성하지마.

질문: {query}
'''


SEARCH_PROMPT = '''
# 너는 질문을 받아서 맛집 검색을 위한 조건을 찾아줘야 해.
# 조건은 총 11개의 타입을 가지고 있고, 각각 필요한 값은 아래에 정의되어 있어.

# 만약 헤당 정보에 대한 조건이 질문에 없다면, 해당 값을 null으로 표기해줘.

1. location
- string. 어떤 지역의 맛집인지에 대한 지역값
2. type
- 다음 값들 중 하나의 string: '가정식', '구내식당/푸드코트', '기사식당', '기타세계요리', '꼬치구이', '단품요리 전문', '도너츠', '도시락', '동남아/인도음식', '떡/한과', '맥주/요리주점', '민속주점', '베이커리', '부페', '분식', '샌드위치/토스트', '스테이크', '아이스크림/빙수', '야식', '양식', '일식', '주스', '중식', '차', '치킨', '커피', '패밀리 레스토랑', '포장마차', '피자', '햄버거'
3. weekday
  - List[List[str, str, float]], 요일에 대한 조건값
  - 형태: [['weekday_value', 'weekday_operator_value', 'weekday_rate'], ['weekday_value', 'weekday_operator_value', 'weekday_rate'], ...]
    - "weekday_value"는 다음 7개의 값 중 하나의 string: "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    - "weekday_operator"는 다음 4개의 값 중 하나의 string: "max", "min", "이상", "이하"
    - 'weekday_rate'는 비교할 수를 말하며 float. %로 나타나 있으면, 소수점으로 바꿔서 표기할 것 (operator가 'max' 또는 'min'이면 null 반환)
4. age
  - List[List[str, str, float]], 나이대에 대한 조건값
  - 형태: [['age_value', 'age_operator', 'age_rate'], ['age_value', 'age_operator', 'age_rate'], ...]
    - "age_value"는 다음 5개의 값 중 하나의 string: "20대 이하", "30대", "40대", "50대", "60대 이상"
    - "age_operator"는 다음 2개의 값 중 하나의 string: "max", "min", "이상", "이하"
    - 'age_rate'는 비교할 수를 말한다. %로 나타나 있으면, 소수점으로 바꿔서 표기할 것 (operator가 'max' 또는 'min'이면 null 반환)
5. local
  - dictionary 현지인 이용 비율에 대한 조건값
  - dictionary의 형태: {{"value": "local_value", "operator": "local_operator_value", 'rate': 'local_rate'}}
    - "local_bool"은 현지인 이용에 대한 내용이 있으면 '현지인 비율'
    - "local_operator"는 다음 2개의 값 중 하나의 string: "max", "min", "이상", "이하"
    - 'age_rate'는 비교할 수를 말하며 float. %로 나타나 있으면, 소수점으로 바꿔서 표기할 것 (operator가 'max' 또는 'min'이면 null 반환)
6. time
  - List[List[str, str, float]], 시간대 별 이용 비율에 대한 조건값
  - 형태: [['time_value', 'time_operator', 'time_rate'], ['time_value', 'time_operator', 'time_rate'], ...]
    - "time_value"는 다음 10개의 값 중 하나의 string: "5시부터 11시", "12시부터 13시", "14시부터 17시", "18시부터 22시", "23시부터 4시"
    - "time_operator"는 다음 2개의 값 중 하나의 string: "max", "min", "이상", "이하"
    - 'time_rate'는 비교할 수를 말하며 float. %로 나타나 있으면, 소수점으로 바꿔서 표기할 것 (operator가 'max' 또는 'min'이면 null 반환)
7. gender
  - dictionary 남녀 이용 비율에 대한 조건값
  - dictionary의 형태: {{"value": "gender_value", "operator": "gender_operator_value", 'rate': 'gender_rate'}}
    - "gender_value"는 다음 2개의 값 중 하나의 string: "남성 이용", "여성 이용"
    - "gender_operator"는 다음 2개의 값 중 하나의 string: "max", "min", "이상", "이하"
    - 'gender_rate'는 비교할 수를 말하며 float. %로 나타나 있으면, 소수점으로 바꿔서 표기할 것 (operator가 'max' 또는 'min'이면 null 반환)
8. open_date 
- string. 가게가 오픈한 날짜에 대한 날짜값
- 형태: yyyy.mm.dd
9. frequency (이용 건수 구간)
- string. "상위 10%", "10~25%", "25~50%", "50~75%", "75~90%", "90% 초과" 중 하나
10. money (이용 금액 구간)
- string. "상위 10%", "10~25%", "25~50%", "50~75%", "75~90%", "90% 초과" 중 하나
11. avg_money_per_visited (건당 평균 이용 금액 구간)
- string. "상위 10%", "10~25%", "25~50%", "50~75%", "75~90%", "90% 초과" 중 하나

# 최종 응답은 json 형태여야 하고, 다음과 같이 정의해야 해. 출력을 할 때, json 형태를 제외한 다른 내용 및 문자는 적지마.

{{
    "location":
    "type":
    "open_date":
    "frequency":
    "money":
    "avg_money_per_visited":
    "weekday":
    "age":
    "local":
    "time":
    "gender":
}}

# 만약 정보를 알 수 없는 필드 값은 null로 채워 넣어줘.

질문: {query}
'''


RECOMMEND_PROMPT = '''
# 너는 조건을 받아서 맛집 추천을 위한 조건을 찾아줘야 해
# 조건은 총 6개가 있고, 각각 필요한 타입은 아래에 정의되어 있어.
# 카페는 커피를 마시는 곳으로 밥을 먹는 곳이 아니다.

# 만약 헤당 정보에 대한 조건이 질문에 없다면, 해당 값을 null로 표기해줘.

1. rating
- float, 몇 점 이상 별점을 가진 가게를 찾기 위한 조건값

2. type
- string, 원하는 식당의 타입, 타입은 아래의 리스트 중 하나의 값을 가져야 해
    - 한식
    - 고기
    - 해산물
    - 카페
    - 치킨,닭강정
    - 중식당
    - 술집
    - 양식
    - 피자
    - 돈가스
    - 국수

3. concept
- List[string], 
- 설명: 유저가 원하는 해당 식당의 컨셉, 여러 컨셉의 값이 나올 수 있고, 컨셉 값은 ['친절해요', '가성비가 좋아요', '양이 많아요', '뷰가 좋아요', '혼밥하기 좋아요', '매장이 청결해요', '대화하기 좋아요', '혼술하기 좋아요', '직접 잘 구워줘요'] 값들만 가지고 구성해야 해! '직접적인 언급'이 있어야만 반환해.
- 추가 설명: 혼밥이란, 혼자 밥먹는 것을 말해. 가성비란, 가격대비 성능이 좋은 것을 말해. 혼술이란, 혼자 술먹는 것을 말해.
    
4. distance
- data type: int
- 설명: 현재 내위치에서 추천하는 가게까지 몇 km 안에 도착했으면 좋겠다는 정보야. 이에 대한 정보가 있으면 'km' 기준으로 정수형으로 반환, 그렇지 않으면 null 반환해줘

5. time
- data type: int
- 설명: 현재 위치에서부터 추천하는 가게까지 몇 분 안에 도착했으면 좋겠다는 정보야. 시간이 상관없다면 -2를 반환해줘. 시간 제한에 대한 정보가 있으면 '분' 기준으로 정수형으로 반환, 그렇지 않으면 null 반환해줘.

6. convenience
- type: List[string]
- 설명: 편의 시설에 관련된 정보야. 여러 편의 값이 나올 수 있고, 편의 값은 ['주차', '예약', '단체 이용 가능', '반려동물 동반', '유아의자', '무선 인터넷', '장애인 편의시설'] 값 중에서 결과가 나와야 해. 이들은 '직접적인 언급'이 있어야만 반환해. 되도록이면 너가 추론하지말고, 직접적인 언급을 기반으로 반환해줘.
- 추가 설명: 와이파이는 무선 인터넷이야


# 응답은 위 6개의 field를 가지는 json 형태로 만들어서 줘, 출력을 할 때, json 형태를 제외한 다른 내용 및 문자는 적지마.

질문: {query}
'''
