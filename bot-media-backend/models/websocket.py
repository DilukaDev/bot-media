from pydantic import BaseModel
from .posts import PostOut


class WSNewPost(BaseModel):
    """WebSocket event payload.
    
    Pushed to all connected clients when a new post is successfully saved.
    """
    event: str = "new_post"
    data: PostOut
