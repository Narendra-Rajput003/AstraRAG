import os
import logging
import asyncio
from langchain_core.documents import Document
# from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from langchain_experimental.text_splitters import SemanticChunker   
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from  langchain.vectorstores import Milvus
from langchain.chains import RetrievalQA
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from config.config import (
    EMBEDDING_MODEL, LLM_MODEL , MILVUS_HOST , MILVUS_PORT , COLLECTION_NAME
)
from backend.security import mask_pii,add_security_metadata



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def load_and_chunk_docs(directory:str):
    """
    Load and semantically chunk large documents asynchronously.
    
    Supports complex PDFs (tables/images) via UnstructuredLoader.
    Applies PII masking and security metadata.
    
    Args:
        directory (str): Path to documents.
    
    Returns:
        list[Document]: Masked and chunked documents.
    """

    loader = DirectoryLoader(directory,glob="**/*.pdf",loader_cls=UnstructuredPDFLoader)
    documents = await asyncio.to_thread(loader.load)


    # Semantic chunking for better context preservation
    embedding = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = SemanticChunker(embedding,breakpoint_threshold_type="percentile")
    chunks = text_splitter.split_documents(documents)

    # Apply PII masking and metadata async
    masked_chunks = []
    for chunk in chunks:
        masked_content = await mask_pii(chunk.page_content)
        masked_chunk = add_security_metadata(Document(page_content=masked_content,metadata=chunk.metadata))
        masked_chunks.append(masked_chunk)

    logger.info(f"Chunked and masked {len(masked_chunks) } chunks")
    return masked_chunks


async def create_vector_store(chunks):
    """
    Embed chunks with Gemini and store in Milvus for scalable vector search.
    
    Args:
        chunks (list[Document]): Chunked documents.
    
    Returns:
        Milvus: Vector store instance.
    """

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    try:
        vector_store = await asyncio.to_thread(
            Milvus.from_documents,
            chunks,
            embedding=embeddings,
            connection_args={"host":MILVUS_HOST,"port":MILVUS_PORT},
            collection_name=COLLECTION_NAME
        )
        logger.infor("Vectore store created/updated successfully")
        return vector_store

    except Exception as e:
        logger.error(f"Vectore store creation failed:{e}")
        raise


def setup_retriever(vector_store,llm):
    """
    Set up advanced retriever: Multi-query + reranking.
    
    Args:
        vector_store (Milvus): Vector DB.
        llm (ChatGoogleGenerativeAI): LLM for multi-query.
    
    Returns:
        ContextualCompressionRetriever: Enhanced retriever.
    """

    multi_query_prompt = PromptTemplate(
        input_variables=["question"],
        template="""Generate 3-5 alternative versions of the user question for better retrieval.
        Original: {question}"""
    )

    # Base retriever with RBAC filter
    base_retriever = vectore_store.as_retriever(search_kwargs={"k":10,"filter":{"user_id":"company_user"}})
""

