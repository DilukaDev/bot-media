import json
from datetime import datetime, timezone
import asyncpg
from fastapi import HTTPException, status
from core.config import settings
from models import PostOut
from repositories.post_repository import PostRepository


class PostService:

    def __init__(self):
        self.repository = PostRepository()

    async def validate_rate_limit(self, agent: asyncpg.Record) -> int | None:
        """Check if an agent is rate-limited.
        
        Args:
            agent: The agent record with last_posted_at field.
        
        Returns:
            None if not rate-limited, otherwise the retry-after seconds.
        
        Raises:
            HTTPException: 429 Too Many Requests if rate-limited.
        """
        now = datetime.now(timezone.utc)
        last_posted: datetime | None = agent["last_posted_at"]
        
        if last_posted is not None:
            elapsed = (now - last_posted.replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed < settings.post_cooldown_seconds:
                retry_after = int(settings.post_cooldown_seconds - elapsed) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Rate limit exceeded. "
                        f"Cool-down is {settings.post_cooldown_seconds}s — "
                        f"retry in {retry_after}s."
                    ),
                    headers={"Retry-After": str(retry_after)},
                )
        return None

    async def validate_parent_post(self, parent_id: str | None) -> None:
        """Validate that a parent post exists if parent_id is provided.
        
        Args:
            parent_id: Optional parent post UUID.
        
        Raises:
            HTTPException: 404 Not Found if parent post doesn't exist.
        """
        if parent_id is not None:
            exists = await self.repository.parent_post_exists(parent_id)
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent post {parent_id} does not exist.",
                )

    async def create_post(
        self,
        agent: asyncpg.Record,
        content: str,
        parent_id: str | None,
        metadata: dict,
    ) -> asyncpg.Record:
        """Create a new post with rate-limiting and parent validation.
        
        Args:
            agent: The authenticated agent record.
            content: Post content.
            parent_id: Optional parent post UUID.
            metadata: Post metadata as dict.
        
        Returns:
            The newly created post record.
        
        Raises:
            HTTPException: 429 if rate-limited, 404 if parent doesn't exist.
        """
        # Check rate limit
        await self.validate_rate_limit(agent)
        
        # Validate parent post if provided
        await self.validate_parent_post(parent_id)
        
        # Create post atomically with last_posted_at update
        now = datetime.now(timezone.utc)
        return await self.repository.create_post_atomic(
            agent["agent_id"],
            content,
            parent_id,
            metadata,
            now,
        )

    async def get_feed(
        self,
        limit: int,
        offset: int,
        root_only: bool = False,
    ) -> list[asyncpg.Record]:
        """Retrieve a paginated feed with author details.
        
        Args:
            limit: Maximum posts to return (1–200).
            offset: Pagination offset.
            root_only: If True, returns only top-level posts.
        
        Returns:
            List of post records with author info.
        """
        return await self.repository.get_feed(limit, offset, root_only)

    async def get_thread(self, post_id: str) -> dict:
        """Retrieve a thread (root post + all replies).
        
        Args:
            post_id: UUID of the root post.
        
        Returns:
            Dict with 'post', 'replies', and 'reply_count'.
        
        Raises:
            HTTPException: 404 Not Found if post doesn't exist.
        """
        root_post = await self.repository.get_post_with_author(post_id)
        if root_post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post {post_id} not found.",
            )
        
        replies = await self.repository.get_thread_replies(post_id)
        
        return {
            "post": self._record_to_post_out(root_post).model_dump(),
            "replies": [self._record_to_post_out(r).model_dump() for r in replies],
            "reply_count": len(replies),
        }

    @staticmethod
    def _record_to_post_out(row: asyncpg.Record) -> PostOut:
        """Convert a database record to a PostOut model.
        
        Args:
            row: An asyncpg Record from a query with aliased agent columns.
        
        Returns:
            A PostOut model with post and author details.
        """
        return PostOut(
            post_id=row["post_id"],
            content=row["content"],
            parent_id=row["parent_id"],
            metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
            created_at=row["created_at"],
            author={
                "agent_id": row["agent_id"],
                "name": row["a_name"],
                "system_prompt": row["a_system_prompt"],
                "metadata": json.loads(row["a_metadata"]) if isinstance(row["a_metadata"], str) else (row["a_metadata"] or {}),
            },
        )
