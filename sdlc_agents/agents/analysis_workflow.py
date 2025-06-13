"""
Analysis workflow implementation using LangGraph.
"""
from typing import Dict, Any, List, Literal, TypedDict, Annotated, Union
from pathlib import Path
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from sdlc_agents.agents.analysis_agent import AnalysisAgent
from sdlc_agents.agents.output_validation_agent import OutputValidationAgent
from sdlc_agents.agents.human_intervention_agent import HumanInterventionAgent
from sdlc_agents.config.config import config
from sdlc_agents.utils.helpers import save_artifact, load_artifact

class AnalysisState(BaseModel):
    """State for the analysis workflow."""
    requirements: str = Field(default="")
    acceptance_criteria: str = Field(default="")
    validation_status: bool = Field(default=False)
    retry_count: int = Field(default=0)
    error_message: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = Field(default=False)
    current_step: str = Field(default="analyze")  # Track current step

class AnalysisWorkflow:
    """LangGraph-based workflow for requirements analysis."""
    
    def __init__(self):
        """Initialize the analysis workflow."""
        self.analysis_agent = AnalysisAgent()
        self.validation_agent = OutputValidationAgent()
        self.human_intervention_agent = HumanInterventionAgent()
        self.max_retries = 3
        
    def create_workflow(self) -> StateGraph:
        """Create the analysis workflow graph."""
        # Initialize the graph with our custom state
        workflow = StateGraph(AnalysisState)
        
        # Add nodes
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("validate_criteria", self._validate_criteria)
        workflow.add_node("human_intervention", self._handle_human_intervention)
        
        # Add edges with conditions
        workflow.add_conditional_edges(
            "analyze_requirements",
            self._should_validate,
            {
                "validate": "validate_criteria",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "validate_criteria",
            self._should_retry,
            {
                "retry": "analyze_requirements",
                "human_intervention": "human_intervention",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "human_intervention",
            self._should_end,
            {
                "end": END,
                "retry": "analyze_requirements"
            }
        )
        
        # Set entry point
        workflow.set_entry_point("analyze_requirements")
        
        return workflow
    
    def _ensure_state(self, state: Union[Dict[str, Any], AnalysisState]) -> AnalysisState:
        """Ensure state is an AnalysisState object."""
        if isinstance(state, dict):
            return AnalysisState(**state)
        return state
    
    def _ensure_dict(self, state: Union[Dict[str, Any], AnalysisState]) -> Dict[str, Any]:
        """Ensure state is a dictionary."""
        if isinstance(state, dict):
            return state
        return state.model_dump()
    
    async def _analyze_requirements(self, state: Union[Dict[str, Any], AnalysisState]) -> Dict[str, Any]:
        """Process requirements and generate acceptance criteria."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete:
            return self._ensure_dict(state_obj)
            
        try:
            if not state_obj.requirements:
                raise ValueError("No requirements provided")
                
            result = await self.analysis_agent.process({
                "requirements": state_obj.requirements
            })
            
            if result["success"]:
                state_obj.acceptance_criteria = result["acceptance_criteria"]
                state_obj.metadata = result.get("metadata", {})
                state_obj.error_message = ""
                state_obj.validation_status = False
                state_obj.current_step = "validate"
            else:
                error_msg = result.get("error", "Failed to generate acceptance criteria")
                state_obj.error_message = f"Analysis failed: {error_msg}"
                state_obj.validation_status = False
                state_obj.is_complete = True
                state_obj.current_step = "end"
                
        except Exception as e:
            state_obj.error_message = f"Analysis failed: {str(e)}"
            state_obj.validation_status = False
            state_obj.is_complete = True
            state_obj.current_step = "end"
            
        return self._ensure_dict(state_obj)
    
    async def _validate_criteria(self, state: Union[Dict[str, Any], AnalysisState]) -> Dict[str, Any]:
        """Validate the generated acceptance criteria."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete:
            return self._ensure_dict(state_obj)
            
        try:
            if not state_obj.acceptance_criteria:
                raise ValueError("No acceptance criteria to validate")
                
            validation_result = await self.validation_agent.validate({
                "output_type": "acceptance_criteria",
                "output_data": state_obj.acceptance_criteria,
                "original_requirements": state_obj.requirements,
                "retry_count": state_obj.retry_count
            })
            
            # Store validation details in state
            state_obj.validation_status = validation_result["success"]
            state_obj.metadata["validation_details"] = validation_result.get("validation_details", {})
            
            if validation_result["success"]:
                # Save valid criteria
                save_artifact(
                    state_obj.acceptance_criteria,
                    config.ACCEPTANCE_CRITERIA_PATH
                )
                state_obj.is_complete = True
                state_obj.current_step = "end"
            else:
                # Handle validation failure
                if validation_result["needs_human"]:
                    state_obj.current_step = "human_intervention"
                    state_obj.error_message = "Validation failed after maximum retries"
                else:
                    state_obj.current_step = "retry"
                    state_obj.retry_count = validation_result["retry_count"]
                    state_obj.error_message = validation_result.get("reason", "Validation failed")
                    # Clear acceptance criteria for retry
                    state_obj.acceptance_criteria = ""
                
        except Exception as e:
            state_obj.error_message = f"Validation failed: {str(e)}"
            state_obj.validation_status = False
            state_obj.metadata["validation_details"] = {
                "status": "error",
                "message": str(e)
            }
            state_obj.current_step = "retry"
            state_obj.retry_count += 1
            
        return self._ensure_dict(state_obj)
    
    async def _handle_human_intervention(self, state: Union[Dict[str, Any], AnalysisState]) -> Dict[str, Any]:
        """Handle cases requiring human intervention."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete:
            return self._ensure_dict(state_obj)
            
        try:
            result = await self.human_intervention_agent.process({
                "requirements": state_obj.requirements,
                "acceptance_criteria": state_obj.acceptance_criteria,
                "error_message": state_obj.error_message
            })
            
            if result["success"]:
                state_obj.acceptance_criteria = result["acceptance_criteria"]
                state_obj.validation_status = True
                state_obj.error_message = ""
                # Save human-reviewed criteria
                save_artifact(
                    state_obj.acceptance_criteria,
                    config.ACCEPTANCE_CRITERIA_PATH
                )
                state_obj.metadata["validation_details"] = {"status": "human_reviewed"}
                state_obj.is_complete = True
                state_obj.current_step = "end"
            else:
                error_msg = result.get("error", "Human intervention failed")
                state_obj.error_message = f"Human intervention failed: {error_msg}"
                state_obj.validation_status = False
                state_obj.is_complete = True
                state_obj.current_step = "end"
                
        except Exception as e:
            state_obj.error_message = f"Human intervention failed: {str(e)}"
            state_obj.validation_status = False
            state_obj.is_complete = True
            state_obj.current_step = "end"
            
        return self._ensure_dict(state_obj)
    
    def _should_validate(self, state: Union[Dict[str, Any], AnalysisState]) -> Literal["validate", "end"]:
        """Determine if validation should proceed."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete or state_obj.error_message:
            return "end"
            
        if state_obj.current_step == "analyze":
            return "validate"
            
        return "end"
    
    def _should_retry(self, state: Union[Dict[str, Any], AnalysisState]) -> Literal["retry", "human_intervention", "end"]:
        """Determine if retry or human intervention is needed."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete or state_obj.error_message:
            return "end"
            
        if state_obj.validation_status:
            state_obj.is_complete = True
            return "end"
            
        if state_obj.retry_count >= self.max_retries:
            return "human_intervention"
            
        # Reset current step to analyze for retry
        state_obj.current_step = "analyze"
        return "retry"
    
    def _should_end(self, state: Union[Dict[str, Any], AnalysisState]) -> Literal["end", "retry"]:
        """Determine if workflow should end."""
        state_obj = self._ensure_state(state)
        
        if state_obj.is_complete or state_obj.error_message:
            return "end"
            
        if state_obj.validation_status:
            state_obj.is_complete = True
            return "end"
            
        return "retry"
    
    async def run(self, requirements: str) -> Dict[str, Any]:
        """Run the analysis workflow."""
        try:
            # Initialize state
            initial_state = AnalysisState(
                requirements=requirements,
                current_step="analyze"
            )
            
            # Create and compile workflow
            workflow = self.create_workflow()
            app = workflow.compile()
            
            # Run workflow
            final_state = await app.ainvoke(self._ensure_dict(initial_state))
            
            # Convert final state to dict
            result = self._ensure_dict(final_state)
            
            # Add success flag and ensure validation details are included
            result["success"] = not bool(result.get("error_message"))
            if not result["success"] and "validation_details" in result.get("metadata", {}):
                result["error_message"] = result["metadata"]["validation_details"].get("reason", result["error_message"])
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error_message": f"Workflow failed: {str(e)}"
            } 