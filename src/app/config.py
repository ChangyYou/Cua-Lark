"""
Configuration loader for CUA-Lark.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables."""

    # API Configuration
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")

    # Model Configuration
    model_image: str = os.getenv("MODEL_IMAGE", "qwen3-vl-flash")
    model_tools: str = os.getenv("MODEL_TOOLS", "qwen-vl-max")
    model_temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0.2"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


# Global config instance
config = Config()
