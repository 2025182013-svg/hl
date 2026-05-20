import streamlit as st
import time
from datetime import datetime

# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="ThinkBack AI",
    layout="centered"
)

st.title("🧠 ThinkBack AI")
st.caption("AI 과의존 방지 자기주도 학습 챗봇")

# -----------------------------------
# 세션 상태 초기화
# -----------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "warning_count" not in st.session_state:
    st.session_state.warning_count = 0

if "last_time" not in st.session_state:
    st.session_state.last_time = time.time()

if "question_lengths" not in st.session_state:
    st.session_state.question_lengths = []

# -----------------------------------
# 과의존 분석 함수
# -----------------------------------
def analyze_dependency(text):
    score = 0

    danger_words = [
        "답만",
        "정답",
        "빨리",
        "그냥 알려줘",
        "숙제 해줘",
        "대신 해줘",
        "요약만",
        "생각하기 싫어",
        "복붙",
        "그대로"
    ]

    # 위험 단어 감지
    for word in danger_words:
        if word in text:
            score += 3

    # 질문 길이
    if len(text) < 8:
        score += 2

    # 연속 질문 감지
    now = time.time()
    diff = now - st.session_state.last_time

    if diff < 10:
        score += 2

    st.session_state.last_time = now

    return score

# -----------------------------------
# 위험도 상태
# -----------------------------------
def risk_status(score):
    if score < 5:
        return "🟢 낮음"
    elif score < 10:
        return "🟡 보통"
    else:
        return "🔴 높음"

# -----------------------------------
# 사이드바
# -----------------------------------
st.sidebar.title("📊 AI 의존도 분석")

st.sidebar.metric(
    "현재 위험도",
    risk_status(st.session_state.risk_score)
)

st.sidebar.metric(
    "위험 점수",
    st.session_state.risk_score
)

st.sidebar.metric(
    "총 질문 수",
    st.session_state.question_count
)

st.sidebar.metric(
    "경고 횟수",
    st.session_state.warning_count
)

# -----------------------------------
# 평균 질문 길이
# -----------------------------------
if st.session_state.question_lengths:
    avg_len = sum(st.session_state.question_lengths) / len(
        st.session_state.question_lengths
    )

    if avg_len < 10:
        level = "짧음"
    elif avg_len < 30:
        level = "보통"
    else:
        level = "깊이 있는 질문"

    st.sidebar.metric(
        "평균 질문 수준",
        level
    )

# -----------------------------------
# 자기 점검 시스템
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("🪞 자기 점검")

check1 = st.sidebar.checkbox(
    "AI 답변을 읽고 다시 생각해봤나요?"
)

check2 = st.sidebar.checkbox(
    "답만 복사하지 않았나요?"
)

check3 = st.sidebar.checkbox(
    "내 생각을 먼저 정리했나요?"
)

check4 = st.sidebar.checkbox(
    "AI 없이도 설명할 수 있나요?"
)

reflection_score = sum([
    check1,
    check2,
    check3,
    check4
])

st.sidebar.markdown("---")

if reflection_score == 4:
    st.sidebar.success(
        "🌱 건강한 AI 활용 습관을 가지고 있어요!"
    )

elif reflection_score >= 2:
    st.sidebar.info(
        "💡 AI를 참고하되 스스로 사고하는 습관을 유지해보세요."
    )

else:
    st.sidebar.warning(
        "⚠️ AI 의존도가 높아질 수 있어요."
    )

# -----------------------------------
# 오늘의 사용 리포트
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("📋 오늘의 사용 리포트")

st.sidebar.write(
    f"- 질문 수: {st.session_state.question_count}"
)

st.sidebar.write(
    f"- 위험 경고: {st.session_state.warning_count}회"
)

st.sidebar.write(
    f"- 현재 위험도: {risk_status(st.session_state.risk_score)}"
)

# -----------------------------------
# 채팅 기록 출력
# -----------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------
# 사용자 입력
# -----------------------------------
user_input = st.chat_input("질문을 입력하세요")

if user_input:

    # 사용자 메시지 저장
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # 질문 통계
    st.session_state.question_count += 1
    st.session_state.question_lengths.append(len(user_input))

    # 위험 점수 계산
    added_score = analyze_dependency(user_input)
    st.session_state.risk_score += added_score

    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(user_input)

    # -----------------------------------
    # 위험 경고
    # -----------------------------------
    if st.session_state.risk_score >= 10:

        st.session_state.warning_count += 1

        st.warning("""
🚨 AI 의존도가 높아지고 있습니다.

정답만 빠르게 얻기보다
스스로 생각하는 과정이 중요합니다.

잠시 직접 고민해보는 시간을 가져보세요 🙂
""")

        # 생각 유도
        with st.expander("✍️ 먼저 스스로 생각해보기"):
            my_thought = st.text_area(
                "당신의 생각을 먼저 적어보세요"
            )

            if my_thought:
                st.success(
                    "좋아요! 스스로 사고하려는 과정이 매우 중요합니다."
                )

        # 강제 대기
        with st.spinner("⏳ 잠시 스스로 생각하는 시간을 가져보세요..."):
            time.sleep(3)

    elif st.session_state.risk_score >= 5:

        st.session_state.warning_count += 1

        st.info("""
💡 AI 답변을 그대로 받아들이기보다
왜 이런 답이 나왔는지 함께 고민해보세요.
""")

    # -----------------------------------
    # AI 응답
    # -----------------------------------
    response = f"""
당신의 질문:

> {user_input}

에 대해 먼저 스스로 생각해볼 수 있는 방향을 추천드립니다.

### 생각해볼 질문
- 이 문제의 핵심은 무엇인가요?
- 본인의 생각은 어떤가요?
- 왜 이런 결과가 나올까요?
- 다른 해결 방법은 없을까요?

### 자기주도 학습 팁
AI 답변은 참고 자료일 뿐,
가장 중요한 것은 자신의 사고 과정입니다.
"""

    # AI 메시지 저장
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    # AI 메시지 출력
    with st.chat_message("assistant"):
        st.markdown(response)

# -----------------------------------
# 하단 안내
# -----------------------------------
st.markdown("---")

st.caption(
    "ThinkBack AI는 건강한 AI 활용 습관과 자기주도 학습을 돕기 위해 제작되었습니다."
)
