from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import close_db, init_db
from services.connection_manager import ConnectionManager
from controllers import health, agents, posts, websocket


# Create global connection manager instance
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI application lifespan.
    
    Initialises the database pool and schema on startup.
    Cleanly closes all connections on shutdown.
    
    Args:
        app: The FastAPI application instance.
    """
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="bot-media API",
    description="Agentic Social Network",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
health_router = health.get_health_router(manager)
app.include_router(health_router)

# Agent management
agents_router = agents.get_agent_router()
app.include_router(agents_router)

# Posts (social)
posts_router = posts.get_post_router(manager)
app.include_router(posts_router)

# WebSocket
ws_router = websocket.get_websocket_router(manager)
app.include_router(ws_router)
