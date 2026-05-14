import re
from typing import List, Dict, Any
from utils.text_utils import normalizar_texto_base

# ─────────────────────────────────────────────────────────────────
# Catálogo de Ejercicios Canónicos
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# Catálogo de Ejercicios por Grupo Muscular
# ─────────────────────────────────────────────────────────────────

EJERCICIOS_POR_MUSCULO: Dict[str, List[str]] = {
    "Pecho": [
        "press plano", "press inclinado", "press declinado", "press banca",
        "press con mancuernas", "aperturas", "aperturas con mancuernas",
        "cruce en polea", "fondos", "peck deck", "press hammer"
    ],
    "Espalda": [
        "dominadas", "dominadas supinas", "dominadas pronas", "dominadas neutras",
        "jalon al pecho", "jalon tras nuca", "remo", "remo con mancuernas",
        "remo con barra", "remo en polea", "remo en t", "pullover", "tiron dominadas",
        "remo horizontal", "remo pendlay", "remo unipolar", "lumbares",
        "tiron al pecho", "tiron polea", "tiron", "remo", "jalon"
    ],
    "Hombro": [
        "elevaciones laterales", "elevaciones frontales", "elevaciones posteriores",
        "vuelos laterales", "vuelos frontales", "vuelos posteriores",
        "pajaro", "face pull", "press hombro", "press militar", "press arnold",
        "encogimientos", "press tras nuca", "upright row", "jalon en polea"
    ],
    "Pierna": [
        "sentadilla", "sentadilla trasera", "sentadilla frontal", "sentadilla bulgara",
        "zancadas", "prensa", "extension cuadriceps", "curl femoral",
        "curl femoral tumbado", "curl femoral sentado", "hip thrust", "puente gluteo",
        "abduccion", "aduccion", "gemelos", "elevaciones de gemelos",
        "peso muerto", "peso muerto convencional", "peso muerto sumo",
        "peso muerto rumano", "hack squat", "leg press", "step up", "glute bridge",
        "sentadilla hack", "zancada", "elevacion de talones"
    ],
    "Brazos": [
        "curl", "curl con barra", "curl con barra z", "curl con mancuernas",
        "curl martillo", "martillo continuo", "curl predicador", "curl concentrado",
        "curl bayesian", "extensiones triceps", "extensiones triceps cuerda",
        "extensiones triceps polea", "extensiones trasnuca", "press cerrado",
        "patada triceps", "dips", "skullcrushers", "frances", "curl araña",
        "press frances", "jalon de triceps"
    ],
    "Core / Otros": [
        "abdominales", "crunch", "plancha", "elevaciones de piernas", "ab wheel",
        "descanso", "burpees", "jumping jacks"
    ],
    "Cardio": [
        "cinta", "bicicleta", "remo ergometro", "eliptica", "natacion", "correr"
    ],
    "HIIT": [
        "burpees", "jumping jacks", "mountain climbers", "skipping", "battle ropes", 
        "sprints", "box jumps", "kettlebell swings", "hiit sesión"
    ]
}

# Lista plana para compatibilidad con el Mapper
EJERCICIOS_CANONICOS: List[str] = [item for sublist in EJERCICIOS_POR_MUSCULO.values() for item in sublist]

# ─────────────────────────────────────────────────────────────────
# DICCIONARIO DE ABREVIATURAS
# ─────────────────────────────────────────────────────────────────

ABREVIATURAS: Dict[str, str] = {
    # Press / Pecho
    "press inc": "press inclinado", "p inc": "press inclinado", "p incl": "press inclinado",
    "ban inc": "press inclinado", "ban incl": "press inclinado", "p plano": "press plano",
    "p plan": "press plano", "p pla": "press plano", "press plan": "press plano",
    "p decl": "press declinado", "press banca": "press banca", "pb": "press banca",
    "press manc": "press con mancuernas", "p manc": "press con mancuernas",
    "apert": "aperturas", "apert manc": "aperturas con mancuernas",
    # Hombro
    "elev lat": "elevaciones laterales", "elev. lat": "elevaciones laterales",
    "elev front": "elevaciones frontales", "elev post": "elevaciones posteriores",
    "vuelos lat": "elevaciones laterales", "pajaro": "pajaro", "face pull": "face pull",
    "press militar": "press militar", "militar": "press militar",
    # Espalda
    "dom": "dominadas", "jal pech": "jalon al pecho", "jalon": "jalon",
    "remo barra": "remo con barra", "remo polea": "remo en polea", "pullover": "pullover",
    # Brazos
    "curl z": "curl con barra z", "curl manc": "curl con mancuernas", "martillo": "curl martillo",
    "ext triceps": "extensiones triceps", "ext tras": "extensiones trasnuca", "press cerr": "press cerrado",
    # Pierna
    "sentadilla": "sentadilla", "sent bulg": "sentadilla bulgara", "prensa": "prensa",
    "ext cuad": "extension cuadriceps", "curl fem": "curl femoral", "ht": "hip thrust",
    "pm": "peso muerto", "pm rum": "peso muerto rumano", "rdl": "peso muerto rumano",
    # Otros
    "abs": "abdominales", "desc": "descanso", "reps": "repeticiones", "ser": "series"
}

def _normalizar_clave_abrev(clave: str) -> str:
    clave = normalizar_texto_base(clave)
    clave = clave.replace(".", " ").replace("-", " ").replace("/", " ")
    return re.sub(r"\s+", " ", clave).strip()

class ExpansorAbreviaturas:
    def __init__(self, abreviaturas: Dict[str, str]) -> None:
        self.abreviaturas = self._normalizar_diccionario(abreviaturas)
        self.patrones = self._compilar_patrones()

    def _normalizar_diccionario(self, abreviaturas: Dict[str, str]) -> Dict[str, str]:
        normalizadas: Dict[str, str] = {}
        for clave, valor in abreviaturas.items():
            k = _normalizar_clave_abrev(clave)
            v = normalizar_texto_base(valor)
            if k: normalizadas[k] = v
        return normalizadas

    def _compilar_patrones(self) -> List[tuple]:
        items = sorted(self.abreviaturas.items(), key=lambda x: len(x[0]), reverse=True)
        patrones = []
        for clave, expansion in items:
            tokens = [re.escape(t) for t in clave.split()]
            separador = r"[\s\.\-\/_]*"
            patron = f"(?<!\\w){separador.join(tokens)}(?!\\w)"
            patrones.append((re.compile(patron, flags=re.IGNORECASE), expansion))
        return patrones

    def expandir(self, texto: str) -> str:
        if not texto: return ""
        texto_norm = normalizar_texto_base(texto)
        for patron, expansion in self.patrones:
            texto_norm = patron.sub(expansion, texto_norm)
        return re.sub(r"\s+", " ", texto_norm).strip()
