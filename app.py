import streamlit as st
import google.generativeai as genai
import time

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
# 세션 상태
# -----------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0

if "warning_count" not in st.session_state:
    st.session_state.warning_count = 0

if "last_time" not in st.session_state:
    st.session_state.last_time = time.time()

# -----------------------------------
# 사이드바
# -----------------------------------
st.sidebar.title("🔑 Gemini API")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password"
)

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------------
# 과의존 분석
# -----------------------------------
def analyze_dependency(text):
    score = 0

    danger_words = [
        "답만",
        "정답",
        "빨리",
        "숙제 해줘",
        "그냥 알려줘",
        "대신 해줘"
    ]

    for word in danger_words:
        if word in text:
            score += 3

    if len(text) < 8:
        score += 2

    return score

# -----------------------------------
# 위험도 표시
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("📊 AI 의존도")

risk = st.session_state.risk_score

if risk < 5:
    st.sidebar.success(f"🟢 낮음 ({risk})")
elif risk < 10:
    st.sidebar.warning(f"🟡 보통 ({risk})")
else:
    st.sidebar.error(f"🔴 높음 ({risk})")

st.sidebar.write(f"경고 횟수: {st.session_state.warning_count}")

# -----------------------------------
# 자기 점검
# -----------------------------------
st.sidebar.markdown("---")
st.sidebar.title("🪞 자기 점검")

st.sidebar.checkbox("AI 답변을 읽고 다시 생각해봤나요?")
st.sidebar.checkbox("답만 복사하지 않았나요?")
st.sidebar.checkbox("내 생각을 먼저 정리했나요?")
st.sidebar.checkbox("AI 없이 설명할 수 있나요?")

# -----------------------------------
# 채팅 출력
# -----------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------
# 입력
# -----------------------------------
user_input = st.chat_input("질문을 입력하세요")

if user_input and api_key:

    # 사용자 메시지 저장
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # 위험도 분석
    added = analyze_dependency(user_input)
    st.session_state.risk_score += added

    # 경고창
    if st.session_state.risk_score >= 10:
        st.session_state.warning_count += 1

        st.warning("""
🚨 AI 의존도가 높아지고 있습니다.

정답을 바로 얻는 것도 좋지만,
스스로 사고하는 과정 역시 중요합니다.
""")

        with st.expander("✍️ 먼저 스스로 생각해보기"):
            st.text_area("당신의 생각을 먼저 적어보세요")

    # -----------------------------------
    # Gemini 응답 생성
    # -----------------------------------
    prompt = f"""
사용자의 질문에 답변하되,
무조건 정답만 주기보다
생각할 수 있는 방향도 함께 제시하세요.

사용자 질문:
{user_input}
"""

    try:
        response = model.generate_content(prompt)
        ai_text = response.text

    except Exception as e:
        ai_text = f"오류 발생: {e}"

    # 저장
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_text
    })

    # 출력
    with st.chat_message("assistant"):
        st.markdown(ai_text)

# -----------------------------------
# 하단
# -----------------------------------
st.markdown("---")
st.caption("ThinkBack AI · 건강한 AI 활용 습관 만들기")
