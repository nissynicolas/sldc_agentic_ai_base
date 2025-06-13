"""
Streamlit UI for testing SDLC agents.
"""
import asyncio
import streamlit as st
from pathlib import Path
from datetime import datetime
import html
import time
from sdlc_agents.agents.analysis_workflow import AnalysisWorkflow
from sdlc_agents.agents.output_validation_agent import OutputValidationAgent
from sdlc_agents.agents.human_intervention_agent import HumanInterventionAgent
from sdlc_agents.config.config import config
from sdlc_agents.utils.helpers import ensure_output_dir

# Initialize session state
if 'analysis_workflow' not in st.session_state:
    st.session_state.analysis_workflow = AnalysisWorkflow()
if 'validation_agent' not in st.session_state:
    st.session_state.validation_agent = OutputValidationAgent()
if 'human_agent' not in st.session_state:
    st.session_state.human_agent = HumanInterventionAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'agent_logs' not in st.session_state:
    st.session_state.agent_logs = []
if 'current_log_text' not in st.session_state:
    st.session_state.current_log_text = ""
if 'requirements_input' not in st.session_state:
    st.session_state.requirements_input = ""
if 'log_placeholder' not in st.session_state:
    st.session_state.log_placeholder = None
if 'typing_index' not in st.session_state:
    st.session_state.typing_index = 0
if 'current_typing_log' not in st.session_state:
    st.session_state.current_typing_log = None

def on_requirements_change():
    """Callback when requirements text changes."""
    st.session_state.requirements_input = st.session_state.requirements_area

def format_log_entry(log, show_cursor=False):
    """Format a single log entry with proper HTML escaping."""
    timestamp = html.escape(log['timestamp'])
    agent = html.escape(log['agent'])
    action = html.escape(log['action'])
    details = html.escape(log.get('details', '')) if log.get('details') else ''
    
    if log.get('is_processing'):
        details = f"{details} [Processing...]"
    
    return f'''<div class="log-entry">
        <span class="timestamp">[{timestamp}]</span> 
        <span class="agent">{agent}</span> » 
        <span class="action">{action}</span>
        <div class="details">{details}</div>
    </div>'''

def update_logs():
    """Update the log display."""
    if not st.session_state.log_placeholder:
        return
        
    log_entries = []
    for log in st.session_state.agent_logs:
        log_entries.append(format_log_entry(log))
        
    log_content = '\n'.join(log_entries)
    
    st.session_state.log_placeholder.markdown(
        f'<div class="terminal"><pre>{log_content}</pre></div>',
        unsafe_allow_html=True
    )

def add_log(agent: str, action: str, details: str = None, is_processing=False):
    """Add a log entry with timestamp and update display."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    new_log = {
        "timestamp": timestamp,
        "agent": agent,
        "action": action,
        "details": details,
        "is_processing": is_processing
    }
    st.session_state.agent_logs.append(new_log)
    update_logs()

def add_message(agent: str, message: str, status: str = "info", details: dict = None):
    """Add a message to the conversation history."""
    st.session_state.messages.append({
        "agent": agent,
        "message": message,
        "status": status,
        "details": details
    })

def display_messages():
    """Display all messages in the conversation history."""
    for msg in st.session_state.messages:
        with st.container():
            # Agent name and message
            col1, col2 = st.columns([2, 8])
            with col1:
                st.markdown(f"**{msg['agent']}**")
            with col2:
                if msg['status'] == 'success':
                    st.success(msg['message'])
                elif msg['status'] == 'warning':
                    st.warning(msg['message'])
                elif msg['status'] == 'error':
                    st.error(msg['message'])
                else:
                    st.info(msg['message'])
            
            # Display generated MD file if available
            if msg.get('details') and 'raw_output' in msg['details']:
                with st.expander("📄 View Generated Acceptance Criteria Document"):
                    st.markdown(msg['details']['raw_output'])
            
            # Display validation details if available
            if msg.get('details') and 'validation_details' in msg['details']:
                with st.expander("🔍 View Validation Analysis"):
                    vd = msg['details']['validation_details']
                    if 'failures' in vd:
                        for failure in vd['failures']:
                            st.error(failure)
                    if 'sections' in vd:
                        for section_name, section in vd['sections'].items():
                            if section.get('found'):
                                st.success(f"✅ Found '{section_name}' section")
                                if section.get('line_number'):
                                    st.text(f"    Line {section['line_number']}")
                            else:
                                st.error(f"❌ Missing '{section_name}' section")

async def process_requirements(requirements: str) -> None:
    """Process requirements through the analysis workflow."""
    try:
        # Clear previous messages and logs
        st.session_state.messages = []
        st.session_state.agent_logs = []
        
        # Show immediate processing message
        add_message(
            "System",
            "🔄 Processing your requirements...",
            "info"
        )
        
        # Analysis Phase
        add_log(
            "System",
            "Starting new analysis session",
            "A new analysis session has started. Preparing to analyze your requirements in detail."
        )
        await asyncio.sleep(0.5)
        
        add_log(
            "Analysis Workflow",
            "Initializing",
            "The Analysis Workflow is loading language models and tools to understand your requirements."
        )
        await asyncio.sleep(1)
        
        add_log(
            "Analysis Workflow",
            "Processing requirements",
            f"The workflow is now carefully reading your requirements and extracting key information.\n\nPreview: {requirements[:100]}...\n\nLooking for user stories, acceptance criteria, technical constraints, and business rules.",
            is_processing=True
        )
        
        # Run the workflow
        workflow = AnalysisWorkflow()
        result = await workflow.run(requirements)
        
        # Update the processing log to remove loading animation
        st.session_state.agent_logs[-1]["is_processing"] = False
        
        if result.get("error_message"):
            add_log(
                "Analysis Workflow",
                "Analysis failed",
                f"The Analysis Workflow could not process your requirements. Reason: {result['error_message']}. Please review your input and try again."
            )
            add_message(
                "Analysis Workflow",
                f"Analysis failed: {result['error_message']}",
                "error"
            )
            return
            
        # Show validation phase
        add_log(
            "Validation Agent",
            "Starting validation",
            "Starting validation of acceptance criteria against template requirements:\n\n" +
            "1. Checking for required sections:\n" +
            "   - Acceptance Criteria heading\n" +
            "   - User Story section\n" +
            "   - Functional Criteria\n" +
            "   - Non-Functional Criteria\n" +
            "   - Validation Methods\n" +
            "   - Open Questions\n\n" +
            "2. Verifying content quality:\n" +
            "   - Completeness of each section\n" +
            "   - Clarity and specificity\n" +
            "   - Traceability to requirements\n" +
            "   - Testability of criteria",
            is_processing=True
        )
        
        # Get validation details from result
        validation_details = result.get("metadata", {}).get("validation_details", {})
        
        if result.get("success"):
            add_log(
                "Validation Agent",
                "Validation successful",
                "✅ All validation checks passed:\n\n" +
                "1. Required sections are present and complete\n" +
                "2. Content meets quality standards\n" +
                "3. Criteria are clear and testable\n" +
                "4. All sections are properly formatted"
            )
            add_message(
                "Analysis Workflow",
                "✅ Analysis completed successfully!",
                "success",
                {
                    "raw_output": result.get("acceptance_criteria", ""),
                    "validation_details": validation_details
                }
            )
        else:
            # Show validation failures
            failures = validation_details.get("failures", [])
            if failures:
                failure_details = "\n".join([f"- {f}" for f in failures])
                add_log(
                    "Validation Agent",
                    "Validation failed",
                    f"❌ Found validation issues:\n\n{failure_details}\n\n" +
                    "Please ensure all required sections are present and properly formatted."
                )
            else:
                add_log(
                    "Validation Agent",
                    "Validation failed",
                    "❌ The acceptance criteria does not meet template requirements.\n\n" +
                    "Please check that all required sections are present and properly formatted."
                )
                
            # Show retry or human intervention status
            if result.get("needs_human"):
                add_log(
                    "Human Intervention",
                    "Required",
                    "⚠️ Maximum retries reached. Human intervention is needed to:\n\n" +
                    "1. Review the current acceptance criteria\n" +
                    "2. Identify missing or incorrect sections\n" +
                    "3. Provide guidance for improvement"
                )
                add_message(
                    "Analysis Workflow",
                    "⚠️ Human intervention required",
                    "warning",
                    {
                        "raw_output": result.get("acceptance_criteria", ""),
                        "validation_details": validation_details
                    }
                )
            else:
                add_log(
                    "Validation Agent",
                    "Retrying",
                    f"🔄 Attempt {result.get('retry_count', 1)} of 3\n\n" +
                    "The system will attempt to improve the acceptance criteria based on validation feedback."
                )
                add_message(
                    "Analysis Workflow",
                    "🔄 Retrying analysis",
                    "warning",
                    {
                        "raw_output": result.get("acceptance_criteria", ""),
                        "validation_details": validation_details
                    }
                )
        
        # Final status
        add_log(
            "System",
            "Workflow complete",
            "The analysis workflow has finished processing."
        )
        
    except Exception as e:
        add_log(
            "System",
            "Error",
            f"An unexpected error occurred: {str(e)}"
        )
        add_message(
            "System",
            f"Error: {str(e)}",
            "error"
        )
    finally:
        st.session_state.processing = False

def main():
    """Main Streamlit UI."""
    st.set_page_config(layout="wide")
    
    # Modernized CSS for look and feel only (no logic/layout changes)
    st.markdown("""
        <style>
        html, body, .stApp {
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #f6f8fa;
        }
        .block-container {
            padding-top: 2.5rem;
            max-width: 100%;
        }
        /* Card-style for main input area */
        .modern-card {
            background: #fff;
            box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
            border-radius: 16px;
            padding: 2rem 2rem 1.5rem 2rem;
            margin-bottom: 2rem;
        }
        /* Modern terminal styling */
        div[data-testid="stMarkdownContainer"] > div.terminal {
            background: #181c24;
            border-radius: 16px;
            box-shadow: 0 2px 16px 0 rgba(0,0,0,0.10);
            padding: 24px 20px 20px 20px;
            font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
            min-height: 500px;
            max-height: 500px;
            height: 500px;
            color: #00e676;
            margin-bottom: 10px;
            position: relative;
            border: 1.5px solid #23272f;
            overflow-y: auto;
        }
        div.terminal pre {
            margin: 0;
            white-space: pre-wrap;
            min-height: 100%;
        }
        div.terminal .log-entry {
            margin: 10px 0;
            animation: fadeIn 0.3s ease-in forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        div.terminal .timestamp { color: #b2b2b2; font-size: 0.95em; }
        div.terminal .agent { color: #00bcd4; font-weight: 600; }
        div.terminal .action { color: #00e676; font-weight: 500; }
        div.terminal .details {
            color: #e0e0e0;
            margin: 8px 0 8px 24px;
            padding-left: 14px;
            border-left: 2px solid #333a;
            font-size: 1.05em;
        }
        div.terminal .cursor {
            display: inline-block;
            width: 8px;
            height: 15px;
            background: #00e676;
            margin-left: 5px;
            animation: blink 1s infinite;
            vertical-align: middle;
        }
        div.terminal .loading::after {
            content: "";
            display: inline-block;
            animation: ellipsis 2s infinite;
            color: #00e676;
        }
        div.terminal .processing {
            display: flex;
            align-items: center;
            color: #00e676;
            margin-top: 10px;
            font-style: italic;
        }
        div.terminal .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            margin-right: 10px;
            border: 2px solid #00e676;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        /* Modern text area */
        .stTextArea textarea {
            background: #f8fafc;
            color: #23272f;
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            padding: 16px;
            font-size: 1.08em;
            border: 1.5px solid #d1d5db;
            border-radius: 12px;
            min-height: 180px;
            box-shadow: 0 2px 8px 0 rgba(0,0,0,0.03);
            margin-bottom: 0.5rem;
        }
        /* Modern button */
        .stButton button {
            width: 100%;
            background: #27ae60 !important;
            color: #fff !important;
            border: none;
            border-radius: 8px;
            padding: 0.75em 0;
            font-size: 1.08em;
            font-weight: 700;
            margin-top: 10px;
            cursor: pointer;
            box-shadow: 0 1px 4px 0 rgba(39, 174, 96, 0.07);
            transition: background 0.2s, box-shadow 0.2s;
        }
        .stButton button:hover {
            background: #219150 !important;
            color: #fff !important;
            box-shadow: 0 2px 8px 0 rgba(39, 174, 96, 0.13);
        }
        /* Section headers */
        .modern-header {
            font-size: 1.6em;
            font-weight: 700;
            color: #23272f;
            margin-bottom: 0.7em;
            letter-spacing: 0.01em;
            display: flex;
            align-items: center;
            gap: 0.5em;
        }
        .modern-header .icon {
            font-size: 1.2em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Modern section headers (markup only)
    st.markdown('<div class="modern-header"><span class="icon">🧠</span> SDLC Analysis Agent</div>', unsafe_allow_html=True)
    st.write("<span style='font-size:1.1em;color:#555;'>Enter your requirements below to generate and validate acceptance criteria.</span>", unsafe_allow_html=True)

    # Create a two-column layout with custom widths
    col1, col2 = st.columns([3, 2])

    with col1:
        ensure_output_dir()
        requirements = st.text_area(
            "Requirements",
            value=st.session_state.requirements_input,
            height=200,
            placeholder="e.g. As a user, I want to reset my password so that I can regain access if I forget it...",
            key="requirements_area",
            on_change=on_requirements_change
        )
        if st.button("Analyze Requirements", disabled=st.session_state.processing):
            if not st.session_state.requirements_area:
                st.error("Please enter requirements first!")
                return
            st.session_state.processing = True
            st.info("🔄 Starting analysis... You'll see updates below as they happen.")
            asyncio.run(process_requirements(st.session_state.requirements_area))
            st.session_state.processing = False
        display_messages()

    with col2:
        st.markdown('<div class="modern-header"><span class="icon">🖥️</span> Agent Activity Log</div>', unsafe_allow_html=True)
        if not st.session_state.log_placeholder:
            st.session_state.log_placeholder = st.empty()
        if st.session_state.agent_logs:
            update_logs()
        else:
            st.session_state.log_placeholder.markdown(
                '<div class="terminal"><pre>System ready. Waiting for input...</pre></div>',
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main() 