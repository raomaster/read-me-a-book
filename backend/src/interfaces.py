from abc import ABC, abstractmethod

class TextToSpeechInterface(ABC):
    
    @abstractmethod
    def text_to_speech(self, text: str, output_path: str) -> None:
        """Convertir texto a voz."""
        pass