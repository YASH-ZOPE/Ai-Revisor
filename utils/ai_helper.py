"""
AI Helper Utility.
Integrates with Google Gemini API using Pydantic schema validation to extract structured revision content.
Runs the generation calls sequentially with safety delays to satisfy free-tier rate limits (RPM / concurrency).
"""
import os
import time
from typing import List
from pydantic import BaseModel, Field
import google.generativeai as genai

# Define Pydantic Sub-schemas and Main Schema

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

# Separate models for 4 split API calls to manage token budgets safely
class RevisionSummaryData(BaseModel):
    summary: str = Field(description="Concise summary of the document, structured nicely in Markdown format.")
    key_points: List[str] = Field(description="Key bullet points summarizing the main ideas of the document.")
    five_minute_sheet: str = Field(description="A 5-minute revision sheet in Markdown format, summarizing key points and formulas/processes.")
    one_minute_sheet: str = Field(description="A 1-minute last-minute revision sheet in Markdown format, containing ultra-concise summaries/mnemonics.")

class RevisionNotesData(BaseModel):
    revision_notes: str = Field(description="Detailed, comprehensive revision notes in Markdown format covering all sections of the document thoroughly.")

class RevisionDefinitionsData(BaseModel):
    definitions: List[DefinitionItem] = Field(description="Important definitions of key concepts found in the document.")

class RevisionTestData(BaseModel):
    flashcards: List[FlashcardItem] = Field(description="A list of flashcards (Question -> Answer) covering important facts.")
    mcqs: List[MCQItem] = Field(description="Exactly 10 multiple choice questions (MCQs) with options, answer, and explanation.")
    viva_questions: List[QAItem] = Field(description="Possible viva/oral exam questions with detailed answers.")
    interview_questions: List[QAItem] = Field(description="Possible job/technical interview questions with detailed answers.")

# Combined model for Streamlit application compatibility
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


def retry_on_rate_limit(max_retries: int = 5, initial_delay: float = 5.0, backoff_factor: float = 2.0):
    """
    Decorator to retry a function if it encounters a rate limit or quota exceeded error from Gemini.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = (
                        "quota" in error_msg or
                        "429" in error_msg or
                        "resourceexhausted" in error_msg or
                        "resource exhausted" in error_msg or
                        "too many requests" in error_msg
                    )
                    
                    # If it's a rate limit and we have attempts left, wait and retry
                    if is_rate_limit and attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise e
        return wrapper
    return decorator


def get_revision_data(text: str, api_key: str, model_name: str = "gemini-1.5-flash") -> RevisionData:
    """
    Sends document text to Google Gemini API using sequential calls with spacing delays.
    This satisfies free-tier rate limits (RPM / concurrency).
    
    Args:
        text: The extracted document text.
        api_key: Google Gemini API key.
        model_name: Model name to use (default: gemini-1.5-flash).
        
    Returns:
        RevisionData: Combined validated Pydantic object.
        
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

    # ------------------------------------------------
    # Call 1: Summaries and Sheets
    # ------------------------------------------------
    @retry_on_rate_limit(max_retries=5, initial_delay=5.0)
    def fetch_summaries():
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4096,
            }
        )
        prompt = f"""
You are an expert academic tutor. Analyze the following document text and generate summaries and revision sheets.
Generate the response in plain text format EXACTLY matching the structure below.
Use the exact headers [SUMMARY], [KEY_POINTS], [FIVE_MINUTE_SHEET], and [ONE_MINUTE_SHEET] to separate the sections.

[SUMMARY]
Provide a concise summary of the key themes of the document in 2-3 paragraphs.

[KEY_POINTS]
Provide 5-10 key points, one point per line, starting with a bullet (-) character.

[FIVE_MINUTE_SHEET]
Design a 5-minute revision sheet summarizing key processes, formulas, or concepts in Markdown format.

[ONE_MINUTE_SHEET]
Design a 1-minute last-minute revision sheet with mnemonics, equations, or rapid-fire lists for last-minute cramming in Markdown format.

Here is the document text:
---
{text}
---
"""
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response received from Gemini API for summaries.")
        
        text_resp = response.text
        
        # Initialize outputs
        summary_text = ""
        key_points = []
        five_minute_sheet = ""
        one_minute_sheet = ""
        
        # Parser logic using delimiters
        if "[SUMMARY]" in text_resp:
            summary_part = text_resp.split("[SUMMARY]")[1]
            if "[KEY_POINTS]" in summary_part:
                summary_text = summary_part.split("[KEY_POINTS]")[0].strip()
                kp_part = summary_part.split("[KEY_POINTS]")[1]
                if "[FIVE_MINUTE_SHEET]" in kp_part:
                    kp_text = kp_part.split("[FIVE_MINUTE_SHEET]")[0].strip()
                    key_points = [line.strip().lstrip("-* ").strip() for line in kp_text.split("\n") if line.strip().lstrip("-* ").strip()]
                    sheet_part = kp_part.split("[FIVE_MINUTE_SHEET]")[1]
                    if "[ONE_MINUTE_SHEET]" in sheet_part:
                        five_minute_sheet = sheet_part.split("[ONE_MINUTE_SHEET]")[0].strip()
                        one_minute_sheet = sheet_part.split("[ONE_MINUTE_SHEET]")[1].strip()
                    else:
                        five_minute_sheet = sheet_part.strip()
                else:
                    key_points = [line.strip().lstrip("-* ").strip() for line in kp_part.split("\n") if line.strip().lstrip("-* ").strip()]
            else:
                summary_text = summary_part.strip()
                
        # Default fallbacks if parsing got truncated or section tokens were missed
        if not summary_text:
            summary_text = text_resp[:800] + "\n...(truncated)" if len(text_resp) > 800 else text_resp
        if not key_points:
            key_points = ["Key takeaways could not be fully parsed."]
        if not five_minute_sheet:
            five_minute_sheet = "Revision sheet details incomplete."
        if not one_minute_sheet:
            one_minute_sheet = "Cram details incomplete."
            
        return RevisionSummaryData(
            summary=summary_text,
            key_points=key_points,
            five_minute_sheet=five_minute_sheet,
            one_minute_sheet=one_minute_sheet
        )

    # ------------------------------------------------
    # Call 2: Detailed Notes (Standalone)
    # ------------------------------------------------
    @retry_on_rate_limit(max_retries=5, initial_delay=5.0)
    def fetch_notes():
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 8192,
            }
        )
        prompt = f"""
You are an expert academic tutor. Analyze the following document text and generate comprehensive study notes based on it.
Ensure all generated content is highly accurate, educational, and formatted professionally in clean Markdown.

Write highly detailed, comprehensive revision notes covering all sections of the document. Use headings, subheadings, bullet points, bold key terms, tables, and short summary boxes where appropriate to structure the information clearly.

Here is the document text:
---
{text}
---
"""
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response received from Gemini API for notes.")
        return RevisionNotesData(revision_notes=response.text)

    # ------------------------------------------------
    # Call 3: Definitions (Plain Text Mode)
    # ------------------------------------------------
    @retry_on_rate_limit(max_retries=5, initial_delay=5.0)
    def fetch_definitions():
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4096,
            }
        )
        prompt = f"""
You are an expert academic tutor. Extract all key terms and definitions from the document below.
Output ONLY a list of definitions, one per line, in this exact format:
TERM | DEFINITION

Example:
Photosynthesis | The process by which green plants convert sunlight into chemical energy.
Mitosis | A type of cell division resulting in two identical daughter cells.

Here is the document text:
---
{text}
---
"""
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response received from Gemini API for definitions.")
        
        definitions = []
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if "|" in line:
                parts = line.split("|", 1)
                term = parts[0].strip().lstrip("- ").strip()
                defn = parts[1].strip()
                if term and defn:
                    definitions.append(DefinitionItem(term=term, definition=defn))
        
        if not definitions:
            definitions.append(DefinitionItem(term="N/A", definition="No definitions could be extracted from this document."))
        
        return RevisionDefinitionsData(definitions=definitions)

    # ------------------------------------------------
    # Call 4: Practice Material (Plain Text Mode)
    # ------------------------------------------------
    @retry_on_rate_limit(max_retries=5, initial_delay=5.0)
    def fetch_test():
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 8192,
            }
        )
        prompt = f"""
You are an expert academic tutor and exam designer. Generate practice materials from the document below.
Use the EXACT section headers shown below. Follow the format precisely.

[FLASHCARDS]
Q: Question here?
A: Answer here.

Q: Another question?
A: Another answer.

[MCQ]
Q: Question text?
A) Option A
B) Option B
C) Option C
D) Option D
ANSWER: B
EXPLANATION: Why B is correct.

Q: Next question?
A) Option A
B) Option B
C) Option C
D) Option D
ANSWER: A
EXPLANATION: Why A is correct.

[VIVA]
Q: Viva question?
A: Detailed answer.

[INTERVIEW]
Q: Interview question?
A: Detailed answer.

Generate at least 4 flashcards, exactly 10 MCQs, 3 viva questions, and 3 interview questions.

Here is the document text:
---
{text}
---
"""
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response received from Gemini API for practice materials.")
        
        resp_text = response.text
        
        # Parse flashcards
        flashcards = []
        if "[FLASHCARDS]" in resp_text:
            fc_section = resp_text.split("[FLASHCARDS]")[1]
            fc_section = fc_section.split("[MCQ]")[0] if "[MCQ]" in fc_section else fc_section
            fc_blocks = fc_section.strip().split("Q:")
            for block in fc_blocks:
                block = block.strip()
                if not block or "A:" not in block:
                    continue
                q_part = block.split("A:")[0].strip()
                a_part = block.split("A:", 1)[1].strip()
                if q_part and a_part:
                    flashcards.append(FlashcardItem(question=q_part, answer=a_part))
        
        if not flashcards:
            flashcards.append(FlashcardItem(question="No flashcards generated", answer="Try with a longer document."))
        
        # Parse MCQs
        mcqs = []
        if "[MCQ]" in resp_text:
            mcq_section = resp_text.split("[MCQ]")[1]
            mcq_section = mcq_section.split("[VIVA]")[0] if "[VIVA]" in mcq_section else mcq_section
            mcq_blocks = mcq_section.strip().split("Q:")
            for block in mcq_blocks:
                block = block.strip()
                if not block or "ANSWER:" not in block:
                    continue
                try:
                    q_text = block.split("A)")[0].strip()
                    options = []
                    for letter in ["A)", "B)", "C)", "D)"]:
                        next_letters = {"A)": "B)", "B)": "C)", "C)": "D)", "D)": "ANSWER:"}
                        if letter in block:
                            start = block.index(letter) + len(letter)
                            end_marker = next_letters[letter]
                            end = block.index(end_marker) if end_marker in block else len(block)
                            options.append(block[start:end].strip())
                    
                    answer_part = block.split("ANSWER:")[1]
                    answer_letter = answer_part.strip().split("\n")[0].strip()
                    explanation = ""
                    if "EXPLANATION:" in block:
                        explanation = block.split("EXPLANATION:")[1].strip().split("\n")[0].strip()
                    
                    # Map answer letter to full option text
                    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                    answer_idx = letter_map.get(answer_letter.upper(), 0)
                    answer_text = options[answer_idx] if answer_idx < len(options) else answer_letter
                    
                    if q_text and len(options) >= 4:
                        mcqs.append(MCQItem(
                            question=q_text,
                            options=options[:4],
                            answer=answer_text,
                            explanation=explanation or "See the document for details."
                        ))
                except (IndexError, ValueError):
                    continue
        
        if not mcqs:
            mcqs.append(MCQItem(
                question="No MCQs could be generated",
                options=["Option A", "Option B", "Option C", "Option D"],
                answer="Option A",
                explanation="Try with a longer document."
            ))
        
        # Parse viva questions
        viva_questions = []
        if "[VIVA]" in resp_text:
            viva_section = resp_text.split("[VIVA]")[1]
            viva_section = viva_section.split("[INTERVIEW]")[0] if "[INTERVIEW]" in viva_section else viva_section
            viva_blocks = viva_section.strip().split("Q:")
            for block in viva_blocks:
                block = block.strip()
                if not block or "A:" not in block:
                    continue
                q_part = block.split("A:")[0].strip()
                a_part = block.split("A:", 1)[1].strip()
                if q_part and a_part:
                    viva_questions.append(QAItem(question=q_part, answer=a_part))
        
        if not viva_questions:
            viva_questions.append(QAItem(question="No viva questions generated", answer="Try with a longer document."))
        
        # Parse interview questions
        interview_questions = []
        if "[INTERVIEW]" in resp_text:
            int_section = resp_text.split("[INTERVIEW]")[1]
            int_blocks = int_section.strip().split("Q:")
            for block in int_blocks:
                block = block.strip()
                if not block or "A:" not in block:
                    continue
                q_part = block.split("A:")[0].strip()
                a_part = block.split("A:", 1)[1].strip()
                if q_part and a_part:
                    interview_questions.append(QAItem(question=q_part, answer=a_part))
        
        if not interview_questions:
            interview_questions.append(QAItem(question="No interview questions generated", answer="Try with a longer document."))
        
        return RevisionTestData(
            flashcards=flashcards,
            mcqs=mcqs,
            viva_questions=viva_questions,
            interview_questions=interview_questions
        )

    # ------------------------------------------------
    # Sequential Execution (Prevents Concurrency Rate Limits)
    # ------------------------------------------------
    # Resolve summaries
    try:
        sum_data = fetch_summaries()
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            raise ValueError("The provided Gemini API Key is invalid. Please check your credentials.")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
            raise Exception("Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.")
        else:
            raise Exception(f"Failed to generate summaries: {error_msg}")

    # Small delay between calls to satisfy free-tier rate limits
    time.sleep(1.0)

    # Resolve notes
    try:
        notes_data = fetch_notes()
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
            raise Exception("Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.")
        else:
            raise Exception(f"Failed to generate detailed notes: {error_msg}")

    time.sleep(1.0)

    # Resolve definitions
    try:
        def_data = fetch_definitions()
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
            raise Exception("Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.")
        else:
            raise Exception(f"Failed to generate definitions: {error_msg}")

    time.sleep(1.0)

    # Resolve test (flashcards, quiz, viva, interview)
    try:
        test_data = fetch_test()
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
            raise Exception("Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.")
        else:
            raise Exception(f"Failed to generate practice materials: {error_msg}")

    # Combine into unified RevisionData schema
    return RevisionData(
        summary=sum_data.summary,
        revision_notes=notes_data.revision_notes,
        key_points=sum_data.key_points,
        definitions=def_data.definitions,
        flashcards=test_data.flashcards,
        mcqs=test_data.mcqs,
        viva_questions=test_data.viva_questions,
        interview_questions=test_data.interview_questions,
        five_minute_sheet=sum_data.five_minute_sheet,
        one_minute_sheet=sum_data.one_minute_sheet
    )


def get_mock_revision_data() -> RevisionData:
    """
    Generates high-quality mock RevisionData for demonstration and testing purposes.
    """
    return RevisionData(
        summary="### Python Programming Basics\n\nPython is a high-level, interpreted programming language designed with an emphasis on code readability. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented, and functional programming. Python is widely used in web development, data science, machine learning, and automation due to its extensive standard library and active ecosystem.",
        revision_notes="""# Comprehensive Python Study Notes

## 1. Syntax and Variables
Python uses indentation to delimit code blocks instead of curly braces or keywords. Variables in Python are dynamically typed, meaning you don't need to declare their type explicitly.

*   **Indentation**: Standard practice is to use 4 spaces.
*   **Comments**: Use `#` for single-line comments and triple quotes `'''` or `\"\"\"` for docstrings.

## 2. Core Data Structures
Python has four built-in collection data types:

1.  **List**: Ordered, mutable, and allows duplicate elements. Defined using square brackets: `my_list = [1, 2, 3]`.
2.  **Tuple**: Ordered, immutable, and allows duplicate elements. Defined using parentheses: `my_tuple = (1, 2, 3)`.
3.  **Set**: Unordered, mutable, and contains unique elements. Defined using curly braces: `my_set = {1, 2, 3}`.
4.  **Dictionary**: Unordered, mutable collection of key-value pairs. Defined using curly braces with colons: `my_dict = {"name": "Python", "version": 3.12}`.

## 3. Control Flow
Python supports standard conditional statements and loops:
*   `if-elif-else` block for decision making.
*   `for` loops for iterating over sequences (lists, tuples, ranges).
*   `while` loops for executing code as long as a condition is true.

## 4. Object-Oriented Programming (OOP)
Python is a fully object-oriented language. Classes are defined using the `class` keyword. The `__init__` method is the constructor, which initializes new instances of the class.""",
        key_points=[
            "Python is an interpreted, high-level, dynamically typed programming language.",
            "Whitespace indentation is syntactically significant, replacing brackets to define block scopes.",
            "Lists are mutable sequences, while Tuples are immutable versions, protecting data from changes.",
            "Dictionaries store data as key-value pairs, providing fast O(1) lookups for records.",
            "Functions are first-class citizens in Python and are defined using the 'def' keyword."
        ],
        definitions=[
            DefinitionItem(
                term="Dynamically Typed",
                definition="A programming language feature where variable types are checked at runtime rather than compile time. You don't need to specify types (e.g. int, string) when creating variables."
            ),
            DefinitionItem(
                term="Mutability",
                definition="The ability of an object to change its state or contents after creation. Lists and Dictionaries are mutable; Tuples and Strings are immutable."
            ),
            DefinitionItem(
                term="Interpreted Language",
                definition="A language where code is executed line-by-line by an interpreter, rather than compiled into machine code beforehand."
            )
        ],
        flashcards=[
            FlashcardItem(
                question="Which built-in Python data structure is ordered and immutable?",
                answer="Tuple. Once created, its elements cannot be changed, added, or removed."
            ),
            FlashcardItem(
                question="What method is used to add an item to the end of a list?",
                answer="The append() method. For example: my_list.append(new_item)."
            ),
            FlashcardItem(
                question="What is the difference between '/' and '//' division operators?",
                answer="'/' performs float division (e.g., 5/2 = 2.5), while '//' performs floor/integer division (e.g., 5//2 = 2)."
            ),
            FlashcardItem(
                question="What keyword is used to return a generator from a function instead of a standard return?",
                answer="The yield keyword. It pauses the function execution and returns a value to the caller, resuming where it left off."
            )
        ],
        mcqs=[
            MCQItem(
                question="Which of the following is NOT a mutable data type in Python?",
                options=["List", "Dictionary", "Tuple", "Set"],
                answer="Tuple",
                explanation="Tuples are immutable sequences, meaning their contents cannot be changed after they are created. Lists, Dictionaries, and Sets are mutable."
            ),
            MCQItem(
                question="What is the output of len({'a': 1, 'b': 2, 'b': 3}) in Python?",
                options=["2", "3", "4", "Error"],
                answer="2",
                explanation="Dictionary keys must be unique. The duplicate key 'b' overrides the previous value, resulting in a dictionary with keys {'a', 'b'}, which has a length of 2."
            ),
            MCQItem(
                question="Which keyword is used to define a function block in Python?",
                options=["function", "def", "func", "define"],
                answer="def",
                explanation="The 'def' keyword is the standard keyword used to define functions in Python."
            ),
            MCQItem(
                question="What is the correct syntax to output 'Hello World' in Python?",
                options=["print('Hello World')", "echo('Hello World')", "console.log('Hello World')", "printf('Hello World')"],
                answer="print('Hello World')",
                explanation="Python uses the built-in print() function to output text to the console."
            ),
            MCQItem(
                question="How do you start a comments section in a Python script?",
                options=["//", "/*", "#", "--"],
                answer="#",
                explanation="The hash symbol (#) is used to indicate comments in Python scripts."
            ),
            MCQItem(
                question="Which method removes and returns the last element of a Python list?",
                options=["remove()", "pop()", "discard()", "delete()"],
                answer="pop()",
                explanation="The pop() method removes the element at the specified index (defaults to the last item) and returns it."
            ),
            MCQItem(
                question="What is the output of 3 * 'Go' in Python?",
                options=["GoGoGo", "9", "Go 3", "Error"],
                answer="GoGoGo",
                explanation="Multiplying a string by an integer in Python repeats the string that many times."
            ),
            MCQItem(
                question="What is the standard indentation recommended by PEP 8?",
                options=["2 spaces", "4 spaces", "8 spaces", "1 tab"],
                answer="4 spaces",
                explanation="PEP 8 specifies using 4 spaces per indentation level for block styling."
            ),
            MCQItem(
                question="Which operator is used for exponentiation (raising to a power) in Python?",
                options=["^", "**", "//", "pow"],
                answer="**",
                explanation="The double asterisk (**) operator is used for raising numbers to a power in Python (e.g. 2**3 = 8)."
            ),
            MCQItem(
                question="What does the append() method do to a list?",
                options=["Adds item at start", "Adds item at end", "Sorts the list", "Clears the list"],
                answer="Adds item at end",
                explanation="The append() method adds a single element to the very end of an existing list."
            )
        ],
        viva_questions=[
            QAItem(
                question="What is the difference between a List and a Tuple in Python?",
                answer="The primary difference is mutability. Lists are mutable (can be changed, items added/removed) and defined using square brackets []. Tuples are immutable (cannot be changed once created) and defined using parentheses ()."
            ),
            QAItem(
                question="Explain the concept of PEP 8.",
                answer="PEP 8 stands for Python Enhancement Proposal 8. It is the official style guide for writing Python code, providing rules and guidelines for naming conventions, code layout, formatting, and indentation to ensure readability."
            ),
            QAItem(
                question="What is the difference between local and global variables?",
                answer="Local variables are defined inside a function scope and are only accessible inside that function. Global variables are defined outside any function block (in the module scope) and can be accessed anywhere in the module."
            )
        ],
        interview_questions=[
            QAItem(
                question="How is memory managed in Python?",
                answer="Python manages memory dynamically using a private heap space. All objects and data structures reside in this private heap. The programmer does not have direct access to it. Memory allocation is managed automatically by the Python Memory Manager, and unused memory is reclaimed automatically by the built-in Garbage Collector using reference counting."
            ),
            QAItem(
                question="What are Python decorators and how do they work?",
                answer="Decorators are a powerful feature in Python that allow you to modify or extend the behavior of a function or class without permanently changing its source code. They take a function as an argument, wrap it with extra functionality in an inner function, and return the wrapper function. They are typically written using the '@decorator_name' syntax above the target function."
            )
        ],
        five_minute_sheet="### ⏱️ Python 5-Minute Syntax Quick Sheet\n\n*   **Variable Assignment**: `x = 5`, `y = \"Hello\"` (no type declaration needed).\n*   **Functions**:\n    ```python\n    def greet(name):\n        return f\"Hello, {name}!\"\n    ```\n*   **List Comprehensions**: `squares = [x**2 for x in range(10)]` (highly readable short-loop list generation).\n*   **Dictionary Operations**:\n    ```python\n    my_dict = {\"key\": \"value\"}\n    value = my_dict.get(\"key\", \"default\")\n    ```\n*   **Class Definition**:\n    ```python\n    class Person:\n        def __init__(self, name):\n            self.name = name\n    ```",
        one_minute_sheet="### ⚡ Python 1-Minute Cheat Sheet\n\n*   **Indent**: 4 Spaces (Critical for scope)\n*   **Lists**: `[1, 2, 3]` (Mutable)\n*   **Tuples**: `(1, 2, 3)` (Immutable)\n*   **Dicts**: `{'key': 'value'}` (Key-Value)\n*   **Print**: `print(value)`\n*   **Types**: `str()`, `int()`, `float()`, `bool()`"
    )

