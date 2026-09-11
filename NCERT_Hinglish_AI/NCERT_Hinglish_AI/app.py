import streamlit as st
import os
import io
from pathlib import Path
from dotenv import load_dotenv

# Ensure the app imports ai_engine correctly
try:
    from ai_engine import process_ncert_content, extract_text_from_pdf
except ImportError:
    from NCERT_Hinglish_AI.ai_engine import process_ncert_content, extract_text_from_pdf

# Load .env
env_file = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_file)

# Configure Streamlit Page
st.set_page_config(
    page_title="NCERT Hinglish AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark, focused styling for the study workspace.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Source+Serif+4:wght@600;700&display=swap');

    * {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: #0d171a;
        color: #e8f2ef;
    }

    [data-testid="stHeader"] {
        background: rgba(13, 23, 26, 0.92);
    }

    [data-testid="stSidebar"] {
        background: #111f23;
        border-right: 1px solid #284047;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: #e8f2ef;
    }

    h4 {
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 1.25rem;
    }

    .main-header {
        color: #71d5c8;
        font-family: 'Source Serif 4', serif;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 700;
        text-align: center;
        line-height: 1.1;
        margin-bottom: 0.45rem;
    }

    .sub-header {
        text-align: center;
        color: #91a6a7;
        font-size: 1rem;
        margin: 0 auto 2rem;
        max-width: 680px;
    }

    div[data-testid="column"] {
        background: #16262a;
        border: 1px solid #294149;
        border-radius: 14px;
        padding: 0.7rem 1.1rem 1rem;
    }

    div[data-testid="column"]:nth-child(2) {
        border-color: #3d8d85;
        box-shadow: 0 0 0 1px rgba(113, 213, 200, 0.12), 0 16px 36px rgba(0, 0, 0, 0.2);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid #2e474d;
    }

    .stTabs [data-baseweb="tab"] {
        color: #91a6a7;
        font-weight: 600;
        padding: 0.65rem 0.85rem;
    }

    .stTabs [aria-selected="true"] {
        color: #71d5c8;
        border-bottom-color: #f2a65a;
    }

    .stButton > button {
        background: #f2a65a;
        color: #172022;
        border: 1px solid #f2a65a;
        border-radius: 8px;
        min-height: 2.75rem;
        font-weight: 600;
        transition: background 0.2s ease, transform 0.2s ease;
    }

    .stButton > button:hover {
        background: #ffc47b;
        border-color: #ffc47b;
        transform: translateY(-2px);
    }

    .stDownloadButton > button {
        background: transparent;
        color: #71d5c8;
        border: 1px solid #3d8d85;
        border-radius: 8px;
        min-height: 2.65rem;
        font-weight: 600;
    }

    .stDownloadButton > button:hover {
        background: #203a3e;
        border-color: #71d5c8;
        transform: translateY(-2px);
    }

    [data-baseweb="input"], [data-baseweb="select"] > div,
    [data-testid="stTextArea"] textarea {
        background: #0f1d20;
        color: #e8f2ef;
        border-color: #365159;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #102024;
        border: 1px dashed #4b7778;
    }

    .pdf-info-box {
        background: #193936;
        border: 1px solid #397a70;
        border-left: 4px solid #71d5c8;
        border-radius: 8px;
        color: #b9eee6;
        margin-top: 0.75rem;
        padding: 0.85rem 1rem;
    }

    [data-testid="stAlert"] {
        border-radius: 8px;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stWidgetLabel"] p {
        color: #d4e2df;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #a9bfbc;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 2rem 1rem;
        }

        .main-header {
            text-align: left;
        }

        .sub-header {
            text-align: left;
        }

        div[data-testid="column"] {
            padding: 0.55rem 0.8rem 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

# Sidebar Controls
with st.sidebar:
    st.markdown("## NCERT Hinglish AI")
    st.caption("A simple study companion for clear, exam-ready explanations.")
    st.markdown("### ⚙️ **AI Settings & Keys**")
    
    user_api_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Reads from .env by default. You can override it here."
    )
    if user_api_key:
        st.session_state.api_key = user_api_key

    st.divider()
    
    st.markdown("### 📚 **NCERT Class & Subject**")
    grade = st.selectbox(
        "Class Level",
        ["Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12", "Competitive (NEET/JEE/UPSC)"],
        index=4
    )
    subject = st.selectbox(
        "Subject",
        ["Science / Physics / Chemistry / Biology", "Mathematics", "Social Science (History/Civics/Geo)", "Economics / Commerce", "General Knowledge & Concepts"]
    )
    
    st.divider()
    st.markdown("### 💡 **Quick NCERT Examples**")
    sample_options = {
        "— Select a Sample —": "",
        "🌱 Photosynthesis (Class 7/10 Biology)": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize nutrients from carbon dioxide and water. In plants, photosynthesis generally involves the green pigment chlorophyll and generates oxygen as a byproduct.",
        "⚡ Newton's 3rd Law (Class 9/11 Physics)": "Newton's Third Law of Motion states that for every action, there is an equal and opposite reaction. When object A exerts a force on object B, object B simultaneously exerts an equal magnitude force in the opposite direction on object A.",
        "🧪 Chemical Reactions & Rusting (Class 10 Chem)": "Corrosion is a natural process that converts a refined metal into a more chemically-stable oxide. Rusting of iron occurs in the presence of water and oxygen: 4Fe + 3O2 + 6H2O -> 4Fe(OH)3.",
        "🌍 French Revolution (Class 9 History)": "The French Revolution began in 1789 with the storming of the Bastille. It led to the end of monarchy in France, the rise of democratic ideals (Liberty, Equality, Fraternity), and profoundly changed modern history."
    }
    selected_sample = st.selectbox("Load Sample Prompt", list(sample_options.keys()))

# Header
st.markdown('<div class="main-header">🎓 NCERT Hinglish AI Tutor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Convert NCERT Textbooks & PDFs into crystal-clear, exam-ready Hinglish explanations</div>', unsafe_allow_html=True)

# Main Grid Layout
col_input, col_output = st.columns([1.1, 1.3], gap="large")

with col_input:
    st.markdown("#### 📥 **Input NCERT Content**")
    
    mode = st.selectbox(
        "🎯 **Choose Hinglish Output Mode**",
        [
            ("concept_explainer", "💡 Concept Explainer (आसान भाषा में deep explanation with examples)"),
            ("exam_notes", "📝 Exam Quick Notes (Summary, Key Terms & Formulas)"),
            ("qa_solver", "❓ NCERT Doubt & Q&A Solver (Direct Answer & Explanation)"),
            ("practice_quiz", "🎯 Practice MCQs & Quiz (5 Test Questions with Hints)"),
            ("direct_translation", "🌐 Direct Line-by-Line Translation (Hinglish)")
        ],
        format_func=lambda x: x[1]
    )[0]

    input_tab1, input_tab2 = st.tabs(["📄 Upload NCERT PDF", "✍️ Enter / Paste Text"])
    
    pdf_bytes = None
    text_content = ""
    extracted_preview = ""

    with input_tab1:
        uploaded_pdf = st.file_uploader(
            "Upload NCERT Chapter / Notes PDF",
            type=["pdf"],
            help="Supports standard textbook PDFs, chapter notes, and question banks."
        )
        if uploaded_pdf is not None:
            pdf_bytes = uploaded_pdf.read()
            st.markdown(f"""
            <div class="pdf-info-box">
                ✅ <b>Uploaded:</b> {uploaded_pdf.name} ({(len(pdf_bytes)/1024):.1f} KB)<br>
                ✨ Multimodal PDF analysis active with fallback text extraction.
            </div>
            """, unsafe_allow_html=True)
            
            # Show extracted text preview toggle
            try:
                extracted_preview = extract_text_from_pdf(pdf_bytes)
                if extracted_preview:
                    with st.expander("🔍 View Extracted PDF Text Preview"):
                        st.text(extracted_preview[:1500] + ("..." if len(extracted_preview) > 1500 else ""))
            except Exception as e:
                st.info("Direct visual multimodal document parsing will be used.")

    with input_tab2:
        default_text = sample_options[selected_sample] if selected_sample != "— Select a Sample —" else ""
        text_content = st.text_area(
            "Paste NCERT Paragraph, Definition or Question:",
            value=default_text,
            height=220,
            placeholder="e.g. What is the difference between speed and velocity? Explain with NCERT formulas."
        )

    custom_notes = st.text_input(
        "🎯 Specific instructions (optional)",
        placeholder="e.g., Focus on Class 10 Board exam questions, use very simple analogies"
    )

    generate_btn = st.button("Explain in Hinglish (कन्वर्ट करें)", width="stretch")

with col_output:
    st.markdown("#### 🌟 **Hinglish AI Output**")
    
    if generate_btn:
        if not pdf_bytes and not text_content.strip():
            st.error("⚠️ Please either upload a PDF file or paste text content to proceed.")
        elif not st.session_state.api_key:
            st.error("⚠️ GEMINI_API_KEY is missing. Please add it to your `.env` or in the sidebar.")
        else:
            with st.spinner("⏳ Analyzing NCERT content and preparing Hinglish explanation..."):
                try:
                    full_custom_inst = f"Target Audience: {grade} - {subject}."
                    if custom_notes:
                        full_custom_inst += f" User instruction: {custom_notes}"

                    response_text = process_ncert_content(
                        text_content=text_content,
                        pdf_bytes=pdf_bytes,
                        mode=mode,
                        custom_instruction=full_custom_inst,
                        api_key=st.session_state.api_key
                    )
                    
                    # Store in session state
                    st.session_state.last_response = response_text
                    st.session_state.history.append({
                        "mode": mode,
                        "grade": grade,
                        "subject": subject,
                        "response": response_text
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error occurred: {str(e)}")

    if "last_response" in st.session_state and st.session_state.last_response:
        st.markdown(st.session_state.last_response)
        
        st.divider()
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Download Hinglish Notes (.md)",
                data=st.session_state.last_response,
                file_name="ncert_hinglish_notes.md",
                mime="text/markdown",
                width="stretch"
            )
        with col_d2:
            st.download_button(
                label="📄 Download Text (.txt)",
                data=st.session_state.last_response,
                file_name="ncert_hinglish_notes.txt",
                mime="text/plain",
                width="stretch"
            )
    else:
        st.info("👈 Upload a PDF or paste text on the left, then click **'Explain in Hinglish'** to generate easy-to-understand explanations!")

# History Section
if st.session_state.history:
    with st.expander(f"📜 View Previous Outputs ({len(st.session_state.history)} generated)"):
        for idx, item in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**Session #{len(st.session_state.history) - idx}** | Mode: `{item['mode']}` | {item['grade']}")
            st.markdown(item["response"][:400] + "...")
            st.divider()
