from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, name: str, role: str, model_provider: str = "groq"):
        self.name = name
        self.role = role
        self.llm = self._initialize_llm(model_provider)
        self.memory: List[Dict] = []
        
    def _initialize_llm(self, provider: str):
        """Initialize the language model"""
        if provider == "groq":
            return ChatGroq(
                groq_api_key=os.getenv('GROQ_API_KEY'),
                model_name="llama3-8b-8192",
                temperature=0.1,
                max_tokens=1500,
            )
        # agar paid api hai to use krlo :)
        elif provider == "openai":
            return ChatOpenAI(
                model_name="o4-mini",
                api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.1
            )
        
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task specific to this agent"""
        pass
        
    def add_to_memory(self, interaction: Dict):
        """Add interaction to agent memory"""
        self.memory.append(interaction)