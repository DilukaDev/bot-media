from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from core.auth import require_admin
from models import AgentCreate, AgentCreated, AgentOut
from services.agent_service import AgentService


def get_agent_router() -> APIRouter:
    """Create and configure the agent management router.
    
    Returns:
        The configured router.
    """
    router = APIRouter(prefix="/agents", tags=["Admin"])
    service = AgentService()


    @router.post(
        "",
        response_model=AgentCreated,
        status_code=status.HTTP_201_CREATED,
        summary="Create a new agent (admin only)",
    )
    async def create_agent(
        body: AgentCreate,
        _: None = Depends(require_admin),
    ) -> AgentCreated:
        """Register a new bot (agent) in the system.
        
        Generates a cryptographically random api_key. The key is returned only
        once and must be stored securely by the caller.
        
        Args:
            body: Agent creation request.
            _: Admin authentication check.
        
        Returns:
            The newly created agent including its api_key.
        
        Raises:
            HTTPException: 401 Unauthorized if not authenticated as admin.
            HTTPException: 409 Conflict if agent name already exists.
        """
        try:
            row = await service.create_agent(body.name, body.system_prompt, body.metadata)
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An agent named '{body.name}' already exists.",
            )

        return AgentCreated(
            agent_id=row["agent_id"],
            name=row["name"],
            system_prompt=row["system_prompt"],
            api_key=row["api_key"],
            metadata=body.metadata,
            created_at=row["created_at"],
            last_posted_at=row["last_posted_at"],
        )


    @router.get(
        "",
        response_model=list[AgentOut],
        summary="List all agents (admin only)",
    )
    async def list_agents(_: None = Depends(require_admin)) -> list[AgentOut]:
        """Retrieve all registered agents.
        
        Args:
            _: Admin authentication check.
        
        Returns:
            List of all agents (api_key is intentionally excluded).
        
        Raises:
            HTTPException: 401 Unauthorized if not authenticated as admin.
        """
        import json

        rows = await service.list_all_agents()
        return [
            AgentOut(
                agent_id=r["agent_id"],
                name=r["name"],
                system_prompt=r["system_prompt"],
                metadata=json.loads(r["metadata"]) if isinstance(r["metadata"], str) else (r["metadata"] or {}),
                created_at=r["created_at"],
                last_posted_at=r["last_posted_at"],
            )
            for r in rows
        ]
    
    return router
