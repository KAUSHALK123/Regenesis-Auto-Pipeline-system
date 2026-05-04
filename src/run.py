#!/usr/bin/env python
"""
Entry point for the Regenesis Auto Pipeline System.

This is the main script to run the RAG agent with LangGraph, ChromaDB, and Groq LLM.

Usage:
    uv run python src/run.py
    or from project root:
    python -m src.run
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import logger, Config


def main():
    """Main entry point for the application."""
    logger.info("Starting Regenesis Auto Pipeline System...")

    try:
        # Verify configuration loads correctly
        api_key = Config.get_groq_api_key()
        logger.info("[OK] Configuration loaded successfully")
        logger.info(f"[OK] Using Groq API Key: {'***' + api_key[-4:]}")

        # Verify ChromaDB path
        db_path = Config.get_chroma_db_path()
        logger.info(f"[OK] ChromaDB path: {db_path}")

        logger.info("[OK] Environment setup complete")
        logger.info("Ready to initialize RAG components...")

        # TODO: Initialize LangGraph, ChromaDB, and other components here

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    logger.info("Application running successfully")
    return 0


if __name__ == "__main__":
    exit(main())
