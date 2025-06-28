import asyncio
import edge_tts

async def tts():
    text = """
    —¡Veinte grados más a babor! —exclamó en voz alta el teniente de guardia en el puente de mando de la corbeta General Baquedano.
    —¡Veinte grados más a babor! —repitió, como un eco, el timonel, mientras sus callosas manos daban vigorosas vueltas a las cabillas de la rueda del timón.
    Una ráfaga del noroeste recostó a la nave hasta hundirle la escoba de babor entre las grandes olas, cuyos negros lomos pasaban rodando hacia la oscuridad de la noche;
    el ulular del viento aumentó entre las jarcias, el velamen hizo crujir la envergadura, y el esbelto buque—escuela de la Armada de Chile, blanco como un albatros, puso proa
    rumbo al sur, empujado a doce millas por hora por la noroestada que pegaba por la aleta de estribor.
    """

    # para conocer las voces edge-tts --list-voices | findstr "es-"
    communicate = edge_tts.Communicate(text=text, voice="es-CL-CatalinaNeural")
    await communicate.save("voz.mp3")

asyncio.run(tts())