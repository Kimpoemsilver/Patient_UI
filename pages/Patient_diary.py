import streamlit as st
from datetime import datetime
from google.cloud import translate
from google.oauth2 import service_account
from transformers import AutoTokenizer, AutoModel
from huggingface_hub import login


import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from DataBase.db_utils import fetch_one, fetch_all, execute_query

DB_PATH = "DataBase/project_db2.db"

st.set_page_config(page_title="하루점검", page_icon="💊", layout="wide")

# 로그인된 patient_id 가져오기
patient_id = st.session_state.get("patient_id")
if not patient_id:
    st.error("잘못된 접근입니다.")
    st.stop()

today_str = datetime.today().date().isoformat()

# DEMO_DAY_NUM_DOSE = int(st.session_state.get("Prescribed_num_dose", 3))

# 1. 하루 복용 횟수의 기준 (처방된 횟수 불러오기)
# prescription_date는 최신값 하나만 가져온다고 가정
row = fetch_one(DB_PATH, """
    SELECT day_drug, prescription_date
    FROM patient_predict
    WHERE patient_id = ?
    ORDER BY prescription_date DESC
    LIMIT 1
""", (patient_id,))
if row:
    PRESCRIBED_NUM_DOSE = int(row["day_drug"]) 
    prescription_date = row["prescription_date"]
else:
    PRESCRIBED_NUM_DOSE, prescription_date = 3, None  # default 값

BACK_PAGE_PATH = "pages/Dashboard.py"

SIDE_EFFECTS = {
    "S01" : ("입마름", "입안이 바싹 마르고 침이 잘 안 나와 물을 자주 마셔야 하는 느낌이 드나요?"),
    "S02" : ("졸림", "낮에도 자꾸 눈이 감기고 깨어 있기 힘들 정도로 졸리신가요?"),
    "S03" : ("불면", "밤에 잠이 잘 안 오거나 자주 깨서 숙면을 못 하고 있나요?"),
    "S04" : ("시야 흐림", "글씨나 사물이 뿌옇게 보여서 초점 맞추기가 어렵나요?"),
    "S05" :("두통", "머리가 무겁거나 지끈거리는 통증이 자주 생기나요?"),
    "S06" : ("변비", "변이 잘 안 나오거나 딱딱해서 힘들게 배변하시나요?"),
    "S07" : ("설사", "변이 묽고 하루에도 여러 번 화장실을 가시나요?"),
    "S08" : ("식욕 증가", "평소보다 배가 자주 고프고 음식을 많이 찾게 되시나요?"),
    "S09" : ("식욕 저하", "밥맛이 없고 음식을 잘 못 드시나요?"),
    "S10" : ("구역감/구토", "속이 울렁거리거나 토한 적이 있으신가요?"),
    "S11" : ("배뇨 문제", "소변이 잘 안 나오거나, 자주 마려운 느낌이 있으신가요?"),
    "S12" : ("성기능 문제", "성욕이 줄거나 성관계 시 어려움이 있으신가요?"),
    "S13" : ("가슴 두근거림", "특별한 이유 없이 심장이 빨리 뛰거나 두근거림을 느끼시나요?"),
    "S14" : ("기립 시 어지러움", "앉았다 일어나거나 갑자기 설 때 어지럽고 눈앞이 하얘지나요?"),
    "S15" : ("빙글빙글 도는 느낌", "주변이 돌거나 몸이 휘청거리는 어지럼증이 있으신가요?"),
    "S16" : ("발한", "특별히 덥지 않은데도 땀이 많이 나시나요?"),
    "S17" : ("체온 상승", "열이 나거나 몸이 평소보다 뜨겁게 느껴지나요?"),
    "S18" : ("떨림", "손이나 몸이 저절로 떨리거나 미세하게 흔들리나요?"),
    "S19" : ("지남력 장애", "지금이 언제인지, 여기가 어딘지 헷갈린 적이 있나요?"),
    "S20" : ("하품", "특별히 피곤하지 않아도 하품이 자주 나오나요?"),
    "S21" : ("체중 증가", "식습관 변화가 없는데도 체중이 늘고 있나요?"),
}
                              
# side_effect as se
# patient_daily as pd
if "pd_step" not in st.session_state:
    st.session_state.pd_step = 1
    st.session_state.side_eff_selected = []      # pd 2단계에서 선택한 부작용들
    st.session_state.side_eff_severity = {}      # pd 3단계 점수 {라벨: 1|2|3}
    st.session_state.emotion_text = ""           # pd 4단계: 자유 기록
    st.session_state.pd_saved = False            # pd 4단계: 저장 성공 여부

st.session_state.setdefault("daily_day_num_dose", None)
name = st.session_state.get("name", patient_id)

st.markdown(
    """
    <style>
    /* 전체 기본 글자 크게 */
    .stApp { font-size: 18px; }

    /* 헤더(제일 크게) */
    .sticky-header { position: sticky; top: 0; z-index: 9; }
    .header-badge {
        display:inline-block;
        padding: 10px 16px;
        border-radius: 18px;
        border: 2px solid #7e9dc5;
        background:#f7f7fb;
        font-weight: 800;
        font-size: 2rem;   /* ← 헤더 가장 큼 */
        line-height: 1.2;
    }

    /* 안내문/질문/선택박스 폰트 */
    .intro-text { font-size: 1.25rem; font-weight: 600; margin: 6px 0 18px; }
    .question-label { font-size: 1.4rem; font-weight: 700; margin-bottom: 10px; display:block; }
    div[data-baseweb="select"] { font-size: 1.2rem !important; }  /* select 안 글자 */

    /* /회 표시 글자 & 간격 미세조정 */
    .right-note { text-align:left; color:#777; font-size: 1.1rem; margin-left: -8px; }

    /* 버튼 글자 */
    .stButton > button { font-size: 1.1rem; padding: 0.4rem 1rem; }

    /* 체크박스(다음 단계에서 쓰일 수 있음) */
    div.stCheckbox > label > div:first-child {
        border-radius: 50% !important;
        width: 1.2em; height: 1.2em; border: 2px solid #888;
    }
    div.stCheckbox > label div[data-testid="stTickIcon"] svg { display: none; }
    div[role="checkbox"][aria-checked="true"] + div {
        background: #4aa5ad !important; border-color:#4aa5ad !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def diary_header():
    st.markdown(
        f"""
        <div class="sticky-header">
          <span class="header-badge">{name}님 하루점검</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # <div> ... </div>: 박스(블록) 단위로 나눌 때 사용
    # -> 이 ...안에 들어간 내용 전체를 하나의 구역으로 묶음.
    # 마지막에 </div>는 여기서 div 블록이 끝났다는 표시. 
    # <div> 안에 있는 class=...는 이 블록의 스타일을 적용해주는 것.
    # -> 블록에 sticky-header 스타일을 적용하겠다는 뜻.
    # <span> ... </spam>: 텍스트 같은 짧은 부분에 스타일을 적용할 때 사용. 
    # -> 여기서는 {name}님 하루점검이란느 글씨에만 header-badge 스타일을 적용하겠다는 뜻.
    # </span>은 여기까지가 span 영역이라는 표시.


def pd_step_1():
    diary_header()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="question-label">오늘 하루 동안 약을 얼마나 복용했나요?</span>', 
                unsafe_allow_html=True)

    col_1, col_2 = st.columns([6,4])
    with col_1:
    # col[0]: 첫 번째 열, col[1]: 두 번째 열, col[2]: 세 번째 열 ... ing
        cols = st.columns([10,1,3])
        st.markdown("<br>", unsafe_allow_html=True)
        with cols[0]:
            options = list(range(0, PRESCRIBED_NUM_DOSE + 1))
            day_num_dose_selected = st.selectbox(
                "",
                options,
                index=None,
                placeholder="선택",
                key="daily_day_num_dose",
                label_visibility="collapsed")

        with cols[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<p class='right-note'>/{PRESCRIBED_NUM_DOSE}회</p>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # <br>: 줄바꿈의 의미,여백을 억지로 버리고 싶을 때 넣음.
        if st.button("다음", key="btn_next_step1", use_container_width=False):
            if day_num_dose_selected is None: 
                st.error("복용 횟수를 선택해주세요.")
            else:
                st.session_state["final_day_num_dose"] = int(st.session_state.daily_day_num_dose)
                st.session_state.pd_step = 2
                st.rerun()
            # st.rerun() = 코드를 즉시 다시 실행해서, 
            # 바뀐 session_state 값이 화면에 바로 반영되도록 함.


def pd_step_2():
    diary_header()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="question-label">오늘, 약물 때문에 겪었다고 느끼는 증상이 아래에 있다면 체크해주세요.</span>', 
                unsafe_allow_html=True)

    num_cols = 5
    cols = st.columns(num_cols)
    for i, (code, (label, tip)) in enumerate(SIDE_EFFECTS.items()):
        with cols[i % num_cols]:
            checked = st.checkbox(label, key=f"se_{code}", help=tip)
    st.markdown("<br>", unsafe_allow_html=True)
    
    prev, spacer1, spacer1, next = st.columns([1,4,4,1])
    with prev:
        if st.button("이전", key="btn_prev_step2", use_container_width=False):
            st.session_state.pd_step = 1
            st.rerun()

    with next:
        if st.button("다음", key="btn_next_step2", use_container_width=False):
            selected = [code for code in SIDE_EFFECTS.keys() if st.session_state.get(f"se_{code}", False)]
            st.session_state.side_eff_selected = selected
            st.session_state.pd_step = 3 if selected else 4
            st.rerun()
    st.write("DEBUG: daily_day_num_dose =", st.session_state.get("daily_day_num_dose"))


def pd_step_3():
    selected = st.session_state.get("side_eff_selected", [])
    if not selected:
        st.session_state.pd_step = 4
        st.rerun()

    diary_header()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="question-label">다음 증상이 느껴지는 정도에 대해 1(약하게 느껴짐)~3(강하게 느껴짐) 점까지 체크해주세요.</span>', 
                unsafe_allow_html=True)

    side_eff_severity = st.session_state.setdefault("side_eff_severity", {})
    for code in selected:
        label, _ = SIDE_EFFECTS[code]
        side_eff_severity[code] = st.radio(
            label,  # 화면에는 label 보여줌
            [1, 2, 3],
            horizontal=True,
            index=None,
            key=f"sev_{code}",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    prev, spacer1, spacer2, next = st.columns([1,4,4,1])
    with prev:
        if st.button("이전", key="btn_prev_step3", use_container_width=False):
            st.session_state.pd_step = 2
            st.rerun()
    with next:
            if st.button("다음", key="btn_next_step3", use_container_width=False):
                missing = [code for code in selected if side_eff_severity.get(code) is None]
                if missing: 
                    st.error("모든 항목에 응답해주세요.")
                else:
                    st.session_state.pd_step = 4
                    st.rerun()

#DB 저장 함수
def save_to_db(phq9_score = None):

    # 입력값 확인
    day_num_dose_val = st.session_state.get("final_day_num_dose")
    if isinstance(day_num_dose_val, dict):  # dict가 들어가면 에러
        raise ValueError(f"❌ day_num_dose 값이 dict로 들어옴: {day_num_dose_val}")
    if day_num_dose_val is None:
        raise ValueError("❌ day_num_dose 값이 None 입니다. selectbox 입력이 안 된 것 같아요.")

    if not st.session_state.side_eff_severity:
        total_severity = 0
    else:
        # dict인데 value가 숫자가 아니면 에러
        if not all(isinstance(v, int) for v in st.session_state.side_eff_severity.values()):
            raise ValueError(f"❌ side_eff_severity 값이 숫자가 아님: {st.session_state.side_eff_severity}")
        total_severity = sum(st.session_state.side_eff_severity.values())

    # patient_daily 저장
    execute_query(DB_PATH, """
    INSERT OR REPLACE INTO patient_daily
    (patient_id, prescription_date, record_date, 
     emotion_text, side_eff_severity, day_num_dose,
     pdc, medication_id, dose_mg, note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        prescription_date,
        today_str,
        st.session_state.get("emotion_text", ""),
        total_severity,
        day_num_dose_val,      # 무조건 int
        None,                  # pdc
        "fluoxetine",          # medication_id
        None,                  # dose_mg
        None                   # note
    ))

    # 부작용 저장
    for code in st.session_state.side_eff_selected:
        sev = st.session_state.side_eff_severity.get(code)
        if sev is None:
            raise ValueError(f"❌ side_eff_selected={code} 에 대해 severity 값이 없습니다.")
        execute_query(DB_PATH, """
            INSERT OR REPLACE INTO asec_response
            (patient_id, prescription_date, record_date, side_effect_code, due_to_med, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            prescription_date,
            today_str,
            code,   # side_effect_code (S01~S21)
            1,      # 약물로 인한 것으로 고정
            sev
        ))
    
    # BERT에서 나온 phq-9 점수 저장
    for score in "모델 연결 후 결과":
        execute_query(DB_PATH,
                      """INSERT OR REPLACE INTO daily_phq9
                      (patient_id, prescription_date, record_date, phq9_score, model_version)
                      VALUES (?,?,?,?,?)
                      """,(
                          patient_id,
                          prescription_date,
                          today_str,
                          phq9_score,  # -> 모델 결과
                          "1.0v"
                      ))

def pd_step_4():
    diary_header()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="question-label">오늘 하루의 기분 또는 느낌을 자유롭게 표현해주세요.</span>', 
                unsafe_allow_html=True)
    
    st.session_state.emotion_text = st.text_area(
        "",
        value=st.session_state.get("emotion_text", ""),
        height=260,
        placeholder="텍스트를 입력해주세요.",
        key="pd_text_area",
    )

    save_col, msg_col, spacer, close_col = st.columns([1, 2, 6, 1])
    with save_col:
        if st.button("이전", key="btn_prev_step4", use_container_width=False):
            st.session_state.pd_step = 3
            st.rerun()
        save_clicked = st.button("저장", key="btn_save_step4")

    def translate_text(text, target='en'):

        credentials = service_account.Credentials.from_service_account_file('phq9translate-b2a11fca5296.json')
        client = translate.Client(credentials=credentials)
        result = client.translate(text, target_language=target)
        return result['translatedText']

    with msg_col:
        if save_clicked:
            text_val = st.session_state.get("emotion_text", "").strip()
            if not text_val:
                st.error("메세지를 입력하세요.")
                st.session_state.pd_saved = False
            else:
                # ============================
                # ✅ Hugging Face 모델 실행 위치
                # → text_val을 HF 모델에 넣어서 phq9_score 추출
                # phq9_score = predict_phq9(text_val)
                # st.info(f"AI 추론된 PHQ-9 점수: {phq9_score}")
                # ============================

                # DB 저장 실행 (argument로 모델에서 나온 phq9_score 변수 할당해야함.)
                hf_token = st.secrets["HF_TOKEN"]
                login(HF_TOKEN)
                model_name = "sasasassaszzd/PHQ8-prototype"
                translated_text = translate_text(text_val, target='en')

                model = AutoModel.from_pretrained(model_name, trust_remote_code=True, torch_dtype="auto")
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                inputs = tokenizer(translated_text, return_tensors="pt", padding=True, truncation=True)
                phq9_score = model.inference(**inputs)

                save_to_db(phq9_score)
                st.success("저장되었습니다.")
                st.session_state.pd_saved = True
                
    with close_col:
        if st.button("닫기", key="btn_close_step4", 
                     disabled=not st.session_state.pd_saved):
                st.switch_page(BACK_PAGE_PATH)

    st.markdown('</div>', unsafe_allow_html=True)


step = int(st.session_state.pd_step)
if step == 1:
    pd_step_1()
elif step == 2:
    pd_step_2()
elif step == 3:
    pd_step_3()
else:
    pd_step_4()

