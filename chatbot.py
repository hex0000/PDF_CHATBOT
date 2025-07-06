from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.embeddings.base import Embeddings
from langchain.schema.document import Document
from langchain.memory import ConversationBufferMemory
from PyPDF2 import PdfReader

from shared_state import shared_state
from typing import List
import re

# === Configuration ===
MEMORY_DEPTH = 50  # Number of chat turns to retain in memory

# === Initialize local LLM (Phi-3 via Ollama) ===
llm = Ollama(model="phi3", temperature=0)


def detect_intent(question: str) -> str:
    """
    Classify a user question into a specific intent category.

    Args:
        question (str): The user's input question.

    Returns:
        str: One of [page stats, page info, document content, summarization, unknown]
    """
    prompt = f"""
You are an intelligent assistant.

Classify the user's question into one of the following intents:
- page stats
- page info
- document content
- summarization
- unknown

Question: {question}

Only respond with a single intent label.
"""
    try:
        return llm.invoke(prompt).strip().lower()
    except Exception as e:
        print("[Intent Detection Error]", e)
        return "unknown"


def needs_memory(question: str) -> bool:
    """
    Determine if the question depends on prior conversation context.

    Args:
        question (str): The user's current question.

    Returns:
        bool: True if memory is needed, else False.
    """
    prompt = f"""
Does the following question depend on past conversation context?

Question: "{question}"
Answer with "yes" or "no" only.
"""
    try:
        return llm.invoke(prompt).strip().lower().startswith("yes")
    except Exception as e:
        print("[Memory Detection Error]", e)
        return False


def get_pdf_stats() -> str:
    """
    Extract and return basic statistics from the uploaded PDF.

    Returns:
        str: A human-readable summary of page, word, sentence, and paragraph counts.
    """
    text = shared_state.global_text
    page_count = shared_state.page_count or 0
    word_count = len(text.split())
    sentence_count = len(re.findall(r'[.!?]', text))
    paragraph_count = len(re.split(r'\n\s*\n', text))

    return (
        f"The document contains:\n"
        f"- {page_count} pages\n"
        f"- {word_count} words\n"
        f"- {sentence_count} sentences\n"
        f"- {paragraph_count} paragraphs"
    )


def document_search_tool_fn(query: str, vectorstore: FAISS) -> str:
    """
    Use vector search to retrieve the most relevant document chunk.

    Args:
        query (str): The search query.
        vectorstore (FAISS): The FAISS vectorstore.

    Returns:
        str: Matching content or fallback message.
    """
    docs: List[Document] = vectorstore.similarity_search(query, k=1)
    return docs[0].page_content.strip() if docs else "No relevant information found in the document."


def page_inspector_tool_fn(query: str) -> str:
    """
    Extract content from a specific page number in the uploaded PDF.

    Args:
        query (str): The user's query mentioning a page number.

    Returns:
        str: Page content or error message.
    """
    match = re.search(r'page\s*(\d+)', query.lower())
    if not match:
        return "Please specify a page number."

    page_num = int(match.group(1))
    try:
        reader = PdfReader(f"uploads/{shared_state.uploaded_filename}")
        if 1 <= page_num <= len(reader.pages):
            text = reader.pages[page_num - 1].extract_text()
            return text.strip() if text else f"Page {page_num} is empty."
        else:
            return f"Page {page_num} is out of range (max page: {len(reader.pages)})."
    except Exception as e:
        return f"Failed to extract text from page {page_num}: {e}"


def chat_with_agent(
    question: str,
    vectorstore: FAISS,
    embeddings_model: Embeddings,
    history: List[dict],
) -> str:
    """
    Handle user interaction using memory, tools, or fallback vector search.

    Args:
        question (str): User's question.
        vectorstore (FAISS): Vectorstore for document retrieval.
        embeddings_model (Embeddings): Embedding model.
        history (List[dict]): List of past conversation turns.

    Returns:
        str: Assistant's response.
    """

    # === Case 1: Context-dependent question ===
    if needs_memory(question):
        try:
            history_slice = shared_state.chat_history[-MEMORY_DEPTH:]
            chat_context = "\n".join(
                f"User: {m['user']}\nAssistant: {m['bot']}" for m in history_slice
            )
            memory_prompt = f"""
You are a helpful assistant with memory.

Here is the previous conversation:
{chat_context}

Now answer this question using only the history above.

User: {question}
Assistant:"""
            answer = llm.invoke(memory_prompt).strip()
            shared_state.chat_history.append({"user": question, "bot": answer})
            return answer
        except Exception as e:
            print("[Memory Recall Failed]", e)
            fallback = "Sorry, I couldn't recall that properly."
            shared_state.chat_history.append({"user": question, "bot": fallback})
            return fallback

    # === Case 2: Stateless — classify intent ===
    intent = detect_intent(question)

    if intent == "page stats":
        response = get_pdf_stats()
        shared_state.chat_history.append({"user": question, "bot": response})
        return response

    # === Case 3: Use tools ===
    tools = [
        Tool(
            name="DocumentSearch",
            func=lambda q: document_search_tool_fn(q, vectorstore),
            description="Finds relevant content from the uploaded PDF"
        ),
        Tool(
            name="PageInspector",
            func=page_inspector_tool_fn,
            description="Extracts content from specific pages"
        )
    ]

    recent_history = history[-MEMORY_DEPTH:]
    formatted_history = "\n".join(
        f"User: {turn['user']}\nAssistant: {turn['bot']}" for turn in recent_history
    )
    prompt_with_history = f"""{formatted_history}
User: {question}
Assistant:"""

    try:
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)
        for turn in recent_history:
            memory.chat_memory.add_user_message(turn["user"])
            memory.chat_memory.add_ai_message(turn["bot"])

        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=False,
            max_iterations=4,
            max_execution_time=15
        )

        response = agent.run(prompt_with_history).strip()

        if not response or response.lower() in [
            "agent stopped due to iteration limit or time limit.",
            "agent stopped due to time limit.",
            "agent stopped due to iteration limit.",
        ]:
            raise RuntimeError("Agent returned empty or timed out.")

        shared_state.chat_history.append({"user": question, "bot": response})
        return response

    except Exception as e:
        print("[Agent Fallback Triggered]", e)

        # === Final fallback: Vector-based search + prompt ===
        try:
            docs: List[Document] = vectorstore.similarity_search(question, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            fallback_prompt = f"""
You are a helpful assistant answering questions about a PDF.

Use only this context:
\"\"\"
{context}
\"\"\"

Question: {question}
Answer:"""
            answer = llm.invoke(fallback_prompt).strip()
            shared_state.chat_history.append({"user": question, "bot": answer})
            return answer
        except Exception as e2:
            print("[Final Fallback Failed]", e2)
            return "Sorry, the assistant could not generate an answer."
