import os, random, hashlib
from typing import List, Optional

try:
    import google.generativeai as genai
except:
    genai = None

class EmbeddingsProcessor:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.enabled = False
        if key and genai:
            try:
                genai.configure(api_key=key)
                self.enabled = True
            except:
                pass
    
    async def embed_text(self, text: str) -> List[float]:
        if not self.enabled or not genai:
            return self._mock(text)
        try:
            response = genai.embed_content(model="models/embedding-001", content=text)
            return response['embedding']
        except:
            return self._mock(text)
    
    def _mock(self, text: str) -> List[float]:
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = random.Random(hash_val)
        embed = [rng.gauss(0, 1) for _ in range(768)]
        mag = sum(x**2 for x in embed) ** 0.5
        return [x/mag for x in embed] if mag > 0 else embed
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        dot = sum(a*b for a,b in zip(v1, v2))
        mag1 = sum(x**2 for x in v1)**0.5
        mag2 = sum(x**2 for x in v2)**0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return max(0.0, min(1.0, (dot/(mag1*mag2)+1)/2))
