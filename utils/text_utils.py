import unicodedata
import re

def quitar_acentos(texto: str) -> str:
    """
    Elimina diacríticos (acentos, tildes, diéresis) de una cadena Unicode.
    """
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def normalizar_texto_base(texto: str) -> str:
    """
    Normaliza un texto para comparaciones y búsquedas robustas.
    Elimina acentos, pasa a minúsculas y colapsa espacios.
    """
    if not texto:
        return ""

    texto = texto.lower()
    texto = quitar_acentos(texto)

    texto = texto.replace("_", " ")
    # Limpieza de ruidos de unión comunes (puntos, guiones, barras bajas entre letras)
    texto = re.sub(r"(?<=[a-z])[\._\-](?=[a-z])", " ", texto)
    
    texto = texto.replace("–", "-")   # dash
    texto = texto.replace("—", "-")   # em dash
    texto = texto.replace("/", " / ")

    texto = re.sub(r"[ \t]+", " ", texto)
    # Colapsar espacios alrededor de separadores comunes
    texto = re.sub(r"\s*\.\s*", ".", texto)
    texto = re.sub(r"\s*-\s*", "-", texto)
    texto = re.sub(r"\s*/\s*", "/", texto)

    return texto.strip()
