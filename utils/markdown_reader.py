"""
Markdown and TXT Reader Utility.
Extracts clean text from Markdown (.md) and plain text (.txt) files.
"""
from typing import BinaryIO

def extract_text_from_markdown(file_obj: BinaryIO) -> str:
    """
    Extracts text from a Markdown or TXT file object.
    
    Args:
        file_obj: A binary file-like object (e.g., BytesIO from Streamlit file uploader).
        
    Returns:
        str: Extracted and cleaned text.
        
    Raises:
        ValueError: If the file is empty or decoding fails.
    """
    try:
        # Reset stream position just in case
        file_obj.seek(0)
        content_bytes = file_obj.read()
        
        if not content_bytes:
            raise ValueError("The file is empty.")
            
        # Try decoding with UTF-8, fallback to Latin-1
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1")
            except Exception as decode_err:
                raise ValueError(f"Decoding failed. Please ensure file is UTF-8 or Latin-1 encoded: {str(decode_err)}")
            
        text = text.strip()
        if not text:
            raise ValueError("The file contains no text content.")
            
        return text
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Error reading file: {str(e)}")
