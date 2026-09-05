import streamlit as st
from google import genai

st.set_page_config(page_title="Devil's Advocate Agent", page_icon="⚔️")
st.title("⚔️ Devil's Advocate Agent")
st.write("Paste your argument, plan, or pitch — I'll challenge it.")

# Load the API key from Streamlit's secrets
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
client = st.session_state.client

modes = {
    "investor": """You are a Skeptical Investor evaluating a pitch.
Find the single strongest weakness a VC would flag before funding this.
Focus on market size, unit economics, and execution risk. Be specific, 3-5 sentences.""",
    "critic": """You are a Hostile Critic reviewing this argument.
Find the single strongest logical or rhetorical weakness.
Be direct and unsparing, but intellectually honest. 3-5 sentences.""",
    "analyst": """You are a Data-Driven Analyst.
Find the single strongest weakness in terms of missing evidence, unverified
assumptions, or lack of data. Demand specifics. 3-5 sentences.""",
    "ethics": """You are an Ethics-focused Devil's Advocate.
Find the single strongest ethical or values-based weakness in this argument
or plan — unintended harm, fairness issues, or long-term consequences.
3-5 sentences."""
}

# Keep the chat session alive across reruns
if "chat" not in st.session_state:
    st.session_state.chat = None
    st.session_state.messages = []

mode_choice = st.selectbox("Choose a mode:", list(modes.keys()))

claim = st.text_area("Your claim, plan, or pitch:")

if st.button("Start Sparring") and claim:
    st.session_state.chat = client.chats.create(
        model="gemini-3.5-flash",
        config={"system_instruction": modes[mode_choice]}
    )
    response = st.session_state.chat.send_message(f"Here is my claim: \"{claim}\"")
    st.session_state.messages = [("AI", response.text)]

for speaker, text in st.session_state.messages:
    st.chat_message("assistant" if speaker == "AI" else "user").write(text)

if st.session_state.chat:
    rebuttal = st.chat_input("Your rebuttal...")
    if rebuttal:
        st.session_state.messages.append(("You", rebuttal))
        response = st.session_state.chat.send_message(rebuttal)
        st.session_state.messages.append(("AI", response.text))
        st.rerun()

    if st.button("Get Final Scorecard"):
        scorecard_prompt = """Based on our entire conversation above, summarize this debate:
1. The strongest objection you raised
2. Whether the user's rebuttal resolved it, partially resolved it, or didn't resolve it
3. An overall confidence score from 1-10 for the user's original claim, with one sentence explaining why."""
        response = st.session_state.chat.send_message(scorecard_prompt)
        st.subheader("📋 Scorecard")
        st.write(response.text)
