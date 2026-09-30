from models import ImageRecord, BlogPost, GuardStatus
from typing import Tuple, Dict, Any

class MismatchGuard:
    RULES = {
        "confidence": {"animal": 0.85, "object": 0.75, "scene": 0.70},
        "similarity": {"animal": 0.75, "object": 0.65, "scene": 0.60},
        "require_match": {"animal": True, "object": False, "scene": False},
        "blocked": ["transfer", "payment", "aadhaar", "ssn"]
    }
    
    @classmethod
    def apply(cls, image: ImageRecord, post: BlogPost, sim: float, conf: float) -> Tuple[GuardStatus, str, Dict[str, Any]]:
        checks = {}
        cat = image.vision_metadata.category if image.vision_metadata else "object"
        
        min_conf = cls.RULES["confidence"].get(cat, 0.75)
        min_sim = cls.RULES["similarity"].get(cat, 0.65)
        require = cls.RULES["require_match"].get(cat, False)
        
        checks["confidence"] = {"value": conf, "threshold": min_conf, "pass": conf >= min_conf}
        if conf < min_conf:
            return (GuardStatus.REJECTED, f"Low confidence: {conf:.2f} < {min_conf}", checks)
        
        checks["similarity"] = {"value": sim, "threshold": min_sim, "pass": sim >= min_sim}
        if sim < min_sim:
            return (GuardStatus.REJECTED, f"Low similarity: {sim:.2f} < {min_sim}", checks)
        
        img_cat = image.vision_metadata.category if image.vision_metadata else "object"
        checks["category"] = {"required": require, "image": img_cat, "post": post.category, "pass": img_cat == post.category or not require}
        if require and img_cat != post.category:
            return (GuardStatus.REJECTED, f"Category mismatch: {img_cat} != {post.category}", checks)
        
        for pattern in cls.RULES["blocked"]:
            if pattern in post.title.lower():
                checks["blocked"] = {"pattern": pattern}
                return (GuardStatus.REJECTED, f"Blocked: {pattern}", checks)
        
        return (GuardStatus.ACCEPTED, None, checks)
