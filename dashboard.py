import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
import markdown

# OpenAI client
client = OpenAI(api_key="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")

# Load meeting data
def get_meeting_dataframe():
    MEETING_FILE = "meeting_log.xlsx"
    if not os.path.exists(MEETING_FILE):
        return pd.DataFrame(columns=["Timestamp", "Question", "Answer"])
    df = pd.read_excel(MEETING_FILE)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df

def main():
    st.set_page_config(layout="wide")
    st.title("📈 Meeting Dashboard")

    chat_state_key = "dashboard_chat_log"
    if chat_state_key not in st.session_state:
        st.session_state[chat_state_key] = []

    try:
        df_long = get_meeting_dataframe()
        if df_long.empty:
            st.info("No meeting data available yet.")
            return

        # Date filter
        today = datetime.now().date()
        last_7_days = today - timedelta(days=6)

        st.subheader("📅 Select Date Range")
        date_range = st.date_input(
            "Date Range",
            value=(last_7_days, today),
            min_value=df_long["Timestamp"].min().date(),
            max_value=df_long["Timestamp"].max().date()
        )

        if len(date_range) != 2:
            st.warning("Please select a valid start and end date.")
            return

        start_date, end_date = date_range
        mask = (df_long["Timestamp"].dt.date >= start_date) & (df_long["Timestamp"].dt.date <= end_date)
        df_long = df_long.loc[mask]

        if df_long.empty:
            st.info("No meeting data available for the selected date range.")
            return

        # Pivot data
        df_wide = df_long.pivot(index="Timestamp", columns="Question", values="Answer").reset_index()
        df_wide.rename(columns={
            "Who attended the meeting?": "Attendees",
            "What was the main agenda?": "Agenda",
            "What key decisions were made?": "Decisions",
            "Any action items or follow-ups?": "Action Items",
            "Were there any blockers or risks discussed?": "Blockers"
        }, inplace=True)

        # Summary
        st.subheader("🔢 Summary Metrics")
        col1, col2 = st.columns(2)
        col1.metric("Total Meetings", len(df_wide))
        last_date = pd.to_datetime(df_wide["Timestamp"]).max()
        col2.metric("Last Meeting", last_date.strftime("%b %d, %Y %H:%M"))

        st.subheader("📄 Meeting Data Table")
        st.dataframe(df_wide)

        csv = df_wide.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download as CSV", data=csv, file_name="meeting_data.csv", mime="text/csv")

        # AI Assistant section
        st.subheader("💬 Ask a Question from Meeting Data")

        chat_html = "<div class='chat-area' id='chat-box'>"
        for speaker, msg in st.session_state[chat_state_key]:
            role_class = "user" if speaker == "user" else "bot"
            if speaker == "bot":
                msg = markdown.markdown(msg)
            chat_html += f"""
            <div class='msg {role_class}'>
                <div class='bubble {role_class}'>
                    {msg}
                </div>
            </div>
            """
        chat_html += "</div>"

        components.html(f"""
        <style>
        .chat-area {{
            height: 300px;
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
        {chat_html}
        <script>
            const el = document.getElementById("chat-box");
            if (el) el.scrollTop = el.scrollHeight;
        </script>
        """, height=350, scrolling=True)

        with st.container():
            st.markdown("<div class='bottom-box'>", unsafe_allow_html=True)
            with st.form("chat_form", clear_on_submit=True):
                default_val = st.session_state.pop("dashboard_user_input", "")
                user_input = st.text_input("", value=default_val, placeholder="Ask something about the meetings")
                submitted = st.form_submit_button("Send")
            st.markdown("</div>", unsafe_allow_html=True)

        if submitted and user_input:
            st.session_state[chat_state_key].append(("user", user_input))
            try:
                context_data = df_wide.to_markdown(index=False)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a detailed and structured meeting assistant. Answer user queries based strictly on the provided meeting table. Use bullet points, numbers, or tables if helpful."},
                        {"role": "user", "content": f"Here is the meeting data table:\n\n{context_data}\n\nQuestion: {user_input}"}
                    ]
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                reply = f"Error: {e}"
            st.session_state[chat_state_key].append(("bot", reply))
            streamlit_js_eval(
                js_expressions="""
                setTimeout(() => {
                    const el = document.getElementById("chat-box");
                    if (el) el.scrollTop = el.scrollHeight;
                }, 100);
                """,
                key=f"scroll_{{len(st.session_state[chat_state_key])}}"
            )

        # Suggestion Section styled and positioned below chat
        with st.expander("💡 Need Help? View Common Questions", expanded=False):
            suggestions = [
                ("🕒 Recent", [
                    "What was discussed in the last meeting?",
                    "Who attended the most recent meetings?",
                    "What decisions were made on June 25th?"
                ]),
                ("✅ Tasks & Follow-ups", [
                    "List all action items assigned this week.",
                    "Summarize the action items across all meetings."
                ]),
                ("⚠️ Risks & Blockers", [
                    "Were there any blockers discussed last week?",
                    "List all meetings that had risks discussed."
                ]),
                ("🧠 Insights", [
                    "How many meetings were conducted this month?",
                    "Who attended the most number of meetings?"
                ])
            ]
            for category, questions in suggestions:
                st.markdown(f"### {category}")
                for q in questions:
                    if st.button(q, key=q):
                        st.session_state["dashboard_user_input"] = q

    except Exception as e:
        st.error(f"Could not load meeting data: {e}")

if __name__ == "__main__":
    main()
