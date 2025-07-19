# TalentScout AI - Agentic-HiringChatBot
*Live Link: https://talentscout-agentic-hiringchatbot.streamlit.app/*

An advanced, conversational AI chatbot designed to conduct initial candidate screenings for the fictional tech recruitment agency, "TalentScout." This project leverages the power of Large Language Models (LLMs) and graph-based agent architecture to create a dynamic, stateful, and intelligent screening experience.

The assistant guides candidates through a multi-phase process: gathering essential information via a professional web form, analyzing their public portfolio or GitHub profile, and conducting a tailored technical interview based on their unique skills and experience.



## Features

This application is more than a simple chatbot; it is a stateful agent with a sophisticated set of capabilities:

*   **Multi-Phase User Experience:** A clean, professional UI built with Streamlit that progresses from an information-gathering form to a "ready" screen, and finally to the interactive technical assessment.
*   **Intelligent Information Gathering:** A streamlined form captures all essential candidate details, from contact information to technical skills.
*   **Live Portfolio Analysis:** The agent is equipped with a **tool** that can scrape a candidate's provided GitHub or portfolio URL. It specifically identifies and extracts information from pinned repositories to gain context on their work.
*   **Dynamic & Tailored Question Generation:** The agent uses the candidate's profile (desired position, years of experience, tech stack) and the scraped portfolio context to generate a unique set of 5 interview questions—3 based on their profile and 2 based on their specific projects.
*   **Dynamic Answer Analysis (Sentiment & Intent):** After each answer, the agent analyzes the candidate's response to classify its intent as a `NORMAL_ATTEMPT`, `GAVE_UP`, or `UNPROFESSIONAL`.
*   **Contextual Acknowledgements:** Based on the answer analysis, the agent provides a dynamic response. It gives a standard acknowledgement for a normal answer, an encouraging message if the candidate gives up, and a professional warning for unprofessional language.
*   **Graceful Error Handling:** If a candidate provides an invalid or unreachable portfolio URL, the agent gracefully handles the error and provides a clear message instead of crashing.
*   **Automated Scorecard Generation:** Upon completion of the interview, the agent synthesizes the entire conversation log and generates a detailed, professional scorecard in Markdown format, saving it to a `scorecards/` directory for a human recruiter to review.
*   **Stateful Conversational Flow:** Built on LangGraph, the agent maintains context and manages a complex, cyclical conversational loop with conditional branching, ensuring a coherent and logical interview process.

## Installation Instructions

Follow these steps to set up and run the application on your local machine.

#### Prerequisites

*   Git
*   Python 3.8+ and `pip`

#### Step 1: Clone the Repository

Clone this project to your local machine.

```bash
git clone https://github.com/drishlekh/Agentic-HiringChatBot
cd Agentic-HiringChatBot
```

#### Step 2: Set Up a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

*   **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

#### Step 3: Install Dependencies

Install all the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

The application requires API keys to connect to external services.

1.  Create a new file named `.env` in the root directory of the project.
2.  Copy the contents of `.env.example` (if provided) or add the following variables to your new `.env` file:

    ```env
    # Get your API key from https://console.groq.com/keys
    GROQ_API_KEY="your_groq_api_key_here"

    # (Optional) For monitoring with LangSmith, get your key from https://smith.langchain.com/
    LANGCHAIN_API_KEY="your_langsmith_api_key_here"
    ```

#### Step 5: Run the Application

Launch the Streamlit web application.

```bash
streamlit run app.py
```

The application should now be running and accessible in your web browser at `http://localhost:8501`.

## Usage Guide

1.  **Launch the application** using the command above.
2.  **Fill out the Candidate Information form** with all the required details and provide consent.
3.  Click **"Submit Information"**.
4.  On the confirmation screen, review the instructions and click **"I am ready, Start the Technical Test"** when you are prepared.
5.  **Answer the 5 questions** presented by the AI assistant one by one in the chat interface.
6.  Upon completion, you will see a final success message.
7.  **(For Developers)** A detailed Markdown scorecard for the completed interview will be generated and saved in the `scorecards/` directory.

## Technical Details

*   **Architecture:** The core of this application is a **stateful agent** built using **LangGraph**. This architectural choice was deliberate. A simple LangChain Expression Language (LCEL) chain is insufficient for this task because the interview process is not linear—it involves **cycles** (the Q&A loop) and **conditional logic** (branching based on answer analysis). LangGraph provides the framework to manage this complex, state-driven flow in a clean, modular, and traceable way.

*   **Core Libraries:**
    *   `LangGraph` & `LangChain`: For building the agent's state machine and logic.
    *   `Streamlit`: For creating the interactive, multi-phase web user interface.
    *   `langchain-groq`: For fast and efficient LLM inference.
    *   `BeautifulSoup4` & `Requests`: For the portfolio/GitHub scraping tool.
    *   `python-dotenv`: For managing environment variables securely.

*   **Language Model:** The agent utilizes the **Llama3-8B-8192** model served via the **Groq API**. This choice was made for its exceptional speed, which provides a real-time, low-latency conversational experience.

## Prompt Design

The agent's intelligence is heavily influenced by carefully crafted prompts.

*   **Question Generation:** The prompt for this node provides the LLM with the candidate's full professional profile and the scraped portfolio text. It uses a "role-playing" instruction ("You are a senior tech recruiter") and a strict output format request (a numbered list) to generate 3 relevant profile-based questions and 2 specific project-based questions. We moved from asking for JSON to a simple list to improve model reliability.

*   **Answer Analysis (The "Triage" Prompt):** This is the most sophisticated prompt. To ensure reliable classification, it uses two key techniques:
    1.  **Few-Shot Examples:** The prompt includes concrete examples of what constitutes a `NORMAL_ATTEMPT`, `GAVE_UP`, and `UNPROFESSIONAL` response. This trains the model on-the-fly to understand the nuanced difference between categories.
    2.  **Structured Output:** We bind the LLM call to a Pydantic schema with a strict `Enum` for the categories. This **forces** the model to return its classification in a guaranteed, machine-readable format, making the agent's routing 100% reliable.

## Challenges & Solutions

*   **Challenge:** The Language Model would often fail to adhere to strict JSON or text formatting instructions, causing the application to crash.
    *   **Solution:** We re-architected the agent to simplify the LLM's tasks. For question generation, we asked for a simple numbered list and parsed it reliably in Python. For answer analysis, we implemented **structured output with Pydantic**, which forces the model to comply with a predefined schema, eliminating formatting errors.

*   **Challenge:** The initial agent logic was a simple sequence, causing it to ask all questions at once without waiting for user input.
    *   **Solution:** The agent's graph was completely redesigned around a **master router** and conditional edges. The `END` node is now used strategically to terminate the agent's turn after it asks a question, creating a proper, turn-based conversational loop.

*   **Challenge:** Streamlit's default components and styling made it difficult to achieve a professional, modern chat UI and led to persistent visual bugs.
    *   **Solution:** We abandoned the restrictive default components and implemented a **fully custom chat interface** using `st.markdown` and a dedicated CSS block. This gave us complete control over the HTML structure and styling, allowing us to build a robust, bug-free UI that precisely matches the desired aesthetic.
