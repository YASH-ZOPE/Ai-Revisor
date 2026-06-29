# 🎓 AI Revision Assistant

A complete, premium AI-powered Revision Assistant built with Python and Streamlit. It uses the Google Gemini API to analyze study materials (PDF, DOCX, TXT, MD) and dynamically generates summaries, detailed study notes, interactive flashcards, practice quizzes, and viva/interview preparation tools.

---

## 🌟 Features

- **Multi-Format File Upload**: Parses PDFs (`pypdf`), Microsoft Word documents (`python-docx`), and plain text/Markdown files in-memory.
- **Single-Call AI Synthesis**: Uses structured Pydantic response schemas with the Gemini API to retrieve all revision material (MCQs, flashcards, summaries) in a single API call.
- **Premium Dark-Theme UI**: Styled with glassmorphic cards, Outfit/Plus Jakarta Sans typography, and subtle glowing border states.
- **5-Minute & 1-Minute Cram Sheets**: Tailored rapid review pages for quick learning.
- **Interactive Flashcards**: Flip between questions and answers, and navigate through cards with tracking indicators.
- **Practice Quiz (10 MCQs)**: Fully interactive quiz with immediate score calculations, custom color feedback (Green/Red checkmarks), and expert explanations.
- **Viva & Interview Prep**: Interactive accordion expanders to quiz yourself on oral defense and technical questions.

---

## 📂 Project Structure

```text
ai-revision-assistant/
│
├── app.py                  # Main Streamlit web application
├── requirements.txt        # Python dependency manifest
├── .env.example            # Environment variables example configuration
├── utils/
│   ├── pdf_reader.py       # Extract text from PDFs using pypdf
│   ├── docx_reader.py      # Extract text from DOCX files using python-docx
│   ├── markdown_reader.py  # Extract text from Markdown and plain text
│   └── ai_helper.py        # Gemini API integration and response schemas
├── uploads/                # Directory for uploaded resources (created dynamically)
├── assets/                 # Image and style assets (created dynamically)
└── README.md               # User guide and setup instructions
```

---

## 🛠️ Installation & Setup

### 1. Navigate to the Directory
Ensure you are in the project folder:
```bash
cd Ai-Revisior
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Google Gemini API Key
Create a `.env` file based on `.env.example` under the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Alternatively, you can input your Gemini API Key directly in the web app's sidebar during execution.)*

---

## 🚀 Running the Web Application

Launch the Streamlit server locally:
```bash
streamlit run app.py
```

This will run the application and print the local URL (usually `http://localhost:8501`). Open this address in your web browser to start revising.

---

## 🔒 Security & Performance Features

- **In-Memory Parsing**: Files are parsed in memory using standard Python streams to avoid local file persistence leakage.
- **Error Boundaries**: Provides clear visual indicators for corrupted files, missing API keys, rate limits, or empty inputs.
- **Pydantic Data Guard**: Guaranteed JSON validation for AI responses, shielding the quiz and flashcard sections from rendering errors.
