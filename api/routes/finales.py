"""
API Routes para manejo de finales
"""

from flask import Blueprint, jsonify, request
import logging
from core.fixture_finales_generator import GeneradorFixtureFinales
from core.models import Grupo, FixtureFinales
from utils.calendario_finales_builder import GeneradorCalendarioFinales
from utils.torneo_storage import storage
from utils.api_helpers import verificar_autenticacion_api

logger = logging.getLogger(__name__)

finales_bp = Blueprint('finales', __name__, url_prefix='/api/finales')


# Middleware para verificar autenticación en todas las rutas de finales
@finales_bp.before_request
def verificar_auth():
    """Verifica que el usuario esté autenticado antes de acceder a la API."""
    authenticated, error_response = verificar_autenticacion_api()
    if not authenticated:
        return error_response


@finales_bp.route('/fixtures', methods=['GET'])
def obtener_fixtures():
    """Obtiene los fixtures de finales para todas las categorías"""
    try:
        torneo = storage.cargar()
        resultado = torneo.get('resultado_algoritmo')
        
        if not resultado:
            return jsonify({
                'success': False,
                'message': 'No hay resultado del algoritmo disponible'
            }), 404
        
        # Obtener fixtures guardados o generarlos
        fixtures_guardados = torneo.get('fixtures_finales', {})
        
        if fixtures_guardados:
            return jsonify({
                'success': True,
                'fixtures': fixtures_guardados
            })
        
        # Generar fixtures por primera vez
        grupos_por_categoria = resultado.get('grupos_por_categoria', {})
        fixtures_nuevos = {}
        
        for categoria, grupos_data in grupos_por_categoria.items():
            # Reconstruir objetos Grupo
            grupos = []
            for grupo_dict in grupos_data:
                grupo = Grupo.from_dict(grupo_dict)
                grupos.append(grupo)
            
            # Generar fixture para esta categoría
            fixture = GeneradorFixtureFinales.generar_fixture(categoria, grupos)
            
            if fixture:
                fixtures_nuevos[categoria] = fixture.to_dict()
        
        # Guardar fixtures generados
        torneo['fixtures_finales'] = fixtures_nuevos
        storage.guardar(torneo)
        
        return jsonify({
            'success': True,
            'fixtures': fixtures_nuevos
        })
        
    except Exception as e:
        logger.error(f"Error al obtener fixtures: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error al obtener fixtures: {str(e)}'
        }), 500


@finales_bp.route('/fixtures/<categoria>', methods=['GET'])
def obtener_fixture_categoria(categoria):
    """Obtiene el fixture de finales para una categoría específica"""
    try:
        torneo = storage.cargar()
        fixtures = torneo.get('fixtures_finales', {})
        
        if categoria not in fixtures:
            # Intentar generar
            resultado = torneo.get('resultado_algoritmo')
            if not resultado:
                return jsonify({
                    'success': False,
                    'message': 'No hay resultado del algoritmo disponible'
                }), 404
            
            grupos_data = resultado.get('grupos_por_categoria', {}).get(categoria, [])
            if not grupos_data:
                return jsonify({
                    'success': False,
                    'message': f'No hay grupos para la categoría {categoria}'
                }), 404
            
            # Reconstruir grupos
            grupos = [Grupo.from_dict(g) for g in grupos_data]
            
            # Generar fixture
            fixture = GeneradorFixtureFinales.generar_fixture(categoria, grupos)
            
            if not fixture:
                return jsonify({
                    'success': False,
                    'message': f'No se pudo generar fixture para {categoria}'
                }), 500
            
            # Guardar
            if 'fixtures_finales' not in torneo:
                torneo['fixtures_finales'] = {}
            torneo['fixtures_finales'][categoria] = fixture.to_dict()
            storage.guardar(torneo)
            
            return jsonify({
                'success': True,
                'fixture': fixture.to_dict()
            })
        
        return jsonify({
            'success': True,
            'fixture': fixtures[categoria]
        })
        
    except Exception as e:
        logger.error(f"Error al obtener fixture de {categoria}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@finales_bp.route('/fixtures/regenerar', methods=['POST'])
def regenerar_fixtures():
    """Regenera los fixtures de finales basándose en las posiciones actuales"""
    try:
        torneo = storage.cargar()
        resultado = torneo.get('resultado_algoritmo')
        
        if not resultado:
            return jsonify({
                'success': False,
                'message': 'No hay resultado del algoritmo disponible'
            }), 404
        
        grupos_por_categoria = resultado.get('grupos_por_categoria', {})
        fixtures_nuevos = {}
        
        for categoria, grupos_data in grupos_por_categoria.items():
            # Reconstruir objetos Grupo
            grupos = [Grupo.from_dict(g) for g in grupos_data]
            
            # Generar fixture para esta categoría
            fixture = GeneradorFixtureFinales.generar_fixture(categoria, grupos)
            
            if fixture:
                fixtures_nuevos[categoria] = fixture.to_dict()
        
        # Guardar fixtures regenerados
        torneo['fixtures_finales'] = fixtures_nuevos
        storage.guardar(torneo)
        
        return jsonify({
            'success': True,
            'message': 'Fixtures regenerados exitosamente',
            'fixtures': fixtures_nuevos
        })
        
    except Exception as e:
        logger.error(f"Error al regenerar fixtures: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@finales_bp.route('/partido/<partido_id>/ganador', methods=['POST'])
def actualizar_ganador_partido(partido_id):
    """Actualiza el ganador de un partido de finales"""
    try:
        data = request.get_json()
        ganador_id = data.get('ganador_id')
        
        if not ganador_id:
            return jsonify({
                'success': False,
                'message': 'ganador_id es requerido'
            }), 400
        
        torneo = storage.cargar()
        resultado = torneo.get('resultado_algoritmo')
        fixtures_dict = torneo.get('fixtures_finales', {})
        
        if not fixtures_dict:
            return jsonify({
                'success': False,
                'message': 'No hay fixtures disponibles'
            }), 404
        
        # Buscar en qué categoría está el partido
        categoria_encontrada = None
        for categoria, fixture_dict in fixtures_dict.items():
            # Buscar en todas las fases
            for fase in ['octavos', 'cuartos', 'semifinales']:
                if fase in fixture_dict:
                    for partido in fixture_dict[fase]:
                        if partido and partido.get('id') == partido_id:
                            categoria_encontrada = categoria
                            break
                if categoria_encontrada:
                    break
            
            # Buscar en final
            if not categoria_encontrada and fixture_dict.get('final'):
                if fixture_dict['final'].get('id') == partido_id:
                    categoria_encontrada = categoria
        
        if not categoria_encontrada:
            return jsonify({
                'success': False,
                'message': f'Partido {partido_id} no encontrado'
            }), 404
        
        # Reconstruir fixture con objetos
        grupos_data = resultado.get('grupos_por_categoria', {}).get(categoria_encontrada, [])
        grupos = [Grupo.from_dict(g) for g in grupos_data]
        
        fixture = FixtureFinales.from_dict(fixtures_dict[categoria_encontrada], grupos)
        
        # Actualizar ganador
        exito = GeneradorFixtureFinales.actualizar_ganador_partido(fixture, partido_id, ganador_id)
        
        if not exito:
            return jsonify({
                'success': False,
                'message': 'No se pudo actualizar el ganador'
            }), 500
        
        # Guardar fixture actualizado
        fixtures_dict[categoria_encontrada] = fixture.to_dict()
        torneo['fixtures_finales'] = fixtures_dict
        storage.guardar(torneo)
        
        return jsonify({
            'success': True,
            'message': 'Ganador actualizado exitosamente',
            'fixture': fixture.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error al actualizar ganador: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@finales_bp.route('/calendario', methods=['GET'])
def obtener_calendario():
    """Obtiene el calendario de finales del domingo"""
    try:
        torneo = storage.cargar()
        fixtures = torneo.get('fixtures_finales', {})
        
        if not fixtures:
            return jsonify({
                'success': False,
                'message': 'No hay fixtures disponibles'
            }), 404
        
        # Generar calendario
        calendario = GeneradorCalendarioFinales.asignar_horarios(fixtures)
        resumen = GeneradorCalendarioFinales.generar_resumen_horarios()
        
        return jsonify({
            'success': True,
            'calendario': calendario,
            'resumen_horarios': resumen
        })
        
    except Exception as e:
        logger.error(f"Error al generar calendario: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
