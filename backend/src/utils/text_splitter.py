import re

def split_text_into_chunks(text: str, max_length: int = 500) -> list[str]:
    """
    Divide el texto en fragmentos de tamaño máximo, respetando finales de oración.
    """
    if not text.strip():
        return []

    chunks = []
    current_pos = 0
    text_len = len(text)

    while current_pos < text_len:
        # Si el texto restante es menor que max_length, tomarlo completo
        if text_len - current_pos <= max_length:
            chunks.append(text[current_pos:])
            break
        
        # Buscar el mejor punto de división
        chunk_candidate = text[current_pos : current_pos + max_length]
        
        # Buscar finales de oración o párrafos
        delimiters = ['\n\n', '. ', '.\n', '! ', '!\n', '? ', '?\n']
        last_break = -1
        
        for delim in delimiters:
            pos = chunk_candidate.rfind(delim)
            if pos != -1 and pos > max_length // 3:  # Solo si el chunk resultante es razonable
                last_break = pos + len(delim)
                break
        
        # Si no se encontró delimitador, buscar el último espacio
        if last_break == -1:
            pos = chunk_candidate.rfind(' ')
            if pos != -1 and pos > max_length // 3:
                last_break = pos + 1
        
        # Dividir el texto
        if last_break != -1:
            chunks.append(text[current_pos : current_pos + last_break])
            current_pos += last_break
        else:
            # Fallback: tomar exactamente max_length caracteres
            chunks.append(text[current_pos : current_pos + max_length])
            current_pos += max_length

    return [chunk.strip() for chunk in chunks if chunk.strip()]