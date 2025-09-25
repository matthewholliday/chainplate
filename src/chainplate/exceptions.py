class MissingAgentGoalsException(Exception):
    """Raised when an AgentElement is initialized without goals."""
    pass

class MissingMessageException(Exception):
    """Raised when a required Message object is missing."""
    pass