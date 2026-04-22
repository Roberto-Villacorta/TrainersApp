# -*- coding: utf-8 -*-
"""
Suite de tests para ``logica/ia_service.py``.

Organización por clases:

- :class:`TestNormalizacion`         → funciones de normalización de texto.
- :class:`TestExpansorAbreviaturas`  → expansión y diagnóstico de abreviaturas.
- :class:`TestDeteccionTabla`        → heurística ``_es_tabla``.
- :class:`TestMetadatos`             → extracción de mesociclo/semana/sesión.
- :class:`TestParserSerie`           → parseo de celda ``NxPESO``.
- :class:`TestParserTabular`         → parser tabular completo.
- :class:`TestGlinerServicePublico`  → métodos públicos sin cargar modelo.
- :class:`TestGlinerServiceIntegracion` → flujo completo con texto tabular real.
- :class:`TestGlinerServiceModelo`   → tests con modelo neuronal real (``@pytest.mark.slow``).

Uso rápido (sin modelo, sin red)::

    pytest tests/test_ia_service.py -m "not slow" -v

Uso completo (requiere modelo GLiNER descargado)::

    pytest tests/test_ia_service.py -v
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Asegurar que el raíz del proyecto esté en el path de importación
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logica.ia_service import (
    ABREVIATURAS,
    EXPANSOR,
    THRESHOLD_DEFAULT,
    MODEL_NAME,
    ExpansorAbreviaturas,
    GlinerService,
    _quitar_acentos,
    _normalizar_texto_base,
    _normalizar_clave_abrev,
    _expandir_abreviaturas,
    _es_tabla,
    _extraer_metadatos,
    _parsear_serie,
    _split_columnas,
    _parsear_tabla,
    _normalizar_nombre_ejercicio,
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES COMPARTIDOS
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def servicio() -> GlinerService:
    """Instancia de :class:`GlinerService` sin cargar el modelo GLiNER."""
    return GlinerService()


@pytest.fixture
def texto_tabla_1() -> str:
    """OCR real: Mesociclo 9, Semana 55, Sesión 71 (formato tabulado)."""
    return (
        "Mesociclo 9\tSemana 55\tSesion 71\n"
        "Ejercicio\tRango\tSerie 1\tSerie 2\tSerie 3\tSerie 4\n"
        "P. Plan\t7-12\t3x120\t10x100\t9x100\t8x100\n"
        "Remo\t6-10\t5x120\t10x110\t9x115\t8x115\n"
        "Mat cont\t11-20\t20x42,5\t19x42,5\t\t\n"
        "T don\t8-10\t10x110\t9x110\t\t\n"
        "Elev lat\t20-25\t27x13,75\t24x13,75\t20x13,75\t\n"
        "Curl bien\t9-14\t15x17,5\t18x17,5\t1x18,75\t8x20\n"
        "Kckton\t12-15\t17x16,11\t17x15,75\t15x18,75\t"
    )


@pytest.fixture
def texto_tabla_2() -> str:
    """OCR real: Mesociclo 9, Semana 51, Sesión P1 (formato tabulado)."""
    return (
        "Mesociclo 9\tSemana 51\tSesion P1\n"
        "Ejercicio\tRango\tSerie 1\tSerie 2\tSerie 3\tSerie 4\n"
        "Ext acl\t8-10\t10x40\t10x40\t10x70\t10x47,5\n"
        "Sentadll\t1-3/5-8\t3x120\t3x125\t8x100\t\n"
        "Abductor\t11-20\t20x85\t20x85\t15x85\t8x160\n"
        "Aductor\t20-21\t21x70\t21x70\t21x70\t\n"
        "Gom\t21-30\t30x60\t30x60\t26x30\t\n"
        "Pres millo\t10-12\t8x27\t11x30\t11x30\t"
    )


# ═══════════════════════════════════════════════════════════════════
# TestNormalizacion
# ═══════════════════════════════════════════════════════════════════

class TestNormalizacion:
    """Tests para las funciones de normalización de texto."""

    # ── _quitar_acentos ──────────────────────────────────────────────────

    def test_quitar_acentos_basico(self):
        assert _quitar_acentos("músculo") == "musculo"

    def test_quitar_acentos_multiples(self):
        assert _quitar_acentos("bíceps") == "biceps"

    def test_quitar_acentos_vacio(self):
        assert _quitar_acentos("") == ""

    def test_quitar_acentos_sin_acentos(self):
        assert _quitar_acentos("press banca") == "press banca"

    def test_quitar_acentos_diéresis(self):
        assert _quitar_acentos("büro") == "buro"

    # ── _normalizar_texto_base ───────────────────────────────────────────

    def test_normalizar_none_devuelve_vacio(self):
        assert _normalizar_texto_base(None) == ""

    def test_normalizar_vacio(self):
        assert _normalizar_texto_base("") == ""

    def test_normalizar_minusculas(self):
        assert _normalizar_texto_base("Press BANCA") == "press banca"

    def test_normalizar_guion_tipografico(self):
        assert _normalizar_texto_base("7–12") == "7-12"

    def test_normalizar_guion_largo(self):
        assert _normalizar_texto_base("7—12") == "7-12"

    def test_normalizar_barra_espaciada(self):
        result = _normalizar_texto_base("a / b")
        assert result == "a/b"

    def test_normalizar_espacios_multiples(self):
        assert _normalizar_texto_base("press   banca") == "press banca"

    def test_normalizar_tabulador(self):
        assert _normalizar_texto_base("press\tbanca") == "press banca"

    def test_normalizar_strip(self):
        assert _normalizar_texto_base("  press banca  ") == "press banca"

    def test_normalizar_guion_bajo(self):
        assert _normalizar_texto_base("hip_thrust") == "hip thrust"

    # ── _normalizar_clave_abrev ──────────────────────────────────────────

    def test_normalizar_clave_punto(self):
        assert _normalizar_clave_abrev("ext. tric") == "ext tric"

    def test_normalizar_clave_guion(self):
        assert _normalizar_clave_abrev("ext-tric") == "ext tric"

    def test_normalizar_clave_barra(self):
        assert _normalizar_clave_abrev("ext/tric") == "ext tric"

    def test_normalizar_clave_espacios_extra(self):
        assert _normalizar_clave_abrev("  elev  lat  ") == "elev lat"


# ═══════════════════════════════════════════════════════════════════
# TestExpansorAbreviaturas
# ═══════════════════════════════════════════════════════════════════

class TestExpansorAbreviaturas:
    """Tests para :class:`ExpansorAbreviaturas`."""

    # ── Casos correctos ──────────────────────────────────────────────────

    def test_expandir_elev_lat(self):
        resultado = EXPANSOR.expandir("Elev lat")
        assert resultado == "elevaciones laterales"

    def test_expandir_curl_bien(self):
        resultado = EXPANSOR.expandir("curl bien")
        assert resultado == "curl predicador"

    def test_expandir_kckton(self):
        resultado = EXPANSOR.expandir("Kckton")
        assert resultado == "patada triceps"

    def test_expandir_mat_cont(self):
        resultado = EXPANSOR.expandir("mat cont")
        assert resultado == "martillo continuo"

    def test_expandir_aductor_sin_espacio(self):
        """Bug corregido: 'aductor' tenía espacio trailing en la clave."""
        resultado = EXPANSOR.expandir("Aductor")
        assert resultado == "aduccion"

    def test_expandir_pres_millo(self):
        resultado = EXPANSOR.expandir("Pres millo")
        assert resultado == "press y martillo"

    def test_expandir_martillo_nombre_completo_no_re_expande(self):
        """'martillo' como nombre completo NO debe re-expandirse a 'curl martillo'.
        La clave 'martillo' fue eliminada del diccionario para evitar re-expansión
        en cadena cuando textos ya expandidos contienen la palabra 'martillo'.
        """
        resultado = EXPANSOR.expandir("martillo")
        # 'martillo' solo debe quedar como está; no debe convertirse en 'curl martillo'
        assert resultado == "martillo"

    def test_expandir_t_don(self):
        resultado = EXPANSOR.expandir("T don")
        assert resultado == "tiron dominadas"

    def test_expandir_gom(self):
        resultado = EXPANSOR.expandir("Gom")
        assert resultado == "gemelos"

    def test_expandir_sentadll(self):
        resultado = EXPANSOR.expandir("Sentadll")
        assert resultado == "sentadilla"

    def test_expandir_p_plan(self):
        resultado = EXPANSOR.expandir("P. Plan")
        assert resultado == "press plano"

    def test_expandir_ext_acl(self):
        resultado = EXPANSOR.expandir("Ext acl")
        assert resultado == "extension acl"

    def test_expandir_abductor(self):
        resultado = EXPANSOR.expandir("Abductor")
        assert resultado == "abduccion"

    # ── Larga (más específica primero) ───────────────────────────────────

    def test_expandir_especificidad_curl_fem_tumb(self):
        """Verifica que 'curl fem tumb' no se expanda antes como 'curl fem'."""
        resultado = EXPANSOR.expandir("curl fem tumb")
        assert resultado == "curl femoral tumbado"

    def test_expandir_especificidad_elev_lat_vs_lat(self):
        resultado = EXPANSOR.expandir("elev lat 20x13,75")
        assert "elevaciones laterales" in resultado

    # ── Casos borde ──────────────────────────────────────────────────────

    def test_expandir_vacio(self):
        assert EXPANSOR.expandir("") == ""

    def test_expandir_none(self):
        assert EXPANSOR.expandir(None) == ""

    def test_expandir_sin_abreviatura(self):
        resultado = EXPANSOR.expandir("texto sin abreviatura conocida xyz123")
        assert "xyz123" in resultado

    def test_expandir_con_numeros(self):
        resultado = EXPANSOR.expandir("curl mart 3x12")
        assert "curl martillo" in resultado

    # ── diagnosticar ─────────────────────────────────────────────────────

    def test_diagnosticar_detecta_match(self):
        info = EXPANSOR.diagnosticar("Elev lat")
        assert len(info["abreviaturas_detectadas"]) > 0

    def test_diagnosticar_claves(self):
        info = EXPANSOR.diagnosticar("curl mart")
        assert "original" in info
        assert "normalizado" in info
        assert "expandido" in info
        assert "abreviaturas_detectadas" in info

    def test_diagnosticar_vacio(self):
        info = EXPANSOR.diagnosticar("")
        assert info["expandido"] == ""
        assert info["abreviaturas_detectadas"] == []

    def test_diagnosticar_expansion_correcta(self):
        info = EXPANSOR.diagnosticar("Kckton")
        assert info["expandido"] == "patada triceps"

    # ── Instancia personalizada ───────────────────────────────────────────

    def test_instancia_custom(self):
        custom = ExpansorAbreviaturas({"sq": "sentadilla"})
        assert custom.expandir("sq") == "sentadilla"

    def test_instancia_custom_clave_vacia_se_descarta(self):
        """Las claves que resulten vacías tras normalización se descartan."""
        custom = ExpansorAbreviaturas({"": "nada", "sq": "sentadilla"})
        assert len(custom.abreviaturas) == 1


# ═══════════════════════════════════════════════════════════════════
# TestDeteccionTabla
# ═══════════════════════════════════════════════════════════════════

class TestDeteccionTabla:
    """Tests para :func:`_es_tabla`."""

    def test_tabla_con_tabs(self):
        texto = "Ejercicio\tRango\tSerie 1\nPress Banca\t7-12\t10x80"
        assert _es_tabla(texto) is True

    def test_tabla_con_espaciado_doble(self):
        texto = "Press Banca  7-12  10x80\nRemo  6-10  8x110"
        assert _es_tabla(texto) is True

    def test_no_tabla_texto_libre(self):
        texto = "Haz 3 series de press banca con 80 kg y descansa 2 minutos"
        assert _es_tabla(texto) is False

    def test_no_tabla_una_linea_con_tabs(self):
        """Una sola línea no es suficiente para ser tabla."""
        texto = "Ejercicio\tRango\tSeries"
        assert _es_tabla(texto) is False

    def test_tabla_con_metadatos_en_primera_linea(self, texto_tabla_1):
        """La línea de metadatos (Mesociclo/Semana) no debe causar falso negativo."""
        assert _es_tabla(texto_tabla_1) is True

    def test_tabla_completa_caso_2(self, texto_tabla_2):
        assert _es_tabla(texto_tabla_2) is True

    def test_vacio_devuelve_false(self):
        assert _es_tabla("") is False
        assert _es_tabla("   ") is False

    def test_una_sola_linea_con_espacios_devuelve_false(self):
        assert _es_tabla("Press Banca  7-12") is False


# ═══════════════════════════════════════════════════════════════════
# TestMetadatos
# ═══════════════════════════════════════════════════════════════════

class TestMetadatos:
    """Tests para :func:`_extraer_metadatos`."""

    def test_extrae_los_tres_campos(self):
        texto = "Mesociclo 9\tSemana 55\tSesion 71"
        meta = _extraer_metadatos(texto)
        assert meta["mesociclo"] == "9"
        assert meta["semana"] == "55"
        assert meta["sesion"] == "71"

    def test_sesion_alfanumerica(self):
        texto = "Mesociclo 9\tSemana 51\tSesion P1"
        meta = _extraer_metadatos(texto)
        assert meta["sesion"] == "p1"

    def test_sin_metadatos(self):
        texto = "Press Banca 3x10"
        meta = _extraer_metadatos(texto)
        assert meta["mesociclo"] is None
        assert meta["semana"] is None
        assert meta["sesion"] is None

    def test_solo_semana(self):
        meta = _extraer_metadatos("Semana 3")
        assert meta["semana"] == "3"
        assert meta["mesociclo"] is None

    def test_texto_vacio(self):
        meta = _extraer_metadatos("")
        assert meta == {"mesociclo": None, "semana": None, "sesion": None}

    def test_insensible_a_mayusculas(self):
        meta = _extraer_metadatos("MESOCICLO 2 SEMANA 10 SESION 5")
        assert meta["mesociclo"] == "2"
        assert meta["semana"] == "10"
        assert meta["sesion"] == "5"


# ═══════════════════════════════════════════════════════════════════
# TestParserSerie
# ═══════════════════════════════════════════════════════════════════

class TestParserSerie:
    """Tests para :func:`_parsear_serie`."""

    def test_formato_simple(self):
        resultado = _parsear_serie("10x80")
        assert resultado == {"reps": 10, "peso_kg": 80.0}

    def test_formato_coma_decimal(self):
        resultado = _parsear_serie("20x42,5")
        assert resultado == {"reps": 20, "peso_kg": 42.5}

    def test_formato_punto_decimal(self):
        resultado = _parsear_serie("10x13.75")
        assert resultado == {"reps": 10, "peso_kg": 13.75}

    def test_formato_mayuscula_x(self):
        resultado = _parsear_serie("8X100")
        assert resultado == {"reps": 8, "peso_kg": 100.0}

    def test_formato_por_unicode(self):
        resultado = _parsear_serie("5×120")
        assert resultado == {"reps": 5, "peso_kg": 120.0}

    def test_celda_vacia_devuelve_none(self):
        assert _parsear_serie("") is None
        assert _parsear_serie(None) is None

    def test_celda_guion_devuelve_none(self):
        assert _parsear_serie("—") is None
        assert _parsear_serie("-") is None

    def test_celda_malformada_devuelve_none(self):
        """Valor de peso no numérico no debe lanzar excepción."""
        assert _parsear_serie("10xabc") is None

    def test_celda_solo_numero_devuelve_none(self):
        assert _parsear_serie("10") is None

    def test_peso_grande(self):
        resultado = _parsear_serie("3x225")
        assert resultado == {"reps": 3, "peso_kg": 225.0}

    def test_peso_coma_multiples_decimales(self):
        resultado = _parsear_serie("17x16,11")
        assert resultado == {"reps": 17, "peso_kg": 16.11}


# ═══════════════════════════════════════════════════════════════════
# TestNormalizarNombreEjercicio
# ═══════════════════════════════════════════════════════════════════

class TestNormalizarNombreEjercicio:
    """Tests para :func:`_normalizar_nombre_ejercicio`."""

    def test_abreviatura_expandida_y_title(self):
        resultado = _normalizar_nombre_ejercicio("elev lat")
        assert resultado == "Elevaciones Laterales"

    def test_kckton_expandido(self):
        resultado = _normalizar_nombre_ejercicio("Kckton")
        assert resultado == "Patada Triceps"

    def test_mat_cont_expandido(self):
        resultado = _normalizar_nombre_ejercicio("Mat cont")
        assert resultado == "Martillo Continuo"

    def test_vacio_devuelve_vacio(self):
        """Bug corregido: antes podía lanzar excepción con cadena vacía."""
        assert _normalizar_nombre_ejercicio("") == ""

    def test_none_devuelve_vacio(self):
        assert _normalizar_nombre_ejercicio(None) == ""

    def test_nombre_largo_con_espacios(self):
        resultado = _normalizar_nombre_ejercicio("press   con   mancuernas")
        # No debe tener doble espacio
        assert "  " not in resultado


# ═══════════════════════════════════════════════════════════════════
# TestSplitColumnas
# ═══════════════════════════════════════════════════════════════════

class TestSplitColumnas:
    """Tests para :func:`_split_columnas`."""

    def test_split_con_tab(self):
        result = _split_columnas("Press Banca\t7-12\t10x80")
        assert result == ["Press Banca", "7-12", "10x80"]

    def test_split_con_espacios_dobles(self):
        result = _split_columnas("Sentadilla  5-8  8x120")
        assert result == ["Sentadilla", "5-8", "8x120"]

    def test_split_filtra_vacios(self):
        result = _split_columnas("\tPress Banca\t\t10x80\t")
        assert "" not in result

    def test_split_multiples_tabs(self):
        result = _split_columnas("A\t\tB\t\t\tC")
        assert result == ["A", "B", "C"]


# ═══════════════════════════════════════════════════════════════════
# TestParserTabular
# ═══════════════════════════════════════════════════════════════════

class TestParserTabular:
    """Tests para :func:`_parsear_tabla`."""

    def test_cantidad_ejercicios_tabla_1(self, texto_tabla_1):
        resultado = _parsear_tabla(texto_tabla_1)
        assert len(resultado) == 7

    def test_cantidad_ejercicios_tabla_2(self, texto_tabla_2):
        resultado = _parsear_tabla(texto_tabla_2)
        assert len(resultado) == 6

    def test_metadatos_tabla_1(self, texto_tabla_1):
        resultado = _parsear_tabla(texto_tabla_1)
        assert resultado[0]["mesociclo"] == "9"
        assert resultado[0]["semana"] == "55"
        assert resultado[0]["sesion"] == "71"

    def test_metadatos_tabla_2(self, texto_tabla_2):
        resultado = _parsear_tabla(texto_tabla_2)
        assert resultado[0]["sesion"] == "p1"

    def test_primer_ejercicio_tabla_1(self, texto_tabla_1):
        resultado = _parsear_tabla(texto_tabla_1)
        ej = resultado[0]
        assert ej["ejercicio"] == "Press Plano"   # P. Plan → press plano → Press Plano
        assert ej["rango_objetivo"] == "7-12"
        assert ej["origen"] == "tabla"

    def test_series_primer_ejercicio(self, texto_tabla_1):
        resultado = _parsear_tabla(texto_tabla_1)
        series = resultado[0]["series"]
        assert len(series) == 4
        assert series[0] == {"reps": 3, "peso_kg": 120.0}
        assert series[1] == {"reps": 10, "peso_kg": 100.0}

    def test_series_con_coma_decimal(self, texto_tabla_1):
        """Mat cont tiene peso 42,5 → debe parsearse como 42.5."""
        resultado = _parsear_tabla(texto_tabla_1)
        mat = next(r for r in resultado if "Martillo" in r["ejercicio"])
        assert mat["series"][0]["peso_kg"] == 42.5

    def test_abduccion_y_aduccion_tabla_2(self, texto_tabla_2):
        """Verifica que Abductor→abduccion y Aductor→aduccion se expandan."""
        resultado = _parsear_tabla(texto_tabla_2)
        ejercicios = [r["ejercicio"] for r in resultado]
        assert any("Abduccion" in e for e in ejercicios)
        assert any("Aduccion" in e for e in ejercicios)

    def test_gemelos_tabla_2(self, texto_tabla_2):
        resultado = _parsear_tabla(texto_tabla_2)
        ejercicios = [r["ejercicio"] for r in resultado]
        assert any("Gemelos" in e for e in ejercicios)

    def test_estructura_resultado(self, texto_tabla_1):
        resultado = _parsear_tabla(texto_tabla_1)
        for ej in resultado:
            assert "ejercicio" in ej
            assert "rango_objetivo" in ej
            assert "series" in ej
            assert "origen" in ej
            assert ej["origen"] == "tabla"

    def test_texto_vacio_devuelve_lista_vacia(self):
        assert _parsear_tabla("") == []
        assert _parsear_tabla("   ") == []

    def test_tabla_sin_cabecera(self):
        """Parser debe funcionar aunque no haya fila de cabecera."""
        texto = "Press Banca\t7-12\t10x80\t9x80\nRemo\t6-10\t8x110"
        resultado = _parsear_tabla(texto)
        assert len(resultado) == 2
        assert resultado[0]["ejercicio"] == "Press Banca"

    def test_rango_objetivo_conservado(self):
        texto = "Sentadilla\t5-8\t8x120\nPeso Muerto\t3-5\t5x140"
        resultado = _parsear_tabla(texto)
        assert resultado[0]["rango_objetivo"] == "5-8"
        assert resultado[1]["rango_objetivo"] == "3-5"

    def test_celdas_series_vacias_no_generan_error(self, texto_tabla_1):
        """Celdas vacías (tabs seguidos) no deben generar series con None."""
        resultado = _parsear_tabla(texto_tabla_1)
        for ej in resultado:
            for serie in ej["series"]:
                assert serie["reps"] is not None
                assert serie["peso_kg"] is not None


# ═══════════════════════════════════════════════════════════════════
# TestGlinerServicePublico
# ═══════════════════════════════════════════════════════════════════

class TestGlinerServicePublico:
    """Tests de los métodos públicos de :class:`GlinerService` que no cargan el modelo."""

    def test_instanciacion_por_defecto(self, servicio):
        assert servicio.threshold == THRESHOLD_DEFAULT
        assert servicio.model_name == MODEL_NAME

    def test_threshold_personalizado(self):
        s = GlinerService(threshold=0.6)
        assert s.threshold == 0.6

    def test_expandir_abreviaturas_wrapper(self, servicio):
        assert servicio.expandir_abreviaturas("Elev lat") == "elevaciones laterales"

    def test_diagnosticar_abreviaturas_wrapper(self, servicio):
        info = servicio.diagnosticar_abreviaturas("curl bien")
        assert "expandido" in info
        assert info["expandido"] == "curl predicador"

    def test_es_tabla_texto_tabulado(self, servicio, texto_tabla_1):
        assert servicio.es_tabla(texto_tabla_1) is True

    def test_es_tabla_texto_libre(self, servicio):
        assert servicio.es_tabla("Haz 3 series de curl con barra") is False

    def test_extraer_metadatos_wrapper(self, servicio):
        meta = servicio.extraer_metadatos("Mesociclo 9 Semana 55 Sesion 71")
        assert meta["mesociclo"] == "9"

    def test_parsear_tabla_wrapper(self, servicio, texto_tabla_1):
        resultado = servicio.parsear_tabla(texto_tabla_1)
        assert len(resultado) == 7

    def test_preprocesar_texto_libre_wrapper(self, servicio):
        resultado = servicio.preprocesar_texto_libre("curl mart 3x12")
        assert "repeticiones" in resultado
        assert "kg" in resultado

    def test_labels_configurados(self, servicio):
        assert "ejercicio" in servicio.labels
        assert "repeticiones" in servicio.labels
        assert "peso en kg" in servicio.labels


# ═══════════════════════════════════════════════════════════════════
# TestPreprocesadorTextoLibre
# ═══════════════════════════════════════════════════════════════════

class TestPreprocesadorTextoLibre:
    """Tests del preprocesador de texto libre (sin cargar GLiNER)."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.s = GlinerService()

    def test_convierte_nxpeso(self):
        result = self.s.preprocesar_texto_libre("curl mart 3x12")
        assert "3 repeticiones" in result
        assert "12 kg" in result

    def test_convierte_x_mayuscula(self):
        result = self.s.preprocesar_texto_libre("press banca 10X80")
        assert "repeticiones" in result

    def test_convierte_por_mano(self):
        result = self.s.preprocesar_texto_libre("curl manc 12 p/mano")
        assert "por mano" in result

    def test_convierte_segundos_comillas(self):
        result = self.s.preprocesar_texto_libre("descanso 90''")
        assert "segundos" in result

    def test_convierte_segundos_s(self):
        result = self.s.preprocesar_texto_libre("descanso 60s")
        assert "segundos" in result

    def test_vacio_devuelve_vacio(self):
        assert self.s.preprocesar_texto_libre("") == ""

    def test_expande_abreviatura_y_convierte(self):
        result = self.s.preprocesar_texto_libre("Elev lat 20x13,75")
        assert "elevaciones laterales" in result
        assert "repeticiones" in result


# ═══════════════════════════════════════════════════════════════════
# TestGlinerServiceIntegracion
# ═══════════════════════════════════════════════════════════════════

class TestGlinerServiceIntegracion:
    """Tests de integración de :class:`GlinerService` con texto tabular real.

    Estos tests verifican el flujo completo ``procesar_texto_rutina`` y
    ``procesar_texto_rutina_debug`` usando texto tabular (no requieren
    el modelo GLiNER).
    """

    def test_procesar_texto_tabular_devuelve_lista(self, servicio, texto_tabla_1):
        resultado = servicio.procesar_texto_rutina(texto_tabla_1)
        assert isinstance(resultado, list)
        assert len(resultado) > 0

    def test_procesar_texto_tabular_estructura(self, servicio, texto_tabla_1):
        resultado = servicio.procesar_texto_rutina(texto_tabla_1)
        for ej in resultado:
            assert "ejercicio" in ej
            assert "series" in ej
            assert "origen" in ej

    def test_procesar_texto_vacio_devuelve_lista_vacia(self, servicio):
        assert servicio.procesar_texto_rutina("") == []
        assert servicio.procesar_texto_rutina(None) == []
        assert servicio.procesar_texto_rutina("   ") == []

    def test_procesar_tabla_2_cantidad(self, servicio, texto_tabla_2):
        resultado = servicio.procesar_texto_rutina(texto_tabla_2)
        assert len(resultado) == 6

    def test_debug_modo_detectado_tabla(self, servicio, texto_tabla_1):
        info = servicio.procesar_texto_rutina_debug(texto_tabla_1)
        assert info["modo_detectado"] == "tabla"
        assert info["es_tabla"] is True

    def test_debug_claves_completas(self, servicio, texto_tabla_1):
        info = servicio.procesar_texto_rutina_debug(texto_tabla_1)
        claves_esperadas = {
            "entrada_original",
            "modo_detectado",
            "es_tabla",
            "metadatos",
            "texto_expandido",
            "texto_preprocesado_gliner",
            "resultado",
        }
        assert claves_esperadas.issubset(info.keys())

    def test_debug_vacio(self, servicio):
        info = servicio.procesar_texto_rutina_debug("")
        assert info["modo_detectado"] is None
        assert info["es_tabla"] is False
        assert info["resultado"] == []

    def test_debug_metadatos_en_resultado(self, servicio, texto_tabla_1):
        info = servicio.procesar_texto_rutina_debug(texto_tabla_1)
        assert info["metadatos"]["mesociclo"] == "9"

    def test_debug_modo_detectado_gliner(self, servicio):
        """Texto libre debe detectarse como modo 'gliner' (aunque no cargue modelo)."""
        texto_libre = "Haz 3 series de curl bayesian con 15 kg"
        # Sólo comprobamos la detección, no el resultado GLiNER
        with patch.object(servicio, "_procesar_texto_libre", return_value=[]):
            info = servicio.procesar_texto_rutina_debug(texto_libre)
            assert info["modo_detectado"] == "gliner"
            assert info["es_tabla"] is False


# ═══════════════════════════════════════════════════════════════════
# TestGlinerServiceModelo  (slow — requieren modelo neuronal)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestGlinerServiceModelo:
    """Tests de integración que cargan el modelo GLiNER real.

    Marcar con ``@pytest.mark.slow``. Saltar con::

        pytest -m "not slow"

    Requieren conexión a internet en la primera ejecución (descarga del modelo)
    o que el modelo ya esté cacheado en ``modelos_ia/``.
    """

    @pytest.fixture(scope="class")
    def servicio_con_modelo(self):
        """Instancia con modelo GLiNER cargado (compartida en la clase)."""
        s = GlinerService(cargar_modelo_al_inicio=True)
        return s

    def test_modelo_cargado(self, servicio_con_modelo):
        assert GlinerService._modelo is not None

    def test_texto_libre_devuelve_entidades(self, servicio_con_modelo):
        texto = "Haz 3 series de curl con barra con 40 kg y descansa 90 segundos"
        resultado = servicio_con_modelo.procesar_texto_rutina(texto)
        # Debe devolver al menos una entidad
        assert isinstance(resultado, list)
        assert len(resultado) > 0

    def test_entidades_tienen_estructura(self, servicio_con_modelo):
        texto = "Press banca 4 series de 10 repeticiones con 80 kg"
        resultado = servicio_con_modelo.procesar_texto_rutina(texto)
        for entidad in resultado:
            assert "tipo" in entidad
            assert "texto" in entidad
            assert "confianza" in entidad
            assert entidad["origen"] == "gliner"

    def test_threshold_filtra_baja_confianza(self, servicio_con_modelo):
        """Todas las entidades deben tener confianza >= threshold."""
        texto = "Press banca 3 series con 80 kg"
        resultado = servicio_con_modelo.procesar_texto_rutina(texto)
        for entidad in resultado:
            assert entidad["confianza"] >= servicio_con_modelo.threshold

    def test_debug_modo_gliner(self, servicio_con_modelo):
        texto = "Curl martillo 3 series de 12 repeticiones con 15 kg"
        info = servicio_con_modelo.procesar_texto_rutina_debug(texto)
        assert info["modo_detectado"] == "gliner"
        assert isinstance(info["resultado"], list)
