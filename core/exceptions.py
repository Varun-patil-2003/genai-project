class NetOpsBaseException(Exception):
    """Base exception for the NetOps AI Sentinel project."""
    pass

class DataIngestionError(NetOpsBaseException):
    """Raised when data cannot be loaded from source"""
    pass 

class LLMInferenceError(NetOpsBaseException):
    """Raised when the Groq API fails or returns invalid content."""
    pass

class RCAGenetionError(NetOpsBaseException):
    """Raised when the RCA report cannot be compiled."""
    pass