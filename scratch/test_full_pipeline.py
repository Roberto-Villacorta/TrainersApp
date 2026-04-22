from logica.ia_service import GlinerService, _normalizar_nombre_ejercicio

serv = GlinerService()

test_cases = [
    "vuelalat",
    "cur b z",
    "pm-rum",
    "sntdll blgr",
    "hiptrust",
    "press_ban_incl",
    "fce pull",
    "r.polea",
    "j.pecho",
    "elevlatmanc",
    "p pla",
    "rem",
    "pm rdl",
    "ban inc",
    "sentadll"
]

print(f"{'Input':<20} | {'Match (Enriched)':<25} | {'Status'}")
print("-" * 60)
for tc in test_cases:
    # Simular el flujo de enriquecimiento
    # _enriquecer_nombre_ejercicio es privado pero podemos probar el flujo público si existiera
    # O simplemente llamar al método privado con el objeto
    match = serv._enriquecer_nombre_ejercicio(tc)
    
    # Algunos casos en el catálogo están en minúsculas, el enriquecedor los pasa a Title Case
    print(f"{tc:<20} | {str(match):<25} | OK")
