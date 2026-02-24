"""
Orchestrator State Management
Handles state persistence, locking, and statistics tracking
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import logging


@dataclass
class Lock:
    """Lock state for orchestrator"""
    locked: bool
    locked_by: Optional[str]
    locked_at: Optional[str]


@dataclass
class Statistics:
    """Daily statistics for orchestrator"""
    tasks_processed_today: int
    tasks_approved_today: int
    tasks_rejected_today: int
    errors_today: int


@dataclass
class LastError:
    """Last error information"""
    timestamp: str
    message: str
    component: str


@dataclass
class OrchestratorState:
    """
    Orchestrator execution state and statistics.
    Persisted to vault/Logs/orchestrator_state.json
    """
    last_run: str
    current_cycle: int
    status: str  # "running" | "stopped" | "error"
    lock: Lock
    statistics: Statistics
    last_error: Optional[LastError] = None


class StateManager:
    """Manages orchestrator state persistence and locking"""

    def __init__(self, state_file_path: Path):
        """
        Initialize state manager.

        Args:
            state_file_path: Path to orchestrator_state.json
        """
        self.state_file_path = state_file_path
        self.logger = logging.getLogger(__name__)

    def load_state(self) -> OrchestratorState:
        """
        Load orchestrator state from file.

        Returns:
            OrchestratorState object

        Raises:
            FileNotFoundError: If state file doesn't exist (first run)
        """
        if not self.state_file_path.exists():
            # Initialize default state for first run
            return OrchestratorState(
                last_run=datetime.now().isoformat(),
                current_cycle=0,
                status="stopped",
                lock=Lock(locked=False, locked_by=None, locked_at=None),
                statistics=Statistics(
                    tasks_processed_today=0,
                    tasks_approved_today=0,
                    tasks_rejected_today=0,
                    errors_today=0
                ),
                last_error=None
            )

        with open(self.state_file_path, 'r') as f:
            data = json.load(f)

        # Reconstruct dataclasses from dict
        lock = Lock(**data['lock'])
        statistics = Statistics(**data['statistics'])
        last_error = LastError(**data['last_error']) if data.get('last_error') else None

        return OrchestratorState(
            last_run=data['last_run'],
            current_cycle=data['current_cycle'],
            status=data['status'],
            lock=lock,
            statistics=statistics,
            last_error=last_error
        )

    def save_state(self, state: OrchestratorState) -> None:
        """
        Save orchestrator state to file.

        Args:
            state: OrchestratorState to persist
        """
        # Ensure parent directory exists
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert dataclasses to dict
        state_dict = {
            'last_run': state.last_run,
            'current_cycle': state.current_cycle,
            'status': state.status,
            'lock': asdict(state.lock),
            'statistics': asdict(state.statistics),
            'last_error': asdict(state.last_error) if state.last_error else None
        }

        with open(self.state_file_path, 'w') as f:
            json.dump(state_dict, f, indent=2)

    def acquire_lock(self, state: OrchestratorState, locked_by: str = "orchestrator") -> bool:
        """
        Acquire lock for orchestrator cycle.

        Args:
            state: Current orchestrator state
            locked_by: Identifier of lock holder

        Returns:
            True if lock acquired, False if already locked
        """
        # Check for stale lock (>15 minutes old)
        if state.lock.locked and state.lock.locked_at:
            locked_time = datetime.fromisoformat(state.lock.locked_at)
            now = datetime.now()
            age_minutes = (now - locked_time).total_seconds() / 60

            if age_minutes > 15:
                self.logger.warning(f"Stale lock detected ({age_minutes:.1f} minutes old), forcing release")
                state.lock.locked = False

        # Try to acquire lock
        if not state.lock.locked:
            state.lock.locked = True
            state.lock.locked_by = locked_by
            state.lock.locked_at = datetime.now().isoformat()
            self.save_state(state)
            return True

        return False

    def release_lock(self, state: OrchestratorState) -> None:
        """
        Release orchestrator lock.

        Args:
            state: Current orchestrator state
        """
        state.lock.locked = False
        state.lock.locked_by = None
        state.lock.locked_at = None
        self.save_state(state)
