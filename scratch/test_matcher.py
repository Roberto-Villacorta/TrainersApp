from logica.ia_service import _buscar_mejor_coincidencia_semantica, EJERCICIOS_CANONICOS

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
    "rem"
]

print(f"{'Input':<20} | {'Match':<25} | {'Status'}")
print("-" * 60)
for tc in test_cases:
    match = _buscar_mejor_coincidencia_semantica(tc)
    status = "OK" if match else "FAIL"
    print(f"{tc:<20} | {str(match):<25} | {status}")
