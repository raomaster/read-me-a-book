from tts_wrapper import TTSWrapper

if __name__ == "__main__":
    voice = "samples/spanish_sample.wav" # "random" for tortoise
    tts = TTSWrapper(engine="coqui", voice="samples/spanish_sample.wav", preset="fast")
    # Input text to be converted to audio
    # text = "Hola, esta es una narración de prueba generada por el proyecto read-me-a-book utilizando Tortoise TTS en español."
    text = "Hola, soy Nicole, tengo 4 años y hoy me toca terapia ocupacional con la tia liss y despues ire al colegio como la niña feliz y ordenada que soy."
    output_path = "../assets/output/intro.wav"

    # Generate audio from the input text
    tts.generate_audio(text, output_path)