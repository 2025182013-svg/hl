import streamlit as st
from openai import OpenAI
import time

st.set_page_config(
    page_title="ThinkBack AI",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 ThinkBack AI")
st.caption("AI 과의존 방지 자기주도 학습 챗봇")

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

# 사이드바
st.sidebar.title("🔑 API 설정")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("연결 완료")
    except Exception as e:
        st.sidebar.error(f"오류: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 AI 의존도")

score = st.session_state.risk_score
if score < 5:
    st.sidebar.success(f"🟢 낮음 · {score}점")
elif score < 10:
    st.sidebar.warning(f"🟡 보통 · {score}점")
else:
    st.sidebar.error(f"🔴 높음 · {score}점")

st.sidebar.progress(min(score / 20, 1.0))

col1, col2 = st.sidebar.columns(2)
col1.metric("총 질문", f"{st.session_state.question_count}개")
col2.metric("경고 횟수", f"{st.session_state.warning_count}회")

# 디버그: 대화 메시지 수 확인
st.sidebar.caption(f"🗨️ 저장된 대화 수: {len(st.session_state.messages)}")

if st.session_state.question_lengths:
    avg_len = sum(st.session_state.question_lengths) / len(st.session_state.question_lengths)
    if avg_len < 10:
        level = "📝 짧음"
    elif avg_len < 30:
        level = "💬 보통"
    else:
        level = "🧠 깊이 있음"
    st.sidebar.caption(f"질문 수준: **{level}**")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🪞 자기 점검")

checks = [
    st.sidebar.checkbox("답변을 읽고 다시 생각했나요?"),
    st.sidebar.checkbox("답만 복사하지 않았나요?"),
    st.sidebar.checkbox("내 생각을 먼저 정리했나요?"),
    st.sidebar.checkbox("AI 없이 설명할 수 있나요?"),
]
reflection_score = sum(checks)
st.sidebar.progress(reflection_score / 4)

if reflection_score == 4:
    st.sidebar.success("🌱 건강한 AI 활용 습관!")
elif reflection_score >= 2:
    st.sidebar.info("💡 조금 더 스스로 생각해봐요")
else:
    st.sidebar.warning("⚠️ 의존도가 높아질 수 있어요")


def analyze_dependency(text):
    score = 0
    danger_words = [
        "답만", "정답", "빨리", "숙제 해줘",
        "그냥 알려줘", "대신 해줘", "요약만",
        "복붙", "생각하기 싫어", "알아서 해줘",
        "그냥 써줘", "답 알려줘"
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


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("질문을 입력하세요")

if user_input:

    if not api_key:
        st.error("OpenAI API Key를 입력해주세요.")
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
        st.image("lizard.png", caption="🦎 스스로 생각해보세요!", use_container_width=True)
        st.warning("""
🚨 AI 의존도가 너무 높아요!

답을 바로 받는 것보다
스스로 고민하는 과정이 훨씬 중요합니다.

잠깐, 먼저 혼자 생각해볼까요? 🙂
""")
        with st.expander("✍️ 내 생각 먼저 적어보기"):
            my_thought = st.text_area("당신의 생각을 먼저 적어보세요")
            if my_thought:
                st.success("좋아요! 스스로 사고하려는 과정이 중요합니다.")
        with st.spinner("⏳ 잠시 스스로 생각해보는 중..."):
            time.sleep(2)

    elif st.session_state.risk_score >= 5:
        st.session_state.warning_count += 1
        st.info("💡 AI 답변을 그대로 복사하기보다 왜 이런 답이 나왔는지 고민해보세요.")

    try:
        with st.spinner("AI가 답변 생성 중입니다..."):
            recent_messages = st.session_state.messages[-10:]
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "너는 학습 도우미야. 반드시 이전 대화 내용을 기억하고 맥락에 맞게 답해야 해. "
                            "정답을 바로 알려주기보다 스스로 생각할 수 있도록 힌트를 주고 유도해. "
                            "절대 이전 대화를 모른다고 하지 마. 짧고 친절하게 답해."
                        )
                    },
                    *recent_messages
                ],
                max_tokens=300,
                temperature=0.7
            )
            ai_text = response.choices[0].message.content

    except Exception as e:
        ai_text = f"오류 발생: {e}"

    st.session_state.messages.append({"role": "assistant", "content": ai_text})

    with st.chat_message("assistant"):
        st.markdown(ai_text)

st.markdown("---")
st.caption("ThinkBack AI · 건강한 AI 활용 습관과 자기주도 학습을 위한 AI 챗봇")
