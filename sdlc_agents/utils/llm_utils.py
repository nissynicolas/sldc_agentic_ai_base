"""
LLM utilities for agent interactions.
"""
from typing import Dict, Any, Optional
import openai
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from sdlc_agents.config.config import config

async def create_llm_chain(system_prompt: str):
    """Create a LangChain chain with the specified system prompt.
    
    Args:
        system_prompt: The system prompt to use
        
    Returns:
        A LangChain chain
    """
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        streaming=True,
        openai_api_key=config.openai_api_key
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    chain = (
        {"input": RunnablePassthrough()} 
        | prompt 
        | llm 
        | StrOutputParser()
    )
    
    return chain

async def execute_prompt(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Execute a prompt using the LLM.
    
    Args:
        prompt: The prompt to execute
        system_prompt: Optional system prompt to use
        
    Returns:
        The LLM's response
    """
    if not system_prompt:
        system_prompt = """You are an expert requirements analyst. Your task is to:
1. Analyze the given requirements
2. Break them down into clear, testable acceptance criteria
3. Structure the output in a clear, markdown format
4. Ensure all functional and non-functional requirements are covered
5. Include specific validation methods for each criterion"""
    
    chain = await create_llm_chain(system_prompt)
    response = await chain.ainvoke(prompt)
    return response 