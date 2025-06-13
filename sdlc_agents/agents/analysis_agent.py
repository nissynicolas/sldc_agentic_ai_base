"""
Analysis Agent for requirements processing.
"""
from typing import Dict, Any
from pathlib import Path
from sdlc_agents.agents.base_agent import BaseSDLCAgent
from sdlc_agents.config.config import config
from sdlc_agents.utils.helpers import save_artifact, load_artifact

class AnalysisAgent(BaseSDLCAgent):
    """Agent responsible for analyzing requirements and generating acceptance criteria."""
    
    def __init__(self):
        """Initialize the Analysis Agent."""
        super().__init__(
            name="AnalysisAgent",
            description="Analyzes requirements and generates acceptance criteria",
            capabilities={
                "analyze_requirements": "Convert raw requirements into structured acceptance criteria",
                "validate_criteria": "Validate generated acceptance criteria for completeness",
                "suggest_improvements": "Suggest improvements to requirements"
            }
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the requirements and generate acceptance criteria.
        
        Args:
            input_data: Dict containing:
                - requirements: Raw requirements text
                
        Returns:
            Dict containing:
                - acceptance_criteria: Generated acceptance criteria
                - metadata: Additional processing metadata
        """
        try:
            requirements = input_data.get("requirements", "")
            if not requirements:
                raise ValueError("No requirements provided")
            
            # Process requirements using LLM to generate acceptance criteria
            acceptance_criteria = await self._generate_acceptance_criteria(requirements)
            
            # Save the generated criteria
            save_artifact(
                acceptance_criteria,
                config.ACCEPTANCE_CRITERIA_PATH
            )
            
            return {
                "success": True,
                "acceptance_criteria": acceptance_criteria,
                "metadata": {
                    "source_requirements": requirements,
                    "criteria_length": len(acceptance_criteria)
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
    
    async def _generate_acceptance_criteria(self, requirements: str) -> str:
        """Generate acceptance criteria from requirements.
        
        Args:
            requirements: Raw requirements text
            
        Returns:
            Structured acceptance criteria
        """
        try:
            # Parse the requirements
            sections = requirements.split("\n\n")
            user_story = sections[0].strip()
            
            # Extract functional and non-functional requirements
            functional_reqs = []
            non_functional_reqs = []
            current_section = None
            
            for section in sections[1:]:
                section = section.strip()
                if "Functional Requirements:" in section:
                    current_section = "functional"
                    continue
                elif "Non-functional Requirements:" in section:
                    current_section = "non-functional"
                    continue
                    
                if current_section == "functional" and section:
                    functional_reqs.append(section)
                elif current_section == "non-functional" and section:
                    non_functional_reqs.append(section)
            
            # Generate acceptance criteria structure
            criteria = f"""# Acceptance Criteria

## User Story
{user_story}

## Functional Acceptance Criteria

### Core Functionality
Given the application requirements
When implementing the core features
Then the system should:
{self._format_requirements(functional_reqs)}

## Non-Functional Acceptance Criteria

### System Requirements
Given the non-functional requirements
When implementing the system
Then it should meet the following criteria:
{self._format_requirements(non_functional_reqs)}

## Validation Methods
1. Unit tests for all core functionality
2. Integration tests for system interactions
3. Performance tests for response times
4. Security testing for data protection
5. Usability testing with target users

## Open Questions and Risks
1. Are there any specific performance benchmarks to meet?
2. What are the expected user load and scalability requirements?
3. Are there any specific security compliance requirements?
4. What are the target platforms and devices?
"""
            return criteria
            
        except Exception as e:
            raise ValueError(f"Failed to generate acceptance criteria: {str(e)}")
    
    def _format_requirements(self, requirements: list) -> str:
        """Format requirements into acceptance criteria format.
        
        Args:
            requirements: List of requirement strings
            
        Returns:
            Formatted requirements string
        """
        formatted = []
        for req in requirements:
            # Clean up the requirement text
            req = req.strip()
            if req.startswith(("1.", "2.", "3.", "4.", "5.")):
                req = req[2:].strip()
            if req:
                formatted.append(f"- {req}")
        
        return "\n".join(formatted) if formatted else "- No specific requirements provided"
    
    async def _validate_criteria_structure(self, criteria: str) -> bool:
        """Validate the structure of generated criteria.
        
        Args:
            criteria: Generated acceptance criteria
            
        Returns:
            True if structure is valid, False otherwise
        """
        required_sections = [
            "# Acceptance Criteria",
            "## User Story",
            "## Functional Acceptance Criteria",
            "## Non-Functional Acceptance Criteria",
            "## Validation Methods"
        ]
        
        required_patterns = [
            "Given",
            "When",
            "Then"
        ]
        
        # Check for required sections
        if not all(section in criteria for section in required_sections):
            return False
            
        # Check for required patterns in functional criteria
        functional_section = criteria.split("## Functional Acceptance Criteria")[1].split("##")[0]
        if not all(pattern in functional_section for pattern in required_patterns):
            return False
            
        return True 