import secrets
import asyncpg
from core.config import settings
from repositories.agent_repository import AgentRepository


class AgentService:

    def __init__(self):
        self.repository = AgentRepository()

    async def create_agent(self, name: str, system_prompt: str, metadata: dict) -> asyncpg.Record:
        """Create a new agent with a randomly generated API key.
        
        Args:
            name: Agent name (must be unique).
            system_prompt: System prompt for the agent.
            metadata: Agent metadata as dict.
        
        Returns:
            The newly created agent record with api_key.
        
        Raises:
            asyncpg.UniqueViolationError: If agent name already exists.
        """
        api_key = secrets.token_hex(32)  # 64-character hex string
        return await self.repository.create_agent(name, system_prompt, api_key, metadata)

    async def list_all_agents(self) -> list[asyncpg.Record]:
        """Retrieve all agents.
        
        Returns:
            List of agent records ordered by creation date (newest first).
        """
        return await self.repository.get_all_agents()

    async def get_agent_by_api_key(self, api_key: str) -> asyncpg.Record | None:
        """Retrieve an agent by API key.
        
        Args:
            api_key: The agent's API key.
        
        Returns:
            The agent record, or None if not found.
        """
        return await self.repository.get_agent_by_api_key(api_key)
