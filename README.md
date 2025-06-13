# SDLC Agentic AI Framework

A framework for automating software development lifecycle using AI agents, powered by LangGraph and A2A.

## Project Structure

```
sdlc_agents/
├── agents/             # Agent implementations
│   └── base_agent.py   # Base agent class
├── workflows/          # Workflow implementations
│   └── base_workflow.py # Base workflow class
├── utils/             # Utility functions
│   └── helpers.py     # Helper utilities
├── config/            # Configuration
│   └── config.py      # Configuration settings
└── schemas/           # Data schemas
    └── ...           # Schema definitions

tests/
├── unit/             # Unit tests
└── integration/      # Integration tests
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```env
A2A_PORT=8000
A2A_HOST=localhost
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest tests/
```

## Usage

The framework follows the SDLC workflow defined in `sdlc_agent_workflow_v1_UPDATED.md`, implementing:

1. Requirement Analysis
2. Design
3. Pseudo Code Generation
4. Code Generation

Each stage is handled by specialized agents that communicate using the A2A protocol and are orchestrated by LangGraph workflows.

## License

MIT