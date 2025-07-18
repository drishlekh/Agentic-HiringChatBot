# # # # agent/nodes.py

# # # import json
# # # import datetime
# # # from langchain_groq import ChatGroq
# # # from langchain_core.prompts import ChatPromptTemplate
# # # from langchain_core.output_parsers import JsonOutputParser
# # # from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
# # # from .state import AgentState
# # # from .tools import scrape_portfolio_tool
# # # from dotenv import load_dotenv
# # # import random

# # # load_dotenv()
# # # # --- Model and Tool Setup ---
# # # llm = ChatGroq(model="llama3-8b-8192", temperature=0.2)
# # # llm_with_tools = llm.bind_tools([scrape_portfolio_tool])


# # # # --- Agent Nodes ---
# # # def entry_node(state: AgentState) -> dict:
# # #     """
# # #     A simple entry node that just passes the state through. Its only job is
# # #     to be the official starting point for the graph so we can use a
# # #     conditional edge immediately after it.
# # #     """
# # #     print("---NODE: ENTRY POINT---")
# # #     # This node doesn't need to change the state, so it returns an empty dictionary.
# # #     return {}

# # # def call_scraper_tool_node(state: AgentState) -> dict:
# # #     """Calls the portfolio scraping tool."""
# # #     print("---NODE: CALLING SCRAPER TOOL---")
# # #     url = state["candidate_info"].get("project_url")
# # #     messages = [HumanMessage(f"Please scrape the content from this URL: {url}")]
# # #     response_with_tool_call = llm_with_tools.invoke(messages)
# # #     return {"messages": [response_with_tool_call]}

# # # def run_scraper_tool_node(state: AgentState) -> dict:
# # #     """Runs the scraping tool and stores the result."""
# # #     print("---NODE: RUNNING SCRAPER TOOL---")
# # #     last_message = state["messages"][-1]
# # #     tool_call = last_message.tool_calls[0]
# # #     scraped_content = scrape_portfolio_tool.invoke(tool_call["args"])
# # #     tool_message = ToolMessage(content=str(scraped_content), tool_call_id=tool_call["id"])
# # #     return {"messages": [tool_message], "project_context": str(scraped_content)}

# # # def generate_questions_node(state: AgentState) -> dict:
# # #     """Generates all 5 questions based on profile and portfolio."""
# # #     print("---NODE: GENERATING ALL QUESTIONS---")
# # #     info = state["candidate_info"]
    
# # #     generation_prompt = ChatPromptTemplate.from_template("""
# # #     You are a senior tech recruiter. Based on the candidate's profile and scraped portfolio content,
# # #     generate a list of exactly 5 interview questions.

# # #     **Candidate Profile:**
# # #     - Desired Position(s): {positions}
# # #     - Years of Experience: {experience}
# # #     - Tech Stack: {tech_stack}

# # #     **Scraped Portfolio Content:**
# # #     {project_context}

# #     # **Instructions:**
# #     # 1.  Generate the **first 3 questions** based on their Tech Stack, Desired Position, and Years of Experience. For example, if Years of Experience is high then ask senior level questions; if Years of Experience is less than ask a bit easier question.
# #     # 2.  Generate the **last 2 questions** based on specific projects or details found in their portfolio content.
# #     # 3.  Return a single JSON object with one key: "questions", which is a list of 5 question strings.
# #     # 4.  Design interview questions that require short, precise answers from candidates. Focus on questions that assess key skills or knowledge without inviting lengthy explanations.
# #     # """)
    
# # #     parser = JsonOutputParser()
# # #     generation_chain = generation_prompt | llm | parser
# # #     questions_json = generation_chain.invoke({
# # #         "positions": info.get("desired_positions"),
# # #         "experience": info.get("years_of_experience"),
# # #         "tech_stack": ", ".join(info.get("tech_stack", [])),
# # #         "project_context": state["project_context"]
# # #     })
    
# # #     return {
# # #         "interview_questions": questions_json.get("questions", []),
# # #         "current_question_index": 0, # Start the counter at 0
# # #         "interview_log": []
# # #     }

# # # def ask_question_node(state: AgentState) -> dict:
# # #     """Asks the next question from the list."""
# # #     print("---NODE: ASKING QUESTION---")
# # #     index = state.get("current_question_index", 0)
# # #     questions = state.get("interview_questions", [])
    
# # #     if index < len(questions):
# # #         question_to_ask = questions[index]
# # #         # We start the chat with a clear message, then the first question.
# # #         if index == 0:
# # #             initial_message = AIMessage(content="Excellent, I have analyzed your profile and prepared 5 questions for you. Let's begin.")
# # #             question_message = AIMessage(content=question_to_ask)
# # #             return {"messages": [initial_message, question_message], "current_question_index": index + 1}
# # #         else:
# # #             return {"messages": [AIMessage(content=question_to_ask)], "current_question_index": index + 1}
# # #     # This should not happen if routing is correct, but it's a safe fallback.
# # #     return {}

# # # def log_answer_node(state: AgentState) -> dict:
# # #     """Logs the last Q&A pair."""
# # #     print("---NODE: LOGGING ANSWER---")
# # #     index = state.get("current_question_index", 1) # The index has already been incremented
# # #     last_question = state["interview_questions"][index - 1]
# # #     last_answer = state["messages"][-1].content
    
# # #     current_log = {"question": last_question, "answer": last_answer}
# # #     updated_log = state.get("interview_log", []) + [current_log]
# # #     return {"interview_log": updated_log}

# # # def generate_scorecard_node(state: AgentState) -> dict:
# # #     """Generates the final scorecard and saves it."""
# # #     print("---NODE: GENERATING SCORECARD---")
# # #     # This node remains the same as before
# # #     interview_summary = "\n\n".join(f"Question: {item['question']}\nCandidate's Answer: {item['answer']}" for item in state["interview_log"])
# # #     scorecard_prompt = ChatPromptTemplate.from_template("""
# # #     You are a senior hiring manager. Write a detailed candidate scorecard based on the interview transcript.
# # #     **Candidate Information:** {candidate_info}
# # #     **Interview Transcript:** {interview_summary}
# # #     **Your Task:** Analyze the transcript and produce a formal scorecard including:
# # #     1. Overall Summary, 2. Technical Proficiency, 3. Project Acumen, 4. Red Flags, 5. Recommendation to go for a interview or not.
# # #     """)
# # #     scorecard_chain = scorecard_prompt | llm
# # #     scorecard_content = scorecard_chain.invoke({"candidate_info": json.dumps(state["candidate_info"], indent=2), "interview_summary": interview_summary}).content
# # #     candidate_name = state["candidate_info"].get("full_name", "unknown").replace(" ", "_")
# # #     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
# # #     filename = f"scorecards/{candidate_name}_{timestamp}.md"
# # #     with open(filename, "w") as f: f.write(scorecard_content)
# # #     print(f"---Scorecard saved to {filename}---")
# # #     return {}

# # # def end_conversation_node(state: AgentState) -> dict:
# # #     """Ends the conversation and sets the finished flag."""
# # #     print("---NODE: ENDING CONVERSATION---")
# # #     end_message = AIMessage(content="Thank you very much for your time. Your initial screening is now complete. Our recruitment team will review your profile and the results, and will get in touch with you regarding the next steps. Have a wonderful day!")
# # #     return {"messages": [end_message], "interview_finished": True}



# # # def give_acknowledgement_node(state: AgentState) -> dict:
# # #     """
# # #     This node adds a short, conversational acknowledgement after the user
# # #     provides an answer, making the interaction feel more natural before
# # #     the next question is asked.
# # #     """
# # #     print("---NODE: GIVING ACKNOWLEDGEMENT---")
    
# # #     # We can randomize the reply to make it less robotic.
# # #     acknowledgements = ["Got it, thank you.", "Okay.", "Alright, thanks for sharing.", "Understood.", "Perfect, thank you."]
# # #     reply = random.choice(acknowledgements)
    
# # #     # This node's only job is to add this one message to the history.
# # #     return {"messages": [AIMessage(content=reply)]}






# # # agent/nodes.py

# # import json
# # import datetime
# # import random
# # from dotenv import load_dotenv

# # # --- NEW IMPORTS FOR THE ROBUST FIX ---
# # from enum import Enum
# # from pydantic import BaseModel, Field
# # from typing import List

# # from langchain_groq import ChatGroq
# # from langchain_core.prompts import ChatPromptTemplate
# # from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
# # from .state import AgentState
# # from .tools import scrape_portfolio_tool
# # from langchain_core.output_parsers import StrOutputParser

# # load_dotenv()

# # # --- Model Setup ---
# # llm = ChatGroq(model="llama3-8b-8192", temperature=0) # Temp 0 for deterministic classification
# # llm_with_tools = llm.bind_tools([scrape_portfolio_tool])


# # # --- NEW, STRICT DATA SCHEMAS FOR ANALYSIS ---

# # # 1. We define the possible categories as an Enum. The LLM's output MUST match one of these.



# # # # This class is for the question generation step to ensure its reliability too.
# # # class QuestionList(BaseModel):
# # #     """A list of interview questions."""
# # #     questions: List[str] = []


# # # --- Agent Nodes ---

# # def entry_node(state: AgentState) -> dict:
# #     """A simple entry node to start the graph."""
# #     return {}

# # def call_scraper_tool_node(state: AgentState) -> dict:
# #     """Calls the portfolio scraping tool."""
# #     url = state["candidate_info"].get("project_url")
# #     messages = [HumanMessage(f"Please scrape the content from this URL: {url}")]
# #     response_with_tool_call = llm_with_tools.invoke(messages)
# #     return {"messages": [response_with_tool_call]}

# # def run_scraper_tool_node(state: AgentState) -> dict:
# #     """Runs the scraping tool and stores the result."""
# #     last_message = state["messages"][-1]
# #     tool_call = last_message.tool_calls[0]
# #     scraped_content = scrape_portfolio_tool.invoke(tool_call["args"])
# #     tool_message = ToolMessage(content=str(scraped_content), tool_call_id=tool_call["id"])
# #     return {"messages": [tool_message], "project_context": str(scraped_content)}

# # def generate_questions_node(state: AgentState) -> dict:
# #     """
# #     Generates all 5 questions by asking for a simple numbered list,
# #     which is more reliable than asking for complex JSON.
# #     """
# #     print("---NODE: GENERATING ALL QUESTIONS (SIMPLE TEXT)---")
# #     info = state["candidate_info"]
    
# #     # We will get a simple string as output.
# #     parser = StrOutputParser()
    
# #     # The prompt is updated to ask for a simple, numbered list.
# #     generation_prompt = ChatPromptTemplate.from_template("""
# #     You are a senior tech recruiter. Based on the candidate's profile and scraped portfolio content,
# #     generate exactly 5 interview questions.

# #     **Candidate Profile:**
# #     - Desired Position(s): {positions}
# #     - Years of Experience: {experience}
# #     - Tech Stack: {tech_stack}

# #     **Scraped Portfolio Content:**
# #     {project_context}

#     # **Instructions:**
#     # 1.  Generate the **first 3 questions** based on their Tech Stack, Desired Position, and Years of Experience.
#     # 2.  Generate the **last 2 questions** based on specific projects or details found in their portfolio content.
#     # 3.  **IMPORTANT:** Respond ONLY with the 5 questions, formatted as a numbered list. Do not include any other text, greetings, or explanations.

# #     Example Output:
# #     1. What is your experience with Python?
# #     2. How do you handle scaling in Django?
# #     3. Describe a time you used Docker.
# #     4. In your 'Project-X', can you explain the database schema?
# #     5. What was the biggest challenge in your 'Project-Y'?
# #     """)
    
# #     generation_chain = generation_prompt | llm | parser
    
# #     # The output is now a single block of text.
# #     response_str = generation_chain.invoke({
# #         "positions": info.get("desired_positions"),
# #         "experience": info.get("years_of_experience"),
# #         "tech_stack": ", ".join(info.get("tech_stack", [])),
# #         "project_context": state["project_context"]
# #     })
    
# #     # We reliably parse this text into a list in our Python code.
# #     # This splits the string by newlines and filters out any empty lines.
# #     question_list = [line.strip() for line in response_str.splitlines() if line.strip()]
# #     # This removes the numbering (e.g., "1. ", "2. ") from the start of each question.
# #     cleaned_questions = [q.split('.', 1)[-1].strip() for q in question_list]

# #     return {
# #         "interview_questions": cleaned_questions,
# #         "current_question_index": 0,
# #         "interview_log": []
# #     }

# # def ask_question_node(state: AgentState) -> dict:
# #     """Asks the next question from the list."""
# #     index = state.get("current_question_index", 0)
# #     questions = state.get("interview_questions", [])
# #     if index < len(questions):
# #         question_to_ask = questions[index]
# #         if index == 0:
# #             initial_message = AIMessage(content="Excellent, I have analyzed your profile and prepared 5 questions for you. Let's begin.")
# #             question_message = AIMessage(content=question_to_ask)
# #             return {"messages": [initial_message, question_message], "current_question_index": index + 1}
# #         else:
# #             return {"messages": [AIMessage(content=question_to_ask)], "current_question_index": index + 1}
# #     return {}

# # def log_answer_node(state: AgentState) -> dict:
# #     """Logs the last Q&A pair."""
# #     index = state.get("current_question_index", 1)
# #     last_question = state["interview_questions"][index - 1]
# #     last_answer = state["messages"][-1].content
# #     current_log = {"question": last_question, "answer": last_answer}
# #     updated_log = state.get("interview_log", []) + [current_log]
# #     return {"interview_log": updated_log}

# # # --- THIS IS THE FULLY REBUILT AND ROBUST ANALYSIS NODE ---

# # def analyze_answer_node(state: AgentState) -> dict:
# #     """
# #     Analyzes the user's last answer with high precision by asking the LLM for a
# #     single-word response, which is much more reliable.
# #     """
# #     print("---NODE: ANALYZING ANSWER (SIMPLE TEXT)---")
# #     index = state.get("current_question_index", 1)
# #     last_question = state["interview_questions"][index - 1]
# #     last_answer = state["messages"][-1].content

# #     # We will get a simple string as output.
# #     parser = StrOutputParser()

# #     # This prompt is extremely forceful about the output format.
# #     analysis_prompt = ChatPromptTemplate.from_template("""
# #     You are a strict interview moderator. Your sole job is to analyze a candidate's response and classify it into one of three categories based on the provided examples.

# #     **Category Definitions:**
# #     - `NORMAL_ATTEMPT`: A genuine effort to answer, regardless of correctness.
# #     - `GAVE_UP`: An explicit refusal to answer (e.g., "I don't know," "skip").
# #     - `UNPROFESSIONAL`: Any response containing rude language, slang, insults, or is aggressively off-topic.

# #     **Examples:**
# #     - Question: "What is Python's GIL?" | Answer: "shut up" -> UNPROFESSIONAL
# #     - Question: "Explain closures." | Answer: "what the hell is that" -> UNPROFESSIONAL
# #     - Question: "Describe your experience with Docker." | Answer: "I have no idea" -> GAVE_UP
# #     - Question: "How would you scale a web app?" | Answer: "I think I would use a load balancer." -> NORMAL_ATTEMPT

# #     **Your Task:**
# #     Classify the following answer based on the rules and examples above.
# #     The interview question was: "{question}"
# #     The candidate's answer is: "{answer}"

# #     **IMPORTANT: Respond ONLY with the single category name in uppercase (NORMAL_ATTEMPT, GAVE_UP, or UNPROFESSIONAL) and absolutely nothing else.**
# #     """)
    
# #     analysis_chain = analysis_prompt | llm | parser
    
# #     # The output is now a simple string, which we clean up.
# #     category = analysis_chain.invoke({"question": last_question, "answer": last_answer}).strip()
    
# #     print(f"---Answer classified as: {category}---")
# #     return {"last_answer_category": category}

# # def give_acknowledgement_node(state: AgentState) -> dict:
# #     """The standard, polite reply for a normal answer."""
# #     print("---NODE: GIVING ACKNOWLEDGEMENT (NORMAL)---")
# #     acknowledgements = ["Got it, thank you.", "Okay.", "Alright, thanks for sharing.", "Understood."]
# #     reply = random.choice(acknowledgements)
# #     return {"messages": [AIMessage(content=reply)]}

# # def handle_give_up_node(state: AgentState) -> dict:
# #     """The empathetic reply for when a user doesn't know the answer."""
# #     print("---NODE: HANDLING 'GAVE UP'---")
# #     reply = "That's perfectly alright, not every question is for everyone. Let's move on to the next one."
# #     return {"messages": [AIMessage(content=reply)]}
    
# # def handle_unprofessional_node(state: AgentState) -> dict:
# #     """The firm reply for unprofessional conduct."""
# #     print("---NODE: HANDLING 'UNPROFESSIONAL'---")
# #     reply = "A professional tone is expected during this assessment. Unprofessional language will be noted. Let's proceed to the next question."
# #     return {"messages": [AIMessage(content=reply)]}

# # def generate_scorecard_node(state: AgentState) -> dict:
# #     """Generates the final scorecard."""
# #     # This node remains the same, its prompt is already robust.
# #     interview_summary = "\n\n".join(f"Question: {item['question']}\nCandidate's Answer: {item['answer']}" for item in state["interview_log"])
# #     scorecard_prompt = ChatPromptTemplate.from_template("""
# #     You are a senior hiring manager. Write a detailed candidate scorecard based on the transcript.
# #     **Candidate Information:** {candidate_info}
# #     **Interview Transcript:** {interview_summary}
# #     **Task:** Produce a formal scorecard: 1. Overall Summary, 2. Technical Proficiency, 3. Project Acumen, 4. Communication & Professionalism (Note if they were unprofessional or gave up on questions), 5. Recommendation.
# #     """)
# #     scorecard_chain = scorecard_prompt | llm
# #     scorecard_content = scorecard_chain.invoke({"candidate_info": json.dumps(state["candidate_info"]), "interview_summary": interview_summary}).content
# #     candidate_name = state["candidate_info"].get("full_name", "unknown").replace(" ", "_")
# #     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
# #     filename = f"scorecards/{candidate_name}_{timestamp}.md"
# #     with open(filename, "w", encoding="utf-8") as f: f.write(scorecard_content)
# #     print(f"---Scorecard saved to {filename}---")
# #     return {}

# # def end_conversation_node(state: AgentState) -> dict:
# #     """Ends the conversation and sets the finished flag."""
# #     end_message = AIMessage(content="Thank you very much for your time. Your initial screening is now complete. Our recruitment team will review your profile and the results, and will get in touch with you regarding the next steps. Have a wonderful day!")
# #     return {"messages": [end_message], "interview_finished": True}


# # # In agent/nodes.py, add this new node:

# # def handle_tool_error_node(state: AgentState) -> dict:
# #     """
# #     This node is called when the scraping tool fails. It informs the user
# #     and gracefully ends the conversation.
# #     """
# #     print("---NODE: HANDLING TOOL ERROR---")
# #     error_message = AIMessage(
# #         content="It appears the GitHub or portfolio link you provided is invalid or unreachable. Please double-check the URL and start the screening process again. Thank you."
# #     )
# #     # We set interview_finished to True to stop the process.
# #     return {"messages": [error_message], "interview_finished": True}



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








def generate_scorecard_node(state: AgentState) -> dict:
    """
    At the end of the interview, this node gathers all the collected information
    and the interview log. It then uses the LLM to write a comprehensive,
    professional scorecard for the human recruiter to review.
    """
    interview_summary = "\n\n".join(f"Question: {item['question']}\nAnswer: {item['answer']}" for item in state["interview_log"])
    scorecard_prompt = ChatPromptTemplate.from_template("""
    You are a senior hiring manager. Write a detailed candidate scorecard based on the transcript.
    **Candidate Info:** {candidate_info}
    **Interview Transcript:** {interview_summary}
    **Task:** Produce a formal scorecard with: 1. Overall Summary, 2. Technical Proficiency, 
    3. Project Acumen, 4. Communication & Professionalism, 5. Recommendation.
    """)
    scorecard_chain = scorecard_prompt | llm | StrOutputParser()
    scorecard_content = scorecard_chain.invoke({"candidate_info": json.dumps(state["candidate_info"]), "interview_summary": interview_summary})
    candidate_name = state["candidate_info"].get("full_name", "unknown").replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"scorecards/{candidate_name}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f: f.write(scorecard_content)
    return {}

def end_conversation_node(state: AgentState) -> dict:
    """
    This is the final step. It provides a polite closing message to the
    candidate and sets a flag to let the UI know the interview is over.
    """
    end_message = AIMessage(content="Thank you very much for your time. Your initial screening is now complete. Our recruitment team will review your profile and the results, and will get in touch with you regarding the next steps. Have a wonderful day!")
    return {"messages": [end_message], "interview_finished": True}




