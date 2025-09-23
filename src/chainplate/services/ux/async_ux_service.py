from ..data.data_service import DataService
from typing import Optional
from ..logging.logging_service import LoggingService

ASSISTANT_ROLE = "assistant"
USER_ROLE = "user"

# Module-level constants (public) used by tests and external callers if needed
DB_POLL_INTERVAL = 2  # seconds between polling for user input
WAIT_FOR_USER_INPUT_TIMEOUT = 300  # seconds to wait for user input before timing out
CHAT_CHANNEL_ID = 1  # Default chat channel ID for user interactions

class AsyncUserExperienceService:
    def __init__(self, execution_id = None, data_service: Optional[DataService] = None):
        # Allow dependency injection for easier testing (use an in-memory DB by default)
        self.data_service = data_service or DataService(":memory:")
        self.execution_id = execution_id
        
    def send_to_user(self, content: str = "") -> int:
        """Send a message to the user (no input expected). Returns created step id."""
        return self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=content,
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
        )

    def get_user_input(self, prompt: str = "") -> str:
        LoggingService.log_info(f"Prompting user with: {prompt}")
        """Send a prompt requiring user input and block (poll) until a response or timeout."""
        row_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=prompt,
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        user_input = self.poll_for_user_input(row_id, WAIT_FOR_USER_INPUT_TIMEOUT)
        return user_input

    def poll_for_user_input(self, step_id: int, timeout: int = WAIT_FOR_USER_INPUT_TIMEOUT, poll_interval: float = DB_POLL_INTERVAL) -> str:
        import time
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            user_input = self.check_for_user_input(step_id)
            if user_input:
                return user_input
            time.sleep(poll_interval)
        return ""

    def check_for_user_input(self, step_id: int) -> str:
        step = self.data_service.get_execution_step_by_response_to(step_id)
        if step and step.get("content"):
            return step["content"]
        return ""