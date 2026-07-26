from abc import ABC, abstractmethod
from app.graph.state import AgentInput, AgentOutput


class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the agent."""
        pass

    @abstractmethod
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent task and return standardized AgentOutput."""
        pass
