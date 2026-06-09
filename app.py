import streamlit as st
from openai import OpenAI
import sqlite3
import time
import os
from datetime import datetime

DB_NAME = "thinkback_chat.db"
LIZARD_IMAGE = "lizard.png"

WARNING_SCORE = 5
DANGER_SCORE = 8

st.set_page_config(
    page_title="ThinkBack AI",
    page_icon="🧠",
    layout="centered"
)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def create_chat(title="새 대화"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO chats (title, created_at) VALUES (?, ?)",
        (title, datetime.now().isoformat())
    )

    conn.commit()
    chat_id = cur.lastrowid
    conn.close()
    return chat_id


def get_chats():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM chats ORDER BY id DESC")
    chats = cur.fetchall()

    conn.close()
    return chats


def get_messages(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC",
        (chat_id,)
    )

    rows = cur.fetchall()
    conn.close()

    return [{"role": role, "content": content} for role, content in rows]


def save_message(chat_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def update_chat_title(chat_id, title):
    clean_title = title.strip().replace("\n", " ")

    if len(clean_title) > 25:
        clean_title = clean_title[:25] + "..."

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "UPDATE chats SET title=? WHERE id=?",
        (clean_title, chat_id)
    )

    conn.commit()
    conn.close()


def delete_chat(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))

    conn.commit()
    conn.close()


def analyze_dependency(text):
    score = 0
    text = text.strip()

    danger_words = [
        "답만", "정답", "빨리", "숙제 해줘",
        "그냥 알려줘", "대신 해줘", "요약만",
        "복붙", "생각하기 싫어", "알아서 해줘",
        "그냥 써줘", "답 알려줘", "모르겠어",
        "해줘", "써줘", "풀어줘", "해답",
        "결론만", "바로 답"
    ]

    strong_words = [
        "답만 알려줘",
        "그냥 답",
        "답을 알려달라고",
        "생각하기 싫어",
        "대신 해줘",
        "복붙하게",
        "그냥 써줘",
        "정답만"
    ]

    for word in danger_words:
        if word in text:
            score += 4

    for word in strong_words:
        if word in text:
            score += 6

    if len(text) <= 5:
        score += 4
    elif len(text) <= 10:
        score += 3

    now = time.time()

    if now - st.session_state.last_time < 15:
        score += 4

    st.session_state.last_time = now
    return score


def reset_learning_state():
    st.session_state.risk_score = 0.0
    st.session_state.risk_history = []
    st.session_state.warning_count = 0
    st.session_state.question_count = 0
    st.session_state.question_lengths = []
    st.session_state.last_time = time.time()
    st.session_state.show_lizard = False


init_db()

if "current_chat_id" not in st.session_state:
    chats = get_chats()
    st.session_state.current_chat_id = chats[0][0] if chats else create_chat()

if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0.0

if "risk_history" not in st.session_state:
    st.session_state.risk_history = []

if "warning_count" not in st.session_state:
    st.session_state.warning_count = 0

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "question_lengths" not in st.session_state:
    st.session_state.question_lengths = []

if "last_time" not in st.session_state:
    st.session_state.last_time = time.time()

if "show_lizard" not in st.session_state:
    st.session_state.show_lizard = False


# -----------------------------
# Sidebar: Lizard warning
# -----------------------------
if st.session_state.show_lizard:
    st.sidebar.markdown("## 🚨 과의존 경고")

    if os.path.exists(LIZARD_IMAGE):
        st.sidebar.image(
            LIZARD_IMAGE,
            use_container_width=True
        )
    else:
        st.sidebar.warning("lizard.png 파일을 app.py와 같은 폴더에 넣어주세요.")

    st.sidebar.error("""
AI가 대신 공부해줄 수는 없습니다.

잠시 멈추고 먼저 스스로 생각해보세요!
""")


# -----------------------------
# Sidebar: Chat list
# -----------------------------
st.sidebar.title("💬 대화 목록")

if st.sidebar.button("➕ 새 대화 시작", use_container_width=True):
    st.session_state.current_chat_id = create_chat()
    reset_learning_state()
    st.rerun()

chats = get_chats()

for chat_id, title in chats:
    col1, col2 = st.sidebar.columns([4, 1])

    is_current = chat_id == st.session_state.current_chat_id
    label = f"✅ {title}" if is_current else title

    if col1.button(label, key=f"chat_{chat_id}", use_container_width=True):
        st.session_state.current_chat_id = chat_id
        reset_learning_state()
        st.rerun()

    if col2.button("🗑️", key=f"delete_{chat_id}"):
        delete_chat(chat_id)
        remaining_chats = get_chats()

        if remaining_chats:
            st.session_state.current_chat_id = remaining_chats[0][0]
        else:
            st.session_state.current_chat_id = create_chat()

        reset_learning_state()
        st.rerun()


# -----------------------------
# Sidebar: API
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.title("🔑 API 설정")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")

client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("연결 완료")
    except Exception as e:
        st.sidebar.error(f"연결 오류: {e}")


# -----------------------------
# Sidebar: dependency score
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 AI 의존도")

score = st.session_state.risk_score

if score < WARNING_SCORE:
    st.sidebar.success(f"🟢 낮음 · {score:.1f}점")
elif score < DANGER_SCORE:
    st.sidebar.warning(f"🟡 보통 · {score:.1f}점")
else:
    st.sidebar.error(f"🔴 높음 · {score:.1f}점")

st.sidebar.progress(min(score / 20, 1.0))

col1, col2 = st.sidebar.columns(2)
col1.metric("총 질문", f"{st.session_state.question_count}개")
col2.metric("경고 횟수", f"{st.session_state.warning_count}회")

if st.session_state.risk_history:
    st.sidebar.caption(
        f"최근 3회 위험 점수: {st.session_state.risk_history}"
    )

if st.session_state.question_lengths:
    avg_len = sum(st.session_state.question_lengths) / len(st.session_state.question_lengths)

    if avg_len < 10:
        level = "📝 짧음"
    elif avg_len < 30:
        level = "💬 보통"
    else:
        level = "🧠 깊이 있음"

    st.sidebar.caption(f"질문 수준: **{level}**")


# -----------------------------
# Sidebar: self-check
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🪞 자기 점검")

check1 = st.sidebar.checkbox("답변을 읽고 다시 생각했나요?")
check2 = st.sidebar.checkbox("답만 복사하지 않았나요?")
check3 = st.sidebar.checkbox("내 생각을 먼저 정리했나요?")
check4 = st.sidebar.checkbox("AI 없이 설명할 수 있나요?")

reflection_score = sum([check1, check2, check3, check4])

if reflection_score == 4:
    st.session_state.show_lizard = False

st.sidebar.progress(reflection_score / 4)

if reflection_score == 4:
    st.sidebar.success("🌱 건강한 AI 활용 습관!")
elif reflection_score >= 2:
    st.sidebar.info("💡 조금 더 스스로 생각해봐요")
else:
    st.sidebar.warning("⚠️ 의존도가 높아질 수 있어요")


# -----------------------------
# Main page
# -----------------------------
st.title("🧠 ThinkBack AI")
st.caption("AI 과의존 방지 자기주도 학습 챗봇")

messages = get_messages(st.session_state.current_chat_id)

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("질문을 입력하세요")

if user_input:
    if not api_key:
        st.error("OpenAI API Key를 입력해주세요.")
        st.stop()

    chat_id = st.session_state.current_chat_id

    save_message(chat_id, "user", user_input)

    current_messages = get_messages(chat_id)
    user_messages = [m for m in current_messages if m["role"] == "user"]

    if len(user_messages) == 1:
        update_chat_title(chat_id, user_input)

    st.session_state.question_count += 1
    st.session_state.question_lengths.append(len(user_input))

    with st.chat_message("user"):
        st.markdown(user_input)

    added_score = analyze_dependency(user_input)

    st.session_state.risk_history.append(added_score)
    st.session_state.risk_history = st.session_state.risk_history[-3:]

    st.session_state.risk_score = round(
        sum(st.session_state.risk_history) / len(st.session_state.risk_history),
        1
    )

    if st.session_state.risk_score >= DANGER_SCORE:
        st.session_state.show_lizard = True
        st.session_state.warning_count += 1

    elif st.session_state.risk_score >= WARNING_SCORE:
        st.session_state.warning_count += 1
        st.warning("""
💡 AI 의존도가 조금 올라갔어요.

답을 그대로 받기보다 먼저 내 생각을 적어보면 좋아요.
""")

    try:
        with st.spinner("AI가 답변 생성 중입니다..."):
            recent_messages = get_messages(chat_id)[-12:]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "너는 AI 과의존을 줄이는 자기주도 학습 도우미야. "
                            "반드시 이전 대화 내용을 참고해서 맥락에 맞게 답해야 해. "
                            "사용자가 '그거', '아니', '답만', '방금 것', '알려줘'처럼 짧게 말하면 "
                            "직전 질문과 대화 흐름을 기준으로 이해해. "
                            "처음에는 정답을 바로 알려주기보다 힌트와 사고 과정을 유도해. "
                            "하지만 사용자가 이미 답을 요구했거나 반복해서 물으면 "
                            "이전 질문을 기준으로 짧게 답을 알려주고 이유를 한 문장으로 설명해. "
                            "절대 이전 대화를 모른다고 말하지 마. "
                            "답변은 짧고 친절한 한국어로 해."
                        )
                    },
                    *recent_messages
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_text = response.choices[0].message.content

    except Exception as e:
        ai_text = f"오류 발생: {e}"

    save_message(chat_id, "assistant", ai_text)

    with st.chat_message("assistant"):
        st.markdown(ai_text)

    st.rerun()

st.markdown("---")
st.caption("ThinkBack AI · 건강한 AI 활용 습관과 자기주도 학습을 위한 AI 챗봇")
