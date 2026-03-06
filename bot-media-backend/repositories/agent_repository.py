import json
import asyncpg
from .base_repository import BaseRepository


class AgentRepository(BaseRepository):

    async def create_agent(
        self,
        name: str,
        system_prompt: str,
        api_key: str,
        metadata: dict,
    ) -> asyncpg.Record:
        """Create a new agent in the database.
        
        Args:
            name: Agent name (unique).
            system_prompt: System prompt for the agent.
            api_key: API key (unique).
            metadata: Agent metadata as dict.
        
        Returns:
            The newly created agent record.
        
        Raises:
            asyncpg.UniqueViolationError: If name or api_key already exists.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agents (name, system_prompt, api_key, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                name,
                system_prompt,
                api_key,
                json.dumps(metadata),
            )
        return row

    async def get_all_agents(self) -> list[asyncpg.Record]:
        """Retrieve all agents.
        
        Returns:
            List of agent records ordered by creation date (newest first).
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT agent_id, name, system_prompt, metadata, created_at, last_posted_at
                FROM agents
                ORDER BY created_at DESC
                """
            )
        return rows

    async def get_agent_by_api_key(self, api_key: str) -> asyncpg.Record | None:
        """Retrieve an agent by API key.
        
        Args:
            api_key: The agent's API key.
        
        Returns:
            The agent record, or None if not found.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agents WHERE api_key = $1",
                api_key,
            )
        return row

    async def update_last_posted_at(self, agent_id: str, timestamp) -> None:
        """Update the last_posted_at timestamp for an agent.
        
        Args:
            agent_id: The agent's UUID.
            timestamp: The new timestamp (should be timezone-aware).
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE agents SET last_posted_at = $1 WHERE agent_id = $2",
                timestamp,
                agent_id,
            )
