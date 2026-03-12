import json
import os
import random
from collections import Counter
import streamlit as st

AXIS_PAIRS = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
TIEBREAK = {"E": "I", "S": "N", "T": "F", "J": "P"}

# 실제 청년기자단 모집 링크로 바꿔서 사용
APPLY_URL = "http://www.dgyouth.kr/board/notice.asp?num=2602&pmode=VIEW&board=notice&page=1&sKey=&sWord=&pCate=0"


def load_json(filename: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def choose_letter(scores, a, b, tie_pick):
    if scores[a] > scores[b]:
        return a
    if scores[b] > scores[a]:
        return b
    return tie_pick


def get_code(scores):
    code = ""
    for a, b in AXIS_PAIRS:
        code += choose_letter(scores, a, b, TIEBREAK.get(a, b))
    return code


def compute_scores(questions, answers):
    scores = Counter()
    for q in questions:
        qid = q["id"]
        pick = answers.get(qid)
        if pick is None:
            continue
        choice = q["choices"][pick]
        for k, v in choice["score"].items():
            scores[k] += v
    return scores


def current_question(questions):
    real_index = st.session_state.order[st.session_state.idx]
    return questions[real_index]


def reset_all(questions):
    st.session_state.order = list(range(len(questions)))
    random.shuffle(st.session_state.order)
    st.session_state.idx = 0
    st.session_state.answers = {}
    st.session_state.done = False
    st.session_state.just_auto_advanced = False
    st.rerun()


def go_next(questions):
    if st.session_state.idx < len(questions) - 1:
        st.session_state.idx += 1
        st.session_state.just_auto_advanced = True
    else:
        st.session_state.done = True


def go_prev():
    if st.session_state.idx > 0:
        st.session_state.idx -= 1
        st.session_state.just_auto_advanced = False


def on_pick_change(questions, qid: str):
    """
    최초 선택 시 자동 다음으로 이동
    """
    if st.session_state.get("just_auto_advanced", False):
        st.session_state.just_auto_advanced = False
        return

    pick_key = f"pick_{qid}"
    picked = st.session_state.get(pick_key, None)

    prev = st.session_state.answers.get(qid, None)
    if prev is None and picked in (0, 1):
        st.session_state.answers[qid] = picked
        go_next(questions)
        st.rerun()

    if prev in (0, 1) and picked in (0, 1) and prev != picked:
        st.session_state.answers[qid] = picked


def find_result_image(code: str):
    """
    결과 코드와 같은 이름의 이미지 파일 찾기
    예: images/INTP.png, images/INTP.jpg
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    exts = ["png", "jpg", "jpeg", "webp"]

    for ext in exts:
        abs_path = os.path.join(base_dir, "images", f"{code}.{ext}")
        if os.path.exists(abs_path):
            return abs_path
    return None


def find_question_image(relative_path: str):
    """
    questions_reporter.json 안의 image 경로를 실제 파일 경로로 변환
    """
    if not relative_path:
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(base_dir, relative_path)

    if os.path.exists(abs_path):
        return abs_path
    return None


st.set_page_config(page_title="청년기자단 유형 테스트", page_icon="🎤", layout="centered")
st.title("🎤 청년기자단 유형 테스트")
st.caption("나는 어떤 스타일의 청년기자일까? · 카드형 · 선택하면 자동으로 다음으로 넘어갑니다.")

questions = load_json("questions_reporter.json")
types = load_json("types_reporter.json")

# 세션 상태 초기화
if "order" not in st.session_state:
    st.session_state.order = list(range(len(questions)))
    random.shuffle(st.session_state.order)

if "idx" not in st.session_state:
    st.session_state.idx = 0

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "done" not in st.session_state:
    st.session_state.done = False

if "just_auto_advanced" not in st.session_state:
    st.session_state.just_auto_advanced = False

total = len(questions)
current = st.session_state.idx + 1
st.progress(current / total, text=f"{current} / {total}")

# =========================
# 결과 화면
# =========================
if st.session_state.done:
    scores = compute_scores(questions, st.session_state.answers)
    code = get_code(scores)
    persona = types.get(code)

    st.success("✨ 당신의 청년기자 유형이 나왔습니다!")
    st.balloons()

    if persona:
        result_img = find_result_image(code)
        if result_img:
            st.image(result_img, use_container_width=True)

        st.markdown(f"## {persona['nickname']} ({code})")
        st.markdown(f"### “{persona['one_liner']}”")
        st.caption(f"{persona.get('group', '')} · {persona.get('tag', '')}")

        st.divider()

        st.subheader("🤝 잘 맞는 케미")
        best_match = persona.get("best_match", "")
        if best_match:
            st.markdown(f"**{best_match}**")
        else:
            st.write("추가 예정")

        st.divider()

        st.subheader("🎤 청년기자단에 지원해보세요")
        st.write(
            "청년의 이야기와 현장을 기록하고, 정책과 이슈를 청년의 시선으로 풀어내는 활동입니다."
        )

        if APPLY_URL:
            st.link_button("청년기자단 지원 알아보기", APPLY_URL, use_container_width=True)
        else:
            st.info("지원 링크를 아직 넣지 않았습니다.")

    else:
        st.markdown(f"## {code}")
        st.warning("types_reporter.json에 이 코드가 없습니다. 파일을 확인해 주세요.")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시하기", use_container_width=True):
            reset_all(questions)

    with col2:
        if persona:
            share_text = (
                f"청년기자단 유형 테스트 결과: {persona['nickname']} ({code})\n"
                f"“{persona['one_liner']}”\n"
                f"{persona.get('group', '')} · {persona.get('tag', '')}\n"
                f"잘 맞는 케미: {persona.get('best_match', '')}"
            )
        else:
            share_text = f"청년기자단 유형 테스트 결과: {code}"

        st.download_button(
            "📋 결과 텍스트 저장",
            data=share_text,
            file_name="reporter_type_result.txt",
            use_container_width=True
        )

    with st.expander("디버그(축 점수 보기)"):
        st.write({k: scores[k] for k in ["E", "I", "S", "N", "T", "F", "J", "P"]})

    st.caption("※ 본 테스트는 재미와 자기이해를 위한 참고용 콘텐츠이며, 심리검사·진단 목적이 아닙니다.")
    st.stop()

# =========================
# 질문 화면
# =========================
q = current_question(questions)
qid = q["id"]

st.markdown(f"### {q['prompt']}")

img = q.get("image")
if img:
    img_path = find_question_image(img)
    if img_path:
        st.image(img_path, use_container_width=True)
    else:
        st.caption(f"(이미지 파일을 못 찾음: {img})")

choices = [q["choices"][0]["text"], q["choices"][1]["text"]]
existing = st.session_state.answers.get(qid, None)

st.radio(
    label="",
    options=[0, 1],
    format_func=lambda x: choices[x],
    index=existing if existing in (0, 1) else 0,
    key=f"pick_{qid}",
    label_visibility="collapsed",
    on_change=on_pick_change,
    args=(questions, qid),
)

picked_now = st.session_state.get(f"pick_{qid}", 0)
st.session_state.answers[qid] = picked_now

st.divider()

left, mid, right = st.columns([1, 1, 1])

with left:
    st.button(
        "⬅️ 이전",
        on_click=go_prev,
        use_container_width=True,
        disabled=(st.session_state.idx == 0)
    )

with mid:
    if st.session_state.idx == total - 1:
        st.button(
            "🎉 결과 보기",
            on_click=lambda: go_next(questions),
            use_container_width=True
        )
    else:
        st.button(
            "➡️ 다음",
            on_click=lambda: go_next(questions),
            use_container_width=True
        )

with right:
    st.button(
        "🔄 초기화",
        on_click=lambda: reset_all(questions),
        use_container_width=True
    )
