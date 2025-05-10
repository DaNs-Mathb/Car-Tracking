from pydantic import BaseModel


class Offer(BaseModel):
    sdp: str
    type: str
    video_transform: str = None
    
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict = None
    error: str = None