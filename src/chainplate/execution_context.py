from .services.logging.logging_service import LoggingService
import dataclasses


@dataclasses.dataclass
class ExecutionContext:
    execution_id: str

    def log_info(self, message: str):
        LoggingService.log_info(f"[ExecutionContext ID: {self.execution_id}] {message}")

    def log_error(self, message: str):
        LoggingService.log_error(f"[ExecutionContext ID: {self.execution_id}] {message}")

    def log_warning(self, message: str):
        LoggingService.log_warning(f"[ExecutionContext ID: {self.execution_id}] {message}")