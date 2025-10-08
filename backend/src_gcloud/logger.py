import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from config import config

# ANSI color codes para terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colores de texto
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Colores brillantes
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            
            if config.is_local:
                # Formato colorido para desarrollo local
                formatter = ColoredLocalFormatter()
            else:
                # Formato JSON estructurado para Cloud Logging
                formatter = StructuredFormatter()
                
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Evitar propagación para no duplicar logs
        self.logger.propagate = False
    
    def _log_structured(self, level: str, message: str, **kwargs):
        if config.is_local:
            # Para local, usar el formatter colorido
            extra = {'structured_data': kwargs} if kwargs else {}
            getattr(self.logger, level.lower())(message, extra=extra)
        else:
            # Log estructurado para producción
            log_data = {
                'severity': level,
                'message': message,
                'timestamp': None,  # Cloud Logging adds this
                **kwargs
            }
            getattr(self.logger, level.lower())(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        self._log_structured('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_structured('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_structured('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_structured('DEBUG', message, **kwargs)

class ColoredLocalFormatter(logging.Formatter):
    """Formatter colorido para desarrollo local"""
    
    LEVEL_COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BRIGHT_RED + Colors.BOLD,
    }
    
    def format(self, record):
        # Timestamp con color dim
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        colored_timestamp = f"{Colors.DIM}{timestamp}{Colors.RESET}"
        
        # Level con color específico
        level_color = self.LEVEL_COLORS.get(record.levelname, Colors.WHITE)
        colored_level = f"{level_color}{record.levelname:8}{Colors.RESET}"
        
        # Logger name con color azul
        colored_name = f"{Colors.BLUE}{record.name}{Colors.RESET}"
        
        # Mensaje principal
        message = record.getMessage()
        
        # Datos estructurados si existen
        structured_info = ""
        if hasattr(record, 'structured_data') and record.structured_data:
            # Formatear datos estructurados de manera legible
            data_parts = []
            for key, value in record.structured_data.items():
                if isinstance(value, (str, int, float, bool)):
                    data_parts.append(f"{Colors.MAGENTA}{key}{Colors.RESET}={Colors.CYAN}{value}{Colors.RESET}")
                else:
                    data_parts.append(f"{Colors.MAGENTA}{key}{Colors.RESET}={Colors.CYAN}{str(value)}{Colors.RESET}")
            
            if data_parts:
                structured_info = f" {Colors.DIM}|{Colors.RESET} " + " ".join(data_parts)
        
        # Formato final: [timestamp] LEVEL logger_name: message | key=value key=value
        return f"[{colored_timestamp}] {colored_level} {colored_name}: {message}{structured_info}"

class StructuredFormatter(logging.Formatter):
    """Formatter JSON para producción"""
    def format(self, record):
        return record.getMessage()

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)

# Función para testing del logger
def test_logger():
    """Función para probar el logger con diferentes niveles y datos"""
    logger = get_logger("test_logger")
    
    print(f"\n{Colors.BOLD}🧪 Testing Logger Output{Colors.RESET}\n")
    
    logger.debug("Debug message", user_id="12345", action="test")
    logger.info("User authenticated successfully", user_id="user123", email="test@example.com")
    logger.warning("Rate limit approaching", requests_count=95, limit=100)
    logger.error("TTS generation failed", provider="google", error_code="QUOTA_EXCEEDED")
    
    # Test con datos complejos
    logger.info("Request processed", 
                method="POST", 
                path="/text_to_audio", 
                duration_ms=1250,
                audio_size=45678,
                success=True)

if __name__ == "__main__":
    # Solo para testing
    test_logger()