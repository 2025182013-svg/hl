import streamlit as st
from datetime import datetime
import time

# -----------------------------------
# 기본 설정
# -----------------------------------
st.set_page_config(
    page_title="ThinkBack AI",
    layout="centered"
)

st.title("🧠 ThinkBack AI")
st.caption("AI 과의존 방지 학습 챗봇")

# -----------------------------------
# 세션 상태 초기화
# -----------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "last_time" not in st.session_state:
    st.session_state.last_time = time.time()

# -----------------------------------
# 과의존 감지 함수
# -----------------------------------
def analyze_dependency(text):
    score = 0

    danger_words = [
        "답만",
        "정답",
        "빨리",
        "그냥 알려줘",
        "생각하기 싫어",
        "숙제 해줘",
        "대신 해줘",
        "요약만"
    ]

    for word in danger_words:
        if word in text:
            score += 3

    # 너무 짧은 질문
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
# 사이드바
# -----------------------------------
st.sidebar.title("📊 AI 의존도 분석")

risk = st.session_state.risk_score

if risk < 5:
    st.sidebar.success(f"🟢 낮음 ({risk}점)")
elif risk < 10:
    st.sidebar.warning(f"🟡 보통 ({risk}점)")
else:
    st.sidebar.error(f"🔴 높음 ({risk}점)")

st.sidebar.markdown("---")
st.sidebar.write(f"총 질문 수: {st.session_state.question_count}")

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

    st.session_state.question_count += 1

    # 위험 점수 계산
    added_score = analyze_dependency(user_input)
    st.session_state.risk_score += added_score

    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(user_input)

    # -----------------------------------
    # 경고 시스템
    # -----------------------------------
    if st.session_state.risk_score >= 10:
        st.warning("""
🚨 AI 의존도가 높아지고 있습니다.

정답을 바로 얻는 것도 좋지만,
스스로 사고하는 과정 역시 중요합니다.

잠시 직접 생각해보는 시간을 가져보세요 🙂
""")

    elif st.session_state.risk_score >= 5:
        st.info("""
💡 AI를 활용할 때는
왜 이런 답이 나왔는지 함께 고민해보세요.
""")

    # -----------------------------------
    # AI 응답
    # -----------------------------------
    response = f"""
당신의 질문:

> {user_input}

에 대해 먼저 스스로 생각해볼 수 있는 방향을 추천드립니다.

- 이 문제의 핵심은 무엇인가요?
- 본인의 생각은 어떤가요?
- 왜 이런 결과가 나올까요?

AI 답변을 참고하되,
자신만의 사고 과정을 함께 만들어보세요.
"""

    # AI 메시지 저장
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    # AI 메시지 출력
    with st.chat_message("assistant"):
        st.markdown(response)
