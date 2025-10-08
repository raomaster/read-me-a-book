from abc import ABC, abstractmethod

class TextToSpeechInterface(ABC):
    
    @abstractmethod
    def text_to_bytes(self, text: str) -> bytes:
        """Genera audio y lo devuelve como un solo bloque de bytes."""
        pass