import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os

from shared_state import shared_state


def extract_text_with_pymupdf(file_path: str) -> str:
    """
    Attempt to extract text from a digitally generated PDF using PyMuPDF.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text or an empty string if none found.
    """
    try:
        doc = fitz.open(file_path)
        extracted_pages = []

        shared_state.page_count = len(doc)
        print(f"[INFO] PyMuPDF detected {shared_state.page_count} pages.")

        for i, page in enumerate(doc):
            page_text = page.get_text().strip()
            if page_text:
                extracted_pages.append(page_text)
            else:
                print(f"[WARN] Page {i + 1} is empty using PyMuPDF.")

        if extracted_pages:
            print(f"[INFO] PyMuPDF extracted text from {len(extracted_pages)} pages.")
        else:
            print("[WARN] PyMuPDF found no usable text.")

        return "\n\n".join(extracted_pages)

    except Exception as e:
        print(f"[ERROR] PyMuPDF failed to read PDF: {e}")
        return ""


def extract_text_with_ocr(file_path: str) -> str:
    """
    Fallback method: Convert each page to an image and extract text using OCR.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Text extracted using OCR or an empty string if unsuccessful.
    """
    try:
        images = convert_from_path(file_path)
        text_blocks = []

        shared_state.page_count = len(images)
        print(f"[INFO] OCR fallback: {shared_state.page_count} image pages found.")

        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang="eng").strip()
            if text:
                text_blocks.append(text)
            else:
                print(f"[WARN] OCR found no text on page {i + 1}.")

        if text_blocks:
            print(f"[INFO] OCR extracted text from {len(text_blocks)} pages.")
        else:
            print("[WARN] OCR found no usable text.")

        return "\n\n".join(text_blocks)

    except Exception as e:
        print(f"[ERROR] OCR extraction failed: {e}")
        return ""


def extract_text_from_pdf(file_path: str) -> str:
    """
    Main function for text extraction from any type of PDF.

    Steps:
    1. Attempt text extraction using PyMuPDF.
    2. If PyMuPDF fails or finds insufficient text, fall back to OCR.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Complete extracted text.
    """
    print(f"[INFO] Starting PDF extraction: {file_path}")

    # Record the uploaded file name in shared state
    shared_state.uploaded_filename = os.path.basename(file_path)

    # Step 1: Try extracting using PyMuPDF
    text = extract_text_with_pymupdf(file_path)

    # Step 2: Fallback to OCR if needed
    if not text or len(text.strip()) < 30:
        print("[INFO] Falling back to OCR-based extraction...")
        text = extract_text_with_ocr(file_path)

    shared_state.global_text = text or ""
    print("[INFO] Text extraction complete.")

    return text or ""
