import streamlit as st
from google import genai

st.set_page_config(page_title="Devil's Advocate Agent", page_icon="⚔️", layout="centered")

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
client = st.session_state.client

st.title("⚔️ Devil's Advocate Agent")
st.write("Paste your argument, plan, or pitch — I'll challenge it.")

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

def safe_send(chat, message):
    """Sends a message and handles temporary server errors gracefully."""
    try:
        return chat.send_message(message).text
    except Exception as e:
        if "UNAVAILABLE" in str(e) or "503" in str(e):
            return "⚠️ The AI is experiencing high demand right now. Please wait a moment and try again."
        elif "429" in str(e):
            return "⚠️ We've hit a usage limit for now. Please wait a minute before trying again."
        else:
            return f"⚠️ Something went wrong: {str(e)[:200]}"

def detect_mode(claim):
    detection_prompt = f"""Given this claim/plan, pick the SINGLE best mode to
challenge it from the list below. Reply with ONLY the mode name, nothing else.

Modes:
- investor: for business plans, pitches, funding-related claims
- critic: for opinions, essays, general arguments
- analyst: for claims relying on data, stats, or research
- ethics: for claims involving fairness, harm, or values

Claim: "{claim}"

Reply with exactly one word: investor, critic, analyst, or ethics."""
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=detection_prompt
        )
        detected = response.text.strip().lower()
        return detected if detected in modes else "critic"
    except Exception:
        return "critic"

if "chat" not in st.session_state:
    st.session_state.chat = None
    st.session_state.messages = []

mode_choice = st.selectbox("Choose a mode:", ["auto-detect"] + list(modes.keys()))
claim = st.text_area("Your claim, plan, or pitch:")

if st.button("Start Sparring") and claim:
    with st.spinner("Thinking of the sharpest objection..."):
        actual_mode = detect_mode(claim) if mode_choice == "auto-detect" else mode_choice
        st.session_state.chat = client.chats.create(
            model="gemini-3.5-flash",
            config={"system_instruction": modes[actual_mode]}
        )
        result = safe_send(st.session_state.chat, f'Here is my claim: "{claim}"')
        st.session_state.messages = [("AI", result)]
        st.session_state.used_mode = actual_mode

if st.session_state.chat:
    st.caption(f"Mode: **{st.session_state.get('used_mode', mode_choice)}**")

for speaker, text in st.session_state.messages:
    st.chat_message("assistant" if speaker == "AI" else "user").write(text)

if st.session_state.chat:
    rebuttal = st.chat_input("Your rebuttal...")
    if rebuttal:
        st.session_state.messages.append(("You", rebuttal))
        with st.spinner("Considering your rebuttal..."):
            result = safe_send(st.session_state.chat, rebuttal)
        st.session_state.messages.append(("AI", result))
        st.rerun()

    if st.button("Get Final Scorecard"):
        scorecard_prompt = """Based on our entire conversation above, summarize this debate:
1. The strongest objection you raised
2. Whether the user's rebuttal resolved it, partially resolved it, or didn't resolve it
3. An overall confidence score from 1-10 for the user's original claim, with one sentence explaining why."""
        with st.spinner("Preparing your scorecard..."):
            result = safe_send(st.session_state.chat, scorecard_prompt)
        st.subheader("📋 Scorecard")
        st.write(result)
