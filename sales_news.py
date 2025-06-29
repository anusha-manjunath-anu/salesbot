import streamlit as st 
import openai
import requests
from bs4 import BeautifulSoup

# === CONFIG ===
openai.api_key = "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"

# === UTILS ===
def deduplicate(items):
    seen = set()
    cleaned = []
    for item in items:
        t = item.strip()
        if len(t) > 10 and t not in seen:
            cleaned.append(t)
            seen.add(t)
    return cleaned

# === NEWS SCRAPERS ===
def fetch_bloomberg_asia():
    try:
        url = "https://www.bloomberg.com/asia"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h1, h2, h3, a[data-tracking-context='headline']")
        return deduplicate([item.text for item in items if item.text.strip()])
    except Exception as e:
        return [f"Error fetching Bloomberg: {e}"]

def fetch_fox_business():
    try:
        url = "https://www.foxbusiness.com/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h2.title, h3.title, a")
        return deduplicate([item.text for item in items if item.text.strip()])
    except Exception as e:
        return [f"Error fetching Fox: {e}"]

# === CHATBOT ===
def get_news_summary(user_input, context_headlines):
    context = "\n".join(f"- {line}" for line in context_headlines)
    messages = [
        {"role": "system", "content": f"You are a sales and market insights assistant. Use only this context:\n{context}"},
        {"role": "user", "content": user_input}
    ]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI Error: {e}"

# === STREAMLIT APP ===
def main():
    st.set_page_config("📊 Sector Dashboard", layout="wide")
    st.title("📊 Sector-wise Sales & Market Insights Dashboard")

    # Scrape news and categorize
    general = fetch_bloomberg_asia() + fetch_fox_business()
    sectors = {
        "General": general,
        "BFSI": [h for h in general if "bank" in h.lower() or "finance" in h.lower()],
        "Retail": [h for h in general if "retail" in h.lower()],
        "Healthcare": [h for h in general if "health" in h.lower()],
        "Opportunities": [h for h in general if any(word in h.lower() for word in ["opportunity", "growth", "expansion", "investment"])]
    }

    tabs = st.tabs(sectors.keys())

    for sector, tab in zip(sectors.keys(), tabs):
        with tab:
            st.subheader(f"🤖 {sector} Sector Chatbot")

            if f"{sector}_chat_log" not in st.session_state:
                st.session_state[f"{sector}_chat_log"] = []

            user_input = st.text_input(f"Ask about {sector} insights:", key=f"{sector}_input")

            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("Ask", key=f"{sector}_ask") and user_input:
                    reply = get_news_summary(user_input, sectors[sector])
                    st.session_state[f"{sector}_chat_log"].insert(0, ("Bot", reply))
                    st.session_state[f"{sector}_chat_log"].insert(0, ("You", user_input))
            with col2:
                if st.button("Clear Chat", key=f"{sector}_clear"):
                    st.session_state[f"{sector}_chat_log"] = []

            for speaker, msg in st.session_state[f"{sector}_chat_log"]:
                st.markdown(f"**{speaker}:** {msg}")

            st.divider()
            st.subheader(f"📰 {sector} Headlines")
            for item in sectors[sector][:10]:
                st.write("•", item)

if __name__ == "__main__":
    main()