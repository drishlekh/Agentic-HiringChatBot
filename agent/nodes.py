import os
import json
import datetime
import random
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from .state import AgentState
from .tools import scrape_portfolio_tool
from enum import Enum
from pydantic import BaseModel, Field

# We load our secret keys from the .env file right at the start.
load_dotenv()

# ==============================================================================
# === Core Setup ===
# We're setting up the connection to our Language Model, which is the "brain"
# that will power our agent's text generation and analysis capabilities.
# ==============================================================================

# We're initializing the ChatGroq client to use the fast Llama3 model.
# Setting temperature to 0 makes the model's responses more predictable and less random.
llm = ChatGroq(model="llama3-8b-8192", temperature=0)

# Here, we're giving the LLM a "toolbelt." We bind our scraping function to it,
# which allows the agent to decide when and how to use this special ability.
llm_with_tools = llm.bind_tools([scrape_portfolio_tool])

# This Enum defines the ONLY valid outputs for our classification.
class AnswerCategory(str, Enum):
    NORMAL_ATTEMPT = "NORMAL_ATTEMPT"
    GAVE_UP = "GAVE_UP"
    UNPROFESSIONAL = "UNPROFESSIONAL"

# This Pydantic model ensures the LLM's output is a JSON object
# containing a field that MUST be one of the categories from our Enum.
class AnswerAnalysis(BaseModel):
    """A model to hold the classification of the user's answer."""
    category: AnswerCategory = Field(description="The single, most appropriate classification for the candidate's answer.")



# ==============================================================================
# === Agent Nodes ===
# Each function below is a "node" in our agent's graph. Think of each one as
# a specific, self-contained action the agent can perform during the interview.
# ==============================================================================

def entry_node(state: AgentState) -> dict:
    """
    This is the official starting point of our graph. It's a simple passthrough
    node that doesn't do much, but it gives us a clean entry for our routers.
    """
    return {}

def call_scraper_tool_node(state: AgentState) -> dict:
    """
    This node's job is to ask the LLM to use its scraping tool. It takes the URL
    from our agent's memory and formulates a request for the tool to be called.
    """
    url = state["candidate_info"].get("project_url")
    messages = [HumanMessage(f"Please scrape the content from this URL: {url}")]
    response_with_tool_call = llm_with_tools.invoke(messages)
    return {"messages": [response_with_tool_call]}

def run_scraper_tool_node(state: AgentState) -> dict:
    """
    After the LLM decides to use the tool, this node actually executes it. It
    runs our `scrape_portfolio_tool` function and saves the scraped text
    back into the agent's memory for later use.
    """
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    scraped_content = scrape_portfolio_tool.invoke(tool_call["args"])
    tool_message = ToolMessage(content=str(scraped_content), tool_call_id=tool_call["id"])
    return {"messages": [tool_message], "project_context": str(scraped_content)}

def handle_tool_error_node(state: AgentState) -> dict:
    """
    This is our safety net. If the scraping tool fails (e.g., due to a bad URL),
    this node provides a polite, professional error message to the user and
    gracefully ends the assessment.
    """
    error_message = AIMessage(
        content="It appears the GitHub or portfolio link you provided is invalid or unreachable. Please double-check the URL and start the screening process again. Thank you."
    )
    return {"messages": [error_message], "interview_finished": True}

def generate_questions_node(state: AgentState) -> dict:
    """
    This is a key step. The agent takes all the information it has—the
    candidate's profile and the scraped portfolio—and uses the LLM to generate
    a fresh, tailored set of interview questions for this specific candidate.
    """
    info = state["candidate_info"]
    parser = StrOutputParser()
    generation_prompt = ChatPromptTemplate.from_template("""
    You are a senior tech recruiter. Based on the candidate's profile and scraped portfolio content,
    generate exactly 5 interview questions, formatted as a numbered list.
    - The first 3 questions should be based on their Tech Stack, Desired Position, and Experience.
    - The last 2 questions should be based on specific projects found in their portfolio.
    IMPORTANT:
    1)Respond ONLY with the 5 questions and nothing else.
    2)The questions asked should be direct and not vague. Frame the questions in such a way that the answers can be typed in maximum of 4-5 words.
    
    Candidate Profile: {profile}
    Scraped Portfolio: {project_context}
    """)

    generation_chain = generation_prompt | llm | parser
    response_str = generation_chain.invoke({
        "profile": json.dumps(info), "project_context": state["project_context"]
    })
    
    # We're cleaning up the LLM's response here in Python to ensure it's a perfect list.
    question_list = [line.strip() for line in response_str.splitlines() if line.strip()]
    cleaned_questions = [q.split('.', 1)[-1].strip() for q in question_list]

    return {
        "interview_questions": cleaned_questions,
        "current_question_index": 0,
        "interview_log": []
    }

def ask_question_node(state: AgentState) -> dict:
    """
    This node manages the flow of the interview, asking one question at a time.
    It checks which question is next, presents it to the candidate, and updates
    the counter for the next turn.
    """
    index = state.get("current_question_index", 0)
    questions = state.get("interview_questions", [])
    if index < len(questions):
        question_to_ask = questions[index]
        if index == 0:
            initial_message = AIMessage(content="Excellent, I have analyzed your profile and prepared 5 questions for you. Let's begin.")
            question_message = AIMessage(content=question_to_ask)
            return {"messages": [initial_message, question_message], "current_question_index": index + 1}
        else:
            return {"messages": [AIMessage(content=question_to_ask)], "current_question_index": index + 1}
    return {}

def log_answer_node(state: AgentState) -> dict:
    """
    After the candidate answers, this node silently records the question and the
    answer in our interview log. This log is crucial for generating the final
    scorecard without cluttering the main chat history.
    """
    index = state.get("current_question_index", 1)
    last_question = state["interview_questions"][index - 1]
    last_answer = state["messages"][-1].content
    current_log = {"question": last_question, "answer": last_answer}
    updated_log = state.get("interview_log", []) + [current_log]
    return {"interview_log": updated_log}

def analyze_answer_node(state: AgentState) -> dict:
    """
    This is the agent's "sentiment analysis" part. It analyzes the candidate's
    answer not for correctness, but for its tone and intent. It determines if
    the candidate is being professional, giving up, or just trying their best.
    """
    index = state.get("current_question_index", 1)
    last_question = state["interview_questions"][index - 1]
    last_answer = state["messages"][-1].content
    parser = StrOutputParser()
    analysis_prompt = ChatPromptTemplate.from_template("""
    You are a strict interview moderator. Classify the candidate's answer into one of
    three categories: NORMAL_ATTEMPT, GAVE_UP, or UNPROFESSIONAL.
    
    Examples:
    - Answer: "shut up" -> UNPROFESSIONAL
    - Answer: "I have no idea" -> GAVE_UP
    - Answer: "I would use a load balancer." -> NORMAL_ATTEMPT

    The interview question was: "{question}"
    The candidate's answer is: "{answer}"

    IMPORTANT: Respond ONLY with the single category name in uppercase.
    """)
    analysis_chain = analysis_prompt | llm | parser
    category = analysis_chain.invoke({"question": last_question, "answer": last_answer}).strip()
    return {"last_answer_category": category}

def give_acknowledgement_node(state: AgentState) -> dict:
    """
    This node provides a simple, human-like acknowledgement after a normal
    answer. It helps the conversation feel less robotic.
    """
    acknowledgements = ["Got it, thank you.", "Okay.", "Alright, thanks for sharing.", "Understood."]
    reply = random.choice(acknowledgements)
    return {"messages": [AIMessage(content=reply)]}

def handle_give_up_node(state: AgentState) -> dict:
    """
    If the candidate says they don't know, this node provides an encouraging
    and empathetic response to keep the interview positive.
    """
    reply = "That's perfectly alright, not every question is for everyone. Let's move on to the next one."
    return {"messages": [AIMessage(content=reply)]}
    
def handle_unprofessional_node(state: AgentState) -> dict:
    """
    If the candidate is unprofessional, this node provides a firm but polite
    correction to guide the conversation back to a professional tone.
    """
    reply = "A professional tone is expected during this assessment. Unprofessional language will be noted. Let's proceed to the next question."
    return {"messages": [AIMessage(content=reply)]}








# def generate_scorecard_node(state: AgentState) -> dict:
#     """
#     At the end of the interview, this node gathers all the collected information
#     and the interview log. It then uses the LLM to write a comprehensive,
#     professional scorecard for the human recruiter to review.
#     """
#     interview_summary = "\n\n".join(f"Question: {item['question']}\nAnswer: {item['answer']}" for item in state["interview_log"])
#     scorecard_prompt = ChatPromptTemplate.from_template("""
#     You are a senior hiring manager. Write a detailed candidate scorecard based on the transcript.
#     **Candidate Info:** {candidate_info}
#     **Interview Transcript:** {interview_summary}
#     **Task:** Produce a formal scorecard with: 1. Overall Summary, 2. Technical Proficiency, 
#     3. Project Acumen, 4. Communication & Professionalism, 5. Recommendation.
#     """)
#     scorecard_chain = scorecard_prompt | llm | StrOutputParser()
#     scorecard_content = scorecard_chain.invoke({"candidate_info": json.dumps(state["candidate_info"]), "interview_summary": interview_summary})
#     candidate_name = state["candidate_info"].get("full_name", "unknown").replace(" ", "_")
#     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
#     filename = f"scorecards/{candidate_name}_{timestamp}.md"
#     with open(filename, "w", encoding="utf-8") as f: f.write(scorecard_content)
#     return {}


def generate_scorecard_node(state: AgentState) -> dict:
    """
    Generates the final scorecard for the recruiter, ensuring the output
    directory exists before saving the file.
    """
    print("---NODE: GENERATING SCORECARD---")

    
    # 1. Define the directory path.
    output_dir = "scorecards"
    
    # 2. Check if the directory exists. If not, create it.
    # The `os.makedirs` function can create a directory, and `exist_ok=True`
    # prevents an error if the directory already exists. This makes the
    # operation safe to run every time.
    os.makedirs(output_dir, exist_ok=True)
    
   
    interview_summary = "\n\n".join(f"Question: {item['question']}\nAnswer: {item['answer']}" for item in state["interview_log"])
    scorecard_prompt = ChatPromptTemplate.from_template("""
    You are a senior hiring manager. Write a detailed candidate scorecard based on the transcript.
    **Candidate Info:** {candidate_info}
    **Interview Transcript:** {interview_summary}
    **Task:** Produce a formal scorecard with: 1. Summary, 2. Technical Proficiency, 3. Project Acumen, 4. Professionalism, 5. Recommendation.
    """)
    scorecard_chain = scorecard_prompt | llm
    scorecard_content = scorecard_chain.invoke({"candidate_info": json.dumps(state["candidate_info"]), "interview_summary": interview_summary}).content
    
    candidate_name = state["candidate_info"].get("full_name", "unknown").replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    # We now construct the full path using our defined output directory.
    filename = os.path.join(output_dir, f"{candidate_name}_{timestamp}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(scorecard_content)
        
    print(f"---Scorecard saved to {filename}---")
    return {}



def end_conversation_node(state: AgentState) -> dict:
    """
    This is the final step. It provides a polite closing message to the
    candidate and sets a flag to let the UI know the interview is over.
    """
    end_message = AIMessage(content="Thank you very much for your time. Your initial screening is now complete. Our recruitment team will review your profile and the results, and will get in touch with you regarding the next steps. Have a wonderful day!")
    return {"messages": [end_message], "interview_finished": True}




