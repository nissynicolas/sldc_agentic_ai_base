"""
Unit tests for the analysis workflow.
"""
import pytest
import asyncio
from pathlib import Path
from sdlc_agents.agents.analysis_workflow import AnalysisWorkflow, AnalysisState
from sdlc_agents.config.config import config

@pytest.fixture
def workflow():
    """Create a workflow instance for testing."""
    return AnalysisWorkflow()

@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return """
    As a user, I want to be able to log in to the system
    So that I can access my personal dashboard
    
    Acceptance Criteria:
    1. User should be able to enter email and password
    2. System should validate credentials
    3. On successful login, redirect to dashboard
    4. On failed login, show error message
    """

@pytest.mark.asyncio
async def test_workflow_initialization(workflow):
    """Test workflow initialization."""
    assert workflow.max_retries == 3
    assert workflow.analysis_agent is not None
    assert workflow.validation_agent is not None
    assert workflow.human_intervention_agent is not None

@pytest.mark.asyncio
async def test_workflow_successful_analysis(workflow, sample_requirements):
    """Test successful analysis workflow."""
    result = await workflow.run(sample_requirements)
    
    assert isinstance(result, dict)
    assert "success" in result
    assert "acceptance_criteria" in result
    assert "metadata" in result
    assert "error_message" in result
    
    if result["success"]:
        assert result["acceptance_criteria"]
        assert "validation_details" in result["metadata"]
        assert result["error_message"] == ""

@pytest.mark.asyncio
async def test_workflow_state_management(workflow, sample_requirements):
    """Test state management during workflow execution."""
    initial_state = AnalysisState(requirements=sample_requirements)
    
    # Test analyze_requirements node
    state_after_analysis = await workflow._analyze_requirements(initial_state)
    assert state_after_analysis["acceptance_criteria"]
    assert state_after_analysis["retry_count"] == 0
    
    # Test validate_criteria node
    state_after_validation = await workflow._validate_criteria(state_after_analysis)
    assert isinstance(state_after_validation["validation_status"], bool)
    assert "validation_details" in state_after_validation["metadata"]

@pytest.mark.asyncio
async def test_workflow_retry_logic(workflow):
    """Test workflow retry logic."""
    # Create a state that will fail validation
    state = AnalysisState(
        requirements="Invalid requirements",
        acceptance_criteria="Invalid criteria",
        validation_status=False,
        retry_count=0
    )
    
    # Test retry decision
    next_step = workflow._should_retry(state)
    assert next_step == "retry"
    assert state.retry_count == 1
    
    # Test max retries
    state.retry_count = workflow.max_retries
    next_step = workflow._should_retry(state)
    assert next_step == "human_intervention"

@pytest.mark.asyncio
async def test_workflow_error_handling(workflow):
    """Test workflow error handling."""
    # Test with empty requirements
    result = await workflow.run("")
    assert not result["success"]
    assert result["error_message"]
    
    # Test with invalid requirements
    result = await workflow.run("Invalid requirements")
    assert isinstance(result, dict)
    assert "error_message" in result

@pytest.mark.asyncio
async def test_workflow_artifact_saving(workflow, sample_requirements, tmp_path):
    """Test workflow artifact saving."""
    # Override config path for testing
    original_path = config.ACCEPTANCE_CRITERIA_PATH
    config.ACCEPTANCE_CRITERIA_PATH = tmp_path / "test_acceptance_criteria.md"
    
    try:
        result = await workflow.run(sample_requirements)
        
        if result["success"]:
            assert config.ACCEPTANCE_CRITERIA_PATH.exists()
            content = config.ACCEPTANCE_CRITERIA_PATH.read_text()
            assert content == result["acceptance_criteria"]
    finally:
        # Restore original path
        config.ACCEPTANCE_CRITERIA_PATH = original_path

@pytest.mark.asyncio
async def test_workflow_complete_analysis(workflow):
    """Test complete workflow analysis with detailed requirements."""
    # Define a detailed requirement
    detailed_requirements = """
    As a user, I want to be able to manage my profile settings
    So that I can keep my information up to date and control my privacy preferences
    
    Functional Requirements:
    1. Profile Information Management
       - Update personal details (name, email, phone)
       - Change password
       - Upload profile picture
       - Set timezone and language preferences
    
    2. Privacy Settings
       - Control visibility of profile information
       - Manage notification preferences
       - Set data sharing preferences
    
    3. Security Features
       - Two-factor authentication
       - Session management
       - Login history
    
    Non-functional Requirements:
    1. Performance
       - Profile updates should complete within 2 seconds
       - Image upload size limit: 5MB
       - Support for common image formats (JPG, PNG, GIF)
    
    2. Security
       - All profile updates require authentication
       - Password changes require current password verification
       - Session timeout after 30 minutes of inactivity
    
    3. Usability
       - Intuitive interface for all settings
       - Clear error messages
       - Mobile-responsive design
    """
    
    # Run the workflow
    result = await workflow.run(detailed_requirements)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "success" in result
    assert "acceptance_criteria" in result
    assert "metadata" in result
    assert "error_message" in result
    
    # If successful, verify the acceptance criteria
    if result["success"]:
        # Check that acceptance criteria contains key sections
        criteria = result["acceptance_criteria"]
        assert "Profile Information Management" in criteria
        assert "Privacy Settings" in criteria
        assert "Security Features" in criteria
        
        # Verify metadata contains validation details
        assert "validation_details" in result["metadata"]
        validation = result["metadata"]["validation_details"]
        assert isinstance(validation, dict)
        
        # Verify no error message when successful
        assert result["error_message"] == ""
        
        # Verify the criteria follows the template structure
        assert "Given" in criteria
        assert "When" in criteria
        assert "Then" in criteria
        
        # Verify specific requirements are covered
        assert "password" in criteria.lower()
        assert "profile picture" in criteria.lower()
        assert "privacy" in criteria.lower()
        assert "security" in criteria.lower()
        
        # Verify non-functional requirements are addressed
        assert "performance" in criteria.lower()
        assert "usability" in criteria.lower()
    else:
        # If not successful, verify error handling
        assert result["error_message"]
        assert not result["acceptance_criteria"] 