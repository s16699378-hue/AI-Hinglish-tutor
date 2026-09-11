import os
import io
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pypdf

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Supported Gemini Models (with fallback options)
MODELS_TO_TRY = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]


def get_gemini_client(api_key: str = None) -> genai.Client:
    """Initializes and returns the Google GenAI client."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing. Please set it in your .env file or UI.")
    return genai.Client(api_key=key)


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text from a PDF file (supports file path, bytes, or file-like object).
    Returns cleaned string text with page demarcations.
    """
    try:
        if isinstance(pdf_file, (bytes, bytearray)):
            stream = io.BytesIO(pdf_file)
        elif isinstance(pdf_file, (str, Path)):
            stream = open(pdf_file, "rb")
        else:
            # File-like object (e.g. UploadedFile from Streamlit)
            stream = pdf_file
            if hasattr(stream, "seek"):
                stream.seek(0)

        reader = pypdf.PdfReader(stream)
        total_pages = len(reader.pages)
        if total_pages == 0:
            return ""

        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_text = page_text.strip()
            if page_text:
                extracted_pages.append(f"--- [Page {i + 1}] ---\n{page_text}")

        return "\n\n".join(extracted_pages)
    except Exception as e:
        raise RuntimeError(f"PDF extraction error: {str(e)}")


def build_system_prompt(mode: str, custom_instruction: str = "") -> str:
    """Constructs a rich pedagogical prompt for NCERT Hinglish translation & explanation."""
    base_guidelines = (
        "You are an expert NCERT Indian Educator and AI Tutor specialized in explaining complex "
        "concepts in clear, natural, engaging Hinglish (Hindi written in Roman English script, "
        "e.g., 'Photosynthesis wo process hai jisme plants apna food banate hain').\n"
        "Rules:\n"
        "1. Keep scientific terms, formulas, and key definitions in standard English in brackets or bold "
        "(e.g., **Mitochondria (Powerhouse of the cell)**, **Force ($F = ma$)**).\n"
        "2. Explain logically with real-world Indian everyday examples/analogies.\n"
        "3. Keep the tone friendly, encouraging, and easy to understand for Class 6-12 students.\n"
        "4. Use neat Markdown formatting with headings, bullet points, and highlight boxes."
    )

    mode_prompts = {
        "concept_explainer": (
            "Mode: Comprehensive Concept Explanation (आसान भाषा में समझाएं).\n"
            "Break down the topic into:\n"
            "1. **Core Concept (Asal Baat Kya Hai?)**\n"
            "2. **Step-by-Step Breakdown (Kaise Kaam Karta Hai?)**\n"
            "3. **Real-Life Example / Analogy (Rozmarra Ki Zindagi Se Example)**\n"
            "4. **Key Takeaways (Yaad Rakhne Wali Baatein)**"
        ),
        "exam_notes": (
            "Mode: Exam Quick Revision Notes (Quick Revision & Highlights).\n"
            "Provide:\n"
            "1. **Quick Summary (Short me)**\n"
            "2. **Important Definitions & Keywords**\n"
            "3. **Crucial Formulas / Equations / Dates**\n"
            "4. **Top 5 High-Yield Exam Questions & Hints**"
        ),
        "qa_solver": (
            "Mode: NCERT Doubt & Question Solver.\n"
            "Answer the student's query thoroughly using the context. Give direct answers, explanations in Hinglish, "
            "and tips on how to write full-marks answers in exams."
        ),
        "practice_quiz": (
            "Mode: Practice Quiz & MCQs.\n"
            "Generate 5 high-quality Multiple Choice Questions (MCQs) based on the text/PDF with options (A, B, C, D), "
            "correct answers, and detailed Hinglish explanations for each."
        ),
        "direct_translation": (
            "Mode: Direct Line-by-Line Hinglish Translation.\n"
            "Translate the text into natural Hinglish, preserving the exact paragraph structure and technical terms."
        )
    }

    selected_mode_prompt = mode_prompts.get(mode, mode_prompts["concept_explainer"])
    
    full_prompt = f"{base_guidelines}\n\n{selected_mode_prompt}"
    if custom_instruction:
        full_prompt += f"\n\nAdditional User Request: {custom_instruction}"
        
    return full_prompt


def process_ncert_content(
    text_content: str = "",
    pdf_bytes: bytes = None,
    mode: str = "concept_explainer",
    custom_instruction: str = "",
    api_key: str = None
) -> str:
    """
    Processes text or PDF content and returns the Hinglish explanation.
    Tries text extraction first; if PDF is scanned or image-based, uses direct Gemini multimodal bytes.
    """
    client = get_gemini_client(api_key)
    system_instruction = build_system_prompt(mode, custom_instruction)

    contents = []
    pdf_extracted_text = ""

    if pdf_bytes:
        # Step 1: Attempt to extract text from PDF
        try:
            pdf_extracted_text = extract_text_from_pdf(pdf_bytes)
        except Exception:
            pdf_extracted_text = ""

        # If text extraction succeeded and has meaningful content
        if pdf_extracted_text and len(pdf_extracted_text.strip()) > 30:
            prompt_content = (
                f"{system_instruction}\n\n"
                f"### NCERT CONTENT EXTRACTED FROM PDF:\n\n{pdf_extracted_text}"
            )
            contents = [prompt_content]
        else:
            # Fallback: Multimodal direct PDF upload
            pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
            contents = [
                pdf_part,
                f"{system_instruction}\n\nPlease read the attached NCERT document and provide the complete response in Hinglish."
            ]
    elif text_content:
        prompt_content = f"{system_instruction}\n\n### NCERT INPUT CONTENT:\n\n{text_content}"
        contents = [prompt_content]
    else:
        raise ValueError("Please provide either text content or upload a PDF file.")

    # Try models in order of priority
    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            if response and response.text:
                return response.text
        except Exception as err:
            last_error = err
            continue

    if last_error:
        raise RuntimeError(f"AI Generation failed across models. Error: {str(last_error)}")
    
    return "No response generated. Please check your input."
