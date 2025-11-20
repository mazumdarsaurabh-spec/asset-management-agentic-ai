from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def make_decision(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Make decisions based on current state
        
        Args:
            state: Dictionary containing current system state
            
        Returns:
            List of decision dictionaries
        """
        pass
    
    def log_decision(self, decision_type: str, message: str, data: Dict = None):
        """Log agent decision"""
        log_entry = {
            'agent': self.name,
            'decision_type': decision_type,
            'message': message,
            'data': data or {}
        }
        self.logger.info(f"{self.name}: {message}", extra=log_entry)
        return log_entry
    
    def validate_state(self, state: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate that state contains required keys"""
        missing = [key for key in required_keys if key not in state]
        if missing:
            self.logger.error(f"Missing required state keys: {missing}")
            return False
        return True