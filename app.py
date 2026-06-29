"""
AI Revision Assistant - Streamlit Application
A premium web application for students to generate comprehensive revision material from their study documents.
"""
import os
import io
import streamlit as st
from dotenv import load_dotenv

# Import file utility readers
from utils.pdf_reader import extract_text_from_pdf
from utils.docx_reader import extract_text_from_docx
from utils.markdown_reader import extract_text_from_markdown
from utils.ai_helper import get_revision_data, RevisionData

# Load environment variables
load_dotenv()

# Ensure required directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("assets", exist_ok=True)

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Revision Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# Custom Styling (Sleek Dark Theme & Typography)
# ----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #0b0a0f;
        color: #f1f0f5;
    }

    /* Main Title & Headers */
    .app-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .app-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        color: #ffffff !important;
        font-weight: 600;
    }

    /* Premium Containers & Cards */
    .revision-card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        transition: border-color 0.3s, transform 0.3s;
    }
    .revision-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
    }
    
    /* Definitions block styling */
    .definition-card {
        background: rgba(99, 102, 241, 0.03);
        border-left: 4px solid #6366f1;
        border-radius: 4px 12px 12px 4px;
        padding: 15px;
        margin-bottom: 12px;
    }
    
    .definition-term {
        font-weight: 700;
        color: #a855f7;
        font-size: 1.1rem;
        margin-bottom: 4px;
    }
    
    .definition-desc {
        color: #e2e8f0;
    }

    /* Interactive Flashcard CSS styling */
    .flashcard-outer {
        display: flex;
        justify-content: center;
        align-items: center;
        perspective: 1000px;
        margin: 20px 0;
    }

    .flashcard-inner {
        width: 100%;
        max-width: 600px;
        min-height: 280px;
        background: linear-gradient(135deg, #181622 0%, #0d0c14 100%);
        border: 2px solid #6366f1;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15);
        padding: 30px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        transition: transform 0.4s;
    }
    
    .flashcard-side-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6366f1;
        font-weight: 700;
        margin-bottom: 15px;
    }
    
    .flashcard-content {
        font-family: 'Outfit', sans-serif;
        font-size: 1.4rem;
        font-weight: 500;
        color: #ffffff;
        line-height: 1.5;
        margin-bottom: 20px;
    }
    
    .flashcard-answer-content {
        font-size: 1.15rem;
        color: #cbd5e1;
        line-height: 1.6;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 20px;
        width: 100%;
    }

    /* Quiz Box styling */
    .quiz-question-box {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .quiz-question-header {
        font-weight: 600;
        font-size: 1.1rem;
        color: #ffffff;
        margin-bottom: 15px;
    }
    
    .explanation-box {
        background: rgba(168, 85, 247, 0.05);
        border-left: 3px solid #a855f7;
        padding: 12px;
        margin-top: 12px;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }

    /* Clean Statistics Badge */
    .stat-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px 12px;
        margin-right: 10px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "file_name" not in st.session_state:
    st.session_state.file_name = ""
if "revision_data" not in st.session_state:
    st.session_state.revision_data = None
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "show_flashcard_answer" not in st.session_state:
    st.session_state.show_flashcard_answer = False
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# ----------------------------------------------------
# Sidebar Setup
# ----------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/gradient/100/graduation-cap.png", width=70)
    st.markdown("### Settings & Config")
    
    # API Key retrieval logic (check env first, then prompt)
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    api_key_placeholder = "Loaded from system environment" if env_api_key else "Enter your Gemini API key"
    
    user_api_key = st.text_input(
        "Google Gemini API Key",
        value=env_api_key if env_api_key else "",
        type="password",
        placeholder=api_key_placeholder,
        help="Generate an API key at https://aistudio.google.com/"
    )
    
    api_key = user_api_key if user_api_key else env_api_key
    
    # Model configuration
    model_name = st.selectbox(
        "AI Model",
        options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"],
        index=0,
        help="gemini-1.5-flash is fast and recommended for general documents."
    )
    
    st.markdown("---")
    st.markdown("### How to use:")
    st.write("1. Provide your Gemini API key above.")
    st.write("2. Go to the **Upload** tab and drop your PDF, DOCX, TXT, or MD file.")
    st.write("3. Click **Generate Study Material**.")
    st.write("4. Navigate the tabs to revise!")

# ----------------------------------------------------
# Main Title Banner
# ----------------------------------------------------
st.markdown('<div class="app-title">🎓 AI Revision Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Transform lecture slides, textbooks, and notes into interactive revision summaries, flashcards, and practice quizzes.</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# Tab Layout Setup
# ----------------------------------------------------
tab_upload, tab_summary, tab_notes, tab_flashcards, tab_quiz, tab_viva = st.tabs([
    "📥 Upload Document",
    "📝 Summary & Sheets",
    "📚 Detailed Revision Notes",
    "🎴 Flashcards",
    "🎯 Practice Quiz",
    "🗣️ Viva & Interview Questions"
])

# ====================================================
# TAB 1: Upload
# ====================================================
with tab_upload:
    st.markdown("### Upload Study Material")
    st.write("Upload a document to extract text and generate study materials. Supported formats: PDF, DOCX, TXT, MD.")
    
    uploaded_file = st.file_uploader(
        "Choose file",
        type=["pdf", "docx", "txt", "md"],
        help="Upload files up to 200MB."
    )
    
    # Read/process uploaded file
    if uploaded_file is not None:
        # Check if it's a new file
        if uploaded_file.name != st.session_state.file_name:
            with st.spinner("Extracting text from file..."):
                try:
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    extracted_text = ""
                    
                    if file_ext == "pdf":
                        extracted_text = extract_text_from_pdf(uploaded_file)
                    elif file_ext == "docx":
                        extracted_text = extract_text_from_docx(uploaded_file)
                    elif file_ext in ["txt", "md"]:
                        extracted_text = extract_text_from_markdown(uploaded_file)
                    else:
                        st.error("Unsupported file extension.")
                        st.stop()
                    
                    # Save to state
                    st.session_state.extracted_text = extracted_text
                    st.session_state.file_name = uploaded_file.name
                    # Clear out previous revision content and quiz state
                    st.session_state.revision_data = None
                    st.session_state.flashcard_index = 0
                    st.session_state.show_flashcard_answer = False
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    
                except Exception as e:
                    st.error(f"Error extracting text: {str(e)}")
                    st.stop()
        
        # Display document statistics
        text_length = len(st.session_state.extracted_text)
        word_count = len(st.session_state.extracted_text.split())
        est_read_time = max(1, round(word_count / 200)) # 200 wpm standard
        
        st.success(f"Successfully loaded document: **{st.session_state.file_name}**")
        
        # Stats layout
        st.markdown(f"""
        <div>
            <span class="stat-badge">📊 Total Characters: {text_length:,}</span>
            <span class="stat-badge">📝 Word Count: {word_count:,}</span>
            <span class="stat-badge">⏱️ Estimated Reading Time: {est_read_time} min</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Text preview inside expander
        with st.expander("Preview Extracted Text"):
            st.text_area("Extracted Text Content", st.session_state.extracted_text, height=250, disabled=True)
            
        st.markdown("### Generate Revision Materials")
        st.info("The application will read this document and use Google Gemini to generate structured notes, MCQs, definitions, and flashcards in one quick run.")
        
        # Prompt model generation
        if st.button("🚀 Generate Study Material", type="primary"):
            if not api_key:
                st.warning("Please provide a Google Gemini API Key in the sidebar to proceed.")
            elif not st.session_state.extracted_text:
                st.error("File seems to contain no extractable text. Please try a different file.")
            else:
                # Warning for large documents
                if len(st.session_state.extracted_text) > 80000:
                    st.toast("Large document detected. AI processing might take up to a minute.")
                    
                with st.spinner("🧠 AI is analyzing and generating study materials... Please wait."):
                    try:
                        revision_data = get_revision_data(
                            text=st.session_state.extracted_text,
                            api_key=api_key,
                            model_name=model_name
                        )
                        st.session_state.revision_data = revision_data
                        st.balloons()
                        st.success("🎉 Revision materials generated successfully! Use the tabs above to start revising.")
                    except Exception as e:
                        st.error(f"AI Generation Failed: {str(e)}")
    else:
        st.info("Please upload a file above to begin.")

# ====================================================
# TAB 2: Summary & Revision Sheets
# ====================================================
with tab_summary:
    if st.session_state.revision_data is None:
        st.info("⚠️ Please upload a document and generate revision materials in the 'Upload Document' tab first.")
    else:
        rev_data: RevisionData = st.session_state.revision_data
        
        # Use columns or expanders to separate subcomponents beautifully
        st.markdown("### Concise Document Summary")
        st.markdown(f'<div class="revision-card">{rev_data.summary}</div>', unsafe_allow_html=True)
        
        # Split Key Takeaways & Definitions
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Key Takeaways")
            key_points_html = "<ul>" + "".join([f"<li>{point}</li>" for point in rev_data.key_points]) + "</ul>"
            st.markdown(f'<div class="revision-card">{key_points_html}</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown("### Key Definitions")
            definitions_html = '<div class="revision-card" style="max-height: 350px; overflow-y: auto;">'
            if not rev_data.definitions:
                definitions_html += "<p>No specific definitions extracted.</p>"
            for item in rev_data.definitions:
                definitions_html += f"""
                <div class="definition-card">
                    <div class="definition-term">{item.term}</div>
                    <div class="definition-desc">{item.definition}</div>
                </div>
                """
            definitions_html += "</div>"
            st.markdown(definitions_html, unsafe_allow_html=True)
            
        # Revision sheets section
        st.markdown("---")
        st.markdown("### Quick Review Sheets")
        
        sheet_5m, sheet_1m = st.tabs(["⏱️ 5-Minute Revision Sheet", "⚡ 1-Minute Cram Sheet"])
        
        with sheet_5m:
            st.markdown(f'<div class="revision-card">{rev_data.five_minute_sheet}</div>', unsafe_allow_html=True)
            
        with sheet_1m:
            st.markdown(f'<div class="revision-card">{rev_data.one_minute_sheet}</div>', unsafe_allow_html=True)

# ====================================================
# TAB 3: Detailed Revision Notes
# ====================================================
with tab_notes:
    if st.session_state.revision_data is None:
        st.info("⚠️ Please upload a document and generate revision materials in the 'Upload Document' tab first.")
    else:
        rev_data: RevisionData = st.session_state.revision_data
        st.markdown("### Comprehensive Revision Notes")
        st.markdown(f'<div class="revision-card">{rev_data.revision_notes}</div>', unsafe_allow_html=True)

# ====================================================
# TAB 4: Flashcards
# ====================================================
with tab_flashcards:
    if st.session_state.revision_data is None:
        st.info("⚠️ Please upload a document and generate revision materials in the 'Upload Document' tab first.")
    else:
        rev_data: RevisionData = st.session_state.revision_data
        flashcards = rev_data.flashcards
        
        if not flashcards:
            st.warning("No flashcards available for this document.")
        else:
            # Boundary security checking
            if st.session_state.flashcard_index >= len(flashcards):
                st.session_state.flashcard_index = 0
                
            current_card = flashcards[st.session_state.flashcard_index]
            
            st.markdown("### Interactive Flashcards")
            st.write("Test your knowledge. Read the question, formulate your answer, then click to reveal.")
            
            # Progress tracker
            st.progress((st.session_state.flashcard_index + 1) / len(flashcards))
            st.caption(f"Card {st.session_state.flashcard_index + 1} of {len(flashcards)}")
            
            # Flashcard container
            # Show either question or answer based on show_flashcard_answer state
            if not st.session_state.show_flashcard_answer:
                card_html = f"""
                <div class="flashcard-outer">
                    <div class="flashcard-inner">
                        <div class="flashcard-side-label">Front (Question)</div>
                        <div class="flashcard-content">{current_card.question}</div>
                    </div>
                </div>
                """
            else:
                card_html = f"""
                <div class="flashcard-outer">
                    <div class="flashcard-inner" style="border-color: #a855f7; box-shadow: 0 10px 30px rgba(168, 85, 247, 0.15);">
                        <div class="flashcard-side-label" style="color: #a855f7;">Back (Answer)</div>
                        <div class="flashcard-content">{current_card.question}</div>
                        <div class="flashcard-answer-content">{current_card.answer}</div>
                    </div>
                </div>
                """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Controls layout
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 2, 2, 1])
            
            with btn_col1:
                if st.button("⏮️ Prev", use_container_width=True):
                    st.session_state.flashcard_index = (st.session_state.flashcard_index - 1) % len(flashcards)
                    st.session_state.show_flashcard_answer = False
                    st.rerun()
                    
            with btn_col2:
                btn_label = "🙈 Hide Answer" if st.session_state.show_flashcard_answer else "👁️ Show Answer"
                if st.button(btn_label, type="primary", use_container_width=True):
                    st.session_state.show_flashcard_answer = not st.session_state.show_flashcard_answer
                    st.rerun()
                    
            with btn_col3:
                if st.button("⏭️ Next", use_container_width=True):
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(flashcards)
                    st.session_state.show_flashcard_answer = False
                    st.rerun()
                    
            with btn_col4:
                if st.button("🔄 Reset", use_container_width=True):
                    st.session_state.flashcard_index = 0
                    st.session_state.show_flashcard_answer = False
                    st.rerun()

# ====================================================
# TAB 5: Practice Quiz (MCQs)
# ====================================================
with tab_quiz:
    if st.session_state.revision_data is None:
        st.info("⚠️ Please upload a document and generate revision materials in the 'Upload Document' tab first.")
    else:
        rev_data: RevisionData = st.session_state.revision_data
        mcqs = rev_data.mcqs
        
        if not mcqs:
            st.warning("No practice quiz questions available for this document.")
        else:
            st.markdown("### Multiple Choice Quiz")
            st.write("Answer the 10 questions below to test your understanding.")
            
            # Form for Quiz
            with st.form("mcq_quiz_form"):
                user_selections = {}
                for idx, item in enumerate(mcqs):
                    st.markdown(f'<div class="quiz-question-box">', unsafe_allow_html=True)
                    st.markdown(f'<div class="quiz-question-header">Q{idx+1}. {item.question}</div>', unsafe_allow_html=True)
                    
                    # Standardized options check
                    # Ensure options is a list of strings
                    options = item.options
                    
                    # Store selected answer in form submission
                    # Find default index or fallback to 0
                    default_choice = 0
                    if idx in st.session_state.quiz_answers:
                        try:
                            default_choice = options.index(st.session_state.quiz_answers[idx])
                        except ValueError:
                            default_choice = 0
                            
                    selected_val = st.radio(
                        label=f"Options for Q{idx+1}",
                        options=options,
                        index=default_choice,
                        key=f"mcq_radio_{idx}",
                        label_visibility="collapsed"
                    )
                    user_selections[idx] = selected_val
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                submit_quiz = st.form_submit_button("Submit Answers", type="primary")
                
            # If form is submitted or state is active
            if submit_quiz:
                st.session_state.quiz_answers = user_selections
                st.session_state.quiz_submitted = True
                
            if st.session_state.quiz_submitted:
                # Compute score
                correct_count = 0
                for idx, item in enumerate(mcqs):
                    user_ans = st.session_state.quiz_answers.get(idx)
                    if user_ans == item.answer:
                        correct_count += 1
                        
                # Score summary styling
                st.markdown("---")
                score_percentage = (correct_count / len(mcqs)) * 100
                if score_percentage >= 80:
                    st.success(f"🏆 Excellent work! You scored **{correct_count} / {len(mcqs)}** ({score_percentage:.0f}%)")
                elif score_percentage >= 50:
                    st.info(f"👍 Good effort! You scored **{correct_count} / {len(mcqs)}** ({score_percentage:.0f}%)")
                else:
                    st.warning(f"📚 Keep studying! You scored **{correct_count} / {len(mcqs)}** ({score_percentage:.0f}%)")
                    
                # Rerender answers with green/red feedback and explanations
                st.markdown("### Detailed Quiz Report")
                for idx, item in enumerate(mcqs):
                    user_ans = st.session_state.quiz_answers.get(idx)
                    is_correct = (user_ans == item.answer)
                    
                    st.markdown(f'<div class="quiz-question-box" style="border-left: 4px solid {"#22c55e" if is_correct else "#ef4444"};">', unsafe_allow_html=True)
                    st.markdown(f'<div class="quiz-question-header">Q{idx+1}. {item.question}</div>', unsafe_allow_html=True)
                    
                    st.write(f"**Your Choice:** {user_ans}")
                    if is_correct:
                        st.markdown(f"<span style='color: #22c55e; font-weight: 700;'>✓ Correct Answer</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #ef4444; font-weight: 700;'>✗ Incorrect</span> — The correct answer is: **{item.answer}**", unsafe_allow_html=True)
                        
                    st.markdown(f'<div class="explanation-box">💡 <b>Explanation:</b> {item.explanation}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                # Reset quiz button
                if st.button("🔄 Reset & Try Again"):
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

# ====================================================
# TAB 6: Viva & Interview Questions
# ====================================================
with tab_viva:
    if st.session_state.revision_data is None:
        st.info("⚠️ Please upload a document and generate revision materials in the 'Upload Document' tab first.")
    else:
        rev_data: RevisionData = st.session_state.revision_data
        
        st.markdown("### Oral Viva Practice Questions")
        st.write("Simulate oral exams. Click on a question to reveal the correct academic response.")
        
        if not rev_data.viva_questions:
            st.warning("No viva questions generated.")
        else:
            for idx, item in enumerate(rev_data.viva_questions):
                with st.expander(f"🗣️ Question {idx+1}: {item.question}"):
                    st.write(item.answer)
                    
        st.markdown("---")
        st.markdown("### Technical / Job Interview Questions")
        st.write("Prepare for interviews related to this topic. Click on a question to see suggested points to include in your answer.")
        
        if not rev_data.interview_questions:
            st.warning("No interview questions generated.")
        else:
            for idx, item in enumerate(rev_data.interview_questions):
                with st.expander(f"💼 Interview Question {idx+1}: {item.question}"):
                    st.write(item.answer)
