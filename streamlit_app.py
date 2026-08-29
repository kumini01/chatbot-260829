import streamlit as st
from openai import OpenAI

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="AI 창업 상담소",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 AI 창업 상담소")

st.write(
    """
    창업 아이디어부터 고객 분석, 비즈니스 모델, MVP, 마케팅까지
    AI와 함께 사업 아이디어를 구체화해 보세요.
    """
)

# --------------------------------------------------
# API KEY
# --------------------------------------------------

openai_api_key = st.text_input(
    "OpenAI API Key",
    type="password"
)

if not openai_api_key:
    st.info(
        "OpenAI API Key를 입력해주세요.",
        icon="🔑"
    )
    st.stop()

client = OpenAI(api_key=openai_api_key)


# --------------------------------------------------
# 창업 정보 선택
# --------------------------------------------------

st.sidebar.header("🚀 창업 상담 설정")

startup_stage = st.sidebar.selectbox(
    "현재 창업 단계",
    [
        "아이디어 단계",
        "시장 조사 단계",
        "MVP 개발 단계",
        "서비스 출시 단계",
        "마케팅 / 고객 확보 단계",
        "성장 단계"
    ]
)

consulting_topic = st.sidebar.selectbox(
    "상담하고 싶은 분야",
    [
        "창업 아이디어",
        "고객 / 시장 분석",
        "비즈니스 모델",
        "수익 모델",
        "MVP 기획",
        "마케팅 전략",
        "사업계획서",
        "투자 / 자금 조달",
        "정부지원사업",
        "기타"
    ]
)


# --------------------------------------------------
# AI 역할 설정
# --------------------------------------------------

SYSTEM_PROMPT = f"""
당신은 예비 창업자와 초기 스타트업을 돕는 전문 창업 컨설턴트입니다.

사용자의 현재 창업 단계:
{startup_stage}

현재 상담 분야:
{consulting_topic}

사용자의 아이디어를 무조건 긍정적으로 평가하지 말고
시장성, 고객 문제, 경쟁력, 비즈니스 모델,
수익성, 실행 가능성을 객관적으로 분석하세요.

상담 원칙:

1. 사용자의 상황을 먼저 파악하세요.
2. 정보가 부족하면 가장 중요한 질문 1~2개를 하세요.
3. 창업 아이디어의 장점과 위험요인을 함께 설명하세요.
4. 추상적인 조언보다 구체적인 실행 방법을 알려주세요.
5. 어려운 창업 용어는 초보자도 이해할 수 있도록 설명하세요.
6. 숫자나 시장 규모를 근거 없이 만들어내지 마세요.
7. 법률, 세금, 정책, 지원사업 등 최신 정보가 필요한 경우
   최신 공식 자료를 확인해야 한다고 알려주세요.
8. 답변은 한국어로 작성하세요.

가능하면 다음 형식을 사용하세요.

### 🔍 현재 상황
사용자의 상황을 간단히 정리합니다.

### 💡 분석
사업 아이디어나 문제를 분석합니다.

### ⚠️ 체크할 부분
위험 요소나 검증해야 할 가설을 알려줍니다.

### 🚀 다음 행동
사용자가 지금 바로 할 수 있는 행동을 1~3개 제안합니다.

### ❓ 다음 질문
다음 상담을 위해 중요한 질문을 합니다.
"""


# --------------------------------------------------
# 대화 기록
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
안녕하세요! 👋

저는 **AI 창업 상담가**입니다.

예를 들어 이렇게 질문해 보세요.

- 카페 창업을 하고 싶은데 시장성이 있을까요?
- AI를 이용한 교육 서비스를 만들고 싶어요.
- 제 아이디어의 고객은 누구일까요?
- 이 아이디어로 어떻게 돈을 벌 수 있을까요?
- MVP에는 어떤 기능만 넣어야 할까요?

만들고 싶은 사업이나 아이디어를 편하게 말씀해주세요. 🚀
"""
        }
    ]


# --------------------------------------------------
# 기존 대화 출력
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# 사용자 질문
# --------------------------------------------------

prompt = st.chat_input(
    "창업 아이디어나 고민을 입력해주세요..."
)

if prompt:

    # 사용자 메시지 저장
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(prompt)


    # --------------------------------------------------
    # OpenAI API
    # --------------------------------------------------

    stream = client.responses.create(

        model="gpt-5.6-terra",

        instructions=SYSTEM_PROMPT,

        input=[
            {
                "role": message["role"],
                "content": message["content"]
            }
            for message in st.session_state.messages
        ],

        stream=True
    )


    # --------------------------------------------------
    # 스트리밍 Generator
    # --------------------------------------------------

    def response_generator():

        for event in stream:

            if event.type == "response.output_text.delta":
                yield event.delta


    # --------------------------------------------------
    # AI 답변 출력
    # --------------------------------------------------

    with st.chat_message("assistant"):

        response = st.write_stream(
            response_generator()
        )


    # AI 답변 저장
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )
