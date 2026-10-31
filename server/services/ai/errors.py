class ModelNotConfigured(RuntimeError):
    """Raised when AI_MOCK=0 but the real model client is not wired yet."""
