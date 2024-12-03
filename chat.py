from typing import Optional
from copy import deepcopy
from random import sample, shuffle

import pandas as pd
import google.generativeai as genai

from config import GOOGLE_API_KEY
from prompt import DISTINGUISH_PROMPT, RECOMMEND_PROMPT, SEARCH_PROMPT
from lib import parse_json, load_shinhan_data, load_crawling_data, load_distance_dict, distance_time_restriction, distance_duration, check_pos


genai.configure(api_key=GOOGLE_API_KEY)
llm = genai.GenerativeModel("gemini-1.5-flash")
shinhan_data = load_shinhan_data()
crawling_data = load_crawling_data()
distance_dict = load_distance_dict()


def chat(prompt:str, input_text: str) -> str:
    prompt = prompt.format(query=input_text)
    response = llm.generate_content(prompt).text

    return response


def search_MCT(chat_response: str) -> str:
    jsoned = parse_json(chat_response)
    short_data = deepcopy(shinhan_data)
    final_operator_list = []
    
    for key, val in jsoned.items():
        if val:
            if type(val) == str:
                if 'open_date' in key:
                    continue
                else:
                    short_data = short_data[short_data[key].str.contains(val)]
            
            elif type(val) == dict:
                if val['operator'] in ['max', 'min']:
                    final_operator_list.append((val['value'], val['operator']))
                else:
                    if key == '이상':
                        short_data = short_data[short_data[val['value']] >= val['rate']]
                    elif key == '이하':
                        short_data = short_data[short_data[val['value']] <= val['rate']]
            
            elif type(val) == list:
                for value, operator, rate in val:
                    if operator == '이상':
                        short_data = short_data[short_data[value] >= rate]
                    elif operator == '이하':
                        short_data = short_data[short_data[value] <= rate]
                    else:
                        final_operator_list.append((value, operator))
    
    if len(short_data) == 0: # 없을 때
        return ""

    if final_operator_list:
        final_value, final_operator = final_operator_list.pop()
        if final_operator == 'max':
            answer = short_data.loc[short_data[final_value].idxmax()]['매장명']
        else:
            answer = short_data.loc[short_data[final_value].idxmin()]['매장명']

    else:
        answer_set = set(short_data['매장명'])
        answer = ", ".join(answer_set)
    
    return answer


def conversation(query: str, in_valid: bool, start_address: Optional[str] = None):
    if start_address == "":
        start_address = None
    response = chat(DISTINGUISH_PROMPT, query).strip()  # llm 사용 1번 -> 정성 평가/ 정량 평가 구분

    if '정량' in response:  # 정량 평가
        response = chat(SEARCH_PROMPT, query)  # llm 사용 2번 -> 정량 평가 답변 생성(제한 부분)
        answer = search_MCT(response)

        if len(answer) == 0:
            return "해당 조건에 해당 하는 식당을 찾을 수가 없습니다. 죄송합니다"
        return answer


    else:  # 정성 평가 -> llm을 통한 생성을 2번 사용할 수 있음
        if in_valid == False:
            return "주소를 입력해주세요!"
        response = chat(RECOMMEND_PROMPT, query)
        result = parse_json(response)
        rating = result.get('rating', None)
        concept = result.get('concept', None)
        restaurant_type = result.get('type', None)
        distance = result.get('distance', None)
        time = result.get('time', None)
        convenience = result.get("convenience", None)
        sub_df = crawling_data

        if rating is not None:
            sub_df = sub_df[sub_df.reputation >= rating]
        if restaurant_type is not None:
            sub_df = sub_df[sub_df.naver_type == restaurant_type]

        if concept is not None:
            sub_df = sub_df[sub_df.visitor_review.apply(
                lambda x: (x is not None) and (not pd.isna(x)) and all([c in x for c in concept])
            )]

        # 시간에 대한 언급이 없으면 20분 이내의 가게를 찾음 -> 거리는 조절 X. 거리는 그냥 있으면 필터링 하고, 아니면 그냥 놔두기
        if distance is not None:
            sub_df = sub_df[sub_df['name'].str.contains(distance_time_restriction(start_address, distance_dict, distance, 'distance'))]
        
        if time is None and time != -2:
            time = 20
            sub_df = sub_df[sub_df['name'].str.contains(distance_time_restriction(start_address, distance_dict, time, 'time'))]
        
        
        if convenience is not None:
            sub_df = sub_df[sub_df['편의'].apply(
                lambda x: all([(c in x) for c in convenience]) if isinstance(x, list) else False
            )]
        
        indices = [i for i in range(len(sub_df))]
        shuffle(indices)
        if not indices:
            return '조건에 맞는 가게가 없습니다 🥲'

        start_lat, start_lon, _, _ = check_pos(start_address)

        cnt = 0
        return_list = []
        return_image = []
        
        # 중복 제거
        duplication = set()

        for i, index in enumerate(indices):
            return_string = ""
            row = sub_df.iloc[index]
            location = row['location']
            
            end_lat, end_lon, _, _, = check_pos(location)
                
            if (end_lat, end_lon) == (0, 0): # End 위치를 찾을 수 없는 것
                continue
            cur_dis, cur_time = distance_duration(start_address, location, start_lat, start_lon, end_lat, end_lon)
            
            if (cur_dis, cur_time) == (-1, -1):
                continue
            
            if time != -2 and cur_time > time: # 20분이나 해당 시간이 넘으면, 없애기
                continue
            
            if distance is not None and cur_dis > distance:
                continue

            name = row['actual_name']
            if name in duplication:
                continue
            
            duplication.add(name)
            
            ratings = row['reputation']
            location = row['location']
            images = row['image']
            homepage = row['홈페이지']
            convenience = row['편의']
            
            concept_list = row['visitor_review']
            menu = row['menu']
            return_string += f" ### {cnt+1}. {name}\n"
            if (ratings is not None) and (not pd.isna(ratings)):
                return_string += f'- ⭐ 별점: {ratings}\n'
            else:
                return_string += '- ⭐ 별점: 비공개\n'
            return_string += f'- 🗺️ 주소: {location}\n'

            return_string += f'- 🛣️ 거리: {cur_dis}km ( 🚕 약 {cur_time} 분 소요 )\n'
            
            if homepage is not None and not pd.isna(homepage):
                return_string += f"- 🌐 홈페이지: {homepage}\n"
            
            if isinstance(convenience, list):
                return_string += f"\n [ℹ️ 편의]\n"
                for conv in convenience:
                    return_string += f" - {conv}\n"    
            
            if (menu is not None) and (not pd.isna(menu)):
                return_string += f'\n[📔 메뉴]\n'
                for name, price in list(eval(menu).items())[:5]:
                    return_string += f' - {name}: {price}\n'
            if concept_list is not None and not pd.isna(concept_list):
                return_string += f'\n[👥 유저️ 대표 리뷰]\n'
                for concept in concept_list.keys():
                    concept = concept.replace('\"', '').replace('\'', '')
                    return_string += f'  - {concept} ({concept_list[concept]}명)\n'
            
            return_list.append(return_string)
            
            if images:
                return_image.append(eval(images)[:3])
            else:
                return_image.append(None)
            
            cnt += 1
            
            if cnt == 3: break

        return return_list, return_image, response
