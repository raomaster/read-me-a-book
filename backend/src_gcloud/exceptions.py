class TTSError(Exception):
    """Base exception for TTS operations"""
    pass

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization related errors"""
    pass

class ValidationError(Exception):
    """Request validation errors"""
    pass

class TTSProviderError(TTSError):
    """TTS provider specific errors"""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}")

class FirestoreError(Exception):
    """Firestore operation errors"""
    pass