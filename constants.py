# constants.py

# Dicionário de prefixos de unidades.
PREFIX_DIVISORS = { 
    'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3, 'K': 1e3, 
    'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9, 'p': 1e-12 
}

# Constante 1: A lista completa para a interface, baseada na sua lista.
# Esta é a lista que será usada no ComboBox.
UNIDADES_PARA_DROPDOWN = ["", "e", "C", "N/C", "S", "V", "A", "Ω", "W", "kWh", "F", "H", "Hz", "s", "m", "g", "kg", "N", "J"]

# Constante 2: Um conjunto (set) de unidades BASE para a lógica do motor.
# Derivamos esta lista da sua, pegando apenas as unidades que podem receber prefixos.
# Usamos um set para buscas mais rápidas.
VALID_BASE_UNITS = {
    # Unidades Elétricas
    'V',  # Volt
    'A',  # Ampere
    'W',  # Watt
    'F',  # Farad
    'H',  # Henry
    'Hz', # Hertz
    'Ω',  # Ohm
    'C',  # Coulomb
    'S',  # Siemens
    
    # Unidades Físicas Comuns
    's',  # segundo
    'm',  # metro
    'g',  # grama
    'N',  # Newton
    'J',  # Joule
    'Pa'  # Pascal
}