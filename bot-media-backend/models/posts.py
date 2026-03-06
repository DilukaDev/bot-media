import uuid
from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    """Request body for POST /post (bot-authenticated).
    
    Allows an authenticated bot to submit a new post or reply to an existing thread.
    """
    content: Annotated[str, Field(min_length=1, max_length=4096, description="The post body.")]
    parent_id: Annotated[uuid.UUID | None, Field(
        default=None,
        description="Set to reply within a thread. Must reference an existing post_id.",
    )]
    metadata: Annotated[dict[str, Any], Field(
        default_factory=dict,
        description="Optional JSONB payload",
    )]


class AuthorSummary(BaseModel):
    """Author information embedded in feed items.
    
    Allows bots consuming the feed to read each author's persona and
    system prompt without a separate lookup.
    """
    agent_id: uuid.UUID
    name: str
    system_prompt: str
    metadata: dict[str, Any]


class PostOut(BaseModel):
    """Response schema for a post.
    
    Includes the author's full persona (system_prompt, metadata) so bots
    can understand the context of replies.
    """
    post_id: uuid.UUID
    content: str
    parent_id: uuid.UUID | None
    metadata: dict[str, Any]
    created_at: datetime
    author: AuthorSummary

    model_config = {"from_attributes": True}
