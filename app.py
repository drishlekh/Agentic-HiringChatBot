

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent.agent import app
import html

# ==============================================================================
# === 1. Page Configuration ===
# First things first, let's set up our browser tab with a professional title
# and a briefcase icon. We'll use a "centered" layout to keep the focus on
# the main content, which looks great for forms and chats.
# ==============================================================================

st.set_page_config(
    page_title="TalentScout AI Screening",
    page_icon=" briefcase",
    layout="centered"
)

# ==============================================================================
# === 2. Session State Initialization ===
# Think of this as our app's short-term memory. Since Streamlit re-runs the
# script with every interaction, we need a place to store information that
# persists, like which stage of the interview we're in ('phase') or the
# ongoing chat history ('messages').
# ==============================================================================

if "phase" not in st.session_state: st.session_state.phase = "form"
if "messages" not in st.session_state: st.session_state.messages = []
if "candidate_info" not in st.session_state: st.session_state.candidate_info = {}
if "agent_state" not in st.session_state: st.session_state.agent_state = {}


# ==============================================================================
# === 3. Dynamic CSS Injection ===
# Here's where the visual magic happens. We're injecting a block of CSS to
# override Streamlit's default styles. This lets us define the dark theme,
# create the card-like containers, and style our chat bubbles to look modern
# and professional.
# ==============================================================================

st.markdown("""
<style>
    .stApp { background-color: #111B21; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    
    /* This complex selector targets Streamlit's main content block to create our "card" effect. */
    div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #202C33; border-radius: 12px; padding: 2.5rem; margin: auto; max-width: 800px; border: 1px solid #333;
    }
    
    .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 2rem; }
    h1, h3, h5, .stMarkdown p { color: #FFFFFF; }
    .stButton > button { width: 100%; border-radius: 8px; border: 1px solid #00A884; background-color: #00A884; color: #FFFFFF; padding: 12px 24px; font-weight: bold; font-size: 16px; }
    
    /* These rules define our custom chat bubbles and their alignment. */
    .chat-row { display: flex; width: 100%; margin-bottom: 0.75rem; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    .chat-bubble { max-width: 85%; padding: 12px 18px; border-radius: 18px; word-wrap: break-word; }
    .chat-bubble.assistant { background-color: #202C33; color: #E1E1E1; }
    .chat-bubble.user { background-color: #005C4B; color: white; }
    
    /* A special style for the formatted list of GitHub projects. */
    .project-list { line-height: 1.6; }
    .project-list h5 { font-size: 1.1rem; color: #00A884; margin-bottom: 0.5rem; }
    .project-list p { margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# === 4. Core Application Logic Functions ===
# These are the helper functions that orchestrate the main logic of our app,
# like starting the test or formatting text for display.
# ==============================================================================

def start_technical_test():
    """
    This function is the bridge between the confirmation screen and the actual
    interview. It tells the app to switch to the 'in_test' phase and gives our
    LangGraph agent the green light to start its process.
    """
    st.session_state.phase = "in_test"
    initial_agent_state = {"candidate_info": st.session_state.candidate_info}
    with st.spinner("Analyzing your profile and preparing questions..."):
        try:
            response_state = app.invoke(initial_agent_state)
            st.session_state.agent_state = response_state
            st.session_state.messages = response_state.get("messages", [])
        except Exception as e:
            st.error(f"An error occurred while starting the test: {e}")
            st.session_state.phase = "form"

def format_project_content(content: str) -> str:
    """
    This is our special formatter. The text we get from scraping a GitHub
    profile can be a bit messy, so this function takes that raw text and
    transforms it into a clean, professional-looking HTML block to display
    in the chat.
    """
    if "ERROR:INVALID_URL" in content or "Could not find any pinned repositories" in content:
        return html.escape(content)

    header = "<h5>Projects Extracted from Profile</h5>"
    projects = content.strip().split('\n\n')
    
    project_html_parts = []
    for project in projects:
        project_part = html.escape(project).replace('\n', '<br>')
        project_html_parts.append(f"<p>{project_part}</p>")

    return f'<div class="project-list">{header}{"".join(project_html_parts)}</div>'


# ==============================================================================
# === 5. Main UI Rendering ===
# The heart of our application. This large conditional block checks which "phase"
# the user is in and renders the appropriate interface, whether it's the initial
# form, the confirmation screen, or the live chat.
# ==============================================================================

# --- Phase 1: The Information Gathering Form ---
if st.session_state.phase == "form":
    st.title("TalentScout AI Screening")
    st.markdown("""**Welcome to TalentScout**""")
    st.markdown("""We are a premier recruitment agency specializing in placing top-tier talent within the technology sector. This AI-powered assistant will conduct a brief initial screening to help us understand your skills and experience.""")
    st.header("Candidate Information")
    
    with st.form("candidate_form"):
        st.subheader("Personal & Contact Details")
        c1, c2 = st.columns(2)
        with c1: full_name, email = st.text_input("Full Name *"), st.text_input("Email Address *")
        with c2: phone_number, current_location = st.text_input("Phone Number"), st.text_input("Current Location")
        
        st.subheader("Professional Profile")
        c3, c4 = st.columns(2)
        with c3: desired_positions, years_of_experience = st.text_input("Desired Position(s) *"), st.number_input("Years of Experience *", 0)
        with c4: tech_stack, project_url = st.text_area("Primary Tech Stack *"), st.text_input("GitHub/Portfolio URL *")
        
        st.markdown("<br>", unsafe_allow_html=True)
        consent = st.checkbox("I consent to my data being processed for this screening.")
        
        if st.form_submit_button("Submit Information"):
            if not all([full_name, email, desired_positions, tech_stack, project_url, consent]):
                st.error("Please fill all required fields and provide consent.")
            else:
                st.session_state.candidate_info = {"full_name": full_name, "email": email, "phone_number": phone_number, "current_location": current_location, "desired_positions": desired_positions, "years_of_experience": years_of_experience, "tech_stack": [s.strip() for s in tech_stack.split(',')], "project_url": project_url}
                st.session_state.phase = "ready_for_test"
                st.rerun()

# --- Phase 2: Instructions and Confirmation Screen ---
elif st.session_state.phase == "ready_for_test":
    st.header("Thank You for Your Submission")
    st.success("Your information has been received successfully.")
    st.markdown("""
    **Next Step: AI-Powered Technical Assessment**

    You will now begin the automated technical assessment.
    
    - The AI assistant will ask you **5 questions** sequentially.
    - Questions are tailored to your declared tech stack and the projects in your portfolio.
    - Please note that the test cannot be paused once it has started.
    """)
    st.warning("Please ensure you are prepared before you begin.")
    st.button("I am ready, Start the Technical Test", on_click=start_technical_test)

# --- Phase 3 & 4: The Live Chat and Final Screen ---
elif st.session_state.phase in ["in_test", "finished"]:
    st.header("Technical Assessment")
    
    # We loop through our message history and render each one according to its role.
    for msg in st.session_state.get("messages", []):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        
        # We have a special case for the 'ToolMessage' to make it look nice.
        if isinstance(msg, ToolMessage):
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(format_project_content(msg.content), unsafe_allow_html=True)
        else:
            # All other messages are rendered using Streamlit's standard component.
            with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
                st.write(html.escape(str(msg.content)))

    # The chat input box only appears if the interview is still in progress.
    if st.session_state.phase == "in_test":
        if prompt := st.chat_input("Type your answer..."):
            # When the user sends a message, we update the state and rerun the agent.
            st.session_state.agent_state["messages"].append(HumanMessage(content=prompt))
            with st.spinner("..."):
                response_state = app.invoke(st.session_state.agent_state)
            
            st.session_state.agent_state = response_state
            st.session_state.messages = response_state.get("messages", [])

            if response_state.get("interview_finished"):
                st.session_state.phase = "finished"
            
            st.rerun()
    else:
        # Once finished, we display a final success message.
        st.success("Screening Complete! Thank you for your time.")
        st.info("Our recruitment team will review your profile and results. You may now close this window.")
        st.balloons()