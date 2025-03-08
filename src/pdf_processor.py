"""
PDF Processor Module

This module handles the extraction of text from PDF files.
"""
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Class for extracting text content from PDF files."""
    
    def __init__(self):
        """Initialize the PDF processor."""
        pass
    
    def extract_text(self, pdf_path):
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        logger.info(f"Extracting text from {pdf_path}")
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            # Process each page
            for i, page in enumerate(reader.pages):
                logger.debug(f"Processing page {i+1}/{len(reader.pages)}")
                page_text = page.extract_text()
                
                if page_text:
                    text += page_text + "\n\n"
                    
            logger.info(f"Successfully extracted {len(reader.pages)} pages from {pdf_path}")
            
            if not text.strip():
                logger.warning(f"No text content extracted from {pdf_path}")
                
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
