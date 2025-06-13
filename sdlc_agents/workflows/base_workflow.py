"""
Base workflow class for SDLC agent workflows.
"""
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph, Graph
from pydantic import BaseModel

class WorkflowState(BaseModel):
    """Base state model for workflows."""
    
    stage: str
    artifacts: Dict[str, str]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class BaseWorkflow(ABC):
    """Base class for all SDLC workflows."""
    
    def __init__(self, name: str):
        """Initialize the workflow.
        
        Args:
            name: Name of the workflow
        """
        self.name = name
        self.graph = StateGraph(WorkflowState)
        
    @abstractmethod
    def define_nodes(self) -> None:
        """Define the nodes in the workflow graph."""
        pass
    
    @abstractmethod
    def define_edges(self) -> None:
        """Define the edges between nodes in the workflow graph."""
        pass
    
    def add_node(
        self,
        name: str,
        handler: Callable[[WorkflowState], WorkflowState]
    ) -> None:
        """Add a node to the workflow graph.
        
        Args:
            name: Name of the node
            handler: Function to handle the node's processing
        """
        self.graph.add_node(name, handler)
    
    def compile(self) -> Graph:
        """Compile the workflow graph.
        
        Returns:
            Compiled graph ready for execution
        """
        self.define_nodes()
        self.define_edges()
        return self.graph.compile()
    
    @abstractmethod
    async def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the workflow.
        
        Args:
            initial_state: Initial state for the workflow
            
        Returns:
            Final state after workflow completion
        """
        pass 