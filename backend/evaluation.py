# src/backend/evaluation.py
# RAG evaluation with Ragas.

import os
import logging
import asyncio
from ragas import evaluate  # pyright: ignore[reportMissingImports]
from ragas.metrics import faithfulness, answer_relevancy, context_precision, answer_correctness  # pyright: ignore[reportMissingImports]
from datasets import Dataset  # pyright: ignore[reportMissingImports]
import pandas as pd  # pyright: ignore[reportMissingImports]
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings  # pyright: ignore[reportMissingImports]
from config.config import EMBEDDING_MODEL, LLM_MODEL, TEST_DATA_PATH, NUM_EVAL_SAMPLES

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def evaluate_rag(qa_chain):
    try:
        llm_evaluator = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0)
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
        if os.path.exists(TEST_DATA_PATH):
            test_data = pd.read_csv(TEST_DATA_PATH)
            dataset = Dataset.from_pandas(test_data)
        else:
            questions = ["What is the main topic of the document?"] * NUM_EVAL_SAMPLES
            ground_truths = ["The main topic is RAG implementation."] * NUM_EVAL_SAMPLES
            data = {"question": questions, "ground_truth": ground_truths, "answer": [], "contexts": []}
            for q in questions:
                result = await qa_chain.ainvoke({"query": q})  # Use ainvoke for async
                data["answer"].append(result["result"])
                data["contexts"].append([doc.page_content for doc in result["source_documents"]])
            dataset = Dataset.from_dict(data)
        metrics = [faithfulness, answer_relevancy, context_precision, answer_correctness]
        results = await asyncio.to_thread(  # Run evaluate in thread since it's sync
            evaluate,
            dataset=dataset,
            metrics=metrics,
            llm=llm_evaluator,
            embeddings=embeddings
        )
        logger.info(f"Ragas results: {results}")
        return results
    except Exception as e:
        logger.error(f"Ragas error: {e}")
        raise