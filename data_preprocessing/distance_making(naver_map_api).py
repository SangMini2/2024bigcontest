# 제주 > 시 > 동 > 읍 > 면 > 리
from naver_map_api_function import distance_duration
from collections import defaultdict
from tqdm import tqdm
import pandas as pd
import json


sinhan_df = pd.read_csv("신한카드 데이터 경로")
distance = defaultdict(dict)
check_set = {"시", "동", "읍", "면", "리"}

addr_set = set()
for i in tqdm(range(len(sinhan_df))):
    addr_lst = sinhan_df.iloc[i, 4].split()
    addr_text = ""
    for sub_addr in addr_lst[1:]:
        if sub_addr[-1] in check_set:
            addr_text += sub_addr + " "
        else:
          break
    addr_text = addr_text.strip()
    addr_set.add(addr_text)

addr_list = list(addr_set)

print(f"총 개수: {len(addr_list)}")

for start_addr in tqdm(addr_list):
  for end_addr in addr_list:
    if (start_addr == end_addr) or (start_addr in end_addr) or (end_addr in start_addr) or (("우도" in start_addr) and ("우도" in end_addr)):
        distance[start_addr][end_addr] = (0, 0)

    elif (("우도" in start_addr) and (not "우도" in end_addr)) or ((not "우도" in start_addr) and ("우도" in end_addr)):
        # 우도와 제주도를 분리
        # 우도에서 제주도는 못간다고 판단 : (-1, -1)은 가깝지 않은 것
        distance[start_addr][end_addr] = (-1, -1)
        distance[end_addr][start_addr] = (-1, -1)
    
    elif start_addr in distance[end_addr]:
        continue
    else:
      try:
        dis, dur = distance_duration(start_addr, end_addr)
        distance[start_addr][end_addr] = (dis, dur)
        distance[end_addr][start_addr] = (dis, dur)
      
      except Exception:
        # error가 나는 부분은 (-3, -3)으로 구분
        distance[start_addr][end_addr] = (-3, -3)
        distance[end_addr][start_addr] = (-3, -3)

with open("/Users/min/workspace/Jeju_LLM/distance2.json", 'w', encoding='utf-8') as f:
        json.dump(distance, f, ensure_ascii=False, indent=4)