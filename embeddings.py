from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import fitz  # PyMuPDF

from shared_state import shared_state


def get_embeddings():
    """
    Load and return a HuggingFace sentence-transformer embedding model.

    Returns:
        HuggingFaceEmbeddings: Embedding model for encoding text.
    """
    print("[INFO] Loading HuggingFace embeddings: all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def chunk_text(input_data: str) -> list:
    """
    Split the given input (PDF path or raw text) into overlapping text chunks.

    Args:
        input_data (str): Either plain text or a PDF file path.

    Returns:
        list: List of chunk dictionaries with 'content' and 'metadata'.
    """
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=75,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        length_function=len
    )

    if input_data.lower().endswith(".pdf"):
        print(f"[INFO] Chunking PDF: {input_data}")
        try:
            doc = fitz.open(input_data)
            shared_state.page_count = len(doc)

            for i, page in enumerate(doc):
                text = page.get_text().strip()
                if not text or len(text) < 20:
                    print(f"[WARN] Skipping page {i + 1} — empty or too short")
                    continue

                splits = splitter.split_text(text)
                for chunk in splits:
                    cleaned = chunk.strip()
                    if cleaned:
                        chunks.append({
                            "content": cleaned,
                            "metadata": {"page": i + 1}
                        })

        except Exception as e:
            print(f"[ERROR] Failed to open PDF: {e}")
            raise e

    else:
        print("[INFO] Chunking plain text input")
        text = input_data.strip()
        splits = splitter.split_text(text)
        for chunk in splits:
            cleaned = chunk.strip()
            if cleaned:
                chunks.append({
                    "content": cleaned,
                    "metadata": {"page": "unknown"}
                })

    print(f"[INFO] Total chunks created: {len(chunks)}")
    shared_state.chunks = chunks
    return chunks


def build_vectorstore(chunks: list, embeddings_model) -> FAISS:
    """
    Build a FAISS vectorstore from the given text chunks using the specified embedding model.

    Args:
        chunks (list): List of dicts with 'content' and 'metadata'.
        embeddings_model (Embeddings): The embeddings model to use.

    Returns:
        FAISS: An in-memory FAISS vector store ready for similarity search.
    """
    print("[INFO] Building FAISS vectorstore...")

    documents = [
        Document(page_content=chunk["content"], metadata=chunk["metadata"])
        for chunk in chunks
    ]

    try:
        vectorstore = FAISS.from_documents(documents, embeddings_model)
        print(f"[SUCCESS] FAISS store created with {len(documents)} documents.")

        # Save references globally
        shared_state.vectorstore = vectorstore
        shared_state.embeddings_model = embeddings_model

        return vectorstore

    except Exception as e:
        print(f"[ERROR] Failed to build vectorstore: {e}")
        raise e
