import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


SHARE_DATA_FILE = Path("shared_consultations.json")


def load_shared_consultations():
    if not SHARE_DATA_FILE.exists():
        return {}
    try:
        return json.loads(SHARE_DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_shared_consultations(data):
    SHARE_DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_share_url(share_id):
    """배포 URL은 .streamlit/secrets.toml의 APP_BASE_URL로 설정합니다."""
    base_url = st.secrets.get("APP_BASE_URL", "http://localhost:8501").rstrip("/")
    return f"{base_url}?{urlencode({'share': share_id})}"


def get_last_consultation():
    """대화 전체가 아닌 마지막 질문·답변만 공유합니다."""
    messages = st.session_state.messages
    last_user_index = next(
        (i for i in range(len(messages) - 1, -1, -1) if messages[i]["role"] == "user"),
        None,
    )
    if last_user_index is None:
        return None
    answer = next(
        (m["content"] for m in messages[last_user_index + 1 :] if m["role"] == "assistant"),
        "",
    )
    return {"question": messages[last_user_index]["content"], "answer": answer}


def render_kakao_share_button(share_url, title):
    """KAKAO_JAVASCRIPT_KEY가 설정된 경우 카카오톡 공유 버튼을 렌더링합니다."""
    kakao_key = st.secrets.get("KAKAO_JAVASCRIPT_KEY", "")
    if not kakao_key:
        st.sidebar.info("카카오톡 공유는 KAKAO_JAVASCRIPT_KEY 설정 후 사용할 수 있습니다.")
        return

    components.html(
        f"""
        <script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js"></script>
        <button id="kakao-share" style="background:#FEE500;border:0;border-radius:8px;padding:10px 16px;font-weight:bold;cursor:pointer;">
          💬 카카오톡으로 공유
        </button>
        <script>
          if (!Kakao.isInitialized()) Kakao.init({json.dumps(kakao_key)});
          document.getElementById('kakao-share').onclick = () => Kakao.Share.sendDefault({{
            objectType: 'feed',
            content: {{
              title: {json.dumps(title, ensure_ascii=False)},
              description: 'AI 가족마음 상담 내용을 확인해 보세요.',
              imageUrl: 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=800&q=80',
              link: {{ mobileWebUrl: {json.dumps(share_url)}, webUrl: {json.dumps(share_url)} }}
            }},
            buttons: [{{ title: '상담 내용 보기', link: {{ mobileWebUrl: {json.dumps(share_url)}, webUrl: {json.dumps(share_url)} }} }}]
          }});
        </script>
        """,
        height=55,
    )


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

# 공유 링크로 열렸을 때는 API Key 없이 공개된 익명 상담을 먼저 보여줍니다.
share_id = st.query_params.get("share")
if share_id:
    shared_item = load_shared_consultations().get(share_id)
    if shared_item:
        st.info("작성자가 익명 공개에 동의한 상담 내용입니다.", icon="🔗")
        st.subheader(shared_item["title"])
        st.caption(f"공유일: {shared_item['created_at']}")
        st.markdown("### 🙋 고민")
        st.markdown(shared_item["question"])
        st.markdown("### 💛 상담 답변")
        st.markdown(shared_item["answer"])
        st.divider()
    else:
        st.warning("공유 상담을 찾을 수 없거나 삭제되었습니다.")


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
# 음성 입력
# --------------------------------------------------
st.divider()
st.caption("🎙️ 음성으로 상담하기")
audio_value = st.audio_input("마이크 버튼을 눌러 고민을 말씀해 주세요.")
voice_prompt = None

if audio_value and st.button("음성을 글로 바꾸고 상담하기"):
    with st.spinner("음성을 텍스트로 변환하고 있습니다..."):
        try:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=("family_counseling_audio.wav", audio_value.getvalue(), audio_value.type),
                language="ko",
            )
            voice_prompt = transcription.text.strip()
        except Exception as error:
            st.error(f"음성을 처리하지 못했습니다. 마이크 권한과 API 설정을 확인해주세요. ({error})")


# --------------------------------------------------
# 텍스트 질문 및 AI 응답
# --------------------------------------------------
typed_prompt = st.chat_input("가족 관계에서 고민되는 상황을 입력해주세요...")
prompt = voice_prompt or typed_prompt

if prompt:
    if voice_prompt:
        st.success(f"음성 해석 결과: {voice_prompt}")
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


# --------------------------------------------------
# 지식인 형태의 익명 공유 및 카카오톡 공유
# --------------------------------------------------
st.sidebar.divider()
st.sidebar.subheader("🔗 상담 사연 공유")
st.sidebar.caption(
    "마지막 질문과 답변만 공개됩니다. 이름·연락처·학교·직장·구체적 장소 등 개인정보를 지운 뒤 공유해주세요."
)
share_consent = st.sidebar.checkbox("개인정보를 제거했고, 익명 공개에 동의합니다.")
share_title = st.sidebar.text_input("공유 글 제목", value="가족마음 상담 이야기", max_chars=60)

if st.sidebar.button("익명 공유 링크 만들기", disabled=not share_consent):
    consultation = get_last_consultation()
    if not consultation or not consultation["answer"]:
        st.sidebar.warning("AI 답변이 포함된 상담 후에 공유할 수 있습니다.")
    else:
        new_share_id = uuid.uuid4().hex
        shared_consultations = load_shared_consultations()
        shared_consultations[new_share_id] = {
            "title": share_title,
            "question": consultation["question"],
            "answer": consultation["answer"],
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        save_shared_consultations(shared_consultations)
        st.session_state.last_share_url = make_share_url(new_share_id)
        st.sidebar.success("익명 공유 링크를 만들었습니다.")

if st.session_state.get("last_share_url"):
    st.sidebar.link_button("🔗 공유 상담 열기", st.session_state.last_share_url)
    render_kakao_share_button(st.session_state.last_share_url, share_title)
