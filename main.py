from fastapi import FastAPI, UploadFile, File, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from PyPDF2 import PdfReader

from pdf_reader import extract_text_from_pdf
from embeddings import chunk_text, get_embeddings, build_vectorstore
from chatbot import chat_with_agent
from shared_state import shared_state

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can change this to ["http://localhost:3000"] or your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, extract its content, generate embeddings,
    build a vector store, and reset any shared memory/state.

    Args:
        file (UploadFile): PDF file to be uploaded.

    Returns:
        dict: Metadata about the upload, such as chunk count, page count, and processing time.
    """
    start_time = time.time()

    # Validate file extension
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are allowed."}

    # Save uploaded file to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Reset previous session state
    shared_state.reset()
    shared_state.uploaded_filename = file.filename

    # Step 1: Extract text from the PDF
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        return {"error": "No readable text found in the PDF."}

    shared_state.global_text = text

    # Step 2: Count number of pages in the PDF
    try:
        reader = PdfReader(file_path)
        shared_state.page_count = len(reader.pages)
    except Exception as e:
        shared_state.page_count = 0
        print("[Page Count Error]", e)

    # Step 3: Chunk the extracted text and generate embeddings
    chunks = chunk_text(text)
    embeddings_model = get_embeddings()
    vectorstore = build_vectorstore(chunks, embeddings_model)

    # Store in shared state
    shared_state.vectorstore = vectorstore
    shared_state.embeddings_model = embeddings_model
    shared_state.chunks = chunks

    return {
        "filename": file.filename,
        "message": "PDF uploaded and processed successfully.",
        "num_chunks": len(chunks),
        "page_count": shared_state.page_count,
        "processing_time_seconds": round(time.time() - start_time, 2)
    }


@app.post("/ask/")
async def ask_question(
    question: str = Body(..., embed=True),
    last_n: int = Query(
        30,
        ge=1,
        le=100,
        description="How many past turns to include in memory"
    )
):
    """
    Respond to a user question using Retrieval-Augmented Generation (RAG) and chat history.

    Args:
        question (str): User's input question.
        last_n (int): Number of past messages to include for context.

    Returns:
        dict: Answer to the user's question, including processing time.
    """
    if not shared_state.vectorstore:
        return {
            "error": "No PDF uploaded yet. Please upload one first.",
            "response_time_seconds": 0
        }

    start_time = time.time()

    # Generate answer using RAG + chat memory
    answer = chat_with_agent(
        question=question,
        vectorstore=shared_state.vectorstore,
        embeddings_model=shared_state.embeddings_model,
        history=shared_state.chat_history[-last_n:]
    )

    # Print chat history for debugging/logging
    shared_state.print_chat_history()

    return {
        "question": question,
        "answer": answer,
        "response_time_seconds": round(time.time() - start_time, 2)
    }
