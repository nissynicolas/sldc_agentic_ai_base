"""
Human Intervention Agent.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from sdlc_agents.agents.base_agent import BaseSDLCAgent
from sdlc_agents.config.config import config
from sdlc_agents.utils.helpers import save_artifact

class HumanInterventionAgent(BaseSDLCAgent):
    """Agent responsible for managing human intervention in the workflow."""
    
    def __init__(self):
        """Initialize the Human Intervention Agent."""
        super().__init__(
            name="HumanInterventionAgent",
            description="Manages human intervention in the workflow",
            capabilities={
                "request_review": "Request human review of failed outputs",
                "collect_feedback": "Collect and process human feedback",
                "resume_workflow": "Resume workflow after human intervention"
            }
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the human intervention request.
        
        Args:
            input_data: Dict containing:
                - stage: Workflow stage that failed
                - output_type: Type of output that failed
                - output_data: Failed output data
                - error_context: Context about the failure
                
        Returns:
            Dict containing:
                - success: Whether human intervention was successful
                - updated_output: Updated output after human review
                - metadata: Additional intervention metadata
        """
        try:
            stage = input_data.get("stage")
            output_type = input_data.get("output_type")
            output_data = input_data.get("output_data")
            error_context = input_data.get("error_context")
            
            if not all([stage, output_type, output_data]):
                raise ValueError("Missing required intervention inputs")
            
            # Create human review request
            review_request = await self._create_review_request(
                stage,
                output_type,
                output_data,
                error_context
            )
            
            # TODO: Implement actual human interaction
            # This is a placeholder that will be replaced with actual human interaction
            human_feedback = await self._simulate_human_feedback(review_request)
            
            # Process and save human feedback
            if human_feedback.get("approved"):
                updated_output = human_feedback.get("updated_output", output_data)
                
                # Save the updated output
                output_path = self._get_output_path(output_type)
                if output_path:
                    save_artifact(updated_output, output_path)
                
                return {
                    "success": True,
                    "updated_output": updated_output,
                    "metadata": {
                        "stage": stage,
                        "output_type": output_type,
                        "human_approved": True,
                        "changes_made": human_feedback.get("changes_made", False)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Human rejected the output",
                    "metadata": {
                        "stage": stage,
                        "output_type": output_type,
                        "human_approved": False,
                        "feedback": human_feedback.get("feedback", "")
                    }
                }
            
        except Exception as e:
            return await self.handle_failure(e)
    
    async def validate(self, output_data: Dict[str, Any]) -> bool:
        """Validate the human intervention results.
        
        Args:
            output_data: Dict containing intervention results
            
        Returns:
            True if valid, False otherwise
        """
        try:
            return all(
                key in output_data
                for key in ["success", "metadata"]
            )
        except Exception:
            return False
    
    async def _create_review_request(
        self,
        stage: str,
        output_type: str,
        output_data: Any,
        error_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a human review request.
        
        Args:
            stage: Workflow stage
            output_type: Type of output
            output_data: Output data to review
            error_context: Optional error context
            
        Returns:
            Formatted review request
        """
        return f"""
# Human Review Request

## Stage: {stage}
## Output Type: {output_type}

### Error Context
{error_context or "No error context provided"}

### Output to Review
{output_data}

### Actions Required
1. Review the output above
2. Make necessary corrections
3. Approve or reject the changes

Please provide your feedback below:
"""
    
    async def _simulate_human_feedback(self, review_request: str) -> Dict[str, Any]:
        """Simulate human feedback (placeholder).
        
        Args:
            review_request: The review request
            
        Returns:
            Simulated human feedback
        """
        # TODO: Replace with actual human interaction
        return {
            "approved": True,
            "updated_output": review_request,
            "changes_made": False,
            "feedback": "Output looks good"
        }
    
    def _get_output_path(self, output_type: str) -> Optional[Path]:
        """Get the output path for a given output type.
        
        Args:
            output_type: Type of output
            
        Returns:
            Path to save output, or None if unknown type
        """
        output_paths = {
            "acceptance_criteria": config.ACCEPTANCE_CRITERIA_PATH,
            "design_document": config.DESIGN_DOC_PATH,
            "developer_document": config.DEVELOPER_DOC_PATH,
            "generated_code": config.GENERATED_CODE_PATH
        }
        return output_paths.get(output_type) 