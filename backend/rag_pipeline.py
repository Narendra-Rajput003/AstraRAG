import os
import logging
import asyncio
import sys
from typing import List, Any

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Try to import optional dependencies
try:
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    Document = Any  # type: ignore
    LANGCHAIN_AVAILABLE = False

try:
    from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    TEXT_SPLITTER_AVAILABLE = True
except ImportError:
    TEXT_SPLITTER_AVAILABLE = False

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GEMINI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    GEMINI_EMBEDDINGS_AVAILABLE = False

try:
    from langchain_community.vectorstores import Milvus
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

try:
    from langchain.chains import RetrievalQA
    from langchain.retrievers.multi_query import MultiQueryRetriever
    from langchain.prompts import PromptTemplate
    from langchain.retrievers import ContextualCompressionRetriever
    from langchain.retrievers.document_compressors import CohereRerank
    FULL_LANGCHAIN_AVAILABLE = True
except ImportError:
    FULL_LANGCHAIN_AVAILABLE = False

from config.config import (
    EMBEDDING_MODEL, MILVUS_HOST , MILVUS_PORT , COLLECTION_NAME
)
from backend.security import mask_pii, add_security_metadata



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def load_and_chunk_docs(directory: str) -> List[Any]:
    """
    Load and semantically chunk large documents asynchronously.

    Supports complex PDFs (tables/images) via UnstructuredLoader.
    Applies PII masking and security metadata.

    Args:
        directory (str): Path to documents.

    Returns:
        list[Document]: Masked and chunked documents.
    """

    if not UNSTRUCTURED_AVAILABLE or not TEXT_SPLITTER_AVAILABLE or not LANGCHAIN_AVAILABLE:
        logger.warning("Document processing dependencies not available, returning empty list")
        return []

    loader = DirectoryLoader(directory, glob="**/*.pdf", loader_cls=UnstructuredPDFLoader)
    documents = await asyncio.to_thread(loader.load)

    # Recursive character chunking for context preservation
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    # Apply PII masking and metadata async
    masked_chunks = []
    for chunk in chunks:
        masked_content = await mask_pii(chunk.page_content)
        masked_chunk = add_security_metadata(Document(page_content=masked_content, metadata=chunk.metadata))
        masked_chunks.append(masked_chunk)

    logger.info(f"Chunked and masked {len(masked_chunks)} chunks")
    return masked_chunks


async def create_vector_store(chunks: List[Any]) -> Any:
    """
    Embed chunks with Gemini and store in Milvus for scalable vector search.

    Args:
        chunks (list[Document]): Chunked documents.

    Returns:
        Milvus: Vector store instance.
    """

    if not GEMINI_EMBEDDINGS_AVAILABLE or not MILVUS_AVAILABLE:
        logger.warning("Vector store dependencies not available, returning None")
        return None

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    try:
        vector_store = await asyncio.to_thread(
            Milvus.from_documents,
            chunks,
            embedding=embeddings,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
            collection_name=COLLECTION_NAME
        )
        logger.info("Vector store created/updated successfully")
        return vector_store

    except Exception as e:
        logger.error(f"Vector store creation failed: {e}")
        raise


def setup_retriever(vector_store: Any, llm: Any, user_id: str) -> Any:
    """
    Set up advanced retriever: Multi-query + reranking.

    Args:
        vector_store (Milvus): Vector DB.
        llm (ChatGoogleGenerativeAI): LLM for multi-query.
        user_id (str): User ID for RBAC filtering.

    Returns:
        ContextualCompressionRetriever: Enhanced retriever.
    """

    if not FULL_LANGCHAIN_AVAILABLE or vector_store is None:
        logger.warning("Retriever dependencies not available, returning None")
        return None

    multi_query_prompt = PromptTemplate(
        input_variables=["question"],
        template="""Generate 3-5 alternative versions of the user question for better retrieval.
        Original: {question}"""
    )
    # Base retriever with RBAC filter
    base_retriever = vector_store.as_retriever(search_kwargs={"k": 10, "filter": {"user_id": user_id}})
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, llm=llm, prompt=multi_query_prompt
    )
    compressor = CohereRerank(cohere_api_key=os.getenv("COHERE_API_KEY"), top_n=5)
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=multi_retriever)
    return compression_retriever


def setup_qa_chain(llm: Any, retriever: Any) -> Any:
    if not FULL_LANGCHAIN_AVAILABLE or retriever is None:
        logger.warning("QA chain dependencies not available, returning None")
        return None

    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""Answer based only on the context. If unsure, say 'I don't know'.
        Context: {context}
        Question: {question}
        Answer:"""
    )
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="refine",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": qa_prompt}
        )
        return qa_chain
    except Exception as e:
        logger.error(f"QA chain error: {e}")
        raise