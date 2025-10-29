# 🏗️ Arquitectura del Proyecto

## 📐 Diseño General

El proyecto sigue una arquitectura modular basada en capas:

```
┌─────────────────────────────────────┐
│         Web Interface               │
│    (Flask + Bootstrap + JS)         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│         API Layer                   │
│    (REST endpoints)                 │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│       Business Logic                │
│    (Algoritmo + Models)             │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│         Utilities                   │
│  (CSV, Export, Google Sheets)       │
└─────────────────────────────────────┘
```

## 📦 Módulos Principales

### 1. Core (`core/`)

Contiene la lógica de negocio principal.

#### `models.py`
- **Pareja**: Representa una pareja de jugadores
- **Grupo**: Representa un grupo de 3 parejas
- **ResultadoAlgoritmo**: Encapsula el resultado completo

```python
@dataclass
class Pareja:
    id: int
    nombre: str
    telefono: str
    categoria: str
    franjas_disponibles: List[str]
```

#### `algoritmo.py`
- **AlgoritmoGrupos**: Clase principal del algoritmo
- Métodos:
  - `ejecutar()`: Ejecuta el algoritmo completo
  - `_formar_grupos_categoria()`: Agrupa por categoría
  - `_calcular_compatibilidad()`: Calcula score de compatibilidad

**Complejidad:** O(n³) para combinaciones + O(n) para iteraciones

### 2. API (`api/`)

Endpoints REST para la aplicación web.

#### `routes/parejas.py`
- `POST /api/cargar-csv`: Importar desde CSV
- `POST /api/agregar-pareja`: Agregar manualmente
- `DELETE /api/eliminar-pareja/<id>`: Eliminar pareja
- `POST /api/ejecutar-algoritmo`: Ejecutar algoritmo
- `POST /api/limpiar-datos`: Limpiar sesión

**Patrón:** Blueprint de Flask para modularidad

### 3. Utils (`utils/`)

Utilidades y servicios auxiliares.

#### `csv_processor.py`
Procesa archivos CSV y DataFrames de pandas.

#### `calendario_builder.py`
Construye el calendario de partidos asignando:
- Días
- Horarios específicos
- Canchas disponibles

#### `exportador.py`
Exporta datos a múltiples formatos:
- JSON
- CSV
- Google Sheets

#### `google_sheets_integration.py`
Integración completa con Google Sheets API:
- Importar desde Forms
- Exportar resultados
- Formatear hojas

### 4. Web (`web/`)

Interfaz de usuario.

#### `templates/`
Plantillas HTML con Jinja2:
- `base.html`: Template base
- `inicio.html`: Página principal
- `datos.html`: Gestión de parejas
- `resultados.html`: Visualización de resultados

#### `static/`
Recursos estáticos:
- `css/style.css`: Estilos personalizados
- `js/app.js`: Lógica del cliente (refactorizado)

### 5. Config (`config/`)

Configuración centralizada.

#### `settings.py`
- Constantes del sistema
- Franjas horarias
- Categorías
- Configuración de Flask

## 🔄 Flujo de Datos

### Flujo de Importación

```
CSV/Google Form
      ↓
CSVProcessor.procesar_dataframe()
      ↓
List[Dict] → parejas
      ↓
Session Storage
```

### Flujo del Algoritmo

```
List[Pareja]
      ↓
AlgoritmoGrupos.ejecutar()
      ↓
├─ _separar_por_categoria()
│       ↓
├─ _formar_grupos_categoria()
│   ├─ Generar combinaciones (3 parejas)
│   ├─ _calcular_compatibilidad()
│   └─ _crear_grupo()
│       ↓
├─ _generar_calendario()
│       ↓
└─ ResultadoAlgoritmo
      ↓
JSON serializable
      ↓
Session Storage
```

### Flujo de Exportación

```
ResultadoAlgoritmo
      ↓
DataExporter / GoogleSheetsIntegration
      ↓
Archivo (CSV/JSON) / Google Sheet
```

## 🎨 Patrones de Diseño

### 1. Factory Pattern
```python
Pareja.from_dict(data)
```

### 2. Builder Pattern
```python
CalendarioBuilder(num_canchas=2).organizar_partidos(resultado)
```

### 3. Strategy Pattern
El algoritmo usa diferentes estrategias de compatibilidad según el score.

### 4. Repository Pattern
Session de Flask actúa como repositorio temporal.

## 🔐 Gestión de Estado

### Server-Side
- **Flask Session**: Almacena parejas y resultados
- **Filesystem**: Guarda sesiones en `flask_session/`

### Client-Side
- **LocalStorage**: Podría usarse para preferencias (futuro)
- **AJAX**: Comunicación asíncrona con API

## 📊 Modelo de Datos

### Diagrama Entidad-Relación

```
┌─────────────┐
│   Pareja    │
├─────────────┤
│ + id        │
│ + nombre    │
│ + telefono  │
│ + categoria │
│ + franjas[] │
└──────┬──────┘
       │ 0..1
       │
       │ 3
┌──────▼──────┐
│    Grupo    │
├─────────────┤
│ + id        │
│ + categoria │
│ + franja    │
│ + parejas[] │
│ + partidos[]│
│ + score     │
└─────────────┘
```

## 🚀 Performance

### Optimizaciones Implementadas

1. **Algoritmo Greedy**: O(n³) pero termina rápido con podas
2. **Session Cache**: Evita recálculos innecesarios
3. **Lazy Loading**: Templates cargan recursos bajo demanda
4. **Conjunto en vez de Lista**: Para búsquedas de parejas disponibles

### Escalabilidad

- **Límite actual**: ~200 parejas (procesamiento < 5s)
- **Límite teórico**: ~500 parejas (requiere optimización)
- **Mejora futura**: Algoritmo genético para > 500 parejas

## 🧪 Testing

### Estrategia de Tests

```
tests/
├── test_models.py          # Tests unitarios de modelos
├── test_algoritmo.py       # Tests del algoritmo
├── test_api.py             # Tests de endpoints
└── test_utils.py           # Tests de utilidades
```

### Coverage Objetivo
- Core: 90%+
- API: 85%+
- Utils: 80%+

## 🔮 Extensibilidad

### Agregar Nueva Categoría

1. Editar `config/settings.py`:
```python
CATEGORIAS = ["Cuarta", "Quinta", "Sexta", "Séptima", "Octava"]
```

2. Agregar color:
```python
COLORES_CATEGORIA = {
    ...
    "Octava": "#ff6b6b"
}
```

### Agregar Nueva Franja

1. Editar `config/settings.py`:
```python
FRANJAS_HORARIAS = [
    ...
    "Domingo 10:00"
]
```

2. Actualizar `HORARIOS_POR_DIA` si es necesario.

### Agregar Nuevo Endpoint

1. Crear en `api/routes/`:
```python
@api_bp.route('/nueva-ruta', methods=['POST'])
def nueva_funcionalidad():
    pass
```

## 📚 Dependencias Externas

### Producción
- **Flask**: Framework web
- **pandas**: Procesamiento de datos
- **gspread**: Google Sheets API
- **google-auth**: Autenticación Google

### Desarrollo
- **pytest**: Testing
- **black**: Code formatter
- **flake8**: Linter

## 🔒 Seguridad

### Implementado
- Secret key para sesiones
- Validación de inputs
- Sanitización de archivos CSV

### Por Implementar
- CSRF protection
- Rate limiting
- Autenticación de usuarios
- Encriptación de datos sensibles

---

**Última actualización:** Octubre 2025
