import streamlit as st
import google.generativeai as genai
import time

# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="ThinkBack AI",
    page_icon="🧠",
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

if "warning_count" not in st.session_state:
    st.session_state.warning_count = 0

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "last_time" not in st.session_state:
    st.session_state.last_time = time.time()

if "question_lengths" not in st.session_state:
    st.session_state.question_lengths = []

# -----------------------------------
# 사이드바 API 입력
# -----------------------------------
st.sidebar.title("🔑 Gemini API 설정")

api_key = st.sidebar.text_input(
    "Gemini API Key 입력",
    type="password"
)

# -----------------------------------
# Gemini 연결
# -----------------------------------
model = None

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.sidebar.success("API 연결 완료")
    except Exception as e:
        st.sidebar.error(f"API 오류: {e}")

# -----------------------------------
# 과의존 분석 함수
# -----------------------------------
def analyze_dependency(text):
    score = 0

    danger_words = [
        "답만", "정답", "빨리", "숙제 해줘",
        "그냥 알려줘", "대신 해줘", "요약만",
        "복붙", "생각하기 싫어"
    ]

    for word in danger_words:
        if word in text:
            score += 3

    if len(text) < 8:
        score += 2

    now = time.time()
    if now - st.session_state.last_time < 10:
        score += 2

    st.session_state.last_time = now
    return score

# -----------------------------------
# 위험도 상태 함수
# -----------------------------------
def risk_status(score):
    if score < 5:
        return "🟢 낮음"
    elif score < 10:
        return "🟡 보통"
    else:
        return "🔴 높음"

# -----------------------------------
# 사이드바 - 의존도 분석
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("📊 AI 의존도 분석")

st.sidebar.metric("현재 위험도", risk_status(st.session_state.risk_score))
st.sidebar.metric("위험 점수", st.session_state.risk_score)
st.sidebar.metric("총 질문 수", st.session_state.question_count)
st.sidebar.metric("경고 횟수", st.session_state.warning_count)

# -----------------------------------
# 질문 수준 분석
# -----------------------------------
if st.session_state.question_lengths:
    avg_len = sum(st.session_state.question_lengths) / len(st.session_state.question_lengths)

    if avg_len < 10:
        level = "짧음"
    elif avg_len < 30:
        level = "보통"
    else:
        level = "깊이 있는 질문"

    st.sidebar.metric("질문 수준", level)

# -----------------------------------
# 자기 점검
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("🪞 자기 점검")

check1 = st.sidebar.checkbox("AI 답변을 읽고 다시 생각해봤나요?")
check2 = st.sidebar.checkbox("답만 복사하지 않았나요?")
check3 = st.sidebar.checkbox("내 생각을 먼저 정리했나요?")
check4 = st.sidebar.checkbox("AI 없이 설명할 수 있나요?")

reflection_score = sum([check1, check2, check3, check4])

st.sidebar.markdown("---")

if reflection_score == 4:
    st.sidebar.success("🌱 건강한 AI 활용 습관을 가지고 있어요!")
elif reflection_score >= 2:
    st.sidebar.info("💡 AI를 참고하되 스스로 사고해보세요.")
else:
    st.sidebar.warning("⚠️ AI 의존도가 높아질 수 있어요.")

# -----------------------------------
# 오늘의 리포트
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("📋 오늘의 사용 리포트")

st.sidebar.write(f"- 질문 수: {st.session_state.question_count}")
st.sidebar.write(f"- 위험 경고: {st.session_state.warning_count}회")
st.sidebar.write(f"- 현재 위험도: {risk_status(st.session_state.risk_score)}")

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

# -----------------------------------
# 질문 처리
# -----------------------------------
if user_input:

    if not api_key:
        st.error("Gemini API Key를 입력해주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.question_count += 1
    st.session_state.question_lengths.append(len(user_input))

    with st.chat_message("user"):
        st.markdown(user_input)

    added_score = analyze_dependency(user_input)
    st.session_state.risk_score += added_score

    if st.session_state.risk_score >= 10:
        st.session_state.warning_count += 1
        st.warning("""
🚨 AI 의존도가 높아지고 있습니다.

정답을 바로 얻는 것도 좋지만,
스스로 사고하는 과정 역시 중요합니다.

잠시 직접 고민해보는 시간을 가져보세요 🙂
""")
        with st.expander("✍️ 먼저 스스로 생각해보기"):
            my_thought = st.text_area("당신의 생각을 먼저 적어보세요")
            if my_thought:
                st.success("좋아요! 스스로 사고하려는 과정이 중요합니다.")

        with st.spinner("⏳ 잠시 스스로 생각해보는 중..."):
            time.sleep(2)

    elif st.session_state.risk_score >= 5:
        st.session_state.warning_count += 1
        st.info("""
💡 AI 답변을 그대로 복사하기보다
왜 이런 답이 나왔는지 고민해보세요.
""")

    prompt = f"""친절한 학습 도우미처럼 답하세요.
사용자가 스스로 생각할 수 있도록 유도하세요.

질문:
{user_input}
"""

    try:
        with st.spinner("AI가 답변 생성 중입니다..."):
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.7
                )
            )
            ai_text = response.text

    except Exception as e:
        ai_text = f"오류 발생: {e}"

    st.session_state.messages.append({"role": "assistant", "content": ai_text})

    with st.chat_message("assistant"):
        st.markdown(ai_text)

# -----------------------------------
# 하단 안내
# -----------------------------------
st.markdown("---")
st.caption("ThinkBack AI · 건강한 AI 활용 습관과 자기주도 학습을 위한 AI 챗봇")
