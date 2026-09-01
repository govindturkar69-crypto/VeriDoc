# Product Requirements Document (PRD)

## 1. Product Overview
VeriDoc is a Retrieval-Augmented Generation (RAG) educational assistant application. It allows users (typically students or institutional staff) to ask questions about official institutional documents (e.g., fee deadlines, exam rules, scholarship eligibility) and receive accurate answers that are strictly grounded in those documents.

## 2. Problem Statement
Traditional chatbots are prone to "hallucinations"—inventing answers when they do not know the truth. In an institutional context, this can lead to students receiving incorrect and harmful information (e.g., missing fee deadlines). VeriDoc solves this by anchoring all answers strictly to official documentation, providing explicit citations, and employing an "honest refusal" mechanism to state when an answer cannot be found.

## 3. Goals
- Provide accurate, institutional-specific answers to user queries.
- Eliminate hallucinations by enforcing strict grounding in provided documents.
- Provide traceability through direct citations to the source file and page.
- Offer a simple, accessible web-based chat interface.

## 4. Target Users and Roles
- **End Users (Students/Parents/Staff):** Ask questions, view citations, download chat transcripts, and interact with the UI.
- **Administrators/Deployers:** Upload official documents (PDFs, DOCX, TXT, HTML) and manage the underlying knowledge base.

## 5. Main Workflows
- **Knowledge Ingestion (Admin):** Users can add documents via the sidebar UI, which are parsed (including OCR if necessary), chunked, and embedded into the vector store.
- **Querying (End User):** Users select which documents to search against in the sidebar, ask a question (via text or voice), and receive a grounded answer with citations.
- **Session Management (End User):** Users can download the chat transcript as a PDF or text file, view statistics (number of questions, likes/dislikes), and clear the conversation.

## 6. Functional Requirements
### Implemented Features
- **Semantic Search:** Uses vector embeddings to find relevant document passages based on meaning, not just keywords.
- **Honest Refusal:** Refuses to answer if relevant passages are not found or if the LLM determines the context lacks the answer.
- **Citations:** Every answer includes the source document name and page number.
- **Document Selection:** Users can filter queries to specific documents via the UI sidebar.
- **Multilingual Support:** Users can ask questions in multiple languages (English, Hindi, Marathi).
- **Voice Input:** Browser-based speech-to-text integration for asking questions.
- **Follow-up Suggestions:** Automatically suggests relevant follow-up questions based on the chat history.
- **Feedback Mechanism:** Thumbs up/down buttons for rating answers.
- **Transcript Export:** Download chat history as a PDF or TXT file.

## 7. Business Rules
- The system must prioritize truthfulness over conversational flow.
- The system must never use outside LLM training knowledge to answer institutional questions.
- If a document conflict is detected (e.g., multiple dates for a deadline), the system should display a warning alert to the user.

## 8. Current Limitations
- **In-Memory Store:** The vector database is an in-memory NumPy array serialized via Pickle. It is not designed for massive, enterprise-scale document lakes without significant memory overhead.
- **Context Size:** Retrieval is limited to the top `K` chunks, so queries requiring synthesizing information across dozens of distant pages might fail.

## 9. Acceptance Criteria (Based on current behavior)
- The application successfully ingests PDF, DOCX, TXT, and HTML files.
- The system returns an exact refusal string ("I could not find this information in the official documents.") when queried about unrelated topics.
- Every successful answer displays an expandable section showing the exact source text used.
