import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to sys.path
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

from ai_engine import process_ncert_content, extract_text_from_pdf

def main():
    load_dotenv(dotenv_path=current_dir / ".env")
    
    parser = argparse.ArgumentParser(
        description="NCERT Hinglish AI - Translate & Explain NCERT Text and PDF documents into simple Hinglish."
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the interactive Streamlit Web UI"
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Direct text or question to explain in Hinglish"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Path to an NCERT PDF file"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["concept_explainer", "exam_notes", "qa_solver", "practice_quiz", "direct_translation"],
        default="concept_explainer",
        help="Hinglish output mode (default: concept_explainer)"
    )
    parser.add_argument(
        "--custom",
        type=str,
        default="",
        help="Additional custom instruction (e.g. 'Class 10 Biology focus')"
    )

    args = parser.parse_args()

    # If --ui flag is passed or no arguments are provided, give option to run UI or demo
    if args.ui or (len(sys.argv) == 1):
        print("=" * 60)
        print("🎓 NCERT HINGLISH AI - TEXT & PDF TRANSLATOR / EXPLAINER")
        print("=" * 60)
        print("\nStarting Interactive Web UI on http://localhost:8501 ...\n")
        app_path = current_dir / "app.py"
        os.system(f'streamlit run "{app_path}"')
        return

    # Process CLI request
    pdf_bytes = None
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"❌ Error: PDF file not found at {args.pdf}")
            sys.exit(1)
        print(f"📖 Reading PDF: {pdf_path.name}...")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

    text_input = args.text
    if not text_input and not pdf_bytes:
        text_input = "Explain Photosynthesis in simple Hinglish with daily life examples."
        print(f"💡 No input provided. Using sample query: '{text_input}'\n")

    print(f"🚀 Processing with Mode: [{args.mode}]...\n")
    try:
        response = process_ncert_content(
            text_content=text_input or "",
            pdf_bytes=pdf_bytes,
            mode=args.mode,
            custom_instruction=args.custom
        )
        print("--- HINGLISH AI RESPONSE ---")
        print(response)
        print("-" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()