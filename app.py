import streamlit as st
import requests
import pandas as pd
import html
import re
from datetime import datetime

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="RefNote AI", layout="wide")
st.title("📚 RefNote AI")
st.caption("출처 기반 리서치 어시스턴트 (네이버 뉴스 기반)")

# -----------------------------
# 세션 상태
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = {}

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "news_sort" not in st.session_state:
    st.session_state.news_sort = "관련도순"

if "paper_sort" not in st.session_state:
    st.session_state.paper_sort = "관련도순"

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("🔑 네이버 API")

naver_client_id = st.sidebar.text_input("Client ID", type="password")
naver_client_secret = st.sidebar.text_input("Client Secret", type="password")

st.sidebar.markdown("---")
st.sidebar.header("📂 리서치 기록")

for k in st.session_state.history:
    if st.sidebar.button(k):
        st.session_state.current_result = st.session_state.history[k]

# -----------------------------
# 입력
# -----------------------------
topic = st.text_input("어떤 주제로 자료를 준비하나요?")
task_type = st.selectbox("과제 유형", ["논문", "발표"])

# -----------------------------
# 텍스트 정리
# -----------------------------
def clean_text(text):
    text = re.sub(r"<.*?>", "", text)
    return html.unescape(text).strip()

def parse_date(pub_date):
    try:
        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d")
    except:
        return pub_date

# -----------------------------
# 🔥 AI 없이 리서치 질문 생성
# -----------------------------
def generate_questions(topic):
    return [
        f"{topic}의 주요 개념과 특징은 무엇인가?",
        f"{topic}이 사회/교육에 미치는 영향은 무엇인가?",
        f"{topic}과 관련된 정책 또는 개선 방향은 무엇인가?"
    ]

# -----------------------------
# 🔥 키워드 추출
# -----------------------------
def extract_keywords(topic):
    words = re.split(r"[ ,]", topic)
    words = [w for w in words if len(w) > 1]
    return list(dict.fromkeys(words))[:5]

# -----------------------------
# 🔥 연구 동향 (템플릿 기반)
# -----------------------------
def generate_trend(topic):
    return f"""
최근 {topic} 관련 연구에서는 해당 주제의 사회적 영향과 정책적 중요성이 강조되고 있습니다.
특히 교육, 복지, 인식 변화와의 연관성이 주요하게 다뤄지고 있으며,
실질적인 개선 방안과 제도적 지원의 필요성이 지속적으로 제기되고 있습니다.
"""

# -----------------------------
# 네이버 뉴스 검색
# -----------------------------
def search_news(keywords):
    url = "https://openapi.naver.com/v1/search/news.json"

    headers = {
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_client_secret
    }

    results = []

    for kw in keywords:
        params = {
            "query": kw,
            "display": 30,
            "sort": "date"
        }

        try:
            res = requests.get(url, headers=headers, params=params)
            items = res.json().get("items", [])
        except:
            continue

        for item in items:
            results.append({
                "제목": clean_text(item["title"]),
                "요약": clean_text(item["description"]),
                "출처": item["originallink"],
                "작성일": parse_date(item["pubDate"])
            })

    df = pd.DataFrame(results).drop_duplicates()
    return df

# -----------------------------
# 관련도 계산
# -----------------------------
def calc_relevance(df, keywords):
    df["관련도"] = df["제목"].apply(
        lambda t: sum(t.count(k) for k in keywords)
    )
    return df

# -----------------------------
# APA 참고문헌
# -----------------------------
def make_apa(df):
    refs = []
    for _, r in df.head(10).iterrows():
        domain = r["출처"].split("/")[2]
        refs.append(
            f"{domain}. ({r['작성일']}). {r['제목']}. {r['출처']}"
        )
    return refs

# -----------------------------
# 실행
# -----------------------------
if st.button("🔍 리서치 시작") and topic and naver_client_id:

    questions = generate_questions(topic)
    keywords = extract_keywords(topic)
    trend = generate_trend(topic)

    news_df = search_news(keywords)
    news_df = calc_relevance(news_df, keywords)

    result = {
        "topic": topic,
        "task": task_type,
        "questions": questions,
        "keywords": keywords,
        "trend": trend,
        "news": news_df
    }

    label = f"[{task_type}] {topic}"
    st.session_state.history[label] = result
    st.session_state.current_result = result

# -----------------------------
# 출력
# -----------------------------
data = st.session_state.current_result

if data:
    st.subheader("🔍 리서치 질문")
    for q in data["questions"]:
        st.write("•", q)

    st.subheader("🔑 키워드")
    st.write(", ".join(data["keywords"]))

    st.subheader("🧠 연구 동향")
    st.write(data["trend"])

    tab1, tab2 = st.tabs(["📰 뉴스", "📄 논문"])

    # 뉴스
    with tab1:
        st.radio(
            "정렬",
            ["관련도순", "최신순"],
            key="news_sort",
            horizontal=True
        )

        df = data["news"]

        if not df.empty:
            if st.session_state.news_sort == "관련도순":
                df = df.sort_values("관련도", ascending=False)
            else:
                df = df.sort_values("작성일", ascending=False)

            st.dataframe(df.drop(columns=["관련도"]))

            st.subheader("📎 참고문헌")
            for r in make_apa(df):
                st.write(r)
        else:
            st.warning("뉴스 없음")

    # 논문
    with tab2:
        st.radio(
            "정렬",
            ["관련도순", "최신순"],
            key="paper_sort",
            horizontal=True
        )
        st.info("논문 API 연동 예정")
