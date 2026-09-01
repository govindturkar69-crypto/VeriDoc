# UI/UX Documentation

## 1. Design Overview
VeriDoc uses the Streamlit framework to render a single-page chat interface. The design prioritizes trust, transparency (via citations), and ease of use. It utilizes standard Streamlit components for layout, state management, and user interaction.

## 2. Layout Structure
The application layout consists of a Main Chat Area and a Collapsible Sidebar.

### Main Chat Area
- **Header:** Displays the application title and a metric showing the current size of the knowledge base.
- **Onboarding/Empty State:** When no chat history exists, the screen displays:
  - Three feature highlight cards (Evidence first, Honest by design, Multilingual).
  - A pill-selector for common example questions (e.g., Fee deadline, Attendance).
- **Chat History:** Displays user messages and assistant responses.
  - **Assistant Messages:** Include confidence badges, execution time, number of sources used, and the text response.
  - **Citations:** Appended to assistant messages in an expandable `st.expander` component, showing the exact source document, page, and chunk text.
  - **Feedback:** "Helpful" (thumbs up) and "Needs work" (thumbs down) buttons appear below each non-refusal response.
  - **Alerts:** Conditional warnings (e.g., conflicting dates detected in sources) are displayed using `st.warning` or `st.info`.
- **Input Area:** 
  - A text input field (`st.chat_input`) fixed to the bottom.
  - A voice input button (`streamlit-mic-recorder`) positioned just above the text input.
  - Contextual "follow-up question" chips that appear based on previous interactions.

### Sidebar (Settings & Data Management)
- **Document Selection:** A multi-select checklist allowing the user to filter which documents the system searches against.
- **Answer Settings:**
  - Language selector (English, Hindi, Marathi).
  - Detail toggle (Concise vs. Detailed).
  - Simplify toggle (checkbox for simpler wording).
- **Upload Section:** A file uploader allowing administrators to add new documents (PDF, DOCX, TXT, HTML) and trigger a full index rebuild.
- **Session Stats:** Metrics showing the number of questions asked and the total likes/dislikes in the session.
- **Session Management:** Buttons to download the chat transcript (PDF or TXT) and clear the conversation.

## 3. UI States
- **IMPLEMENTED:** Loading spinners during document indexing and LLM querying.
- **IMPLEMENTED:** Warning states when attempting to ask a question without selecting any documents in the sidebar.
- **IMPLEMENTED:** Warning states when uploading unsupported file types.
- **IMPLEMENTED:** Error states if the LLM API fails.
- **IMPLEMENTED:** Conditional TTS (Text-to-Speech) read-aloud button for assistant answers.
- **NOT IMPLEMENTED:** Persistent user accounts or login screens.
- **NOT IMPLEMENTED:** Chat history persistence across page reloads (state is stored in Streamlit session memory).
