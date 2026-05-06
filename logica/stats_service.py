from typing import List, Optional, Dict, Any
from bbdd.models import FormularioSemanal

class StatsService:
    """
    Servicio especializado en el análisis de datos históricos y estadísticas de atletas.
    Desacopla los cálculos matemáticos y comparativos de la interfaz gráfica.
    """

    @staticmethod
    def obtener_comparativa_formularios(formularios: List[FormularioSemanal]) -> Optional[Dict[str, Any]]:
        """
        Compara los dos últimos formularios para identificar tendencias.
        """
        if len(formularios) < 2:
            return None

        actual = formularios[0]
        anterior = formularios[1]

        metricas = {
            "Satisfacción": (actual.satisfaccion_general, anterior.satisfaccion_general),
            "Mejora (Entreno)": (actual.mejora_entrenamiento, anterior.mejora_entrenamiento),
            "Fruta": (actual.fruta_consumo, anterior.fruta_consumo),
            "Verdura": (actual.verdura_consumo, anterior.verdura_consumo),
            "P. Blanco": (actual.pescado_blanco_consumo, anterior.pescado_blanco_consumo),
            "P. Azul": (actual.pescado_azul_consumo, anterior.pescado_azul_consumo)
        }

        mejor_metrica, mejor_diff = "", -999
        peor_metrica, peor_diff = "", 999

        for nombre, (val_act, val_ant) in metricas.items():
            if val_act is None or val_ant is None:
                continue
            
            diff = val_act - val_ant
            if diff > mejor_diff:
                mejor_diff = diff
                mejor_metrica = nombre
            if diff < peor_diff:
                peor_diff = diff
                peor_metrica = nombre

        return {
            "labels": list(metricas.keys()),
            "valores_actual": [m[0] or 0 for m in metricas.values()],
            "valores_anterior": [m[1] or 0 for m in metricas.values()],
            "mejor_cambio": {"nombre": mejor_metrica, "diff": mejor_diff} if mejor_diff > 0 else None,
            "peor_cambio": {"nombre": peor_metrica, "diff": peor_diff} if peor_diff < 0 else None
        }
