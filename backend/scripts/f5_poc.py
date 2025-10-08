from f5_tts import F5TTS
import torch

def main():
    # Inicializar el dispositivo (GPU si está disponible)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando dispositivo: {device}")
    
    # Inicializar el modelo
    model = F5TTS(device=device)
    
    # Texto de prueba
    text = "Hola, esto es una prueba de F5 TTS en español."
    
    # Generar audio
    print("Generando audio...")
    audio = model.generate(
        text=text,
        language="es",
        speed=1.0
    )
    
    # Guardar el audio
    output_file = "prueba_tts.wav"
    import soundfile as sf
    sf.write(output_file, audio, 22050)
    print(f"¡Audio guardado como {output_file}!")

if __name__ == "__main__":
    main()