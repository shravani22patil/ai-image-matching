from typing import List, Dict

class Evaluator:
    @staticmethod
    def evaluate(suggestions: Dict) -> Dict:
        if not suggestions:
            return {"status": "error", "message": "No suggestions"}
        return {"status": "success", "total": len(suggestions)}
