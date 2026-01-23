"""Base AI Provider Interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def evaluate(self, jd_text: str, cv_text: str, criteria: list[str] = None, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Evaluate CV against JD and return structured result.
        
        Returns:
            {
                "score": int (1-10),
                "strengths": str,
                "weaknesses": str,
                "justification": str,
                "recommendation": str (RECOMMEND/CONSIDER/REJECT)
            }
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if provider is accessible"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
