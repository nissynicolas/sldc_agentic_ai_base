"""
Configuration settings for the SDLC Agents system.
"""
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict

class SDLCConfig(BaseSettings):
    """Base configuration for SDLC Agents."""
    
    # API Keys
    openai_api_key: str
    
    # Base paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    
    # Agent configuration
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 300
    
    # A2A Configuration
    A2A_PORT: int = 8000
    A2A_HOST: str = "localhost"
    
    # Document paths
    REQUIREMENTS_PATH: Path = OUTPUT_DIR / "requirements.txt"
    ACCEPTANCE_CRITERIA_PATH: Path = OUTPUT_DIR / "AcceptanceCriteria.md"
    DESIGN_DOC_PATH: Path = OUTPUT_DIR / "DesignDocument.md"
    DEVELOPER_DOC_PATH: Path = OUTPUT_DIR / "DeveloperDocument.md"
    GENERATED_CODE_PATH: Path = OUTPUT_DIR / "generated_code.txt"
    
    # LangGraph configuration
    GRAPH_STATE_PATH: Path = OUTPUT_DIR / "graph_state"
    
    # Use Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
        
config = SDLCConfig() 