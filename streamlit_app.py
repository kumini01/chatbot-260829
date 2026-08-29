import streamlit as st
from openai import OpenAI


# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="AI 가족마음 상담소",
    page_icon="💛",
    layout="centered",
)

st.title("💛 AI 가족마음 상담소")
st.write(
    "가족 간 갈등, 대화의 어려움, 양육 고민을 함께 정리해 보세요. "
    "이 서비스는 전문 치료를 대신하지 않는 정서적 지원·정보 제공 도구입니다."
)


# --------------------------------------------------
# API Key
# --------------------------------------------------
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.info("OpenAI API Key를 입력해주세요.", icon="🔑")
    st.stop()

client = OpenAI(api_key=openai_api_key)


# --------------------------------------------------
# 상담 설정
# --------------------------------------------------
st.sidebar.header("💛 상담 설정")

family_relation = st.sidebar.selectbox(
    "주로 이야기하고 싶은 관계",
    [
        "배우자 / 부부",
        "부모와 자녀",
        "형제자매",
        "부모님(성인 자녀와의 관계)",
        "가족 전체",
        "기타",
    ],
)

consulting_topic = st.sidebar.selectbox(
    "상담 주제",
    [
        "갈등과 다툼",
        "대화·의사소통",
        "양육 고민",
        "사춘기·진로 문제",
        "정서적 거리감",
        "돌봄·가족 역할 부담",
        "상실·질병·큰 변화 적응",
        "기타",
    ],
)

if st.sidebar.button("🗑️ 대화 초기화"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "대화를 새로 시작했어요. 지금 가장 마음에 걸리는 가족 이야기를 들려주세요.",
        }
    ]
    st.rerun()


# --------------------------------------------------
# AI 역할 설정
# --------------------------------------------------
SYSTEM_PROMPT = f"""
당신은 가족 관계와 의사소통을 돕는 따뜻하고 신중한 AI 상담 동반자입니다.

사용자가 주로 이야기하고 싶은 관계: {family_relation}
현재 상담 주제: {consulting_topic}

중요한 역할과 한계:
- 당신은 정신건강 전문의, 심리치료사, 법률가를 대체하지 않습니다.
- 진단명이나 약물 복용·중단 지시를 하지 마세요.
- 한 사람을 단정적으로 비난하거나, 상대방의 의도·성격을 추측해 확정하지 마세요.
- 사용자의 감정은 공감하되, 확인되지 않은 사실을 사실처럼 받아들이지 마세요.
- 가족 갈등에서 안전, 존중, 경계 설정을 우선으로 하세요.

위기 대응 원칙:
사용자가 자신이나 타인을 해칠 생각·계획, 폭력·학대, 즉각적인 위험을 말하면
평소 형식보다 안전을 먼저 다루세요. 혼자 있지 말고 가까운 신뢰할 사람이나
긴급 서비스에 즉시 연락하도록 권하세요. 한국 기준으로 즉시 위험하면 112 또는 119,
자살예방 상담전화 109, 정신건강위기 상담전화 1577-0199를 안내하세요.
사용자가 한국 외 지역에 있다면 현지 긴급전화와 위기상담기관 이용을 권하세요.
다만 위험 여부가 불분명하면 차분하게 "지금 본인이나 다른 사람을 다치게 할 위험이 있나요?"라고 물으세요.

상담 원칙:
1. 먼저 사용자의 감정과 상황을 짧게 공감하고 요약하세요.
2. 정보가 부족하면 한 번에 핵심 질문 1~2개만 하세요.
3. '나 전달법', 경청, 구체적 요청, 대화 시간 정하기처럼 바로 실천 가능한 방법을 제안하세요.
4. 갈등의 양쪽 관점과 현실적 제약을 함께 살피세요.
5. 학대, 지속적 공포, 심각한 우울·불안, 중독 등 전문 도움이 필요해 보이면 지역 정신건강복지센터,
   가족센터, 상담기관 또는 의료 전문가와의 상담을 권하세요.
6. 답변은 한국어 존댓말로 작성하세요.

일반 답변은 필요할 때 아래 형식을 사용하세요.

### 💬 마음과 상황
### 🔎 함께 살펴볼 점
### 🌱 지금 해볼 행동
### ❓ 다음 질문
"""


# --------------------------------------------------
# 대화 기록
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """안녕하세요. 저는 **AI 가족마음 상담 동반자**입니다. 💛

가족과의 갈등, 대화의 답답함, 양육 고민을 편하게 말씀해 주세요.

예를 들면:

- 배우자와 같은 문제로 계속 다투는데 어떻게 대화해야 할까요?
- 사춘기 자녀가 말을 하지 않아요.
- 부모님 돌봄 문제로 형제끼리 갈등이 있어요.

다만, 자신이나 다른 사람을 다치게 할 위험이 있거나 폭력이 발생한 상황이라면 즉시 112 또는 119에 도움을 요청해 주세요.""",
        }
    ]


# --------------------------------------------------
# 기존 대화 출력
# --------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# 사용자 질문 및 AI 응답
# --------------------------------------------------
prompt = st.chat_input("가족 관계에서 고민되는 상황을 입력해주세요...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    stream = client.responses.create(
        model="gpt-5.6-terra",
        instructions=SYSTEM_PROMPT,
        input=[
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.messages
        ],
        stream=True,
    )

    def response_generator():
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    with st.chat_message("assistant"):
        response = st.write_stream(response_generator())

    st.session_state.messages.append({"role": "assistant", "content": response})
