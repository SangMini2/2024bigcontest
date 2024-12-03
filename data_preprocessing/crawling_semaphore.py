# 멀티프로세싱 -> 최종

# 만약 2개가 뜰 때, 어떻게 할지 코드
from multiprocessing import Pool, BoundedSemaphore
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
import time
import pandas as pd
import os


semaphore = BoundedSemaphore(4)
# 웹페이지 열기

def function(input):
    semaphore.acquire()
    try:
        restaurant_name_lst = []
        actual_name = []
        reputation_lst = []
        crawling_lst = []
        errors = []
        global_idx = 0
        types = []
        images = []
        lst = input[1]
        
        print(f"총 df의 수는??? {len(lst)}")
        
        wait_time = 5
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Headless 모드로 실행
        chrome_options.add_argument("--no-sandbox")  # 권한 문제 해결을 위해 추가
        chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 크기 문제 해결을 위해 추가
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        time.sleep(3)

        for idx, addr_name in tqdm(enumerate(lst)):
            # chrome_options = Options()
            # chrome_options.add_argument("--headless")  # Headless 모드로 실행
            # chrome_options.add_argument("--no-sandbox")  # 권한 문제 해결을 위해 추가
            # chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 크기 문제 해결을 위해 추가
            # chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
            # driver = webdriver.Chrome(options=chrome_options)

            driver.get(f"https://map.naver.com/p/search/{addr_name}")
            time.sleep(wait_time)
            restaurant_name_lst.append(addr_name)
            # error = ""
            try:
                iframes = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
                        )

                flag = 1
                error = ""
                if len(iframes) < 6:
                    iframe = iframes[-1]
                    WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it(iframe))
                    try:
                        place_bluelink = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place_bluelink.C6RjW, div.place_bluelink.N_KDL"))
                            )
                    except Exception:
                        flag = 0
                        error += "조건에 맞는 업체 없음/"
                    
                    if flag == 1:
                        try:
                            place_bluelink = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place_bluelink.C6RjW, div.place_bluelink.N_KDL"))
                                )
                            place_bluelink.click()
                            time.sleep(wait_time)

                            driver.switch_to.default_content()
                            time.sleep(wait_time)
                            
                            iframes = WebDriverWait(driver, 10).until(
                                    EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
                                )
                        
                        except TimeoutException:
                            error += 'Bluelink/'
                            flag = 0
                        except ElementClickInterceptedException: # 클릭이 안되었을 때 -> 이게 없는건가?
                            error += "searchIFrame click/"
                            flag = 0


                if flag:
                    entryIframe = iframes[-1]
                    WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it(entryIframe))
                    
                    '''Naver 기준 이름'''
                    try:
                        # 이름에 "div.place_bluelink.C6RjW" 가 들어가있었는데, 그러지 않아도 될듯?
                        act_name = WebDriverWait(driver, 7).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.GHAhO"))
                        )
                        actual_name.append(act_name.text)

                    except TimeoutException:
                        error += "name/"
                        actual_name.append(None)
                    
                    '''육류 / 한식 등 네이버 맵에서 정해 놓은 타입'''
                    try:
                        type_name = WebDriverWait(driver, 7).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.lnJFt"))
                        )
                        types.append(type_name.text)
                    except Exception:
                        error += "type/"
                        types.append(None)
                    
                    
                    '''이미지'''
                    try:    
                        image_info = WebDriverWait(driver, 7).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'img.K0PDV._div')))
                        image_subset = []
                        for image in image_info:
                            if image.get_attribute('src'):
                                image_subset.append(image.get_attribute('src'))
                        images.append(image_subset)
                        
                    except Exception:
                        images.append(None)
                        error += 'image/'

                    '''여기가 평점'''
                    try:
                        reputation = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.PXMot.LXIwF"))
                        )
                        # reputation = driver.find_element(By.CSS_SELECTOR, "span.PXMot.LXIwF")
                        reputation_lst.append(reputation.text)
                        error += "reputation pass/"

                    except TimeoutException: # 평점이 없는 경우
                        reputation_lst.append(None)
                    
                    '''영업 시간 체크하기 위해 영업시간 자세히 보기'''
                    try:
                        on_time = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.w9QyJ.vI8SM'))
                        )
                        on_time.click()
                        time.sleep(2)
                    except Exception:
                        error += "영업시간 click/"

                    # 전체 페이지 높이 확인
                    total_page_height = driver.execute_script("return document.body.scrollHeight;")

                    '''crawling 부분'''
                    
                    crawling = set()
                    
                    for _ in range(3):
                        try:
                            menus = WebDriverWait(driver, 7).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.place_section_content"))
                            )
                            for menu in menus:
                                crawling.add(menu.text)
                            
                            # 스크롤을 특정 만큼 내리기
                            driver.execute_script(f"window.scrollBy(0, {total_page_height});")
                            time.sleep(3)
                        
                        except TimeoutException:
                            crawling.add(addr_name)

                    crawling_lst.append(crawling)

                else:
                    images.append("X")
                    types.append("X")
                    crawling_lst.append("X")
                    actual_name.append("X")
                    reputation_lst.append("X")
            
            except Exception:
                error = "iframe search timeout error/"
                crawling_lst.append("X")
                actual_name.append("X")
                reputation_lst.append("X")
                images.append("X")
                types.append("X")
            
            errors.append(error)


            if idx % 100 == 99 or idx == (len(lst) - 1):
                tmp_df = pd.DataFrame({"name": restaurant_name_lst, "actual_name": actual_name, "reputation": reputation_lst, 
                                       'naver_type': types, "errors": errors, "crawling": crawling_lst, 'image': images})
                tmp_df.to_csv(f"/Users/min/workspace/Jeju_LLM/crawling_{input[0]}_{global_idx}.csv")
                print(f"\n------하나 완성! {input[0]}_{global_idx}번째 csv 만듦------ \| 크기는: {len(tmp_df)}")
                global_idx += 1
                
                errors = []
                restaurant_name_lst = []
                crawling_lst = []
                reputation_lst= []
                actual_name = []
                types = []
                images = []
                
                driver.quit()
                time.sleep(30)
                
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Headless 모드로 실행
                chrome_options.add_argument("--no-sandbox")  # 권한 문제 해결을 위해 추가
                chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 크기 문제 해결을 위해 추가
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
                driver = webdriver.Chrome(options=chrome_options)
                time.sleep(10)

    finally:
        semaphore.release()
        
if __name__ == "__main__":
    
    sinhan_df = pd.read_csv("/Users/min/workspace/Jeju_LLM/JEJU_MCT_DATA_v2.csv", encoding='cp949')
    print("=======데이터 추가=======")
    for i in range(len(sinhan_df)):
        if sinhan_df.loc[i, "ADDR"].strip() == "":
            sinhan_df.loc[i, "ADDR"] = "제주 제주시 외도일동 441-12 돈삼춘"
    
    check_lst = list()
    print("=======데이터 가공 중=======")
    for name in tqdm(set(sinhan_df['MCT_NM'])):
        step_df = sinhan_df[sinhan_df['MCT_NM'] == name].sort_values(by="YM", ascending=False).iloc[0, :]
        detail = step_df["ADDR"].split()
        name = step_df['MCT_NM']
        search_name = detail[1] + " " + detail[2] + " " + name

        check_lst.append(search_name)
    
    
    print(f"========전체 데이터 수: {len(check_lst)}==========")
    remove_df = pd.read_csv("/Users/min/workspace/Jeju_LLM/crawling_11_8.csv", index_col=0)
    
    print(f"========이미 크롤링 된 데이터는 제거 ! ! ! {len(remove_df)}========")
    for i in range(len(remove_df)):
        check_lst.remove(remove_df.loc[i, 'name'])
    
    
    print(f"========총 진행될 데이터 수: {len(check_lst)}========")
        
    
    num_process = 4
    print(f"이대로 하면 크롤링 끝날 때까지 남은 시간: {((len(check_lst) // num_process) / 50) * 35 / 60} 시간(한 번 저장에 35분 걸린다고 가정)")
    
    print(f"=======Multiprocessing 시작 & num_process: {num_process}=======")
    
    lst = []
    p = len(check_lst) // num_process
    for l in range(num_process):
        if l == num_process - 1:
            print(f"{l * p} ~")
            lst.append((l, check_lst[l * p:]))
        else:
            print(f"{l*p} ~ {p*(l+1)}")
            lst.append((l, check_lst[l * p: p * (l+1)]))


    pool = Pool(processes=num_process) 

    pool.map(function, lst)
