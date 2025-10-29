# Algoritmo de Torneos de Pádel

Sistema para organizar torneos de pádel con agrupación automática por categoría y disponibilidad horaria.

## Instalación

```bash
git clone https://github.com/JavierMachadoo/Algoritmo-Torneos.git
cd Algoritmo-Torneos
pip install -r requirements.txt
python main.py
```

Accede a `http://localhost:5000`

## Estructura del Proyecto

```
Algoritmo-Torneos/
├── main.py                    # Aplicación Flask principal
├── config/
│   └── settings.py            # Configuración y constantes
├── core/
│   ├── models.py              # Modelos: Pareja, Grupo, ResultadoAlgoritmo
│   └── algoritmo.py           # Lógica de agrupación
├── api/
│   └── routes/
│       └── parejas.py         # Endpoints REST
├── utils/
│   ├── csv_processor.py       # Procesamiento de archivos
│   ├── calendario_builder.py # Generación de calendario
│   ├── exportador.py          # Exportación CSV/JSON
│   └── google_sheets_integration.py  # Integración Google Sheets
├── web/
│   ├── templates/             # Plantillas HTML
│   └── static/                # CSS y JavaScript
└── data/                      # Datos y uploads
```

## Uso

### 1. Importar Parejas
- CSV con columnas: Nombre, Teléfono, Categoría, Franjas horarias
- Google Forms conectado a Google Sheets
- Entrada manual desde la interfaz web

### 2. Ejecutar Algoritmo
Agrupa automáticamente 3 parejas por grupo basándose en:
- Categoría (Cuarta, Quinta, Sexta, Séptima)
- Compatibilidad de franjas horarias
- Optimización para 2 canchas

### 3. Revisar Resultados
- Visualización de grupos por categoría
- Calendario con asignación de canchas
- Lista de parejas sin asignar

### 4. Exportar
- Google Sheets con formato
- CSV para análisis
- Impresión directa

## Algoritmo de Agrupación

**Sistema de Puntuación:**
- Score 3.0: Las 3 parejas comparten horario (óptimo)
- Score 2.0: 2 de 3 parejas comparten horario
- Score 0.0: Sin compatibilidad

**Proceso:**
1. Separar parejas por categoría
2. Generar combinaciones de 3 parejas
3. Calcular compatibilidad horaria
4. Seleccionar mejores grupos (greedy)
5. Asignar canchas y horarios

## Configuración

### Variables de Entorno
Crea `.env`:
```env
SECRET_KEY=tu_clave_secreta
DEBUG=True
NUM_CANCHAS_DEFAULT=2
```

### Google Sheets API
1. Crear proyecto en Google Cloud Console
2. Habilitar Google Sheets API
3. Descargar credenciales JSON
4. Guardar en `data/credentials.json`

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/cargar-csv` | Carga parejas desde CSV |
| POST | `/api/agregar-pareja` | Agrega pareja manual |
| DELETE | `/api/eliminar-pareja/<id>` | Elimina pareja |
| POST | `/api/ejecutar-algoritmo` | Genera grupos |
| POST | `/api/limpiar-datos` | Limpia sesión |

## Migración desde Versión Anterior

### Cambios de Imports
```python
# Antes
from src.algoritmo import AlgoritmoGrupos, Pareja
from src.google_sheets import GoogleSheetsManager

# Después
from core import AlgoritmoGrupos, Pareja
from utils import GoogleSheetsIntegration
from config import FRANJAS_HORARIAS, CATEGORIAS
```

### Cambios de Archivos
| Antes | Después |
|-------|---------|
| `app.py` | `main.py` |
| `src/algoritmo.py` | `core/algoritmo.py` |
| `src/google_sheets.py` | `utils/google_sheets_integration.py` |
| `static/js/main.js` | `web/static/js/app.js` |

### Migrar Templates
```powershell
# Windows PowerShell
.\migrate.ps1
```

O manualmente:
```powershell
Copy-Item -Path templates\* -Destination web\templates\ -Recurse
Copy-Item -Path static\* -Destination web\static\ -Recurse
```

## Testing

```bash
pytest tests/
```

## Desarrollo

### Instalar dependencias de desarrollo
```bash
pip install pytest black flake8
```

### Formatear código
```bash
black .
flake8 .
```

## Licencia

MIT License

## Autor

Javier Machado - [@JavierMachadoo](https://github.com/JavierMachadoo)
