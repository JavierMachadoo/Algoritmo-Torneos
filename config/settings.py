import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_super_segura_aqui_123')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Franjas horarias exactas del formulario de Google Forms
FRANJAS_HORARIAS = [
    "Jueves 18:00",      # Jueves 18:00 a 21:00
    "Jueves 20:00",      # Jueves 20:00 a 23:00
    "Viernes 18:00",     # Viernes 18:00 a 21:00
    "Viernes 21:00",     # Viernes 21:00 a 00:00
    "Sábado 09:00",      # Sábado 9:00 a 12:00
    "Sábado 12:00",      # Sábado 12:00 a 15:00
    "Sábado 16:00",      # Sábado 16:00 a 19:00
    "Sábado 19:00"       # Sábado 19:00 a 22:00
]

CATEGORIAS = ["Cuarta", "Quinta", "Sexta", "Séptima"]

COLORES_CATEGORIA = {
    "Cuarta": "#28a745",
    "Quinta": "#ffc107",
    "Sexta": "#007bff",
    "Séptima": "#6f42c1"
}

EMOJI_CATEGORIA = {
    "Cuarta": "🟢",
    "Quinta": "🟡",
    "Sexta": "🔵",
    "Séptima": "🟣"
}

NUM_CANCHAS_DEFAULT = 2
DURACION_PARTIDO_DEFAULT = 1

# Horarios por día según las franjas del formulario
HORARIOS_POR_DIA = {
    'Jueves': ['18:00', '19:00', '20:00', '21:00', '22:00'],
    'Viernes': ['18:00', '19:00', '20:00', '21:00', '22:00', '23:00'],
    'Sábado': ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', 
               '16:00', '17:00', '18:00', '19:00', '20:00', '21:00']
}
