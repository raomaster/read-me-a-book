import logging
import os
import subprocess
from ..interfaces import TextToSpeechInterface


class PiperEngine(TextToSpeechInterface):
    def __init__(self, model_path: str, piper_executable_path: str):
        if not os.path.exists(piper_executable_path):
            logging.error(f"Piper ejecutable no encontrado en: {piper_executable_path}")
            raise FileNotFoundError(f"Piper ejecutable no encontrado en: {piper_executable_path}")
        if not os.path.exists(model_path):
            logging.error(f"Modelo de voz de Piper no encontrado en: {model_path}")
            raise FileNotFoundError(f"Modelo de voz de Piper no encontrado en: {model_path}")

        self.model_path = model_path
        self.piper_executable_path = piper_executable_path
        logging.info(
            f"PiperEngine Inicializado con modelo: {self.model_path} y ejecutable: {self.piper_executable_path}"
        )

    def text_to_speech(self, text: str, output_path: str) -> None:
        # Implementa la conversión de texto a voz usando Piper
        # Asegurarse de que el directorio de salida exista
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Directorio de salida creado: {output_dir}")

        try:
            command = [
                self.piper_executable_path,
                "--model", self.model_path,
                "--output_file", output_path
            ]
            logging.debug(f"Ejecutando comando Piper: {' '.join(command)}")
            logging.debug(f"Texto de entrada para Piper (primeros 100 caracteres): {text[:100]}")

            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 # Evitar ventana de consola en Windows
            )
            stdout_bytes, stderr_bytes = process.communicate(input=text.encode('utf-8'))

            stdout_decoded = stdout_bytes.decode('utf-8', errors='ignore').strip()
            stderr_decoded = stderr_bytes.decode('utf-8', errors='ignore').strip()

            if process.returncode != 0:
                error_message = f"Proceso Piper finalizó con código {process.returncode}."
                if stderr_decoded:
                    error_message += f" Stderr: {stderr_decoded}"
                if stdout_decoded: # Registrar stdout también, podría contener información del error
                    error_message += f" Stdout: {stdout_decoded}"
                if not stderr_decoded and not stdout_decoded:
                    error_message += " No se capturó salida de stderr o stdout de Piper."
                
                logging.error(f"Error al generar audio con Piper: {error_message}")
                raise Exception(error_message) # Usar el mensaje de error más detallado
            else:
                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    warning_message = f"Proceso Piper finalizó correctamente (código 0) pero el archivo de salida '{output_path}' no se creó o está vacío."
                    if stdout_decoded: 
                        warning_message += f" Stdout: {stdout_decoded}"
                    if stderr_decoded: 
                        warning_message += f" Stderr (inesperado en éxito): {stderr_decoded}"
                    logging.warning(warning_message)
                    # Considerar lanzar una excepción aquí también si un archivo vacío es un fallo crítico.
                else:
                    logging.info(f"Audio generado con Piper y guardado en: {output_path}")
                    if stdout_decoded: 
                        logging.debug(f"Piper stdout (éxito): {stdout_decoded}")
                    if stderr_decoded: 
                        logging.debug(f"Piper stderr (éxito, inesperado): {stderr_decoded}")
        except FileNotFoundError as fnf_e:
            logging.error(f"Ejecutable de Piper no encontrado al intentar ejecutar el proceso: {self.piper_executable_path}. Error: {fnf_e}")
            raise
        except Exception as e:
            logging.error(f"Excepción durante la generación de audio con Piper: {e}")
            raise
