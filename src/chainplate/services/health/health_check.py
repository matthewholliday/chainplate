import os
import dataclasses

class HealthCheck:
    def __init__(self,status="unknown", errors=[]):
        self.status = status
        self.errors = errors
    
    def to_dict(self):
        return dataclasses.asdict(self)


class HealthCheckService:

    @staticmethod
    def check():
        errors: list[str] = []
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            errors.append("OPENAI_API_KEY not configured")
        
        status = "ok" if not errors else "error"

        return HealthCheck(status=status, errors=errors)

