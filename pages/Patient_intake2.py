import streamlit as st
import sys, os

# DB 유틸 불러오기
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from DataBase.db_utils import fetch_one, execute_query

DB_PATH = "DataBase/project_db2.db"

st.markdown("## 프로필 등록")

patient_id = st.session_state.get("patient_id", None)
if not patient_id:
    st.error("❌ 환자 정보가 없습니다. 로그인 후 다시 시도해주세요.")
    st.stop()

# DB에서 기존 프로필 불러오기
patient = fetch_one(DB_PATH, """
    SELECT name, age, sex, height, weight, egfr, HSI, AST, ALT, FBG
    FROM patient_info
    WHERE patient_id=?
""", (patient_id,))

# 이름은 수정 불가
name = st.session_state.get("patient_name", patient.get("name") if patient else "")
st.text_input("이름", value=name or "", disabled=True)

# 기본 정보
col1, col2 = st.columns(2)
with col1:
    age_val = patient.get("age") if (patient and patient.get("age") is not None) else 0
    age = st.number_input("나이", min_value=0, max_value=120, step=1, value=int(age_val))
with col2:
    sex_val = patient.get("sex") if patient and patient.get("sex") is not None else 0
    sex = st.radio("성별", ["남", "여"], index=0 if sex_val == 1 else 1)

col3, col4 = st.columns(2)
with col3:
    height_val = patient.get("height") if (patient and patient.get("height") is not None) else 0.0
    height = st.number_input("키 (cm)", min_value=0.0, step=0.1, value=float(height_val))
with col4:
    weight_val = patient.get("weight") if (patient and patient.get("weight") is not None) else 0.0
    weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1, value=float(weight_val))

# 검사 수치
st.write("### 검사 수치 입력")
egfr = st.text_input("eGFR (mL/min/1.73㎡)", value=str(patient.get("egfr")) if patient and patient.get("egfr") is not None else "")
ast  = st.text_input("AST (IU/L)", value=str(patient.get("AST")) if patient and patient.get("AST") is not None else "")
alt  = st.text_input("ALT (IU/L)", value=str(patient.get("ALT")) if patient and patient.get("ALT") is not None else "")
fbg  = st.text_input("공복혈당 (mg/dL)", value=str(patient.get("FBG")) if patient and patient.get("FBG") is not None else "")

# ---------------------------------------------
# 프로필 저장 버튼
# ---------------------------------------------
if st.button("프로필 저장"):
    sex_db = 1 if sex == "남" else 0

    # BMI 계산
    bmi = 0
    if float(height) > 0:
        bmi = float(weight) / ((float(height) / 100) ** 2)

    # HSI 자동 계산
    try:
        ast_val = float(ast) if ast else 0
        alt_val = float(alt) if alt else 0
        fbg_val = float(fbg) if fbg else 0

        if ast_val > 0:
            hsi_calc = 8 * (alt_val / ast_val) + bmi + (2 if sex_db == 0 else 0)
            if fbg_val > 0:
                hsi_calc += (fbg_val / 100)
            hsi_calc = round(hsi_calc)   # 정수로 반올림
        else:
            hsi_calc = None
    except Exception:
        hsi_calc = None

    execute_query(DB_PATH, """
        INSERT OR REPLACE INTO patient_info
        (patient_id, name, age, sex, height, weight, egfr, HSI, AST, ALT, FBG,
         phq9, birth_date, first_visit_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE((SELECT phq9 FROM patient_info WHERE patient_id=?),0),
                COALESCE((SELECT birth_date FROM patient_info WHERE patient_id=?),''),
                COALESCE((SELECT first_visit_date FROM patient_info WHERE patient_id=?),''))
    """, (patient_id, name, age, sex_db, height, weight, egfr, hsi_calc, ast, alt, fbg,
          patient_id, patient_id, patient_id))

    st.session_state["edit_mode"] = False
    st.session_state["saved"] = True

    if hsi_calc is not None:
        st.success(f"{name} 환자 프로필이 저장되었습니다. ✅ (HSI 자동 계산: {hsi_calc})")
    else:
        st.success(f"{name} 환자 프로필이 저장되었습니다. (HSI 계산 불가: AST/ALT 값 필요)")

if st.session_state.get("saved", False):
    if st.button("닫기"):
        st.session_state["saved"] = False 
        st.switch_page("pages/Patient_intake1.py")
