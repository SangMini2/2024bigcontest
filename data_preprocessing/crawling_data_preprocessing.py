import pandas as pd
from tqdm import tqdm
import re

data_path = "/Users/min/workspace/Jeju_LLM/data/crawling_final.csv"
output_path = "/Users/min/workspace/Jeju_LLM/data/ex.csv"

df = pd.read_csv(data_path, index_col=0)

basic_info = [] # 기본 정보(주소, 전화번호, 편의 등)
menu = [] # 메뉴
visitor_review = [] # 방문자 리뷰 (이 키워드를 선택한 인원)
basic_info_set = {"주소", "영업시간", "찾아가는길", "전화번호", "홈페이지", "편의", "TV방송정보", "가격표", "모두", '블로그', '스마트스토어', '인스타그램', '예약'} 
break_cnt = 0

for i in tqdm(range(len(df))):
    if df.loc[i, 'crawling'] != "X":
        menu_dic = dict()
        basic_dic = dict()
        visitor_dic = dict()       
        
        for thing in eval(df.loc[i, 'crawling']):
            lst = thing.split('\n')
            lst = [item for item in lst if item != "펼쳐보기"]
            flag = 1
            if '대표' in lst: # 대표를 없애주며 -> '000원'이 무조건 짝수번째에 오게 만든다.
                while True:
                    try:
                        lst.remove('대표')
                    except Exception:
                        break
            
            '''메뉴인지 찾고, 가공'''
            for idx, a in enumerate(lst):
                if (idx % 2 == 1) and (not '원' in a):
                    flag = 0
                    break

            if flag==1:
                for new_idx in range(len(lst) // 2):
                    menu_dic[lst[2*new_idx]] = lst[2*new_idx + 1]

            
            '''기본 정보(주소, 편의, 전화번호 등'''
            if thing.startswith('주소'): # 기본 정보 가지고 오는 코드 완성해야 함
                key = '주소'
                value = []
                for b in lst[1:]:
                    b = b.strip()
                    if b != "영업시간 수정 제안하기" and b != "접기":
                        b = re.sub("복사", "", b)
                        
                        if b in basic_info_set:
                            basic_dic[key] = value
                            key = b
                            value = []
                        else:
                            if b:
                                value.append(b)
                
                basic_dic[key] = value # 마지막 남은거 털기 -> 왜냐면 '주소: ~~~, 전화번호: ~~' 순서니까
                
                '''가격표 조정 & 가격표 정보를 menu 정보에 넣기'''
                if '가격표' in basic_dic:
                    if '가격표 이미지로 보기' in basic_dic['가격표']:
                        basic_dic['가격표'].remove('가격표 이미지로 보기')
                    
                    for l in range(len(basic_dic['가격표']) // 2):
                        menu_dic[basic_dic['가격표'][2*l]] = basic_dic['가격표'][2*l + 1]
                    
                    del basic_dic['가격표']
                
                '''전화번호 딱 전화번호만 string 받게 만들기!'''
                if '전화번호' in basic_dic:
                    if '안내' in basic_dic['전화번호']:
                        basic_dic['전화번호'].remove('안내')
                    # if '펼쳐보기' in basic_dic['전화번호']:
                    #     basic_dic['전화번호'].remove('펼쳐보기')
                        
                    basic_dic['전화번호'] = basic_dic['전화번호'].pop()
                
                
                '''인스타그램 같은게 홈페이지 내에 들어가 있는 경우, 새로운 key로 등장하는 것을 없애기 위해. 해당 구분 ex) 홈페이지: [url, "인스타그램"], 인스타그램: [url]'''
                remove_keys = []
                for key1, val1 in basic_dic.items():
                    if not val1:
                        remove_keys.append(key1)
                
                for remove_key in remove_keys:
                    del basic_dic[remove_key]
                
                
                '''모두, 블로그, 인스타그램, 스마트스토어 을 "홈페이지"로 통일 시키자!'''
                if '모두' in basic_dic:
                    basic_dic['홈페이지'] = basic_dic.pop('모두')
                
                elif '블로그' in basic_dic:
                    basic_dic['홈페이지'] = basic_dic.pop('블로그')
                    
                elif '인스타그램' in basic_dic:
                    basic_dic['홈페이지'] = basic_dic.pop("인스타그램")
                    
                elif '스마트스토어' in basic_dic:
                    basic_dic['홈페이지'] = basic_dic.pop("스마트스토어")
            
            '''visitor review'''
            if "이 키워드를 선택한 인원" in lst: # '객실/사이트 전체' 라는 부분이 인덱스 0번에 나올 수 있다. 펜션 같은 경우에는 추가 됨
                check_lst = []
                for c_idx, c in enumerate(lst):
                    if c == '이 키워드를 선택한 인원':
                        check_lst.append(c_idx)
                
                for d in check_lst:
                    visitor_dic[lst[d-1]] = lst[d+1]
            
        if menu_dic:
            menu.append(menu_dic)
        else:
            menu.append(None)
        
        if visitor_dic:
            visitor_review.append(visitor_dic)
        else:
            visitor_review.append(None)
        
        if basic_dic:
            basic_info.append(basic_dic)
        else:
            basic_info.append(None)
    
    else:
        basic_info.append(None)
        menu.append(None)
        visitor_review.append(None)

df['basic_info'] = basic_info
df['menu'] = menu
df['visitor_review'] = visitor_review


# 여기서 부터는 따로 column 만들기

from collections import defaultdict

dic = defaultdict(int)
convince = []
time = []
number = []
homepage = []
address = []

for info in basic_info:
    if isinstance(info, dict):
        if '편의' in info:
            convince.append(info['편의'])
        else:
            convince.append(None)
        
        if '영업시간' in info:
            time.append(info['영업시간'])
        else:
            time.append(None)
            
        if '전화번호' in info:
            number.append(info['전화번호'])
        else:
            number.append(None)
        
        if '홈페이지' in info:
            homepage.append(info['홈페이지'])
        else:
            homepage.append(None)
            
        if '주소' in info:
            address.append(info['주소'][0])
        else:
            address.append(None)
    else:
        convince.append(None)
        time.append(None)
        number.append(None)
        homepage.append(None)
        address.append(None)
        
        
df['편의'] = convince
df['영업시간'] = time
df['전화번호'] = number
df['홈페이지'] = homepage
df['location'] = address

df.to_csv(output_path)

# naver_type 합쳐주기

change_dic = {"한정식": "한식", "육류,고기요리": "고기", "돼지고기구이": "고기", "카페,디저트": "카페", '생선회': '해산물', '해물,생선요리': '해산물',
              '요리주점': '술집', "맥주,호프": '술집', '포장마차': '술집', '포장마차': "술집", "이자카야": '술집'}


df.naver_type = df.naver_type.apply(lambda x: change_dic[x] if isinstance(x, str) and x in change_dic else x)
df.reset_index(inplace=True, drop=True)
df.to_csv(output_path)