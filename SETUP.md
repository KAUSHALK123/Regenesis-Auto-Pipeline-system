# Regenesis Auto Pipeline System - Environment Setup Guide

## Overview

This project is a self-healing RAG (Retrieval-Augmented Generation) system built with:
- **LangGraph** - for orchestrating AI workflows
- **ChromaDB** - for vector storage and retrieval
- **Groq LLM** - for fast inference
- **LangChain** - for RAG components and integrations

## Environment Setup Checklist

### 1. Dependencies ✓

All required dependencies are installed via `uv`:

```toml
[project]
dependencies = [
    "chromadb>=1.5.8",
    "langchain-community>=0.4.1",
    "langchain-groq>=1.1.2",
    "langchain-text-splitters>=1.1.2",
    "langgraph>=1.1.10",
    "python-dotenv>=1.2.2",
]
```

To verify installation:
```powershell
Set-Location 'D:\PROJECTS\Regenesis-CICD\Regenesis-Auto-Pipeline-system'
& '.\.venv\Scripts\Activate.ps1'
pip list
```

### 2. Environment Variables (.env)

The `.env` file is created with placeholders:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**To use it:**

1. Get your Groq API key from [Groq Console](https://console.groq.com)
2. Replace `your_groq_api_key_here` in `.env` with your actual key
3. The `python-dotenv` library automatically loads it when `config.py` is imported

**Security Note:**
- `.env` is excluded in `.gitignore` - never commit API keys
- Use `Config.get_groq_api_key()` to safely access it in code

### 3. Configuration (src/utils/config.py)

Provides safe, centralized access to environment variables:

```python
from src.utils import Config, GROQ_API_KEY

# Option 1: Direct import (raises error if not set)
api_key = GROQ_API_KEY

# Option 2: Safe method (with custom handling)
api_key = Config.get_groq_api_key()

# Option 3: Generic method
custom_value = Config.get_env_variable("MY_VAR", default="fallback")

# Get ChromaDB path
db_path = Config.get_chroma_db_path()
```

### 4. Logging (src/utils/logger.py)

Provides production-style logging with console and file output:

```python
from src.utils import logger

logger.info("Starting RAG agent")
logger.error("An error occurred", exc_info=True)
```

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/app.log` (DEBUG level and above)

### 5. .gitignore

Properly configured to exclude:
- `.env` files (never commit secrets)
- `.venv/` and virtual environments
- `__pycache__/` and compiled Python files
- `chroma_db/` (vector database)
- IDE files (`.vscode/`, `.idea/`)
- Logs and temporary files

### 6. Project Entry Point (src/run.py)

Minimal entry point that demonstrates configuration and logging:

```bash
# Run with uv
uv run src/run.py

# Or with Python
python src/run.py
```

This script:
- Loads and verifies configuration
- Tests logger output
- Shows how to access API keys safely
- Ready for RAG component initialization

## Project Structure

```
Regenesis-Auto-Pipeline-system/
├── .env                      # Environment variables (secret, not in git)
├── .gitignore               # Git ignore patterns
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Locked dependencies (for reproducibility)
├── .venv/                   # Virtual environment
├── logs/                    # Application logs
├── src/
│   ├── __init__.py          # Package marker
│   ├── run.py               # Entry point
│   ├── rag_agent.py         # RAG agent implementation
│   ├── ingest.py            # Data ingestion pipeline
│   ├── nodes/               # LangGraph nodes
│   └── utils/
│       ├── __init__.py      # Utils package
│       ├── config.py        # Configuration management
│       └── logger.py        # Logging setup
└── docs/                    # Documentation
```

## Running the Project

### 1. Activate the virtual environment

```powershell
Set-Location 'D:\PROJECTS\Regenesis-CICD\Regenesis-Auto-Pipeline-system'
& '.\.venv\Scripts\Activate.ps1'
```

### 2. Verify setup

```powershell
python src/run.py
```

You should see:
```
2026-05-04 10:30:45 - src.run - INFO - Starting Regenesis Auto Pipeline System...
2026-05-04 10:30:45 - src.run - INFO - ✓ Configuration loaded successfully
...
```

### 3. Run the main RAG agent

```powershell
# Once RAG agent is implemented
python src/rag_agent.py
```

## Next Steps

1. **Set your GROQ_API_KEY** in `.env`
2. **Implement LangGraph nodes** in `src/nodes/`
3. **Build the RAG pipeline** in `src/rag_agent.py`
4. **Add data ingestion** logic to `src/ingest.py`
5. **Test with sample data** using ChromaDB

## Troubleshooting

### `GROQ_API_KEY not set` error
- Check `.env` file exists in project root
- Verify your key is not `your_groq_api_key_here` (placeholder)
- Run from the project root directory

### Import errors with `src.utils`
- Make sure you're in the virtual environment: `& '.\.venv\Scripts\Activate.ps1'`
- Ensure `__init__.py` files exist in `src/` and `src/utils/`

### ChromaDB path issues
- Set `CHROMA_DB_PATH` in `.env` if needed
- Default is `./chroma_db` (created automatically)
- Ensure the directory is not in `.gitignore` permanently (only ignore data files)

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Groq API](https://console.groq.com)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
