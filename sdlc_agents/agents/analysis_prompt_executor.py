"""
Analysis Prompt Executor Agent.
"""
from typing import Dict, Any
from pathlib import Path
from sdlc_agents.agents.base_agent import BaseSDLCAgent
from sdlc_agents.config.config import config
from sdlc_agents.utils.helpers import save_artifact, load_artifact
from sdlc_agents.utils.llm_utils import execute_prompt

class AnalysisPromptExecutor(BaseSDLCAgent):
    """Agent responsible for executing analysis prompts and generating acceptance criteria."""
    
    def __init__(self):
        """Initialize the Analysis Prompt Executor."""
        super().__init__(
            name="AnalysisPromptExecutor",
            description="Executes analysis prompt template for requirements",
            capabilities={
                "execute_prompt": "Execute analysis prompt with requirements",
                "generate_criteria": "Generate acceptance criteria from requirements",
                "save_output": "Save generated criteria to file"
            }
        )
        self.template_path = Path("Role Prompts/1. Analyst.md")
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process requirements using the analysis prompt template.
        
        Args:
            input_data: Dict containing:
                - requirements: Requirements text or Jira story
                
        Returns:
            Dict containing:
                - success: Whether processing was successful
                - acceptance_criteria: Generated acceptance criteria
                - metadata: Additional processing metadata
        """
        try:
            # Get requirements from input
            requirements = input_data.get("requirements", "")
            if not requirements:
                raise ValueError("No requirements provided")
            
            # Load prompt template
            template = await self._load_prompt_template()
            if not template:
                raise ValueError("Could not load analysis prompt template")
            
            # Replace placeholder in template
            filled_prompt = template.replace("_[Paste the main requirement here]_", requirements)
            
            # Execute prompt using LLM
            acceptance_criteria = await self._execute_prompt(filled_prompt)
            
            # Save output
            save_artifact(
                acceptance_criteria,
                config.ACCEPTANCE_CRITERIA_PATH
            )
            
            return {
                "success": True,
                "acceptance_criteria": acceptance_criteria,
                "metadata": {
                    "source_requirements": requirements,
                    "template_used": str(self.template_path),
                    "output_path": str(config.ACCEPTANCE_CRITERIA_PATH)
                }
            }
            
        except Exception as e:
            return await self.handle_failure(e)
    
    async def validate(self, output_data: Dict[str, Any]) -> bool:
        """Validate the generated acceptance criteria.
        
        Args:
            output_data: Dict containing the generated acceptance criteria
            
        Returns:
            True if valid, False otherwise
        """
        try:
            criteria = output_data.get("acceptance_criteria", "")
            if not criteria:
                return False
            
            # Validate criteria structure and completeness
            validation_result = await self._validate_criteria_structure(criteria)
            return validation_result
            
        except Exception:
            return False
    
    async def _load_prompt_template(self) -> str:
        """Load the analysis prompt template.
        
        Returns:
            Template content as string
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        return self.template_path.read_text()
    
    async def _execute_prompt(self, prompt: str) -> str:
        """Execute the filled prompt using LLM.
        
        Args:
            prompt: Filled prompt template
            
        Returns:
            Generated acceptance criteria
        """
        return await execute_prompt(prompt)
    
    async def _validate_criteria_structure(self, criteria: str) -> bool:
        """Validate the structure of generated criteria.
        
        Args:
            criteria: Generated acceptance criteria
            
        Returns:
            True if structure is valid, False otherwise
        """
        required_sections = [
            "# Acceptance Criteria",
            "## Requirements Overview",
            "## Functional Criteria",
            "## Non-Functional Criteria",
            "## Validation Methods"
        ]
        
        return all(section in criteria for section in required_sections) 