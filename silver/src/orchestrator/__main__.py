"""
Orchestrator Entry Point
Loads configuration and starts orchestrator loop
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.orchestrator import Orchestrator
from src.utils.logger import setup_logger


def main():
    """Main entry point for orchestrator"""
    # Load environment variables
    load_dotenv()

    # Get configuration
    vault_path = os.getenv('VAULT_PATH', './vault')
    cycle_interval = int(os.getenv('ORCHESTRATOR_INTERVAL', '300'))

    # Setup logger
    logger = setup_logger('orchestrator-main', f'{vault_path}/Logs')

    logger.info("=" * 60)
    logger.info("Silver Tier AI Assistant - Orchestrator")
    logger.info("=" * 60)
    logger.info(f"Vault Path: {vault_path}")
    logger.info(f"Cycle Interval: {cycle_interval}s ({cycle_interval/60:.1f} minutes)")
    logger.info("=" * 60)

    # Create and start orchestrator
    try:
        orchestrator = Orchestrator(vault_path, cycle_interval)
        orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
