import logging
import bcrypt  # pyright: ignore[reportMissingImports]
import base64

# setup logging for security events
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# PII Anonymization Engines - optional
try:
    from presidio_analyzer import AnalyzerEngine  # pyright: ignore[reportMissingImports]
    from presidio_anonymizer import AnonymizerEngine  # pyright: ignore[reportMissingImports]
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    PRESIDIO_AVAILABLE = True
except ImportError:
    logger.warning("Presidio not available, PII anonymization disabled")
    analyzer = None
    anonymizer = None
    PRESIDIO_AVAILABLE = False

try:
    from langchain.schema import Document  # pyright: ignore[reportMissingImports]
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available")
    LANGCHAIN_AVAILABLE = False

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

    if not PRESIDIO_AVAILABLE:
        logger.warning("PII masking not available - Presidio not installed")
        return text

    try:
        analyzed_results = analyzer.analyze(text=text,language='en')
        anonymized_text = anonymizer.anonymize(text=text,analyzed_results=analyzed_results)
        return anonymized_text.text
    except Exception as e:
        logger.error(f"PII masking failed : {e}")
        return text


def add_security_metadata(chunk, user_id:str="company_user"):
    """
    Add security metadata to document chunks for RBAC filtering.

    Tags chunks with user_id/role for metadata-based retrieval filters in Milvus.

    Args:
        chunk: Document object (LangChain Document if available).
        user_id (str): Identifier for access control.

    Returns:
        Updated chunk with metadata.
    """

    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain not available, cannot add security metadata")
        return chunk

    chunk.metadata['user_id']=user_id
    return chunk

def hash_password(password: str) -> str:
    """Hash a password for secure storage using bcrypt with cost factor 12."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    return base64.b64encode(hashed).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        hashed_bytes = base64.b64decode(hashed.encode('utf-8'))
        return bcrypt.checkpw(password.encode(), hashed_bytes)
    except Exception:
        return False


def validate_password_policy(password: str) -> bool:
    """Validate password meets security requirements: min 12 chars, mix of upper/lower/numbers/symbols."""
    if len(password) < 12:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    return has_upper and has_lower and has_digit and has_symbol
    
