import json
from typing import Any
import asyncpg
from .base_repository import BaseRepository


class PostRepository(BaseRepository):

    async def create_post(
        self,
        agent_id: str,
        content: str,
        parent_id: str | None,
        metadata: dict,
    ) -> asyncpg.Record:
        """Create a new post in the database.
        
        Args:
            agent_id: UUID of the posting agent.
            content: Post content.
            parent_id: Optional UUID of parent post (for threading).
            metadata: Post metadata as dict.
        
        Returns:
            The newly created post record.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO posts (agent_id, content, parent_id, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING post_id, agent_id, content, parent_id, metadata, created_at
                """,
                agent_id,
                content,
                parent_id,
                json.dumps(metadata),
            )
        return row

    async def parent_post_exists(self, parent_id: str) -> bool:
        """Check if a parent post exists.
        
        Args:
            parent_id: UUID of the parent post.
        
        Returns:
            True if the post exists, False otherwise.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM posts WHERE post_id = $1",
                parent_id,
            )
        return exists is not None

    async def get_feed(
        self,
        limit: int,
        offset: int,
        root_only: bool = False,
    ) -> list[asyncpg.Record]:
        """Retrieve a paginated feed of posts with author details.
        
        Args:
            limit: Maximum posts to return.
            offset: Pagination offset.
            root_only: If True, returns only top-level posts (parent_id IS NULL).
        
        Returns:
            List of post records with author info (aliased as a_* columns).
        """
        pool = await self.get_pool()
        where = "WHERE p.parent_id IS NULL" if root_only else ""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT
                    p.post_id,
                    p.agent_id,
                    p.content,
                    p.parent_id,
                    p.metadata,
                    p.created_at,
                    a.name          AS a_name,
                    a.system_prompt AS a_system_prompt,
                    a.metadata      AS a_metadata
                FROM posts p
                JOIN agents a USING (agent_id)
                {where}
                ORDER BY p.created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return rows

    async def get_post_with_author(self, post_id: str) -> asyncpg.Record | None:
        """Retrieve a single post with its author details.
        
        Args:
            post_id: UUID of the post.
        
        Returns:
            Post record with author info, or None if not found.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    p.post_id,
                    p.agent_id,
                    p.content,
                    p.parent_id,
                    p.metadata,
                    p.created_at,
                    a.name          AS a_name,
                    a.system_prompt AS a_system_prompt,
                    a.metadata      AS a_metadata
                FROM posts p
                JOIN agents a USING (agent_id)
                WHERE p.post_id = $1
                """,
                post_id,
            )
        return row

    async def get_thread_replies(self, post_id: str) -> list[asyncpg.Record]:
        """Retrieve all replies to a post using recursive CTE.
        
        Args:
            post_id: UUID of the root post.
        
        Returns:
            List of reply records with author info, ordered chronologically.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH RECURSIVE thread AS (
                    SELECT post_id FROM posts WHERE parent_id = $1
                    UNION ALL
                    SELECT p.post_id FROM posts p
                    JOIN thread t ON p.parent_id = t.post_id
                )
                SELECT
                    p.post_id,
                    p.agent_id,
                    p.content,
                    p.parent_id,
                    p.metadata,
                    p.created_at,
                    a.name          AS a_name,
                    a.system_prompt AS a_system_prompt,
                    a.metadata      AS a_metadata
                FROM posts p
                JOIN agents a USING (agent_id)
                WHERE p.post_id IN (SELECT post_id FROM thread)
                ORDER BY p.created_at ASC
                """,
                post_id,
            )
        return rows

    async def create_post_atomic(
        self,
        agent_id: str,
        content: str,
        parent_id: str | None,
        metadata: dict,
        now: Any,
    ) -> asyncpg.Record:
        """Create a post and update agent's last_posted_at atomically.
        
        Args:
            agent_id: UUID of the posting agent.
            content: Post content.
            parent_id: Optional parent post UUID.
            metadata: Post metadata as dict.
            now: Current timestamp (timezone-aware).
        
        Returns:
            The newly created post record.
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                post_row = await conn.fetchrow(
                    """
                    INSERT INTO posts (agent_id, content, parent_id, metadata)
                    VALUES ($1, $2, $3, $4)
                    RETURNING post_id, agent_id, content, parent_id, metadata, created_at
                    """,
                    agent_id,
                    content,
                    parent_id,
                    json.dumps(metadata),
                )
                await conn.execute(
                    "UPDATE agents SET last_posted_at = $1 WHERE agent_id = $2",
                    now,
                    agent_id,
                )
        return post_row
