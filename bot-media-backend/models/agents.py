import uuid
from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Request body for POST /agents (admin only)."""
    name: Annotated[str, Field(min_length=1, max_length=64, description="Unique display name for the bot.")]
    system_prompt: Annotated[str, Field(min_length=1, description="The bot's persona / instructions.")]
    metadata: Annotated[dict[str, Any], Field(
        default_factory=dict,
        description="Arbitrary JSONB config stored with the agent.",
    )]


class AgentOut(BaseModel):
    """Public representation of an agent.
    
    The api_key is intentionally omitted from this schema.
    """
    agent_id: uuid.UUID
    name: str
    system_prompt: str
    metadata: dict[str, Any]
    created_at: datetime
    last_posted_at: datetime | None

    model_config = {"from_attributes": True}


class AgentCreated(AgentOut):
    """Response for POST /agents.
    
    Includes the api_key exactly once (on creation only).
    """
    api_key: str
