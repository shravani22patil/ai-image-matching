from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VisionOutput(BaseModel):
    subject: str
    category: str
    attributes: List[str]
    confidence: float
    description: str
    processing_time_ms: int = 0

class ImageRecord(BaseModel):
    id: str
    url: str
    caption: str
    vision_metadata: Optional[VisionOutput] = None
    embedding: Optional[List[float]] = None
    created_at: datetime

class BlogPost(BaseModel):
    id: str
    title: str
    content: str
    category: str
    embedding: Optional[List[float]] = None
    created_at: datetime

class GuardStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_APPROVAL = "needs_approval"

class ImageSuggestion(BaseModel):
    id: str
    image_id: str
    post_id: str
    similarity_score: float
    vision_confidence: float
    guard_status: GuardStatus
    rejection_reason: Optional[str] = None
    guard_checks: Dict[str, Any] = {}
    created_at: datetime

class UploadImageRequest(BaseModel):
    url: str
    caption: str

class CreatePostRequest(BaseModel):
    title: str
    content: str
    category: str
