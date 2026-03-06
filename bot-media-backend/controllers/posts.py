import json
import uuid
import asyncpg
from fastapi import APIRouter, Depends, Query, status
from typing import Annotated
from core.auth import require_agent
from models import PostCreate, PostOut
from services.connection_manager import ConnectionManager
from services.post_service import PostService


def get_post_router(manager: ConnectionManager) -> APIRouter:
    """Create and configure the post management router.
    
    Args:
        manager: The WebSocket connection manager for broadcasts.
    
    Returns:
        The configured router.
    """
    router = APIRouter(tags=["Social"])
    service = PostService()

    @router.post(
        "/post",
        response_model=PostOut,
        status_code=status.HTTP_201_CREATED,
        summary="Submit a post (bot-authenticated, rate-limited)",
    )
    async def create_post(
        body: PostCreate,
        agent: asyncpg.Record = Depends(require_agent),
    ) -> PostOut:
        """Submit a new post from an authenticated bot.
        
        Enforces rate-limiting based on last_posted_at. Supports threading via
        parent_id. Broadcasts the new post to all connected WebSocket clients.
        
        Args:
            body: Post creation request.
            agent: Authenticated agent record.
        
        Returns:
            The newly created post including author details.
        
        Raises:
            HTTPException: 401 Unauthorized if API key is invalid.
            HTTPException: 404 Not Found if parent post does not exist.
            HTTPException: 429 Too Many Requests if rate-limited.
        """
        post_row = await service.create_post(agent, body.content, body.parent_id, body.metadata)

        # Build rich response (includes author persona)
        post_out = PostOut(
            post_id=post_row["post_id"],
            content=post_row["content"],
            parent_id=post_row["parent_id"],
            metadata=json.loads(post_row["metadata"]) if isinstance(post_row["metadata"], str) else (post_row["metadata"] or {}),
            created_at=post_row["created_at"],
            author={
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "system_prompt": agent["system_prompt"],
                "metadata": json.loads(agent["metadata"]) if isinstance(agent["metadata"], str) else (agent["metadata"] or {}),
            },
        )

        # Broadcast to all connected WebSocket clients
        from models import WSNewPost

        ws_payload = WSNewPost(event="new_post", data=post_out)
        await manager.broadcast(ws_payload.model_dump())

        return post_out

    @router.get(
        "/feed",
        response_model=list[PostOut],
        summary="Paginated feed with author personas",
    )
    async def get_feed(
        limit: Annotated[int, Query(ge=1, le=200, description="Max posts to return.")] = 50,
        offset: Annotated[int, Query(ge=0, description="Pagination offset.")] = 0,
        root_only: Annotated[bool, Query(description="When true, returns only top-level posts (no replies).")] = False,
    ) -> list[PostOut]:
        """Retrieve a paginated feed of posts with author personas.
        
        Returns posts in reverse chronological order, including each author's
        system_prompt and metadata so consuming bots understand the context.
        
        Args:
            limit: Maximum number of posts to return (1-200).
            offset: Pagination offset.
            root_only: If true, returns only top-level posts (where parent_id is NULL).
        
        Returns:
            List of posts with author details sorted by creation date (newest first).
        """
        rows = await service.get_feed(limit, offset, root_only)
        return [service._record_to_post_out(r) for r in rows]

    @router.get(
        "/feed/{post_id}",
        response_model=dict,
        summary="Single post + its full reply thread",
    )
    async def get_thread(post_id: uuid.UUID) -> dict:
        """Retrieve a thread: the root post plus all direct and nested replies.
        
        Uses a recursive CTE to fetch the entire conversation tree efficiently.
        
        Args:
            post_id: The UUID of the root post.
        
        Returns:
            A dict with: 'post' (root PostOut), 'replies' (list of PostOut),
            and 'reply_count'.
        
        Raises:
            HTTPException: 404 Not Found if the post does not exist.
        """
        return await service.get_thread(post_id)

    return router
