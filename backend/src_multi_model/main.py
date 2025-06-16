from tts_wrapper import TTSWrapper

if __name__ == "__main__":
    voice = "samples/spanish_sample.wav" # "random" for tortoise
    tts = TTSWrapper(engine="coqui-modern", voice="samples/spanish_sample.wav", preset="fast")
    # Input text to be converted to audio
    # text = "Hola, esta es una narración de prueba generada por el proyecto read-me-a-book utilizando Tortoise TTS en español."
    # text = "Hola, soy una princesa. Tengo cuatro años y hoy me toca terapia ocupacional con la tía Liss. Después, iré al colegio como la niña feliz y ordenada que soy."

    text = """
     —¡Veinte	grados	más	a	babor!	—exclamó	en	voz	alta	el	teniente	de	guardia	en	el
 puente	de	mando	de	la	corbeta	General	Baquedano.
 —¡Veinte	grados	más	a	babor!	—repitió,	como	un	eco,	el	timonel,	mientras	sus
 callosas	manos	daban	vigorosas	vueltas	a	las	cabillas	de	la	rueda	del	timón.
 Una	ráfaga	del	noroeste	recostó	a	la	nave	hasta	hundirle	la	escoba	de	babor	entre
 las	grandes	olas,	cuyos	negros	lomos	pasaban	rodando	hacia	la	oscuridad	de	la	noche;
 el	ulular	del	viento	aumentó	entre	las	jarcias,	el	velamen	hizo	crujir	la	envergadura,	y
 el	esbelto	buque—escuela	de	la	Armada	de	Chile,	blanco	como	un	albatros,	puso	proa
 rumbo	al	sur,	empujado	a	doce	millas	por	hora	por	la	noroestada	que	pegaba	por	la
 aleta	de	estribor.
    """
    output_path = "../assets/output/test.wav"

    # Generate audio from the input text
    tts.generate_audio(text, output_path)