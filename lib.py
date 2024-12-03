import re
import json
import requests
from typing import Tuple, Dict, List, Any

import pandas as pd

from config import START_COORDINATE_URL, END_COORDINATE_URL, CLIENT_ID, CLIENT_SECRET, DIRECTION_URL


def parse_address(address) -> str:
    loc_list = []
    for loc in address.split():
        if loc == '제주':
            loc_list.append(loc)
        elif re.match('.+[시동면읍리]$', loc):
            loc_list.append(loc)
        else:
            break
    return ' '.join(loc_list)



def load_crawling_data() -> pd.DataFrame:
    # 신한 데이터

    # JEJU_MCT_DATA_v2 -> sinhan_df
    crawling_path = "./data/shinhan_data+crawling_data.csv"
    crawling_df = pd.read_csv(crawling_path, index_col=0)
    crawling_df.visitor_review = crawling_df.visitor_review.apply(
        lambda x: {k.replace('\"', '').replace('\'', ''): v for k, v in eval(x).items()} if type(x) == str else x
    )
    crawling_df.편의 = crawling_df.편의.apply(lambda x: eval(x) if isinstance(x, str) else x)

    return crawling_df

def load_shinhan_data() -> pd.DataFrame:
    shinhan_path = "./data/JEJU_MCT_DATA_v2.csv"
    shinhan_df = pd.read_csv(shinhan_path, encoding='cp949')
    
    # 보기 쉽고, LLM이 이해하기 쉽게 column 명 change!
    change_dic = {"MON_UE_CNT_RAT": "monday", "TUE_UE_CNT_RAT": "tuesday", 'WED_UE_CNT_RAT': 'wednesday', "THU_UE_CNT_RAT": 'thursday',
              "FRI_UE_CNT_RAT": 'friday', "SAT_UE_CNT_RAT": 'saturday', "SUN_UE_CNT_RAT": 'sunday',
              "HR_5_11_UE_CNT_RAT": "5시부터 11시", "HR_12_13_UE_CNT_RAT": "12시부터 13시", "HR_14_17_UE_CNT_RAT": "14시부터 17시",
              "HR_18_22_UE_CNT_RAT": "18시부터 22시", "HR_23_4_UE_CNT_RAT": "23시부터 4시",
              "LOCAL_UE_CNT_RAT": "현지인 비율", "RC_M12_MAL_CUS_CNT_RAT": '남성 이용', 'RC_M12_FME_CUS_CNT_RAT': '여성 이용',
              "RC_M12_AGE_UND_20_CUS_CNT_RAT": '20대 이하', 'RC_M12_AGE_30_CUS_CNT_RAT': '30대', "RC_M12_AGE_40_CUS_CNT_RAT": "40대",
              "RC_M12_AGE_50_CUS_CNT_RAT": "50대", "RC_M12_AGE_OVR_60_CUS_CNT_RAT": "60대 이상",
              "UE_CNT_GRP": "frequency", "UE_AMT_GRP": "money", "UE_AMT_PER_TRSN_GRP": "avg_money_per_visited",
              "OP_YMD": "open_date", "MCT_NM": "매장명", "MCT_TYPE": "type", "ADDR": 'location'}
    shinhan_df = shinhan_df.rename(columns=change_dic)
    
    return shinhan_df


def load_distance_dict() -> Dict[str, Dict[str, Tuple[float, int]]]: # tuple(거리, 시간)
    with open('./data/distance.json', 'r', encoding='utf-8') as reader:
        distance_dict = json.load(reader)
    return distance_dict


def distance_duration(start: str, end: str) -> Tuple[float, int]:
    # 요청 헤더
    headers = {
      "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
      "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }

    # 좌표
    start_response = requests.get(START_COORDINATE_URL.format(start=start), headers=headers)
    end_response = requests.get(END_COORDINATE_URL.format(end=end), headers=headers)

    start_lat = start_response.json()['addresses'][0]['y']
    start_lon = start_response.json()['addresses'][0]['x']
    end_lat = end_response.json()['addresses'][0]['y']
    end_lon = end_response.json()['addresses'][0]['x']

    response = requests.get(
        DIRECTION_URL.format(end_lon=end_lon, end_lat=end_lat, start_lon=start_lon, start_lat=start_lat),
        headers=headers
    )
    data = response.json()
    distance = round(data['route']['traoptimal'][0]['summary']['distance'] / 1000, 1)
    duration = int(round(data['route']['traoptimal'][0]['summary']['duration'] / 60000))

    return distance, duration


def distance_time_restriction(current_location: str,
             distance_dict: Dict[str, Dict[str, Tuple[float, int]]],
             threshold: int,
             restriction_type: str) -> str:
    check_set = {"시", "동", "읍", "면", "리"}
    total_lst = []
    
    for name in current_location.split():
        if name[-1] in check_set:
            total_lst.append(name)
    # 없는 경우가 있을 수 있음 -> 뭐 제주시 00동 00읍 00면 00리 -> 없으면 오른족부터 시작해서 가지고 있는 것들만 해보자.
    # 즉, '상도리'가 없으니까 그 전인 '구좌읍'을 포함하고 있는 가게들 정보만 가져오기'
    
    total = ' '.join(total_lst)
    possible_location = []
    if restriction_type == 'distance':
        check_idx = 0
    elif restriction_type == 'time':
        check_idx = 1
    else:
        raise "Distance_time_restriction에서 type을 distance 또는 time으로 설정해주세요"
    
    if total in distance_dict:
        for key, val in distance_dict[total].items():
            if 0 <= val[check_idx] <= threshold:
                possible_location.append(key)
        
    else: # 데이터에 없는 경우
        while len(total_lst) > 1:
            total_lst = total[:-1]
            total = " ".join(total_lst)
            possible_location = []
            for key in distance_dict.keys():
                if total in key:
                    possible_location.append(key)
            
            if possible_location:
                break
    
    return "|".join(possible_location)
                    
    
        
def check_pos(pos: str):    
    pos_coordinate = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={pos}'
    headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }
    response = requests.get(pos_coordinate, headers=headers).json()
    
    if response['addresses']: # 찾을 수 있는 위치임
        lat = response['addresses'][0]['y']
        lon = response['addresses'][0]['x']
        jibun_address = response['addresses'][0]['jibunAddress']
        road_address = response['addresses'][0]['roadAddress']
        return lat, lon, jibun_address, road_address
    else:
        return 0, 0, 0, 0

def distance_duration(start: str, end: str, start_lat=None, start_lon=None, end_lat=None, end_lon=None) -> tuple[float, int]:
    
    # 요청 헤더
    headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }
    
    if start_lat is None or start_lon is None:
        start_coordinate = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={start}'
        
        # 좌표
        start_response = requests.get(start_coordinate, headers=headers)
        start_lat = start_response.json()['addresses'][0]['y']
        start_lon = start_response.json()['addresses'][0]['x']

    if end_lat is None or end_lon is None:
        end_coordinate = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={end}'
    
        # 좌표
        end_response = requests.get(end_coordinate, headers=headers)
        end_lat = end_response.json()['addresses'][0]['y']
        end_lon = end_response.json()['addresses'][0]['x']

    direction_url = f'https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?goal={end_lon}%2C{end_lat}&start={start_lon}%2C{start_lat}'
    response = requests.get(direction_url, headers=headers)
    data = response.json()
    try:
        distance = round(data['route']['traoptimal'][0]['summary']['distance'] / 1000, 1)
        duration = int(round(data['route']['traoptimal'][0]['summary']['duration'] / 60000))
    except Exception: # 거리, 소요 시간을 못찾는 경우!
        distance = -1
        duration = -1

    return distance, duration


def parse_json(text: str) -> Dict:
    text = text.replace('```json', '')
    text = text.replace('`', '')
    try:
        result = json.loads(text)
    except:
        print(text)
        raise Exception
    return result
