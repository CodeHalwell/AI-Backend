"""
API Router

Aggregates all API endpoints under /api/v1.

Why versioned APIs?
- Backward compatibility
- Gradual migrations
- Clear API contracts
- Support multiple versions simultaneously

Structure:
/api/v1/
├── auth/      - Authentication endpoints
├── agents/    - AI agent management
├── conversations/ - Conversation management
├── messages/  - Message endpoints
└── tools/     - Tool management
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, agents, conversations, tools

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"],
)

api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["conversations"],
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["tools"],
)
