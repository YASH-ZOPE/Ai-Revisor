"""
AI Helper Utility.
Integrates with Google Gemini API using Pydantic schema validation to extract structured revision content.
"""
import os
from typing import List, Optional
from pydantic import BaseModel, Field
import google.generativeai as genai

# Define Pydantic Schema for Structured Output

class FlashcardItem(BaseModel):
    question: str = Field(description="A revision question for the front of the flashcard.")
    answer: str = Field(description="The concise, clear answer for the back of the flashcard.")

class MCQItem(BaseModel):
    question: str = Field(description="The multiple-choice question text.")
    options: List[str] = Field(description="List of exactly 4 choices.")
    answer: str = Field(description="The exact correct answer option, which must match one of the choices in the options list.")
    explanation: str = Field(description="Short explanation of why this choice is correct.")

class QAItem(BaseModel):
    question: str = Field(description="The question.")
    answer: str = Field(description="The detailed correct answer.")

class DefinitionItem(BaseModel):
    term: str = Field(description="The key term or concept.")
    definition: str = Field(description="The definition or explanation of the term.")

class RevisionData(BaseModel):
    summary: str = Field(description="Concise summary of the document, structured nicely in Markdown format.")
    revision_notes: str = Field(description="Detailed revision notes in Markdown format, covering all key topics thoroughly.")
    key_points: List[str] = Field(description="Key bullet points summarizing the main ideas of the document.")
    definitions: List[DefinitionItem] = Field(description="Important definitions of key concepts found in the document.")
    flashcards: List[FlashcardItem] = Field(description="A list of flashcards (Question -> Answer) covering important facts.")
    mcqs: List[MCQItem] = Field(description="Exactly 10 multiple choice questions (MCQs) with options, answer, and explanation.")
    viva_questions: List[QAItem] = Field(description="Possible viva/oral exam questions with detailed answers.")
    interview_questions: List[QAItem] = Field(description="Possible job/technical interview questions with detailed answers.")
    five_minute_sheet: str = Field(description="A 5-minute revision sheet in Markdown format, summarizing key points and formulas/processes.")
    one_minute_sheet: str = Field(description="A 1-minute last-minute revision sheet in Markdown format, containing ultra-concise summaries/mnemonics.")

def get_revision_data(text: str, api_key: str, model_name: str = "gemini-1.5-flash") -> RevisionData:
    """
    Sends document text to Google Gemini API and returns validated RevisionData.
    
    Args:
        text: The extracted document text.
        api_key: Google Gemini API key.
        model_name: Model name to use (default: gemini-1.5-flash).
        
    Returns:
        RevisionData: Validated Pydantic object containing all revision components.
        
    Raises:
        ValueError: For API key issues, parsing issues, or empty inputs.
        Exception: General Gemini API calling exceptions.
    """
    if not text.strip():
        raise ValueError("Provided document text is empty.")
    if not api_key.strip():
        raise ValueError("Gemini API Key is not set.")

    # Configure Gemini SDK
    genai.configure(api_key=api_key)
    
    # Initialize the model with structured output configurations
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": RevisionData,
            "temperature": 0.2, # Lower temperature for analytical and revision consistency
        }
    )
    
    # Prompt detailing what we want
    prompt = f"""
You are an expert academic tutor and study assistant.
Analyze the following document text and generate comprehensive study and revision materials based on it.
Ensure all generated content is highly accurate, educational, and formatted professionally.
Use Markdown inside text fields where appropriate for headings, lists, bold text, tables, or code formatting.

Specific guidelines:
1. 'summary': Write a concise summary of the key themes of the document in 2-3 paragraphs.
2. 'revision_notes': Write highly detailed, comprehensive revision notes covering all sections of the document.
3. 'key_points': Write 5-10 key points summarizing core takeaways.
4. 'definitions': Extract all important definitions or terms.
5. 'flashcards': Create 8-12 flashcards mapping critical concepts (question -> answer).
6. 'mcqs': Create EXACTLY 10 multiple choice questions. Make sure the 'answer' field matches one of the options EXACTLY.
7. 'viva_questions': Create 5-8 potential viva/oral exam questions with answers.
8. 'interview_questions': Create 5-8 job/technical interview questions with answers.
9. 'five_minute_sheet': Design a 5-minute revision sheet summarizing key processes, formulas, or concepts.
10. 'one_minute_sheet': Design a 1-minute revision sheet with mnemonics, equations, or rapid-fire lists for last-minute cramming.

Here is the document text:
---
{text}
---
"""
    
    try:
        response = model.generate_content(prompt)
        
        # Verify response text is present
        if not response.text:
            raise ValueError("Empty response received from Gemini API.")
            
        # Parse output using Pydantic V2 model validation
        validated_data = RevisionData.model_validate_json(response.text)
        return validated_data
        
    except Exception as e:
        # Catch JSON validation, API, and connection errors and re-raise with clear messages
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            raise ValueError("The provided Gemini API Key is invalid. Please check your credentials.")
        elif "quota" in error_msg.lower():
            raise Exception("Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.")
        elif "validation" in error_msg.lower() or "parsing" in error_msg.lower():
            raise ValueError(f"Failed to parse the Gemini AI response into the required structure: {error_msg}")
        else:
            raise Exception(f"Failed to generate revision material: {error_msg}")
