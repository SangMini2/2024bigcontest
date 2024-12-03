import streamlit as st
from lib import check_pos
from chat import conversation

if 'first' not in st.session_state:
    st.session_state['first'] = True

if 'in_valid' not in st.session_state:
    st.session_state['in_valid'] = False

st.sidebar.title("✔️ 현재 위치 입력란 ✔️")

with st.sidebar:
    current_location = st.text_input("현재 주소/시작 주소를 입력하세요", key='current_location')
    if not st.session_state['current_location']:
        st.sidebar.write("정확한 주소를 입력하셔야 합니다!")
    # 주소 확정 버튼
    if current_location:
        with st.spinner('주소를 확인 중!!'):
            y, x, jibun, road = check_pos(st.session_state.current_location)
            if (x, y) != (0, 0):
                flag = 1
            else:
                flag = 0
        st.session_state['first'] = False
        if flag:
            st.sidebar.write("\n")
            st.sidebar.success(f"✅ **입력 완료!** ✅")

            st.sidebar.write("\n위의 시작 위치를 기반으로 맛집 추천이 진행됩니다!")
            st.sidebar.write("혹시 주소를 재설정하고 싶으시다면, **주소를 재입력**하시면 됩니다!")
            st.session_state['in_valid'] = True
        
        else:
            st.sidebar.error("❌ **주소가 올바르지 않습니다. 다시 입력해주세요!** ❌")
            st.session_state['in_valid'] = False
        
    elif not st.session_state['first']:
        st.sidebar.write("✘ 받아온 입력값이 없습니다 ✘")
        st.session_state['in_valid'] = False
        # st.sidebar.error(f"✘ 받아온 입력값이 없습니다 ✘ **입력을 해주세요!!**")


description = """
안녕하세요, 현재 위치 또는 시작 위치 기반으로 제주도 맛집을 추천해드립니다 🙌<br>
편하게 질문해주세요.<br><br>
<img src="https://www.agoda.com/wp-content/uploads/2024/07/Jeju-Island-1244x700.jpg">
"""

# 💬
st.title("🤖 제주 맛집 추천 Bot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": description}]

for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.chat_message(msg["role"]).write(msg["content"])
    else:
        st.chat_message(msg['role']).markdown(msg['content'], unsafe_allow_html=True)

# 사용자가 위치 안넣고, 질문하려고 할 때?
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    # 
    # if st.session_state['in_valid'] == True and ('제주' in jibun or '제주' in road):
    output = conversation(prompt, st.session_state['in_valid'], st.session_state['current_location'])
    if len(output) == 3:
        response_list, response_image, response_raw = output

        response_content = f'### 🏠 총 추천해 드릴 가게: {len(response_list)}개 \n'
        for idx, response in enumerate(response_list):
            response_content += response
            if isinstance(response_image[idx], list):
                response_content += "\n[📷 가게 관련 사진]<br><br>"
                
                image_html = " ".join(f'<img src="{url}" width="200">' for url in response_image[idx])
                response_content += f"{image_html}<br><br>출처: 네이버 맵<br><hr>\n"
            
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.chat_message('assistant').markdown(response_content, unsafe_allow_html=True)
    else:
        st.session_state.messages.append({'role': "assistant", 'content': output})
        st.chat_message('assistant').write(output)
    # else:
    #     output = "주소가 올바르지 않습니다. 정확한 주소를 입력해주신 후, 다시 질문해주세요 😊"
    #     st.session_state.messages.append({'role': "assistant", 'content': output})
    #     st.chat_message('assistant').write(output)
    