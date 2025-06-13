"""
Base agent class for SDLC agents.
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

class AgentCapability(BaseModel):
    """Model for agent capabilities."""
    name: str
    description: str

class BaseSDLCAgent(ABC):
    """Base class for all SDLC agents."""
    
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: Dict[str, str],
        retry_count: int = 0
    ):
        """Initialize the base agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's role
            capabilities: Dict of capability name to description
            retry_count: Number of retries attempted
        """
        self.name = name
        self.description = description
        self.capabilities = {
            name: AgentCapability(name=name, description=desc)
            for name, desc in capabilities.items()
        }
        self.retry_count = retry_count
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Dict containing processing results
        """
        pass
    
    @abstractmethod
    async def validate(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data.
        
        Args:
            output_data: Output data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def handle_failure(self, error: Exception) -> Dict[str, Any]:
        """Handle processing failures.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Dict containing error handling results
        """
        self.retry_count += 1
        return {
            "success": False,
            "error": str(error),
            "retry_count": self.retry_count
        } 