"""
API Decorators for Flask routes.
Following refactor:flask best practices for custom decorators.
"""
from functools import wraps
from flask import jsonify, current_app
from typing import Callable, Any
import logging

from utils.torneo_storage import storage
from utils.api_helpers import obtener_datos_desde_token, sincronizar_con_storage_y_token
from config import CATEGORIAS

logger = logging.getLogger(__name__)


def with_resultado_data(f: Callable) -> Callable:
    """
    Decorator to fetch and validate resultado_algoritmo data.
    
    Eliminates boilerplate code pattern that appears 15+ times in parejas.py:
        datos_actuales = obtener_datos_desde_token()
        resultado_data = datos_actuales.get('resultado_algoritmo')
        if not resultado_data:
            return jsonify({'error': '...'}), 404
    
    Usage:
        @api_bp.route('/some-route', methods=['POST'])
        @with_resultado_data
        def some_route(resultado_data, datos_actuales):
            # resultado_data is guaranteed to exist
            # datos_actuales is also available
            ...
    
    Args:
        f: Route handler function
        
    Returns:
        Decorated function that injects resultado_data and datos_actuales
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Fetch current tournament data
        datos_actuales = obtener_datos_desde_token()
        resultado_data = datos_actuales.get('resultado_algoritmo')
        
        # Early return if no algorithm results exist
        if not resultado_data:
            logger.warning(f"Route {f.__name__} called without resultado_algoritmo")
            return jsonify({
                'error': 'No hay resultados del algoritmo disponibles',
                'message': 'Debes ejecutar el algoritmo primero'
            }), 404
        
        # Inject data into route handler
        kwargs['resultado_data'] = resultado_data
        kwargs['datos_actuales'] = datos_actuales
        
        return f(*args, **kwargs)
    
    return decorated_function


def with_storage_sync(f: Callable) -> Callable:
    """
    Decorator to automatically synchronize data with storage after route execution.
    
    Eliminates repetitive pattern that appears 20+ times:
        sincronizar_con_storage_y_token(datos_actuales)
        return crear_respuesta_con_token_actualizado({...}, datos_actuales)
    
    This decorator ensures that any changes made during the route execution
    are persisted to storage before the response is sent.
    
    Usage:
        @api_bp.route('/some-route', methods=['POST'])
        @with_storage_sync
        def some_route():
            # Make changes to data
            # No need to call sync manually
            return jsonify({'success': True})
    
    Args:
        f: Route handler function
        
    Returns:
        Decorated function that auto-syncs after execution
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Execute the route handler
            result = f(*args, **kwargs)
            
            # Auto-sync with storage after successful execution
            # Only sync if datos_actuales is available in kwargs or function has it
            if 'datos_actuales' in kwargs:
                datos_actuales = kwargs['datos_actuales']
                sincronizar_con_storage_y_token(datos_actuales)
                logger.debug(f"Auto-synced storage after {f.__name__}")
            else:
                # Fallback: get fresh data and sync
                datos_actuales = obtener_datos_desde_token()
                sincronizar_con_storage_y_token(datos_actuales)
                logger.debug(f"Auto-synced storage (fallback) after {f.__name__}")
            
            return result
            
        except Exception as e:
            # Don't sync if there was an error
            logger.error(f"Error in {f.__name__}, skipping storage sync: {e}")
            raise
    
    return decorated_function


def validate_categoria(f: Callable) -> Callable:
    """
    Decorator to validate that a categoria parameter exists and is valid.
    
    Validates against CATEGORIAS defined in config (Cuarta, Quinta, Sexta, Séptima).
    
    Usage:
        @api_bp.route('/some-route/<categoria>', methods=['GET'])
        @validate_categoria
        def some_route(categoria):
            # categoria is guaranteed to be valid
            ...
    
    The decorator checks both:
    - URL path parameters (e.g., /route/Cuarta)
    - Request JSON body (e.g., {"categoria": "Quinta"})
    
    Args:
        f: Route handler function
        
    Returns:
        Decorated function that validates categoria parameter
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if categoria is in URL path parameters
        categoria = kwargs.get('categoria')
        
        # If not in path, check request JSON
        if not categoria:
            from flask import request
            if request.is_json:
                data = request.get_json()
                categoria = data.get('categoria')
        
        # Early return if categoria is missing
        if not categoria:
            logger.warning(f"Route {f.__name__} called without categoria parameter")
            return jsonify({
                'error': 'Falta el parámetro categoria',
                'valid_categorias': CATEGORIAS
            }), 400
        
        # Validate categoria against allowed values
        if categoria not in CATEGORIAS:
            logger.warning(f"Route {f.__name__} called with invalid categoria: {categoria}")
            return jsonify({
                'error': f'Categoría inválida: {categoria}',
                'valid_categorias': CATEGORIAS,
                'message': 'Las categorías válidas son: ' + ', '.join(CATEGORIAS)
            }), 400
        
        # Categoria is valid, proceed with route handler
        return f(*args, **kwargs)
    
    return decorated_function


def combine_decorators(*decorators):
    """
    Helper function to combine multiple decorators in a clean way.
    
    Usage:
        common_decorators = combine_decorators(
            with_resultado_data,
            with_storage_sync,
            validate_categoria
        )
        
        @api_bp.route('/some-route', methods=['POST'])
        @common_decorators
        def some_route(resultado_data, datos_actuales):
            ...
    """
    def decorator(f):
        for dec in reversed(decorators):
            f = dec(f)
        return f
    return decorator
