"""
config.py — Central configuration for the Financial Snapshot Agent.
Now using Groq (free, works in all regions).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).parent
load_dotenv(dotenv_path=_ROOT / ".env")

# ── API Settings ──────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# ── Model Settings ────────────────────────────────────────────────────────────
# Free Groq models: llama-3.3-70b-versatile, mixtral-8x7b-32768, llama-3.1-8b-instant
MODEL_NAME: str = "llama-3.1-8b-instant"
MAX_TOKENS: int = 1500

# ── App Settings ──────────────────────────────────────────────────────────────
APP_NAME: str    = "Financial Snapshot Agent"
APP_VERSION: str = "1.0.0"
