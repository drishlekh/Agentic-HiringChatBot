

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    entry_node,
    call_scraper_tool_node, run_scraper_tool_node, generate_questions_node,
    ask_question_node, log_answer_node, 
    analyze_answer_node, give_acknowledgement_node, handle_give_up_node, handle_unprofessional_node,
    handle_tool_error_node,
    generate_scorecard_node, end_conversation_node
)

# ==============================================================================
# === Agent Router Functions ===
# These functions act as the "brain's" decision-makers. They look at the current
# state of the conversation and decide which path to take next.
# ==============================================================================

def master_router(state: AgentState) -> str:
    """
    This is the main traffic cop of our agent. It checks if the interview has 
    started yet. If not, it kicks off the question generation process. Otherwise, 
    it knows the user has just answered a question and sends them to be processed.
    """
    if "interview_questions" not in state:
        return "generate_questions_branch"
    else:
        return "process_answer_branch"

def tool_error_router(state: AgentState) -> str:
    """
    After we try to scrape the candidate's portfolio, this function acts as a 
    safety check. It looks to see if our tool returned a specific error message.
    If it did, we route to a graceful exit; otherwise, we proceed as normal.
    """
    project_context = state.get("project_context", "")
    if project_context == "ERROR:INVALID_URL":
        return "tool_error"
    else:
        return "tool_success"

def analysis_router(state: AgentState) -> str:
    """
    This router directs the agent's response based on the sentiment and content
    of the candidate's answer. It's what allows the agent to react differently
    to a professional answer, an unprofessional one, or someone giving up.
    """
    category = state.get("last_answer_category", "NORMAL_ATTEMPT")
    if category == "GAVE_UP":
        return "handle_give_up"
    elif category == "UNPROFESSIONAL":
        return "handle_unprofessional"
    else:
        return "give_acknowledgement"

def should_ask_next_question(state: AgentState) -> str:
    """
    This function manages the main interview loop. It checks how many questions
    we've asked against the total number of questions we have. It decides whether
    to continue the interview or to move to the final wrap-up.
    """
    index = state.get("current_question_index", 0)
    questions = state.get("interview_questions", [])
    if index < len(questions):
        return "ask_next_question"
    else:
        return "finish_interview"

# ==============================================================================
# === Graph Definition ===
# Here, we build the "wiring diagram" for our agent. We define all the possible
# steps it can take and then connect them based on the decisions made by our
# router functions above.
# ==============================================================================

# First, we create an instance of a StateGraph, which will hold our agent's structure.
workflow = StateGraph(AgentState)

# Next, we register every function from our nodes file as a "node" in our graph.
# Each node represents a specific action or step the agent can take.
workflow.add_node("entry_node", entry_node)
workflow.add_node("call_scraper_tool", call_scraper_tool_node)
workflow.add_node("run_scraper_tool", run_scraper_tool_node)
workflow.add_node("handle_tool_error", handle_tool_error_node)
workflow.add_node("generate_questions", generate_questions_node)
workflow.add_node("ask_question", ask_question_node)
workflow.add_node("log_answer", log_answer_node)
workflow.add_node("analyze_answer", analyze_answer_node)
workflow.add_node("give_acknowledgement", give_acknowledgement_node)
workflow.add_node("handle_give_up", handle_give_up_node)
workflow.add_node("handle_unprofessional", handle_unprofessional_node)
workflow.add_node("generate_scorecard", generate_scorecard_node)
workflow.add_node("end_conversation", end_conversation_node)

# The agent's journey always begins at our simple entry_node.
workflow.set_entry_point("entry_node")

# From the entry point, we use our master_router to decide the agent's main path.
workflow.add_conditional_edges(
    "entry_node", master_router,
    {"generate_questions_branch": "call_scraper_tool", "process_answer_branch": "log_answer"}
)

# This defines the linear path for setting up the interview the first time.
workflow.add_edge("call_scraper_tool", "run_scraper_tool")

# After running the scraper, we check for errors before proceeding.
workflow.add_conditional_edges(
    "run_scraper_tool",
    tool_error_router,
    {
        "tool_success": "generate_questions",
        "tool_error": "handle_tool_error"
    }
)
workflow.add_edge("generate_questions", "ask_question")

# This defines the main conversational loop for processing answers.
workflow.add_edge("log_answer", "analyze_answer")

# After analyzing, we branch to a specific response based on the answer's category.
workflow.add_conditional_edges(
    "analyze_answer", analysis_router,
    {
        "give_acknowledgement": "give_acknowledgement",
        "handle_give_up": "handle_give_up",
        "handle_unprofessional": "handle_unprofessional"
    }
)

# All response paths converge here to decide whether to continue or finish.
workflow.add_conditional_edges(
    "give_acknowledgement", should_ask_next_question,
    {"ask_next_question": "ask_question", "finish_interview": "generate_scorecard"}
)
workflow.add_conditional_edges(
    "handle_give_up", should_ask_next_question,
    {"ask_next_question": "ask_question", "finish_interview": "generate_scorecard"}
)
workflow.add_conditional_edges(
    "handle_unprofessional", should_ask_next_question,
    {"ask_next_question": "ask_question", "finish_interview": "generate_scorecard"}
)


# This defines the final, linear path to gracefully end the conversation.
workflow.add_edge("generate_scorecard", "end_conversation")

# 'END' is a special node that tells LangGraph the agent's work for this turn is done.
# The agent will stop here and wait for the next user input.
workflow.add_edge("ask_question", END)
workflow.add_edge("end_conversation", END)
workflow.add_edge("handle_tool_error", END)

# Finally, we compile our entire structure into a runnable application.
app = workflow.compile()

print("---AGENT COMPILED WITH ROBUST ERROR HANDLING---")
