# agent/state.py

from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # The full conversation history. operator.add makes sure messages are appended.
    messages: Annotated[List[BaseMessage], operator.add]
    
    # A dictionary holding all the candidate's info from the form.
    candidate_info: dict
    
    # This will hold the scraped content from their portfolio.
    project_context: str
    
    # A single, simple list to hold all 5 interview questions.
    interview_questions: List[str]
    
    # A simple counter for which question we are currently on.
    current_question_index: int
    
    # A list of dictionaries to log the Q&A for the final report.
    interview_log: List[dict]
    
    # A simple flag to tell the UI when the interview is over.
    interview_finished: bool
    
    # This will hold the classification of the user's last answer.
    
    last_answer_category: str