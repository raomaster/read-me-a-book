import pyttsx3

# Inicializa la biblioteca
engine = pyttsx3.init()

# Obtiene la lista de voces disponibles
voces = engine.getProperty('voices')

# Imprime la lista de voces
for voz in voces:
    print(voz.id, voz.name)

# Configura la voz y el idioma
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ES-MX_SABINA_11.0 Microsoft Sabina Desktop - Spanish (Mexico)')

# Define el texto a leer
texto = """
¡Rumbo al sur! —¡Veinte grados más a babor! —exclamó en voz alta el teniente de guardia en el puente de mando de la corbeta General Baquedano. —¡Veinte grados más a babor! —repitió, como un eco, el timonel, mientras sus callosas manos daban vigorosas vueltas a las cabillas de la rueda del timón. Una ráfaga del noroeste recostó a la nave hasta hundirle la escoba de babor entre las grandes olas, cuyos negros lomos pasaban rodando hacia la oscuridad de la noche; el ulular del viento aumentó entre las jarcias, el velamen hizo crujir la envergadura, y el esbelto buque—escuela de la Armada de Chile, blanco como un albatros, puso proa rumbo al sur, empujado a doce millas por hora por la noroestada que pegaba por la aleta de estribor. Era el último viaje de este hermoso barco.
"""

# Lee el texto
engine.say(texto)

# Reproduce el audio
engine.runAndWait()