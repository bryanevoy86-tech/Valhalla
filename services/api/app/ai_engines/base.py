"""Autonomous AI engines base class - plug-in ready for different engines."""
from abc import ABC, abstractmethod
from datetime import datetime


class AutonomousEngine(ABC):
    """Abstract base class for autonomous execution engines."""
    
    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description
        self.active = False
        self.last_evaluation = None
        self.last_execution = None
        self.evaluation_count = 0
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    def evaluate(self, context: dict) -> dict:
        """
        Evaluate conditions for execution.
        
        Args:
            context: Dict with relevant data for evaluation
        
        Returns:
            dict with keys:
                - ready: bool (can this engine execute?)
                - score: float (0-1, confidence)
                - reason: str (why this decision)
                - metadata: dict (additional info)
        """
        pass
    
    @abstractmethod
    def execute(self, context: dict) -> dict:
        """
        Execute the engine's action.
        
        Args:
            context: Dict with relevant data for execution
        
        Returns:
            dict with keys:
                - success: bool
                - result: any (action result)
                - error: str (if not successful)
        """
        pass
    
    def run(self, context: dict) -> dict:
        """
        Full run: evaluate then execute if ready.
        
        Returns:
            dict with evaluation and execution results
        """
        try:
            # Evaluate
            evaluation = self.evaluate(context)
            self.last_evaluation = datetime.now()
            self.evaluation_count += 1
            
            result = {
                "engine": self.name,
                "evaluation": evaluation,
                "execution": None
            }
            
            # Execute if ready
            if evaluation.get("ready", False):
                execution = self.execute(context)
                self.last_execution = datetime.now()
                self.execution_count += 1
                result["execution"] = execution
            
            return result
        
        except Exception as e:
            self.error_count += 1
            return {
                "engine": self.name,
                "error": str(e),
                "error_count": self.error_count
            }
    
    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            "name": self.name,
            "active": self.active,
            "evaluations": self.evaluation_count,
            "executions": self.execution_count,
            "errors": self.error_count,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation else None,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None
        }
