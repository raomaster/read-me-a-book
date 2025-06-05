# script para comparar modelos TTS para el proyecto read-me-a-book (lector de libros en español)

import json
import subprocess

def comparar_modelos_tts_espanol():
    """
    Compara modelos TTS que soportan español, enfocándose en la naturalidad de la voz
    para un proyecto de lector de libros (read-me-a-book), y considerando la
    compatibilidad con DirectML o CPU.
    """
    print("Comparando modelos TTS para el proyecto read-me-a-book (lector de libros en español)...")

    comparativa_modelos = [
        {
            "nombre": "Mozilla TTS",
            "soporte_espanol": "Sí, varios modelos pre-entrenados en español de alta calidad.",
            "naturalidad_voz": "Generalmente alta, con opciones de voces más naturales que otros modelos.",
            "compatibilidad_directml": "Potencialmente a través de ONNX Runtime. Requiere investigación y configuración. La optimización para DirectML puede ser limitada.",
            "compatibilidad_cpu": "Sí, funciona bien en CPU. Puede requerir ajustes para un rendimiento óptimo.",
            "pros": [
                "Buena calidad de voz en español.",
                "Proyecto de código abierto con comunidad activa.",
                "Variedad de modelos y voces disponibles.",
                "Potencial para personalización y fine-tuning."
            ],
            "contras": [
                "La implementación con ONNX Runtime para DirectML puede ser compleja.",
                "El uso en CPU para textos largos puede consumir recursos.",
                "La configuración inicial puede requerir algo de experiencia."
            ]
        },
        {
            "nombre": "Coqui TTS (fork de Mozilla TTS)",
            "soporte_espanol": "Sí, hereda los modelos de Mozilla TTS y puede tener modelos adicionales con mejoras.",
            "naturalidad_voz": "Similar a Mozilla TTS, potencialmente con mejoras en algunos modelos.",
            "compatibilidad_directml": "Potencialmente a través de ONNX Runtime. Requiere investigación y configuración.",
            "compatibilidad_cpu": "Sí, similar a Mozilla TTS.",
            "pros": [
                "Se beneficia de las mejoras y la continuación del proyecto Mozilla TTS.",
                "Buena calidad de voz en español.",
                "Comunidad activa.",
                "Potencialmente más fácil de usar en algunas áreas."
            ],
            "contras": [
                "Al igual que Mozilla TTS, la implementación con DirectML puede ser compleja.",
                "Rendimiento en CPU similar a Mozilla TTS."
            ]
        },
        {
            "nombre": "Espeak-ng",
            "soporte_espanol": "Sí, soporta español.",
            "naturalidad_voz": "Baja en comparación con modelos modernos basados en deep learning. Suena más robótico.",
            "compatibilidad_directml": "Soporte limitado o nulo. Principalmente CPU.",
            "compatibilidad_cpu": "Sí, ligero y funciona bien en CPU con bajo consumo de recursos.",
            "pros": [
                "Ligero y fácil de instalar.",
                "Bajo consumo de recursos en CPU."
            ],
            "contras": [
                "Baja calidad y naturalidad de la voz, no ideal para lectura de libros.",
                "Opciones de personalización limitadas."
            ]
        },
        {
            "nombre": "Vosk TTS",
            "soporte_espanol": "Sí, a través de modelos Kaldi.",
            "naturalidad_voz": "Puede variar dependiendo del modelo Kaldi utilizado. Algunos modelos pueden tener una naturalidad aceptable, pero generalmente no al nivel de Mozilla/Coqui TTS.",
            "compatibilidad_directml": "Potencialmente a través de ONNX Runtime. Requiere investigación y configuración.",
            "compatibilidad_cpu": "Sí.",
            "pros": [
                "Enfocado en ser ligero y rápido.",
                "Soporte para varios idiomas."
            ],
            "contras": [
                "La naturalidad de la voz puede no ser la mejor para lectura de libros.",
                "La configuración y el uso de modelos Kaldi pueden tener una curva de aprendizaje."
            ]
        },
        {
            "nombre": "Modelos en Hugging Face Hub",
            "soporte_espanol": "Sí, existen varios modelos TTS pre-entrenados en español.",
            "naturalidad_voz": "Varía significativamente dependiendo del modelo. Algunos pueden ofrecer una naturalidad muy alta.",
            "compatibilidad_directml": "Potencialmente si el modelo puede ser exportado a ONNX y ONNX Runtime soporta las operaciones del modelo en DirectML.",
            "compatibilidad_cpu": "Sí, la mayoría de los modelos pueden ejecutarse en CPU.",
            "pros": [
                "Gran variedad de modelos disponibles, con diferentes arquitecturas y calidades de voz.",
                "Potencial para encontrar modelos muy naturales."
            ],
            "contras": [
                "Requiere una investigación exhaustiva para encontrar modelos adecuados y bien documentados.",
                "La implementación y configuración pueden ser más complejas.",
                "La compatibilidad con DirectML a través de ONNX no está garantizada y puede requerir experimentación."
            ]
        }
    ]

    print(json.dumps(comparativa_modelos, indent=4, ensure_ascii=False))
    print("\nRecomendaciones para el proyecto read-me-a-book:")
    print("- **Priorizar la naturalidad de la voz:** Dado que el proyecto es un lector de libros, la naturalidad de la voz es crucial para una buena experiencia del usuario.")
    print("- **Mozilla TTS o Coqui TTS:** Estos modelos son los más recomendables como punto de partida debido a su buena calidad de voz en español y su activa comunidad.")
    print("- **Explorar Hugging Face Hub:** Dedica tiempo a buscar modelos TTS en español en Hugging Face Hub. Algunos modelos más recientes podrían ofrecer una naturalidad aún mayor.")
    print("- **Considerar la compatibilidad con DirectML como un objetivo secundario:** Dada la posible complejidad de usar ONNX Runtime y la incertidumbre del soporte optimizado, enfócate primero en lograr una buena calidad de voz en CPU con Mozilla TTS o un modelo de Hugging Face.")
    print("- **Prototipar y evaluar:** Implementa prototipos con los modelos más prometedores y evalúa la calidad de la voz en textos largos para asegurar una buena experiencia de lectura.")

if __name__ == "__main__":
    comparar_modelos_tts_espanol()