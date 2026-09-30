from typing import List, Dict, Callable
from models import ImageRecord, BlogPost, ImageSuggestion, GuardStatus
from embeddings import EmbeddingsProcessor
from datetime import datetime

class Matcher:
    def __init__(self, embeddings: EmbeddingsProcessor):
        self.embeddings = embeddings
    
    def rank(self, post: BlogPost, images: Dict[str, ImageRecord], guard: Callable) -> List[ImageSuggestion]:
        if not post.embedding:
            return []
        
        matches = []
        for img_id, img in images.items():
            if not img.embedding:
                continue
            
            sim = EmbeddingsProcessor.cosine_similarity(post.embedding, img.embedding)
            conf = img.vision_metadata.confidence if img.vision_metadata else 0.0
            
            status, reason, checks = guard(image=img, post=post, sim=sim, conf=conf)
            
            match = ImageSuggestion(
                id=f"m_{len(matches)+1}", image_id=img_id, post_id=post.id,
                similarity_score=sim, vision_confidence=conf,
                guard_status=status, rejection_reason=reason,
                guard_checks=checks, created_at=datetime.now()
            )
            matches.append(match)
        
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches
