import logging
import bcrypt
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from langchain.schema import Document 
import asyncio


# setup logging for security events
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# PPI Anonymization Engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

async def mask_pii(text:str)->str:
    """
    Anonymize Personally Identifiable Information (PII) in text.
    
    Uses Presidio to detect and replace PII (e.g., names, emails) with placeholders.
    Async for scalability in batch processing.
    
    Args:
        text (str): Input text to mask.
    
    Returns:
        str: Masked text.
    """

    try:
        analyzed_results = analyzer.analyze(text=text,language='en')
        anonymized_text = anonymizer.anonymize(text=text,analyzed_results=analyzed_results)
        return anonymized_text.text
    except Exception as e:
        logger.error(f"PII masking failed : {e}")
        return text


def add_security_metadata(chunk:Document,user_id:str="company_user") -> Document:
    """
    Add security metadata to document chunks for RBAC filtering.
    
    Tags chunks with user_id/role for metadata-based retrieval filters in Milvus.
    
    Args:
        chunk (Document): LangChain Document object.
        user_id (str): Identifier for access control.
    
    Returns:
        Document: Updated chunk with metadata.
    """

    chunk.metadata['user_id']=user_id
    return chunk

def hash_password(password:str) -> bytes:
    """Hash a password for secure storage using bcrypt."""
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt())

def check_password(password:str,hashed:bytes) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(),hashed)
    
