Overview:
This backend powers an interactive PDF chatbot that allows users to upload PDF documents and query their content in natural language. It uses LangChain with a local LLM (Phi-3 via Ollama), retrieval-augmented generation (RAG), and intelligent intent handling. It supports both digital PDFs and scanned documents through OCR, and stores chat history for context-aware interactions.

Project Structure:
This backend consists of the following key Python modules:

main.py – FastAPI routes

chatbot.py – Core chat logic, tool use, fallback handling

pdf_reader.py – Extracts text from PDFs using PyMuPDF and OCR

embeddings.py – Chunks and embeds text using HuggingFace + FAISS

shared_state.py – Shared global memory, chat history, and metadata

Setup Instructions:

Prerequisite: Install Docker

Clone the backend repo:
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

Navigate to the backend folder:
cd YOUR_REPO_NAME/backend

Build the Docker image:
docker build -t pdf-backend .

Run the container:
docker run -p 8000:8000 pdf-backend

Access the API locally at:
http://localhost:8000

API Endpoints:

POST /upload/

Description: Upload a PDF file for text extraction and vector indexing

Form data: file (PDF document)

Response:
• Processed filename
• Total number of pages and chunks
• Time taken

POST /ask/

Description: Ask a question related to the uploaded PDF

Body (JSON): { "question": "your question here" }

Optional query param: last_n (default 30)

Response:
• Answer
• Original question
• Response time

Features and Functionalities:

Upload and extract text from PDFs using PyMuPDF or OCR (Tesseract)

Chunk text using LangChain's recursive splitter

Generate semantic embeddings using HuggingFace transformers

Store and search document chunks via FAISS vectorstore

Use Ollama with the Phi-3 model to generate answers

Intelligent intent detection (page stats, content, summaries, etc.)

Tool-based agent for document search and page-specific queries

Chat memory maintained across turns (ConversationBufferMemory)

Dockerized for clean, reproducible deployment

This backend is designed to integrate seamlessly with the frontend (chat UI) and can be deployed using a single Docker container. For local development, FastAPI endpoints can be accessed directly for testing and debugging.
