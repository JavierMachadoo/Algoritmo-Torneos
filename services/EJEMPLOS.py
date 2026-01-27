"""
EJEMPLOS DE USO - ParejaService
================================

Este archivo documenta cómo usar el ParejaService siguiendo el patrón
de service layer de refactor:flask.

PRINCIPIOS DEL SERVICE LAYER:
1. Métodos estáticos (@staticmethod) - No mantienen estado
2. Sin dependencias de Flask (no request, no jsonify)
3. Excepciones personalizadas para errores
4. Type hints completos
5. Pure business logic - La ruta maneja request/response

"""

# =============================================================================
# EJEMPLO 1: Agregar una pareja nueva
# =============================================================================

# ❌ ANTES (lógica en la ruta - 45 líneas):
@api_bp.route('/agregar-pareja', methods=['POST'])
def agregar_pareja():
    data = request.json
    nombre = data.get('nombre', '').strip()
    # ... 15 líneas de validación
    # ... 10 líneas de generación de ID
    # ... 10 líneas de creación de pareja
    # ... 10 líneas de actualización de estadísticas
    return jsonify({'success': True})

# ✅ DESPUÉS (ruta delgada - 15 líneas):
from services import ParejaService, ParejaValidationError

@api_bp.route('/agregar-pareja', methods=['POST'])
@with_storage_sync
def agregar_pareja():
    """Agrega una pareja manualmente al torneo."""
    try:
        data = request.json
        datos_actuales = obtener_datos_desde_token()
        
        nueva_pareja = ParejaService.add(
            datos_actuales=datos_actuales,
            nombre=data.get('nombre', '').strip(),
            telefono=data.get('telefono', '').strip(),
            categoria=data.get('categoria', 'Cuarta'),
            franjas=data.get('franjas', []),
            desde_resultados=data.get('desde_resultados', False)
        )
        
        return crear_respuesta_con_token_actualizado({
            'success': True,
            'pareja': nueva_pareja
        }, datos_actuales)
    
    except ParejaValidationError as e:
        return jsonify({'error': str(e)}), 400


# =============================================================================
# EJEMPLO 2: Eliminar una pareja
# =============================================================================

# ❌ ANTES (lógica en la ruta - 35 líneas):
@api_bp.route('/eliminar-pareja', methods=['POST'])
def eliminar_pareja():
    data = request.json
    pareja_id = data.get('id')
    # ... 10 líneas para eliminar de lista base
    # ... 15 líneas para eliminar de grupos
    # ... 5 líneas para recalcular estadísticas
    # ... 5 líneas para regenerar calendario
    return jsonify({'success': True})

# ✅ DESPUÉS (ruta delgada - 12 líneas):
from services import ParejaService, ParejaValidationError

@api_bp.route('/eliminar-pareja', methods=['POST'])
@with_storage_sync
def eliminar_pareja():
    """Elimina una pareja del torneo completamente."""
    try:
        data = request.json
        datos_actuales = obtener_datos_desde_token()
        
        result = ParejaService.delete(datos_actuales, data.get('id'))
        return crear_respuesta_con_token_actualizado(result, datos_actuales)
    
    except ParejaValidationError as e:
        return jsonify({'error': str(e)}), 400


# =============================================================================
# EJEMPLO 3: Actualizar una pareja
# =============================================================================

# ❌ ANTES (lógica en la ruta - 115 líneas):
@api_bp.route('/editar-pareja', methods=['POST'])
def editar_pareja():
    data = request.json
    # ... 20 líneas de validación
    # ... 30 líneas para buscar pareja en grupos
    # ... 20 líneas para manejar cambio de categoría
    # ... 25 líneas para actualizar datos
    # ... 10 líneas para recalcular score y calendario
    # ... 10 líneas para sincronizar storage
    return jsonify({'success': True})

# ✅ DESPUÉS (ruta delgada - 20 líneas):
from services import (
    ParejaService,
    ParejaValidationError,
    ResultadoAlgoritmoNotFoundError,
    ParejaNotFoundError
)

@api_bp.route('/editar-pareja', methods=['POST'])
def editar_pareja():
    """Edita los datos de una pareja."""
    try:
        data = request.json
        datos_actuales = obtener_datos_desde_token()
        
        result = ParejaService.update(
            datos_actuales=datos_actuales,
            pareja_id=data.get('pareja_id'),
            nombre=data.get('nombre'),
            telefono=data.get('telefono'),
            categoria=data.get('categoria'),
            franjas=data.get('franjas', [])
        )
        
        sincronizar_con_storage_y_token(datos_actuales)
        guardar_estado_torneo()
        
        return crear_respuesta_con_token_actualizado(result, datos_actuales)
    
    except ParejaValidationError as e:
        return jsonify({'error': str(e)}), 400
    except ResultadoAlgoritmoNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ParejaNotFoundError as e:
        return jsonify({'error': str(e)}), 404


# =============================================================================
# EJEMPLO 4: Remover pareja de grupo
# =============================================================================

# ❌ ANTES (lógica en la ruta - 50 líneas):
@api_bp.route('/remover-pareja-de-grupo', methods=['POST'])
def remover_pareja_de_grupo():
    data = request.json
    # ... 5 líneas de validación
    # ... 20 líneas para buscar pareja en grupos
    # ... 10 líneas para remover y agregar a no asignadas
    # ... 10 líneas para recalcular score y estadísticas
    # ... 5 líneas para regenerar calendario
    return jsonify({'success': True})

# ✅ DESPUÉS (ruta delgada - 18 líneas):
from services import (
    ParejaService,
    ParejaValidationError,
    ResultadoAlgoritmoNotFoundError,
    ParejaNotFoundError
)

@api_bp.route('/remover-pareja-de-grupo', methods=['POST'])
def remover_pareja_de_grupo():
    """Remueve una pareja de un grupo."""
    try:
        data = request.json
        datos_actuales = obtener_datos_desde_token()
        
        result = ParejaService.remove_from_group(
            datos_actuales, data.get('pareja_id')
        )
        
        sincronizar_con_storage_y_token(datos_actuales)
        guardar_estado_torneo()
        
        return crear_respuesta_con_token_actualizado(result)
    
    except ParejaValidationError as e:
        return jsonify({'error': str(e)}), 400
    except ResultadoAlgoritmoNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ParejaNotFoundError as e:
        return jsonify({'error': str(e)}), 404


# =============================================================================
# VENTAJAS DEL SERVICE LAYER
# =============================================================================

"""
1. SEPARATION OF CONCERNS:
   - Rutas: Solo manejan request/response (15-20 líneas)
   - Services: Contienen toda la business logic (testeable)
   
2. TESTABILIDAD:
   - Services son pure functions sin Flask dependencies
   - Fácil escribir unit tests sin mock de request/jsonify
   
3. REUTILIZACIÓN:
   - La misma lógica se puede usar desde CLI, tests, jobs, etc.
   - No limitado a rutas HTTP
   
4. MANTENIBILIDAD:
   - Cambios en business logic solo afectan al service
   - Type hints claros sobre inputs/outputs
   - Excepciones personalizadas facilitan debugging
   
5. ESCALABILIDAD:
   - Fácil agregar validación, logging, caching en un solo lugar
   - Service puede llamar otros services (composición)

RESULTADO EN PAREJAS.PY:
- Antes: 1729 líneas (con decorators y validators)
- Después: 1569 líneas (service layer aplicado)
- Reducción: 160 líneas (-9.3%)
- Reducción total desde inicio: 321 líneas (-17%)

ESTRUCTURA FINAL:
api/routes/parejas.py       → Thin controllers (request/response)
services/pareja_service.py  → Business logic (pure functions)
decorators/api_decorators.py → Cross-cutting concerns
validators/cancha_validator.py → Validation rules
"""


# =============================================================================
# PATRÓN DE EXCEPCIONES PERSONALIZADAS
# =============================================================================

"""
Las excepciones permiten separar errores de negocio de errores técnicos:

- ParejaValidationError: Datos inválidos (400 Bad Request)
- ParejaNotFoundError: Recurso no encontrado (404 Not Found)
- ResultadoAlgoritmoNotFoundError: Estado inválido (404 Not Found)

La ruta mapea cada excepción al status HTTP correcto.
"""

# Ejemplo completo con todas las excepciones:
@api_bp.route('/ejemplo', methods=['POST'])
def ejemplo_completo():
    try:
        result = ParejaService.metodo(datos)
        return jsonify(result), 200
    
    except ParejaValidationError as e:
        # Usuario envió datos inválidos
        return jsonify({'error': str(e)}), 400
    
    except ParejaNotFoundError as e:
        # Recurso no existe
        return jsonify({'error': str(e)}), 404
    
    except ResultadoAlgoritmoNotFoundError as e:
        # Estado de aplicación inválido
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        # Error técnico no esperado
        logger.error(f"Error inesperado: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
