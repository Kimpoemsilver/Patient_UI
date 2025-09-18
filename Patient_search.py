import streamlit as st

st.set_page_config(page_title="환자 조회", page_icon="🩺", layout="centered")

DEMO_MODE = True
NEXT_PAGE_PATH = "pages/Consultation.py"

dummy_id = {"dsaintprofessor", "kimsingni"}

def search_in_dummy(patient_id:str) -> bool:
    if not patient_id:
    # patient_id가 빈 문자열이거나 None 등으로 입력 X라면,
        return False
    return patient_id in dummy_id
    # if 구문 안에서 return을 쓰면 함수 실행이 즉시 종료됨.


col1, col2 = st.columns([6,2])
with col1:
    st.title("환자 아이디 조회")
    patient_id = st.text_input("환자 아이디", placeholder="아이디를 입력하세요.")

with col2:
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    search_clicked = st.button("검색", use_container_width=True)


if search_clicked:
    if not patient_id:
        st.error("환자 아이디를 입력해주세요.")
        st.stop()
    if DEMO_MODE:
        found = search_in_dummy(patient_id)
        if found:
            st.session_state["patient_id"] = patient_id
            st.switch_page(NEXT_PAGE_PATH)
        else:
            st.error("등록된 아이디가 아닙니다.")

    else:
        st.warning("현재 DEMO MODE가 꺼져있지만, DB 연동이 되어있지 않네요오")
        # DB자리