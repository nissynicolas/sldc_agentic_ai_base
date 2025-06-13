"""
Output Validation Agent.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import re
from sdlc_agents.agents.base_agent import BaseSDLCAgent
from sdlc_agents.config.config import config

class OutputValidationAgent(BaseSDLCAgent):
    """Agent responsible for validating outputs."""
    
    def __init__(self):
        """Initialize the Output Validation Agent."""
        super().__init__(
            name="OutputValidationAgent",
            description="Validates output against Analyst template requirements",
            capabilities={
                "validate_output": "Validate output matches template requirements",
                "track_retries": "Track retry attempts",
                "trigger_human": "Trigger human intervention when needed"
            }
        )
        
    async def validate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Required abstract method implementation.
        
        Args:
            input_data: Dict containing validation input data
            
        Returns:
            Dict containing validation results
        """
        return await self.process(input_data)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the output data.
        
        Args:
            input_data: Dict containing:
                - output_type: Type of output to validate
                - output_data: Data to validate
                - original_requirements: Original requirements text
        """
        try:
            output_type = input_data.get("output_type")
            output_data = input_data.get("output_data")
            original_requirements = input_data.get("original_requirements", "")
            
            if not output_type or not output_data:
                raise ValueError("Missing required validation inputs")
            
            # Perform validation
            validation_result, validation_details = await self._validate_output(
                output_type,
                output_data,
                original_requirements
            )
            
            return {
                "success": validation_result,
                "needs_retry": False,  # Simplified - no retries
                "needs_human": not validation_result,  # If validation fails, need human review
                "reason": validation_details["reason"],
                "validation_details": validation_details
            }
            
        except Exception as e:
            return await self.handle_failure(e)
    
    async def _validate_output(
        self,
        output_type: str,
        output_data: str,
        original_requirements: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Validate output against template requirements."""
        if output_type == "acceptance_criteria":
            return await self._validate_acceptance_criteria(output_data, original_requirements)
        else:
            return False, {"reason": f"Unknown output type: {output_type}", "details": {}}
    
    async def _validate_acceptance_criteria(self, criteria: str, requirements: str) -> tuple[bool, Dict[str, Any]]:
        """Validate acceptance criteria against template requirements.
        
        Checks:
        1. Has Acceptance Criteria heading
        2. Contains Stakeholders/User Roles
        3. Contains Business Goals
        4. Contains User Stories in proper format
        5. Contains Acceptance Criteria for stories
        6. Contains Open Questions/Risks section
        """
        validation_details = {
            "sections": {
                "acceptance_criteria_heading": {
                    "found": False,
                    "content": "",
                    "line_number": None
                },
                "stakeholders": {
                    "found": False,
                    "content": "",
                    "line_number": None
                },
                "business_goals": {
                    "found": False,
                    "content": "",
                    "line_number": None
                },
                "user_stories": {
                    "found": False,
                    "content": [],
                    "line_number": None,
                    "format_valid": False
                },
                "story_criteria": {
                    "found": False,
                    "content": [],
                    "line_number": None
                },
                "open_questions": {
                    "found": False,
                    "content": "",
                    "line_number": None
                }
            },
            "reason": "",
            "failures": []
        }

        # Check each section
        lines = criteria.split('\n')
        for i, line in enumerate(lines):
            # Check Acceptance Criteria heading
            if re.search(r'acceptance criteria', line.lower()):
                validation_details["sections"]["acceptance_criteria_heading"]["found"] = True
                validation_details["sections"]["acceptance_criteria_heading"]["line_number"] = i + 1

            # Check Stakeholders section
            if re.search(r'^#+.*stakeholder|.*user.*role', line.lower()):
                validation_details["sections"]["stakeholders"]["found"] = True
                validation_details["sections"]["stakeholders"]["line_number"] = i + 1

            # Check Business Goals
            if re.search(r'^#+.*business.*goal|.*value|.*problem', line.lower()):
                validation_details["sections"]["business_goals"]["found"] = True
                validation_details["sections"]["business_goals"]["line_number"] = i + 1

            # Check User Stories
            if re.search(r'^#+.*user.*stor', line.lower()):
                validation_details["sections"]["user_stories"]["found"] = True
                validation_details["sections"]["user_stories"]["line_number"] = i + 1
                # Check for proper user story format
                stories = [l for l in lines[i+1:] if re.search(r'as a.*i want.*so that', l.lower())]
                validation_details["sections"]["user_stories"]["content"] = stories
                validation_details["sections"]["user_stories"]["format_valid"] = len(stories) > 0

            # Check Story Acceptance Criteria
            if re.search(r'^#+.*acceptance.*criteria', line.lower()):
                validation_details["sections"]["story_criteria"]["found"] = True
                validation_details["sections"]["story_criteria"]["line_number"] = i + 1

            # Check Open Questions/Risks
            if re.search(r'^#+.*open.*question|.*risk', line.lower()):
                validation_details["sections"]["open_questions"]["found"] = True
                validation_details["sections"]["open_questions"]["line_number"] = i + 1

        # Collect failures
        if not validation_details["sections"]["acceptance_criteria_heading"]["found"]:
            validation_details["failures"].append("Missing 'Acceptance Criteria' heading")
        
        if not validation_details["sections"]["stakeholders"]["found"]:
            validation_details["failures"].append("Missing 'Stakeholders & User Roles' section")
        
        if not validation_details["sections"]["business_goals"]["found"]:
            validation_details["failures"].append("Missing 'Business Goals' section")
        
        if not validation_details["sections"]["user_stories"]["found"]:
            validation_details["failures"].append("Missing 'User Stories' section")

        
        if not validation_details["sections"]["story_criteria"]["found"]:
            validation_details["failures"].append("Missing 'Acceptance Criteria' for user stories")
        
        if not validation_details["sections"]["open_questions"]["found"]:
            validation_details["failures"].append("Missing 'Open Questions/Risks' section")

        # Set overall validation result
        is_valid = len(validation_details["failures"]) == 0
        validation_details["reason"] = (
            "Validation successful"
            if is_valid
            else "Validation failed:\n" + "\n".join(f"- {failure}" for failure in validation_details["failures"])
        )

        return is_valid, validation_details 