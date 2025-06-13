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
                - retry_count: Number of retry attempts (optional)
        """
        try:
            output_type = input_data.get("output_type")
            output_data = input_data.get("output_data")
            original_requirements = input_data.get("original_requirements", "")
            retry_count = input_data.get("retry_count", 0)
            
            if not output_type or not output_data:
                raise ValueError("Missing required validation inputs")
            
            # Perform validation
            validation_result, validation_details = await self._validate_output(
                output_type,
                output_data,
                original_requirements
            )
            
            # Determine if we need retry or human intervention
            needs_retry = not validation_result and retry_count < 3
            needs_human = not validation_result and retry_count >= 3
            
            return {
                "success": validation_result,
                "needs_retry": needs_retry,
                "needs_human": needs_human,
                "retry_count": retry_count + 1 if needs_retry else retry_count,
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
                    "line_number": None,
                    "required": True
                },
                "user_story": {
                    "found": False,
                    "content": "",
                    "line_number": None,
                    "required": True
                },
                "functional_criteria": {
                    "found": False,
                    "content": [],
                    "line_number": None,
                    "required": True
                },
                "non_functional_criteria": {
                    "found": False,
                    "content": [],
                    "line_number": None,
                    "required": True
                },
                "validation_methods": {
                    "found": False,
                    "content": "",
                    "line_number": None,
                    "required": True
                },
                "open_questions": {
                    "found": False,
                    "content": "",
                    "line_number": None,
                    "required": True
                }
            },
            "reason": "",
            "failures": []
        }

        # Check each section
        lines = criteria.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check Acceptance Criteria heading
            if re.search(r'^#\s*acceptance criteria', line.lower()):
                validation_details["sections"]["acceptance_criteria_heading"]["found"] = True
                validation_details["sections"]["acceptance_criteria_heading"]["line_number"] = i + 1
                validation_details["sections"]["acceptance_criteria_heading"]["content"] = line
                current_section = "acceptance_criteria_heading"

            # Check User Story section
            elif re.search(r'^##\s*user story', line.lower()):
                validation_details["sections"]["user_story"]["found"] = True
                validation_details["sections"]["user_story"]["line_number"] = i + 1
                current_section = "user_story"
                # Get the story content
                story_lines = []
                j = i + 1
                while j < len(lines) and not re.search(r'^##\s*', lines[j]):
                    if lines[j].strip():
                        story_lines.append(lines[j].strip())
                    j += 1
                validation_details["sections"]["user_story"]["content"] = "\n".join(story_lines)

            # Check Functional Criteria section
            elif re.search(r'^##\s*functional acceptance criteria', line.lower()):
                validation_details["sections"]["functional_criteria"]["found"] = True
                validation_details["sections"]["functional_criteria"]["line_number"] = i + 1
                current_section = "functional_criteria"
                # Get the criteria content
                criteria_lines = []
                j = i + 1
                while j < len(lines) and not re.search(r'^##\s*', lines[j]):
                    if lines[j].strip():
                        criteria_lines.append(lines[j].strip())
                    j += 1
                validation_details["sections"]["functional_criteria"]["content"] = criteria_lines

            # Check Non-Functional Criteria section
            elif re.search(r'^##\s*non-functional acceptance criteria', line.lower()):
                validation_details["sections"]["non_functional_criteria"]["found"] = True
                validation_details["sections"]["non_functional_criteria"]["line_number"] = i + 1
                current_section = "non_functional_criteria"
                # Get the criteria content
                criteria_lines = []
                j = i + 1
                while j < len(lines) and not re.search(r'^##\s*', lines[j]):
                    if lines[j].strip():
                        criteria_lines.append(lines[j].strip())
                    j += 1
                validation_details["sections"]["non_functional_criteria"]["content"] = criteria_lines

            # Check Validation Methods section
            elif re.search(r'^##\s*validation methods', line.lower()):
                validation_details["sections"]["validation_methods"]["found"] = True
                validation_details["sections"]["validation_methods"]["line_number"] = i + 1
                current_section = "validation_methods"
                # Get the methods content
                method_lines = []
                j = i + 1
                while j < len(lines) and not re.search(r'^##\s*', lines[j]):
                    if lines[j].strip():
                        method_lines.append(lines[j].strip())
                    j += 1
                validation_details["sections"]["validation_methods"]["content"] = "\n".join(method_lines)

            # Check Open Questions section
            elif re.search(r'^##\s*open questions', line.lower()):
                validation_details["sections"]["open_questions"]["found"] = True
                validation_details["sections"]["open_questions"]["line_number"] = i + 1
                current_section = "open_questions"
                # Get the questions content
                question_lines = []
                j = i + 1
                while j < len(lines) and not re.search(r'^##\s*', lines[j]):
                    if lines[j].strip():
                        question_lines.append(lines[j].strip())
                    j += 1
                validation_details["sections"]["open_questions"]["content"] = "\n".join(question_lines)

        # Collect failures with detailed information
        for section_name, section_data in validation_details["sections"].items():
            if section_data["required"] and not section_data["found"]:
                validation_details["failures"].append({
                    "section": section_name,
                    "reason": f"Missing required section: {section_name}",
                    "expected_format": f"## {section_name.replace('_', ' ').title()}"
                })
            elif section_data["found"] and not section_data["content"]:
                validation_details["failures"].append({
                    "section": section_name,
                    "reason": f"Section {section_name} is empty",
                    "line_number": section_data["line_number"]
                })

        # Set overall validation result and reason
        is_valid = len(validation_details["failures"]) == 0
        if not is_valid:
            failure_reasons = [f["reason"] for f in validation_details["failures"]]
            validation_details["reason"] = "Validation failed:\n" + "\n".join(f"- {reason}" for reason in failure_reasons)
        else:
            validation_details["reason"] = "Validation successful"

        return is_valid, validation_details 