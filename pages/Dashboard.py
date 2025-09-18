import streamlit as st
import calendar
from datetime import date, datetime, time
import random
import pandas as pd
import sqlite3
from pathlib import Path 
import base64
import logging
import altair as alt
# Altair = 파이썬 데이터 시각화 라이브러리
# -> 데이터 프레임을 간단하게 그래프로 보여줄 때 유용(데이터프레임 -> 차트 변환에 유용).

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from DataBase.db_utils import fetch_one, fetch_all

DB_PATH = "DataBase/project_db2.db"

st.set_page_config(page_title="Home", page_icon="💊", layout="wide")

if not st.session_state.get("is_logged_in", False):
    st.error("잘못된 접근입니다.")
    st.stop()

# 로그인 세션에서 patient_id 가져오기
patient_id = st.session_state["patient_id"]

# DB 연결 후 환자 이름 불러오기 (patient_info에 이름 컬럼 없으니 우선 patient_id 그대로 표시)
# DB에서 환자 이름 가져오기
row = fetch_one(DB_PATH, "SELECT name FROM patient_info WHERE patient_id = ?", (patient_id,))
if row and row["name"]:
    name = row["name"]
else:
    name = patient_id   # fallback

header_col1, header_col2 = st.columns([4,1])
with header_col1:
    st.markdown( f""" 
                <div style="padding: 1.2rem 1.5rem; border-radius: 12px; 
                background-color: #f5f7fa; border: 1px solid #e5e7eb; 
                width: fit-content; color:#111;"> 
                <span style="font-size: 2rem; font-weight: 800; 
                letter-spacing: 0.5px;"> 
                {name} 님 </span> </div> """, 
                unsafe_allow_html=True )

def is_diary_time(now: datetime) -> bool:
    now_time = now.time()
    return now_time >= time(18, 0) or now_time <= time(2,0)
    # now.time() = datetime 객체에서 시간만 뽑아내는 메서드.
    # -> datetime(2025, 08, 26, 20, 30)에서 now.time()은 20:30
    
now = datetime.now()

left, right = st.columns([2,1])
st.markdown(" ")
st.markdown(" ")
with right:
    right_col1, right_col2 = st.columns([1,1])
    with right_col2:
        button_1, button_2 = st.columns([1,1])
        with button_1:
            if st.button("프로필", use_container_width=True):
                st.switch_page("pages/Patient_intake1.py")

        with button_2:
            if st.button("하루점검", use_container_width=True):
                st.switch_page("pages/Patient_diary.py")
            # else:
            #     if "프로필 등록을 하지 않았을 경우":
            #         st.warning("프로필을 먼저 작성해주세요!")
            #     elif is_diary_time(now):
            #         st.switch_page("pages/Patient_diary.py")
            #     else:
            #         st.success("하루 점검은 오후 6시부터 가능합니다.")

# 하루 메세지
MESSAGES = [
    "오늘도 잘 버텨낸 당신, 충분히 잘하고 있어요!", 
    "오늘 하루도 정말 수고 많았어요.(토닥토닥)",
    "당신은 생각보다 훨씬 잘하고 있어요!",
    "힘든 하루였지만 여기까지 온 당신이 대단해요.",
    "실수해도 괜찮아요, 그건 배우고 있다는 증거니까요.",
    "당신의 오늘은 분명 의미 있었어요.",
    "오늘의 당신은 분명 어제보다 더 나은 사람이에요.",
    "지금 이 순간에도 성장 중이에요 🌱",
    "마음이 무거운 날엔 가볍게 쉬어도 괜찮아요.",
    "쉬어 가도 괜찮아요. 이런 날도 있어야죠!",
    "자신을 칭찬해 주세요. 스스로를 향한 믿음이 가장 힘이 세답니다.",
    "당신은 충분히 잘하고 있고, 잘 해낼 거예요.",
    "누구보다 당신이 당신을 아껴야 해요.💖",
    "오늘 하루도 버텨낸 당신에게 박수를 보내요!👏🏻",
    "힘들 땐 잠시 쉬어가도 괜찮아요.",
    "당신은 존재만으로도 커다란 의미를 주는 사람이에요.",
    "지금의 노력은 분명 좋은 결과로 돌아올 거예요. 믿어봐요!",
    "언제나 당신의 편에 서있을테니 함께 해봐요!",
    "지금 당신이 부단히 보낸 하루하루가 모여 평안한 매일이 되기를.",
    "조금 느려도 괜찮아요. 당신은 당신의 속도일 때 가장 자유로워요.",
    "완벽하지 않아도 충분히 아름다워요.",
    "다가올 당신의 모든 시간을 사랑하세요!",
    "당신이 만든 작은 변화가 당신을 크게 도울거에요.",
    "사랑할 줄 아는 당신을 정말 사랑해요!",
    "어떤 순간에도 자신을 믿어요!",
    "당신은 무너져도 다시 일어날 수 있는 사람이에요.",
    "오늘의 감정도, 당신의 일부이기에 그것마저 소중하고 귀하답니다.",
    "오늘을 살아낸 당신은 이미 그것만으로 충분히 자랑스러워요.",
    "당신의 감정을 이해해요. 오늘 하루도 정말 수고 많았어요.",
    "당신의 오늘이 어제보다 나아지길 바라요🌈"
]

def with_tooltip(title: str, tip: str) -> str:
                return f"""
                <div style="display:inline-flex; align-items:center; font-size:1.4rem; font-weight:600;">
                    {title}
                    <span style="
                        display:inline-block; 
                        margin-left:8px; 
                        width:22px; 
                        height:22px; 
                        border-radius:50%; 
                        background:#e5e7eb; 
                        color:#374151; 
                        font-size:1rem; 
                        font-weight:bold;
                        text-align:center; 
                        line-height:22px; 
                        cursor:default;" 
                        title="{tip}">?
                    </span>
                </div>
                """

today_str = date.today().isoformat()

st.session_state.setdefault("day_num_dose", {})


st.session_state.setdefault("daily_msg",{})
if today_str not in st.session_state["daily_msg"]:
    rnd = random.Random(f"{name}-{today_str}")
    st.session_state["daily_msg"][today_str] = rnd.choice(MESSAGES)
    # st.session_state[key][subkey] 
    # -> st.session_state 안에 있는 딕셔너리 key를 먼저 찾고, 
    # -> 그 안에서 또 다른 key(subkey)를 찾아서 값(value)에 접근.
    # daily_msg에 ""가 붙는 이유: 문자열 그 자체를 key로 쓰기 때문. 딕셔너리 이름이 daily_msg
    # today_str에 ""가 안붙는 이유: 변수에 저장된 값을 key로 쓰기 때문. 매일 바뀌는 날짜가 변수에 저장되고 그걸 key로 쓰나까.

msg = st.session_state["daily_msg"][today_str]

def image_to_base64(img_path:str) -> str:
    try:
    # try: 오류가 날 수도 있는 코드 except: 오류가 나면 실행되는 코드
        with open(img_path, "rb") as f:
        # open() = 파일을 여는 함수
        # rb = r(읽기) + b(바이너리) = 바이너리(이진 데이터)로 읽겠다.
        # -> 여기서는 이미지 파일을 이진 데이터로 읽겠다는 뜻. 
        # r(읽기), w(쓰기), a(이어쓰기), b(바이너리) -> 모드를 뜻하는 인자들.
        # with: = 파일을 열고, 끝나면 자동으로 닫아주는 안전한 문법.
        # as ... = ...으로 부르겠다(별명 지정).
            b64 = base64.b64encode(f.read()).decode("utf-8")
            # read() = 파일 내용을 전부 읽어서 반환해줌.
            # -> read니까 문자열을 반환함. 
            # encode() = 문자열(str)을 이진 데이터(bytes)로 바꿔줌.
            # decode() - bytes를 문자열로 바꿔줌.
            # base64는 데이터를 문자로 안전하게 표현하는 방법.
            # utf-g = 문자 <-> 바이트 변환을 할 때 쓰는 규칙 중 하나. 
            # HTML에는 이미지(이진 데이터)를 직접 넣을 수 없음. -> 텍스트로 바꿔주어야 함.
        return f"data:image/png;base64,{b64}"
        # data:[MIME 타입];base64,[데이터]
        # MIME = 데이텉가 어떤 종류인지 알려주는 태그 역할.
    except Exception as e:
    # Exception = 파이썬에서 발생할 수 있는 모든 에외(Error)의 부모 class.
        logging.warning(f"이미지 로드 실패: {img_path} - {e}")
        # logging: 프로그램이 실행되는 동안 생기는 기록인 로그(log)를 기록하고 관리하는 것. 
        # -> 주로 콘솔(터미널)에 기록됨, 디버깅(오류) 확인용으로 많이 사용. 
        return ""

# --- 이미지 로드 함수 ---
def image_to_base64(img_path: str) -> str:
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logging.warning(f"이미지 로드 실패: {img_path} - {e}")
        return ""

# --- 절대 경로 기반 이미지 폴더 설정 ---
# 🔧 이 부분을 네 환경에 맞는 절대 경로로 수정해줘
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # C:\Users\minkj\Desktop\3-1\project_DT\CJS\neproject25 - share\projectUI\pages\
IMG_DIR = os.path.join(BASE_PATH, "images")  ## C:\Users\minkj\Desktop\3-1\project_DT\CJS\neproject25 - share\projectUI\images

IMG_ELIF_10  = image_to_base64(os.path.join(IMG_DIR, "elif_1.0.png"))
IMG_ELIF_066 = image_to_base64(os.path.join(IMG_DIR, "elif_0.6.png"))
IMG_ELSE     = image_to_base64(os.path.join(IMG_DIR, "else.png"))


# adherence 기록 가져오기
query_adherence = """
SELECT record_date, day_num_dose
FROM patient_daily
WHERE patient_id = ?
ORDER BY record_date
"""
rows = fetch_all(DB_PATH, query_adherence, (patient_id,))
# rows = [(날짜, 순응도), ...]
# 예: [("2025-09-01", 1.0), ("2025-09-02", 0.66), ("2025-09-03", 0.33)]
if rows:  # 데이터가 있으면 딕셔너리 변환
    st.session_state["day_num_dose"] = {r["record_date"]: r["day_num_dose"] for r in rows}
else:  # 데이터 없으면 빈 딕셔너리
    st.session_state["day_num_dose"] = {}
    st.info("아직 복용 기록이 없습니다. 하루점검에서 복용 여부를 기록해 주세요!")

# 2. 순응도 퍼센티지 → 이미지 변환 함수
def get_adherence_imoji(r):
    """ 
    순응도 r(0.0~1.0)에 따라 이미지를 선택해 HTML 태그로 반환 
    - 1.0 = 약 100% 복용 → IMG_ELIF_10
    - 0.66 이상 = 2/3 이상 복용 → IMG_ELIF_066
    - 그 외 = IMG_ELSE
    """
    if r is None:
        return ""
    if r >= 1.0:
        src = IMG_ELIF_10
    elif r >= (2/3):
        src = IMG_ELIF_066
    else:
        src = IMG_ELSE

    if not src:  # 이미지 로드 실패 시
        return ""
    return f"<img src='{src}' class='mark-img' alt='adherence'/>"
    # class 속성: HTML에서 요소를 특정 그룹으로 묶어주는 속성.
    # alt 속성: <img>에서만 쓰이는 속성, 대체 텍스트라는 뜻.
    # -> 이미지가 깨져서 안 보일 때 대신 보여줄 텍스트.

    # if 다음 코드가 한 줄일 땐 문단을 띄우지 않아도 괜찮음.
    # elif = 그렇지 않으면(if와 else 사이에 낑겨있음.)
    # if-elif-else 구조: 조건이 맞으면 아래는 전혀 안 봄, 하나만 실행, 중복 실행 걱정 X.
    # if-if-if 구조: 각 조건이 독립적으로 모두 검사됨.
    # return은 함수가 즉시 종료되는 명령으로, 실행되면 함수 바깥으로 값을 돌려주고 함수 실행이 끝남. 
    # -> 그래서 if-if-if 구조를 사용해도 문제가 없었던 것.
    # 그치만 난 안전빵으로 elif를 쓰겠다.
    # <img.../> or <img> = 이미지를 화면에 보여주기 위한 태그 문법.
    # src = source의 줄임말, 이미지 파일이 어디 있는지 알려주는 경로.

with left:
    calendar_left, spacer_left = st.columns([9,1])
    with calendar_left:
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(with_tooltip("칭찬 기록", 
                                 "약을 얼마나 잘 복용하고 있는지, 한 달 간의 복용 기록을 확인할 수 있어요. \n처방받은 약을 전부 복용했을 경우 : 너무 훌륭해! 스티커 \n처방받은 약을 2/3 이상 복용했을 경우 : 넌 할 수 있어! 스티커 \n처방받은 약을 2/3 미만으로 복용했을 경우 : 좀 더 열심히~ 스티커"), 
                                 unsafe_allow_html=True)

        today = date.today()
        st.markdown(f"### {today.year}년 {today.month}월")
        monthly_calendar = calendar.Calendar(firstweekday=0)
        # calendar.Calendar = calendar 모듈에서 달력 객체(Calendar)를 만들겠다는 뜻.
        # firstweekday=0 = 월요일부터 시작하는 달력을 만들겠다는 뜻(0=Monday).
        weeks = monthly_calendar.monthdayscalendar(today.year, today.month)
        # today.year, today.month는 몇 년도 몇 월의 달력을 만들지 지정해주기 위함.
        # today.day는 여기선 없어도 됨.(내가 헷갈렸던 부분)

        st.markdown("""
                <style>
                .cal-wrap{
                    max-width: 860px;
                    width: 100%;
                }
                table.calendar{
                    border-collapse: collapse;
                    width: 100%;
                    table-layout: fixed;
                }
                table.calendar th, table.calendar td{
                    border: 1px solid #ddd;
                    width: 14.2857%;
                    height: 110px;
                    position: relative;
                    background: #fafafa;
                    padding: 0;
                    vertical-align: middle;
                }
                table.calendar th{
                    background:#f7f7f9;
                    color:#111;
                    font-weight:700;
                    height: 42px;
                }
                table.calendar td .day-num{
                    position: absolute;
                    top: 6px;
                    left: 8px;
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: #374151;
                    z-index: 2;
                }
                table.calendar td .mark-wrap{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                }
                img.mark-img{
                    width: 72px;
                    height: 72px;
                    object-fit: contain;
                    display: block;
                    margin: 0 auto;
                }
                td.empty{ background:#fdfdfd; }
                </style>
                """, unsafe_allow_html=True)
                # img.mark-img -> 여기에 'mark-img'라는 딕셔너리 만들어놓음.

        header_html = "<tr>" + "".join(f"<th>{d}</th>" for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]) + "</tr>"

        rows_html = ""
        for week in weeks:
            row_tds = ""
            for daynum in week:
                if daynum == 0:  # 달력 빈칸
                    row_tds += "<td class='empty'></td>"
                else:
                    cell_date = date(today.year, today.month, daynum)
                    key = cell_date.isoformat()  # "YYYY-MM-DD"
                    r = st.session_state["day_num_dose"].get(key)  # DB에서 불러온 순응도
                    mark_html = get_adherence_imoji(r)  # 순응도 → 이미지 변환
                    # HTML에 날짜와 이미지 같이 표시
                    row_tds += f"<td><div class='day-num'>{daynum}</div><div class='mark-wrap'>{mark_html}</div></td>"
            rows_html += f"<tr>{row_tds}</tr>"

        # 달력 최종 HTML 출력
        table_html = f"<table class='calendar'>{header_html}{rows_html}</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        with right:
            st.markdown(with_tooltip("오늘의 메세지",
                                      "매일 랜덤 메세지를 띄워줍니다. \n하루동안 유지되어 당신의 하루를 응원해요."), 
                                      unsafe_allow_html=True)
            st.write(f"> {msg}")
            # 중간에 들어간 > = Markdown 문법, 인용구를 만들 때 주로 사용.
            # -> 깔끔한 박스 스타일로 한 줄 메세지를 보여줄 수 있음.

            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(with_tooltip("마음 기록", "하루점검에서 작성한 하루 기록 텍스트를 phq9 기반 감정 점수로 변환하여 그래프로 나타내줘요. \n우울감의 정도와 감정 변화를 확인할 수 있어요."), unsafe_allow_html=True)

            # PHQ-9 점수 불러오기
            query_phq = """
            SELECT record_date, phq9_score
            FROM daily_phq9
            WHERE patient_id = ?
            ORDER BY record_date
            """
            rows_phq = fetch_all(DB_PATH, query_phq, (patient_id,))

            if rows_phq:  # 데이터가 있을 때만
                df_phq = pd.DataFrame(rows_phq)
                # 컬럼명 통일 (record_date → today_str, phq9_score → phq_score)
                df_phq = df_phq.rename(columns={"record_date": "today_str", "phq9_score": "phq_score"})

                if not df_phq.empty:
                    chart = (
                        alt.Chart(df_phq.tail(7))
                        .mark_bar()
                        .encode(
                            x=alt.X("today_str:N", title="날짜", axis=alt.Axis(labelAngle=0)),
                            y=alt.Y("phq_score:Q", title="점수")
                        )
                        .properties(width="container", height=360)
                    )
                    st.altair_chart(chart, use_container_width=True)
            else:
                st.info("아직 감정 기록이 없어요.. 하루점검에서 기록해 보세요!")


            st.markdown("---")
            spacer, logout_button = st.columns([7,2])
            with logout_button:
                if st.button("로그아웃", use_container_width=True):
                    st.session_state.clear()
                    st.switch_page("Login.py")