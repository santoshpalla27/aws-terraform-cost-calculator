"""
Base stage executor.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.job import Job


class BaseStageExecutor(ABC):
    """Base class for stage executors."""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
    
    @abstractmethod
    async def execute(self, job: Job) -> Dict[str, Any]:
        """
        Execute the stage.
        
        Args:
            job: Job to execute stage for
            
        Returns:
            Stage execution result
        """
        pass
    
    @abstractmethod
    async def validate_input(self, job: Job) -> None:
        """Validate input before execution."""
        pass
    
    @abstractmethod
    async def validate_output(self, result: Dict[str, Any]) -> None:
        """Validate output after execution."""
        pass
