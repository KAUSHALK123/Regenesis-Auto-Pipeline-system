"""
Configuration module for loading and managing environment variables.

This module uses python-dotenv to safely load sensitive configuration
from environment files and provides a centralized access point.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Load environment variables from .env file
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """Configuration class for managing environment variables."""

    @staticmethod
    def get_groq_api_key() -> str:
        """
        Retrieve the Groq API key from environment variables.

        Returns:
            str: The Groq API key.

        Raises:
            ValueError: If GROQ_API_KEY is not set in the environment.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        return api_key

    @staticmethod
    def get_env_variable(key: str, default: Optional[str] = None) -> str:
        """
        Safely retrieve any environment variable.

        Args:
            key: The environment variable name.
            default: Default value if the variable is not set.

        Returns:
            str: The environment variable value or default.
        """
        return os.getenv(key, default)

    @staticmethod
    def get_chroma_db_path() -> Path:
        """
        Get the ChromaDB path from environment or use default.

        Returns:
            Path: The path to the ChromaDB directory.
        """
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        return Path(db_path)


# Export common configurations
GROQ_API_KEY = Config.get_groq_api_key()
CHROMA_DB_PATH = Config.get_chroma_db_path()


if __name__ == "__main__":
    # Quick test to verify configuration loads correctly
    print(f"[OK] GROQ API Key loaded: {'***' + GROQ_API_KEY[-4:]}")
    print(f"[OK] ChromaDB path: {CHROMA_DB_PATH}")
