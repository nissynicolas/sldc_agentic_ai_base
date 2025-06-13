"""
Helper utilities for SDLC agents.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
import yaml
from sdlc_agents.config.config import config

def ensure_output_dir() -> None:
    """Ensure the output directory exists."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.GRAPH_STATE_PATH.mkdir(parents=True, exist_ok=True)

def save_artifact(content: str, path: Path) -> None:
    """Save content to a file.
    
    Args:
        content: Content to save
        path: Path to save the content to
    """
    ensure_output_dir()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def load_artifact(path: Path) -> Optional[str]:
    """Load content from a file.
    
    Args:
        path: Path to load content from
        
    Returns:
        File contents if file exists, None otherwise
    """
    if path.exists():
        return path.read_text()
    return None

def save_state(state: Dict[str, Any], name: str) -> None:
    """Save workflow state.
    
    Args:
        state: State to save
        name: Name of the state file
    """
    ensure_output_dir()
    state_path = config.GRAPH_STATE_PATH / f"{name}.json"
    with state_path.open('w') as f:
        json.dump(state, f)

def load_state(name: str) -> Optional[Dict[str, Any]]:
    """Load workflow state.
    
    Args:
        name: Name of the state file
        
    Returns:
        State dict if file exists, None otherwise
    """
    state_path = config.GRAPH_STATE_PATH / f"{name}.json"
    if state_path.exists():
        with state_path.open('r') as f:
            return json.load(f)
    return None 