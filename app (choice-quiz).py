import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import time

st.title("4択クイズ（CSV版）")

# ==== CSV読み込み ====
uploaded_file = st.file_uploader("問題CSVをアップロードしてください（列名: 問題, 答え）", type=["csv"])
if uploaded_file is None:
    st.info("まずは CSV をアップロードしてください。")
    st.stop()

try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, encoding="shift-jis")

if not {"問題", "答え"}.issubset(df.columns):
    st.error("CSVには『問題』『答え』列が必要です。")
    st.stop()

# ==== セッション初期化 ====
ss = st.session_state
if "remaining" not in ss: ss.remaining = df.to_dict("records")
if "current" not in ss: ss.current = None
if "phase" not in ss: ss.phase = "quiz"   # quiz / feedback / done
if "last_outcome" not in ss: ss.last_outcome = None
if "start_time" not in ss: ss.start_time = time.time()

def next_question():
    if not ss.remaining:
        ss.current = None
        ss.phase = "done"
        return
    ss.current = random.choice(ss.remaining)
    ss.phase = "quiz"
    ss.last_outcome = None

def reset_quiz():
    ss.remaining = df.to_dict("records")
    ss.current = None
    ss.phase = "quiz"
    ss.last_outcome = None
    ss.start_time = time.time()

# ==== 全問終了 ====
if ss.phase == "done":
    st.success("全問終了！お疲れさまでした🎉")

    elapsed = int(time.time() - ss.start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60
    st.info(f"所要時間: {minutes}分 {seconds}秒")

    if st.button("もう一回"):
        reset_quiz()
        st.rerun()
    st.stop()

# ==== 新しい問題 ====
if ss.current is None and ss.phase == "quiz":
    next_question()

# ==== 出題 ====
if ss.phase == "quiz" and ss.current:
    current = ss.current
    st.subheader(f"問題: {current['問題']}")

    # --- 4択生成 ---
    correct_answer = current["答え"]
    other_answers = [r["答え"] for r in df.to_dict("records") if r != current]
    choices = random.sample(other_answers, min(3, len(other_answers)))
    choices.append(correct_answer)
    random.shuffle(choices)

    choice_map = {str(i+1): ans for i, ans in enumerate(choices)}

    # 表示
    for num, ans in choice_map.items():
        st.write(f"{num}. {ans}")

    with st.form("answer_form", clear_on_submit=True):
        ans = st.text_input("番号を入力（1〜4）", max_chars=1, key="answer_box")
        submitted = st.form_submit_button("解答")

    # 自動フォーカス
    components.html(
        """
        <script>
        const box = window.parent.document.querySelector('input[type="text"]');
        if (box) { box.focus(); box.select(); }
        </script>
        """,
        height=0,
    )

    if submitted and ans in choice_map:
        if choice_map[ans] == correct_answer:
            ss.remaining = [q for q in ss.remaining if q != current]
            ss.last_outcome = ("correct", correct_answer)
        else:
            ss.last_outcome = ("wrong", correct_answer)
        ss.phase = "feedback"
        st.rerun()

# ==== フィードバック ====
if ss.phase == "feedback" and ss.last_outcome:
    status, answer = ss.last_outcome
    if status == "correct":
        st.success(f"正解！ {answer} 🎉")
    else:
        st.error(f"不正解！ 正解は {answer}")

    if st.button("次の問題へ"):
        next_question()
        st.rerun()
