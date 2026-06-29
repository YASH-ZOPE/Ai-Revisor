"""
PDF Reader Utility.
Extracts clean text from PDF documents using pypdf.
"""
from typing import BinaryIO
import pypdf

def extract_text_from_pdf(file_obj: BinaryIO) -> str:
    """
    Extracts text from a PDF file object.
    
    Args:
        file_obj: A binary file-like object (e.g., BytesIO from Streamlit file uploader).
        
    Returns:
        str: Extracted and cleaned text.
        
    Raises:
        ValueError: If the file is empty or text extraction yields no content.
    """
    try:
        # Reset stream position just in case
        file_obj.seek(0)
        reader = pypdf.PdfReader(file_obj)
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ValueError("The PDF file contains no pages.")
            
        extracted_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text.append(text)
                
        full_text = "\n\n".join(extracted_text).strip()
        if not full_text:
            raise ValueError(
                "Could not extract any text from the PDF. "
                "The PDF might be empty, password-protected, or contain scanned images without OCR."
            )
            
        return full_text
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Error reading PDF file: {str(e)}")
