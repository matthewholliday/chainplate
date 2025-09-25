import os
import dataclasses
from typing import List

@dataclasses.dataclass
class HealthCheck:
    status: str = "unknown"
    errors: List[str] = dataclasses.field(default_factory=list)
    
    def to_dict(self):
        return dataclasses.asdict(self)


class HealthCheckService:

    @staticmethod
    def check():
        errors: List[str] = []
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            errors.append("OPENAI_API_KEY not configured")
        
        status = "ok" if not errors else "error"

        return HealthCheck(status=status, errors=errors)

