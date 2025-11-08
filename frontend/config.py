"""Streamlit frontend configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Frontend configuration
FRONTEND_DIR = Path(__file__).parent

