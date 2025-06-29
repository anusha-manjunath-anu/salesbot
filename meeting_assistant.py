import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime
import os
import pandas as pd
from openai import OpenAI
import streamlit.components.v1 as components

client = OpenAI(api_key="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")

MEETING_FILE = "meeting_log.xlsx"
meeting_questions = [
    "Who attended the meeting?",
    "What was the main agenda?",
    "What key decisions were made?",
    "Any action items or follow-ups?",
    "Were there any blockers or risks discussed?"
]

def save_meeting_answers(answers: dict):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    records = [{"Timestamp": timestamp, "Question": q, "Answer": a} for q, a in answers.items()]
    df_new = pd.DataFrame(records)
    if os.path.exists(MEETING_FILE):
        df_old = pd.read_excel(MEETING_FILE)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_excel(MEETING_FILE, index=False)

def get_latest_meeting_summary():
    if not os.path.exists(MEETING_FILE):
        return "No previous meeting found."
    df = pd.read_excel(MEETING_FILE)
    latest_time = df["Timestamp"].max()
    latest_df = df[df["Timestamp"] == latest_time]
    summary = "\n".join(f"**{q}**: {a}" for q, a in zip(latest_df['Question'], latest_df['Answer']))
    return f"\U0001F4CB Summary of last meeting ({latest_time}):\n\n{summary}"

def get_bot_response(user_input, session):
    if any(k in user_input.lower() for k in ["summary", "last meeting", "yesterday"]):
        return get_latest_meeting_summary()

    keywords = ["meeting", "discussion", "standup", "sync"]
    if any(k in user_input.lower() for k in keywords) and not session.meeting_mode:
        session.meeting_mode = True
        session.answers = {}
        session.q_index = 0
        return "Let’s log your meeting. " + meeting_questions[0]

    if session.meeting_mode:
        last_q = meeting_questions[session.q_index]
        session.answers[last_q] = user_input
        session.q_index += 1
        if session.q_index < len(meeting_questions):
            return meeting_questions[session.q_index]
        else:
            save_meeting_answers(session.answers)
            session.meeting_mode = False
            return "✅ Meeting notes saved. Thank you!"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    st.set_page_config(layout="wide")

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []
        st.session_state.meeting_mode = False
        st.session_state.answers = {}
        st.session_state.q_index = 0

    st.title("🤖 Meeting Assistant")

    chat_html = """
    <div class='chat-area' id='chat-box'>
    """
    for speaker, msg in st.session_state.chat_log:
        role_class = "user" if speaker == "user" else "bot"
        chat_html += f"""
        <div class='msg {role_class}'>
            <div class='bubble {role_class}'>
                {msg}
            </div>
        </div>
        """
    chat_html += "</div>"

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    .chat-area {{
        height: calc(100vh - 150px);
        overflow-y: auto;
        background: #f9f9f9;
        padding: 1rem 2rem;
        border: 1px solid #ccc;
        border-radius: 8px;
    }}
    .msg.user {{ text-align: right; }}
    .msg.bot {{ text-align: left; }}
    .bubble {{
        display: inline-block;
        padding: 10px 15px;
        border-radius: 20px;
        margin: 5px 0;
        max-width: 70%;
        font-size: 15px;
    }}
    .bubble.user {{ background-color: #007aff; color: white; }}
    .bubble.bot {{ background-color: #e5e5ea; color: black; }}
    </style>
    </head>
    <body>
    {chat_html}
    <script>
        const el = document.getElementById("chat-box");
        if (el) el.scrollTop = el.scrollHeight;
    </script>
    </body>
    </html>
    """, height=500, scrolling=True)

    with st.container():
        st.markdown("<div class='bottom-box'>", unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("", placeholder="Type your message and press Enter")
            submitted = st.form_submit_button("Send")
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted and user_input:
        st.session_state.chat_log.append(("user", user_input))
        bot_reply = get_bot_response(user_input, st.session_state)
        st.session_state.chat_log.append(("bot", bot_reply))
        streamlit_js_eval(
            js_expressions="""
            setTimeout(() => {
                const el = document.getElementById("chat-box");
                if (el) el.scrollTop = el.scrollHeight;
            }, 100);
            """,
            key=f"scroll_{len(st.session_state.chat_log)}"
        )

if __name__ == "__main__":
    main()
