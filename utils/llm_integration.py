from typing import Dict, List, Any
from .query_processor import ArgoQueryProcessor

# Simple mock instead of actual LLM
def init_llm(model_path):
    """Mock LLM initialization"""
    return {"model": "rule-based-argo-processor", "status": "ready"}

def create_llm_chain(llm):
    """Mock LLM chain creation"""
    return llm

def generate_response(question, context, file_list, recent_queries, llm_chain, db_session):
    """Generate response using the rule-based processor"""
    processor = ArgoQueryProcessor(db_session)
    return processor.process_query(question)