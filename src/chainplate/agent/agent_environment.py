from ..services.data.data_service import DataService
from typing import Optional

ASSISTANT_ROLE = "assistant"
USER_ROLE = "user"

# Module-level constants (public) used by tests and external callers if needed
DB_POLL_INTERVAL = 2  # seconds between polling for user input
WAIT_FOR_USER_INPUT_TIMEOUT = 300  # seconds to wait for user input before timing out
CHAT_CHANNEL_ID = 1  # Default chat channel ID for user interactions


class AgentEnvironment:
    """Environment abstraction for agent <-> user interactions.

    Parameters
    ----------
    execution_id: int | None
        The execution id in the database whose conversation steps we append to.
    data_service: DataService | None
        Optionally inject a DataService (facilitates unit testing with in-memory DB).
    """

    def __init__(self, execution_id = None, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService(":memory:")
        
    def set_execution_id(self, execution_id: int) -> 'AgentEnvironment':
        self.execution_id = execution_id
        return self

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
        

