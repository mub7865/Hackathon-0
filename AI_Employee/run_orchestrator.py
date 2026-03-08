#!/usr/bin/env python
"""
Orchestrator Launcher Script
Properly sets up Python path and runs the orchestrator
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded environment variables from {env_file}")
else:
    print(f"[WARN] No .env file found at {env_file}")

# Now import and run orchestrator
from src.orchestrator.orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator(vault_path="vault")
    orchestrator.start()  # Use start() method, not run()
