import streamlit as st
import sys, os
import pandas as pd

# DB 유틸 불러오기
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from DataBase.db_utils import fetch_all, execute_query

DB_PATH = "DataBase/project_db2.db"

st.set_page_config(page_title="프로필", page_icon="🧑‍⚕️", layout="wide")

# 로그인 상태 확인
if not st.session_state.get("is_logged_in", False):
    st.error("잘못된 접근입니다. 먼저 로그인해주세요.")
    st.stop()

# 현재 로그인된 patient_id 가져오기
patient_id = st.session_state.get("patient_id", None)
if not patient_id:
    st.error("❌ 환자 정보가 없습니다. 로그인 후 접근해주세요.")
    st.stop()

# 환자 기본 정보 불러오기
profile = fetch_all(DB_PATH, """
    SELECT name, age, sex, height, weight, egfr, HSI, AST, ALT, FBG, phq9
    FROM patient_info
    WHERE patient_id=?
""", (patient_id,))

if not profile:
    st.error("DB에 환자 정보가 없습니다. 회원가입부터 진행해주세요.")
    st.stop()

info = profile[0]
name = info.get("name", st.session_state.get("patient_name", ""))

st.title(f"{name}님 프로필")

# 프로필이 비어있는지 확인
fields = ["age", "sex", "height", "weight", "egfr", "AST", "ALT", "FBG", "phq9"]
empty_fields = all(info.get(f) is None for f in fields)

if empty_fields:
    st.info("아직 프로필이 등록되지 않았습니다. 기본 정보와 PHQ-9 설문을 입력해주세요.")

    # -------------------------
    # 기본 정보 입력
    # -------------------------
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("나이", min_value=0, max_value=120, step=1)
        sex = st.radio("성별", ["남", "여"], horizontal=True)
    with col2:
        height = st.number_input("키 (cm)", min_value=0.0, step=0.1)
        weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1)

    col3, col4 = st.columns(2)
    with col3:
        egfr = st.number_input("eGFR (mL/min/1.73㎡)", min_value=0.0, step=0.1)
    with col4:
        ast = st.number_input("AST (IU/L)", min_value=0.0, step=0.1)
        alt = st.number_input("ALT (IU/L)", min_value=0.0, step=0.1)
        fbg = st.number_input("공복혈당 (mg/dL)", min_value=0.0, step=0.1)

    # -------------------------
    # PHQ-9 설문
    # -------------------------
    st.markdown("### 📝 PHQ-9 설문")
    phq9_questions = [
        "1. 일상적인 일에 대한 흥미나 즐거움이 거의 없음",
        "2. 기분이 가라앉거나 우울하거나 희망이 없음",
        "3. 잠들기 어렵거나 자주 깸, 또는 잠을 너무 많이 잠",
        "4. 피곤하거나 기운이 거의 없음",
        "5. 식욕이 감소하거나 과식함",
        "6. 자신에 대해 나쁘게 느낌, 실패자라고 생각하거나 자신/가족을 실망시킴",
        "7. 신문 읽기, TV 시청 등 집중하기 어려움",
        "8. 다른 사람이 알아챌 정도로 너무 느리게 움직이거나 말을 하거나, 반대로 너무 안절부절못함",
        "9. 죽는 것이 더 낫다고 생각하거나 자해할 생각을 함"
    ]
    phq9_scores = []
    for i, q in enumerate(phq9_questions):
        score = st.radio(
            q,
            [0, 1, 2, 3],
            format_func=lambda x: ["전혀 없음(0)", "며칠 동안(1)", "절반 이상(2)", "거의 매일(3)"][x],
            horizontal=True,
            key=f"phq9_{i}"
        )
        phq9_scores.append(score)
    total_score = sum(phq9_scores)
    st.markdown(f"**총점: {total_score} / 27**")

    # -------------------------
    # 저장 버튼
    # -------------------------
    if st.button("프로필 저장"):
        sex_val = 1 if sex == "남" else 0

        # BMI 계산 (키는 cm 단위 → m 단위 변환)
        bmi = 0
        if height > 0:
            bmi = weight / ((height / 100) ** 2)

        # HSI 계산 (FBG 반영 포함)
        if ast > 0:
            hsi_calc = 8 * (alt / ast) + bmi + (2 if sex_val == 0 else 0)
            if fbg > 0:
                hsi_calc += (fbg / 100)
            hsi_calc = round(hsi_calc)   # ✅ 정수 반올림
        else:
            hsi_calc = None

        # DB 업데이트
        execute_query(DB_PATH, """
            UPDATE patient_info
            SET age=?, sex=?, height=?, weight=?, egfr=?, AST=?, ALT=?, FBG=?, HSI=?, phq9=?
            WHERE patient_id=?
        """, (age, sex_val, height, weight, egfr, ast, alt, fbg, hsi_calc, total_score, patient_id))

        if hsi_calc is not None:
            st.success(f"프로필과 PHQ-9 설문이 저장되었습니다. ✅ (HSI 자동 계산: {hsi_calc})")
        else:
            st.success("프로필과 PHQ-9 설문이 저장되었습니다. (HSI 계산 불가: AST/ALT 값 필요)")
        st.rerun()


else:
    # 기존 프로필 표시
    def safe(val, unit=""):
        return f"{val}{unit}" if val is not None else "-"

    left, right = st.columns([6, 2])
    with right:
        if st.button("수정"):
            st.session_state["edit_mode"] = True
            st.session_state["selected_patient"] = info
            st.switch_page("pages/Patient_intake2.py")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**나이**: {safe(info['age'])}")
        st.write(f"**성별**: {'남' if info['sex']==1 else '여'}")
    with col2:
        st.write(f"**키**: {safe(info['height'], ' cm')}")
        st.write(f"**몸무게**: {safe(info['weight'], ' kg')}")

    st.markdown("### 검사 수치")
    st.write(f"- eGFR: {safe(info['egfr'], ' mL/min/1.73㎡')}")
    st.write(f"- HSI: {safe(info['HSI'])}")
    st.write(f"- AST: {safe(info['AST'], ' IU/L')}")
    st.write(f"- ALT: {safe(info['ALT'], ' IU/L')}")
    st.write(f"- FBG: {safe(info['FBG'], ' mg/dL')}")

    st.markdown("### PHQ-9 점수")
    st.write(f"- 총점: {safe(info['phq9'], ' / 27')}")

if st.button("돌아가기"):
    st.session_state["is_logged_in"] = True
    st.switch_page("pages/Dashboard.py")
