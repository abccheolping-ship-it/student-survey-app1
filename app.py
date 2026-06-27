import re
import pandas as pd
import streamlit as st
from supabase import create_client

# =========================
# 페이지 설정
# =========================

st.set_page_config(
    page_title="학생 생활습관 설문",
    page_icon="📘",
    layout="centered"
)

# =========================
# 디자인 설정
# =========================

st.markdown("""
<style>

.block-container {
    max-width: 900px;
    padding-top: 2rem;
}

h1 {
    text-align: center;
    color: #1f2937;
    font-weight: 800;
}

h2, h3 {
    color: #374151;
}

.stForm {
    background-color: white;
    padding: 30px;
    border-radius: 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.stButton button {
    width: 100%;
    border-radius: 12px;
    font-size: 18px;
    font-weight: bold;
    padding: 12px;
}

div[data-testid="stMetric"] {
    background-color: #f8fafc;
    padding: 16px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
}

</style>
""", unsafe_allow_html=True)

# =========================
# Supabase 연결 정보
# =========================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    TABLE_NAME = st.secrets.get("TABLE_NAME", "student_life")

except Exception:
    st.error("Streamlit Secrets에 SUPABASE_URL, SUPABASE_KEY, TABLE_NAME을 입력해야 합니다.")
    st.stop()

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# =========================
# 함수
# =========================

def load_data():
    response = (
        supabase
        .table(TABLE_NAME)
        .select("*")
        .execute()
    )

    df = pd.DataFrame(response.data)

    return df


def make_next_student_id(df):
    if df.empty or "student_id" not in df.columns:
        return "S001"

    max_number = 0

    for sid in df["student_id"].dropna():
        match = re.search(r"\d+", str(sid))

        if match:
            number = int(match.group())

            if number > max_number:
                max_number = number

    return f"S{max_number + 1:03d}"


def make_next_index(df):
    if df.empty or "index" not in df.columns:
        return None

    index_series = pd.to_numeric(
        df["index"],
        errors="coerce"
    ).dropna()

    if index_series.empty:
        return 0

    return int(index_series.max()) + 1


def clean_numeric_data(df):
    numeric_columns = [
        "sleep_hours",
        "phone_hours",
        "commute_minutes",
        "tired_score",
        "focus_score"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# =========================
# 제목
# =========================

st.title("📘 학생 생활습관 설문 웹앱")

st.write(
    "설문을 입력하고 제출하면 Supabase 데이터베이스에 자동으로 저장됩니다."
)

st.divider()

# =========================
# 메뉴 선택
# =========================

menu = st.radio(
    "메뉴 선택",
    ["📝 설문하기", "📊 분석 확인하기"],
    horizontal=True
)

st.divider()

# =========================
# 1. 설문하기 화면
# =========================

if menu == "📝 설문하기":

    try:
        current_df = load_data()

    except Exception as e:
        st.error("Supabase 데이터를 불러오지 못했습니다.")
        st.write("확인할 것: Supabase 프로젝트 상태, RLS 설정, URL, KEY, 테이블 이름")
        st.write(e)
        st.stop()

    next_id = make_next_student_id(current_df)

    st.info(f"자동 생성 학생 ID : {next_id}")

    st.subheader("1. 설문 입력하기")

    with st.form("survey_form"):

        grade_class = st.selectbox(
            "반",
            [
                "1-1",
                "1-2",
                "1-3",
                "1-4",
                "1-5",
                "1-6",
                "1-7",
                "1-8",
                "1-9",
                "1-10"
            ]
        )

        sleep_hours = st.number_input(
            "수면시간",
            min_value=0.0,
            max_value=24.0,
            value=6.0,
            step=0.5
        )

        phone_hours = st.number_input(
            "스마트폰 사용시간",
            min_value=0.0,
            max_value=24.0,
            value=3.0,
            step=0.5
        )

        breakfast = st.selectbox(
            "아침식사 여부",
            ["YES", "NO"]
        )

        commute_minutes = st.number_input(
            "통학시간(분)",
            min_value=0,
            max_value=180,
            value=30,
            step=5
        )

        st.markdown("### 피곤함 점수")
        st.caption("1 = 전혀 피곤하지 않음, 5 = 매우 피곤함")

        tired_score = st.radio(
            "피곤함 점수 선택",
            [1, 2, 3, 4, 5],
            horizontal=True,
            label_visibility="collapsed"
        )

        st.markdown("### 집중도 점수")
        st.caption("1 = 집중이 잘 안 됨, 5 = 매우 잘 집중됨")

        focus_score = st.radio(
            "집중도 점수 선택",
            [1, 2, 3, 4, 5],
            horizontal=True,
            label_visibility="collapsed"
        )

        favorite_subject = st.selectbox(
            "좋아하는 과목",
            [
                "국어",
                "영어",
                "수학",
                "과학",
                "사회",
                "체육",
                "음악",
                "미술",
                "정보"
            ]
        )

        submitted = st.form_submit_button(
            "💾 설문 제출하기"
        )

    if submitted:

        latest_df = load_data()

        new_student_id = make_next_student_id(latest_df)
        new_index = make_next_index(latest_df)

        data = {
            "student_id": new_student_id,
            "grade_class": grade_class,
            "sleep_hours": sleep_hours,
            "phone_hours": phone_hours,
            "breakfast": breakfast,
            "commute_minutes": commute_minutes,
            "tired_score": tired_score,
            "focus_score": focus_score,
            "favorite_subject": favorite_subject
        }

        if new_index is not None:
            data["index"] = new_index

        try:
            supabase.table(TABLE_NAME).insert(data).execute()

            st.success(f"설문이 저장되었습니다. 학생 ID : {new_student_id}")
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error("저장 중 오류가 발생했습니다.")
            st.write("확인할 것: RLS 설정, 테이블 이름, 컬럼 이름, Primary Key 중복 여부")
            st.write(e)


# =========================
# 2. 분석 확인하기 화면
# =========================

elif menu == "📊 분석 확인하기":

    st.subheader("2. 분석 확인하기")

    try:
        df = load_data()
        df = clean_numeric_data(df)

    except Exception as e:
        st.error("데이터를 불러오는 중 오류가 발생했습니다.")
        st.write(e)
        st.stop()

    if df.empty:
        st.info("아직 저장된 설문 데이터가 없습니다.")
        st.stop()

    if "student_id" in df.columns:
        df = df.sort_values(by="student_id")

    st.markdown("## 📌 전체 설문 요약")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "참여 학생 수",
            f"{len(df)}명"
        )

    with col2:
        st.metric(
            "평균 수면시간",
            f"{df['sleep_hours'].mean():.1f}시간"
        )

    with col3:
        st.metric(
            "평균 스마트폰 사용",
            f"{df['phone_hours'].mean():.1f}시간"
        )

    with col4:
        st.metric(
            "평균 집중도",
            f"{df['focus_score'].mean():.1f}점"
        )

    st.divider()

    # =========================
    # 나와 친구들 비교
    # =========================

    st.markdown("## 👤 나와 친구들 평균 비교하기")

    student_ids = df["student_id"].dropna().unique().tolist()
    student_ids = sorted(student_ids)

    selected_id = st.selectbox(
        "내 학생 ID를 선택하세요.",
        student_ids,
        index=len(student_ids) - 1
    )

    my_data = df[df["student_id"] == selected_id].iloc[0]

    compare_df = pd.DataFrame({
        "항목": [
            "수면시간",
            "스마트폰 사용시간",
            "통학시간",
            "피곤함점수",
            "집중도점수"
        ],
        "나": [
            my_data["sleep_hours"],
            my_data["phone_hours"],
            my_data["commute_minutes"],
            my_data["tired_score"],
            my_data["focus_score"]
        ],
        "전체 평균": [
            df["sleep_hours"].mean(),
            df["phone_hours"].mean(),
            df["commute_minutes"].mean(),
            df["tired_score"].mean(),
            df["focus_score"].mean()
        ]
    })

    compare_df = compare_df.set_index("항목")

    st.bar_chart(compare_df)

    st.markdown("### 🧠 간단 해석")

    my_sleep = my_data["sleep_hours"]
    avg_sleep = df["sleep_hours"].mean()

    my_phone = my_data["phone_hours"]
    avg_phone = df["phone_hours"].mean()

    my_focus = my_data["focus_score"]
    avg_focus = df["focus_score"].mean()

    if my_sleep >= avg_sleep:
        st.write(f"- {selected_id} 학생의 수면시간은 전체 평균보다 많거나 비슷합니다.")
    else:
        st.write(f"- {selected_id} 학생의 수면시간은 전체 평균보다 적습니다.")

    if my_phone >= avg_phone:
        st.write(f"- {selected_id} 학생의 스마트폰 사용시간은 전체 평균보다 많거나 비슷합니다.")
    else:
        st.write(f"- {selected_id} 학생의 스마트폰 사용시간은 전체 평균보다 적습니다.")

    if my_focus >= avg_focus:
        st.write(f"- {selected_id} 학생의 집중도는 전체 평균보다 높거나 비슷합니다.")
    else:
        st.write(f"- {selected_id} 학생의 집중도는 전체 평균보다 낮습니다.")

    st.divider()

    # =========================
    # 반별 평균 집중도
    # =========================

    st.markdown("## 🏫 반별 평균 집중도")

    class_focus = (
        df.groupby("grade_class")["focus_score"]
        .mean()
        .sort_index()
    )

    st.bar_chart(class_focus)

    st.caption("각 반의 평균 집중도 점수를 비교한 그래프입니다.")

    st.divider()

    # =========================
    # 수면시간과 집중도 관계
    # =========================

    st.markdown("## 😴 수면시간과 집중도 관계")

    scatter_df = df[[
        "sleep_hours",
        "focus_score",
        "student_id"
    ]].dropna()

    st.scatter_chart(
        scatter_df,
        x="sleep_hours",
        y="focus_score"
    )

    st.caption("점 하나는 학생 한 명을 의미합니다. 오른쪽으로 갈수록 수면시간이 많고, 위로 갈수록 집중도 점수가 높습니다.")

    st.divider()

    # =========================
    # 아침식사 여부별 피곤함 점수
    # =========================

    st.markdown("## 🍚 아침식사 여부별 평균 피곤함 점수")

    breakfast_tired = (
        df.groupby("breakfast")["tired_score"]
        .mean()
        .sort_index()
    )

    st.bar_chart(breakfast_tired)

    st.caption("아침식사를 한 학생과 하지 않은 학생의 평균 피곤함 점수를 비교합니다.")

    st.divider()

    # =========================
    # 좋아하는 과목별 집중도
    # =========================

    st.markdown("## 📚 좋아하는 과목별 평균 집중도")

    subject_focus = (
        df.groupby("favorite_subject")["focus_score"]
        .mean()
        .sort_values(ascending=False)
    )

    st.bar_chart(subject_focus)

    st.caption("좋아하는 과목에 따라 평균 집중도 점수가 어떻게 다른지 확인합니다.")

    st.divider()

    # =========================
    # 원본 데이터 보기
    # =========================

    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(
            df,
            use_container_width=True
        )

        st.success(f"총 데이터 수 : {len(df)}개")
