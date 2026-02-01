# Skill: Python Flask MVC

### Metadata
- **Name:** `python-flask-mvc`
- **Description:** Patrones MVC + Service Layer
- **Trigger:** Modificar api/routes/*, crear endpoints
- **Scope:** `backend`

## 🎯 Objetivo
Asegurar que el código siga los patrones arquitectónicos del proyecto: MVC con Service Layer, evitando acoplamiento y manteniendo separación de concerns.

## 🔔 Triggers de Auto-invocación
El agente debe activar esta skill cuando:
- Se modifiquen archivos en `api/routes/`
- Se editen archivos en `core/` (algoritmo, modelos)
- Se creen nuevos servicios en `services/`
- Se agreguen validadores en `validators/`
- Se mencionen: "endpoint", "API", "servicio", "validador"

## 🏗️ Arquitectura del Proyecto

```
┌─────────────────────────────────────────────┐
│           Flask Routes (API Layer)           │  ← Solo HTTP handling
│         api/routes/parejas.py                │
│         api/routes/finales.py                │
└──────────────────┬──────────────────────────┘
                   │ llama a
┌──────────────────▼──────────────────────────┐
│        Service Layer (Business Logic)        │  ← Sin dependencias Flask
│       services/pareja_service.py             │
│       services/exceptions.py                 │
└──────────────────┬──────────────────────────┘
                   │ usa
┌──────────────────▼──────────────────────────┐
│         Core Domain (Lógica Central)         │  ← Algoritmos puros
│         core/algoritmo.py                    │
│         core/models.py                       │
│         core/clasificacion.py                │
└──────────────────┬──────────────────────────┘
                   │ usa
┌──────────────────▼──────────────────────────┐
│       Utils & Validators (Helpers)           │  ← Funciones reutilizables
│       validators/cancha_validator.py         │
│       utils/torneo_storage.py                │
└──────────────────────────────────────────────┘
```

## 📐 Reglas de Separación

### 1. Routes (api/routes/*.py)
**Responsabilidad:** Solo manejar HTTP (request/response)

```python
# ✅ CORRECTO
@api_bp.route('/parejas', methods=['POST'])
@require_auth
@with_resultado_data
@with_storage_sync
def crear_pareja(resultado_data):
    """Solo extrae datos del request y delega al servicio"""
    try:
        nueva_pareja = ParejaService.add(
            resultado_data,
            nombre=request.json.get('nombre'),
            telefono=request.json.get('telefono'),
            categoria=request.json.get('categoria'),
            franjas=request.json.get('franjas', [])
        )
        return jsonify(nueva_pareja), 201
    except ParejaValidationError as e:
        return jsonify({'error': str(e)}), 400

# ❌ INCORRECTO - Validación en route
@api_bp.route('/parejas', methods=['POST'])
def crear_pareja():
    nombre = request.json.get('nombre')
    if not nombre:  # ❌ Validación aquí
        return jsonify({'error': 'Nombre obligatorio'}), 400
    
    if '/' not in nombre:  # ❌ Lógica de negocio aquí
        return jsonify({'error': 'Formato inválido'}), 400
    
    # ❌ Manipulación directa de datos aquí
    pareja_id = str(uuid.uuid4())
    nueva_pareja = {
        'id': pareja_id,
        'nombre': nombre,
        # ...
    }
    resultado_data['parejas'].append(nueva_pareja)
    return jsonify(nueva_pareja), 201
```

### 2. Service Layer (services/*.py)
**Responsabilidad:** Lógica de negocio SIN dependencias Flask

```python
# ✅ CORRECTO - Sin imports de Flask
from typing import List, Dict, Any, Optional
from core.models import Pareja
from services.exceptions import ParejaValidationError, ParejaNotFoundError

class ParejaService:
    """Servicio puro sin dependencias de framework"""
    
    @staticmethod
    def add(datos_actuales: Dict, nombre: str, telefono: str, 
            categoria: str, franjas: List[str]) -> Dict:
        """Toda la validación y lógica aquí"""
        # Validaciones
        if not nombre:
            raise ParejaValidationError('El nombre es obligatorio')
        
        if '/' not in nombre:
            raise ParejaValidationError('Formato debe ser "Jugador1/Jugador2"')
        
        if categoria not in CATEGORIAS:
            raise ParejaValidationError(f'Categoría inválida: {categoria}')
        
        # Lógica de negocio
        pareja_id = str(uuid.uuid4())
        nueva_pareja = {
            'id': pareja_id,
            'nombre': nombre.strip(),
            'telefono': telefono or '',
            'categoria': categoria,
            'franjas_disponibles': franjas
        }
        
        datos_actuales['parejas'].append(nueva_pareja)
        return nueva_pareja
    
    @staticmethod
    def remove(datos_actuales: Dict, pareja_id: str) -> None:
        """Eliminar pareja con validaciones de integridad"""
        # Verificar que existe
        pareja = next((p for p in datos_actuales['parejas'] 
                       if p['id'] == pareja_id), None)
        if not pareja:
            raise ParejaNotFoundError(f'Pareja {pareja_id} no encontrada')
        
        # Verificar que no esté en grupos
        for categoria, grupos in datos_actuales['grupos_por_categoria'].items():
            for grupo in grupos:
                if any(p['id'] == pareja_id for p in grupo['parejas']):
                    raise ParejaValidationError(
                        f'No se puede eliminar: está en {grupo["nombre"]}'
                    )
        
        # Eliminar
        datos_actuales['parejas'] = [
            p for p in datos_actuales['parejas'] if p['id'] != pareja_id
        ]

# ❌ INCORRECTO - Dependencias de Flask
from flask import request, jsonify  # ❌ NO en Service Layer

class ParejaService:
    @staticmethod
    def add():
        nombre = request.json.get('nombre')  # ❌ request aquí
        # ...
        return jsonify(nueva_pareja)  # ❌ jsonify aquí
```

### 3. Core Domain (core/*.py)
**Responsabilidad:** Algoritmos puros y lógica de dominio

```python
# ✅ CORRECTO - Funciones puras
class AlgoritmoGrupos:
    """Lógica pura sin efectos secundarios"""
    
    @staticmethod
    def ejecutar(parejas: List[Pareja], config: Dict) -> ResultadoAlgoritmo:
        """Input → Output, sin I/O ni dependencias externas"""
        grupos_por_categoria = {}
        
        for categoria in CATEGORIAS:
            parejas_categoria = [p for p in parejas if p.categoria == categoria]
            grupos = AlgoritmoGrupos._generar_grupos(parejas_categoria)
            grupos_por_categoria[categoria] = grupos
        
        return ResultadoAlgoritmo(
            grupos_por_categoria=grupos_por_categoria,
            parejas_sin_asignar=...,
            calendario=...,
            estadisticas=...
        )
    
    @staticmethod
    def _calcular_compatibilidad(parejas: List[Pareja]) -> Tuple[float, str]:
        """Función matemática pura"""
        # Solo cálculos, sin I/O
        interseccion = set(parejas[0].franjas_disponibles)
        for pareja in parejas[1:]:
            interseccion &= set(pareja.franjas_disponibles)
        
        if interseccion:
            return 3.0, list(interseccion)[0]
        # ...
        return score, franja
```

### 4. Validators (validators/*.py)
**Responsabilidad:** Validaciones específicas reutilizables

```python
# ✅ CORRECTO - Validador puro
class CanchaValidator:
    """Validaciones sin lógica de negocio"""
    
    @staticmethod
    def validar_numero_canchas(num_canchas: int, num_grupos: int) -> None:
        """Lanza excepción si inválido"""
        if num_canchas <= 0:
            raise ValueError('Debe haber al menos 1 cancha')
        
        if num_canchas < num_grupos:
            raise ValueError(
                f'Necesitas mínimo {num_grupos} canchas para '
                f'{num_grupos} grupos simultáneos'
            )
    
    @staticmethod
    def validar_formato_canchas(canchas: List[Dict]) -> None:
        """Validar estructura de datos"""
        for cancha in canchas:
            if 'numero' not in cancha:
                raise ValueError('Cada cancha debe tener número')
            if not isinstance(cancha['numero'], int):
                raise ValueError('Número de cancha debe ser entero')
```

## 🔄 Flujo de Datos

### Request → Response
```
1. Usuario → POST /api/parejas
   ↓
2. Route extrae datos del request
   ↓
3. Route llama a ParejaService.add(datos, nombre, telefono, ...)
   ↓
4. ParejaService valida (lanza excepciones si hay error)
   ↓
5. ParejaService ejecuta lógica de negocio
   ↓
6. ParejaService retorna Dict con pareja creada
   ↓
7. Route convierte a JSON y retorna 201
```

### Manejo de Errores
```python
# En Route
try:
    resultado = Service.metodo(...)
    return jsonify(resultado), 200
except ValidationError as e:
    return jsonify({'error': str(e)}), 400
except NotFoundError as e:
    return jsonify({'error': str(e)}), 404
except Exception as e:
    return jsonify({'error': 'Error interno'}), 500
```

## 📝 Checklist de Code Review

Al revisar código, verificar:

### Routes
- [ ] ¿Solo extrae datos del request?
- [ ] ¿Delega validaciones al Service?
- [ ] ¿Usa decoradores apropiados (@require_auth, @with_resultado_data)?
- [ ] ¿Maneja excepciones del Service?
- [ ] ¿Retorna códigos HTTP correctos?

### Services
- [ ] ¿Sin imports de Flask?
- [ ] ¿Sin uso de request o jsonify?
- [ ] ¿Lanza excepciones custom?
- [ ] ¿Métodos estáticos cuando es posible?
- [ ] ¿Testeable sin servidor HTTP?

### Core
- [ ] ¿Funciones puras sin efectos secundarios?
- [ ] ¿Sin I/O directo?
- [ ] ¿Type hints en parámetros y retorno?
- [ ] ¿Documentación clara del algoritmo?

### Validators
- [ ] ¿Validaciones específicas y reutilizables?
- [ ] ¿Lanzan excepciones descriptivas?
- [ ] ¿Sin lógica de negocio?

## 🚫 Anti-patrones Comunes

### 1. God Route
```python
# ❌ MALO - 200 líneas de lógica en route
@api_bp.route('/parejas/procesar', methods=['POST'])
def procesar_parejas():
    # 50 líneas de validación
    # 100 líneas de lógica de negocio
    # 50 líneas de cálculos
    return jsonify(resultado)
```

### 2. Service con Flask
```python
# ❌ MALO - Service acoplado a Flask
class ParejaService:
    def add(self):
        nombre = request.json.get('nombre')  # ❌
        # ...
        return jsonify(pareja)  # ❌
```

### 3. Validación Duplicada
```python
# ❌ MALO - Validar en route Y en service
@api_bp.route('/parejas', methods=['POST'])
def crear():
    if not request.json.get('nombre'):  # ❌ Validación en route
        return jsonify({'error': '...'}), 400
    
    ParejaService.add(...)  # ❌ Service también valida

# ✅ BUENO - Solo en service
@api_bp.route('/parejas', methods=['POST'])
def crear():
    try:
        ParejaService.add(...)  # Service valida
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
```

## 🎯 Ejemplo Completo

### Crear Nuevo Endpoint

**1. Definir excepción (services/exceptions.py)**
```python
class GrupoNotFoundError(Exception):
    pass
```

**2. Crear método en Service (services/grupo_service.py)**
```python
class GrupoService:
    @staticmethod
    def remove(datos_actuales: Dict, grupo_id: str, categoria: str) -> None:
        if categoria not in datos_actuales['grupos_por_categoria']:
            raise ValueError(f'Categoría {categoria} no existe')
        
        grupos = datos_actuales['grupos_por_categoria'][categoria]
        grupo = next((g for g in grupos if g['id'] == grupo_id), None)
        
        if not grupo:
            raise GrupoNotFoundError(f'Grupo {grupo_id} no encontrado')
        
        # Liberar parejas
        for pareja in grupo['parejas']:
            datos_actuales['parejas'].append(pareja)
        
        # Eliminar grupo
        datos_actuales['grupos_por_categoria'][categoria] = [
            g for g in grupos if g['id'] != grupo_id
        ]
```

**3. Crear route (api/routes/parejas.py)**
```python
@api_bp.route('/grupos/<categoria>/<grupo_id>', methods=['DELETE'])
@require_auth
@with_resultado_data
@with_storage_sync
def eliminar_grupo(resultado_data, categoria, grupo_id):
    try:
        GrupoService.remove(resultado_data, grupo_id, categoria)
        return jsonify({'message': 'Grupo eliminado'}), 200
    except GrupoNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

## 🔗 Referencias

- [Flask Blueprints](https://flask.palletsprojects.com/en/3.0.x/blueprints/)
- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
