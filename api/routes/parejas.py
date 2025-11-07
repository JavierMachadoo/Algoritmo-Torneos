from flask import Blueprint, request, jsonify, session
import pandas as pd
import os

from core import (
    Pareja, AlgoritmoGrupos, ResultadoAlgoritmo, Grupo,
    PosicionGrupo, FixtureGenerator, FixtureFinales
)
from utils import CSVProcessor, CalendarioBuilder
from utils.calendario_finales_builder import CalendarioFinalesBuilder
from utils.google_sheets_export_calendario import GoogleSheetsExportCalendario
from config import CATEGORIAS, NUM_CANCHAS_DEFAULT

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/cargar-csv', methods=['POST'])
def cargar_csv():
    """Carga parejas desde un archivo CSV."""
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['archivo']
    
    if file.filename == '' or not CSVProcessor.validar_archivo(file.filename):
        return jsonify({'error': 'Archivo inválido'}), 400
    
    try:
        df = pd.read_csv(file)
        parejas = CSVProcessor.procesar_dataframe(df)
        
        session['parejas'] = parejas
        session.modified = True
        
        return jsonify({
            'success': True,
            'mensaje': f'✅ {len(parejas)} parejas cargadas correctamente',
            'parejas': parejas
        })
    except Exception as e:
        return jsonify({'error': f'Error al procesar CSV: {str(e)}'}), 500


@api_bp.route('/agregar-pareja', methods=['POST'])
def agregar_pareja():
    """Agrega una pareja manualmente al torneo."""
    data = request.json
    
    nombre = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    categoria = data.get('categoria', 'Cuarta')
    franjas = data.get('franjas', [])
    
    if not nombre:
        return jsonify({'error': 'El nombre es obligatorio'}), 400
    
    if not franjas:
        return jsonify({'error': 'Selecciona al menos una franja horaria'}), 400
    
    parejas = session.get('parejas', [])
    
    nueva_pareja = {
        'id': len(parejas) + 1,
        'nombre': nombre,
        'telefono': telefono or 'Sin teléfono',
        'categoria': categoria,
        'franjas_disponibles': franjas
    }
    
    parejas.append(nueva_pareja)
    session['parejas'] = parejas
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': f'Pareja "{nombre}" agregada correctamente',
        'pareja': nueva_pareja
    })


@api_bp.route('/eliminar-pareja/<int:pareja_id>', methods=['DELETE'])
def eliminar_pareja(pareja_id):
    """Elimina una pareja del torneo."""
    parejas = session.get('parejas', [])
    parejas = [p for p in parejas if p['id'] != pareja_id]
    
    session['parejas'] = parejas
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': 'Pareja eliminada correctamente'
    })


@api_bp.route('/limpiar-datos', methods=['POST'])
def limpiar_datos():
    """Limpia todos los datos de la sesión."""
    session.clear()
    return jsonify({
        'success': True,
        'mensaje': 'Datos limpiados correctamente'
    })


@api_bp.route('/intercambiar-pareja', methods=['POST'])
def intercambiar_pareja():
    """Intercambia una pareja entre dos grupos."""
    data = request.json
    pareja_id = data.get('pareja_id')
    grupo_origen = data.get('grupo_origen')
    grupo_destino = data.get('grupo_destino')
    
    resultado = session.get('resultado_algoritmo')
    if not resultado:
        return jsonify({'error': 'No hay resultados cargados'}), 400
    
    try:
        pareja_movida = None
        pareja_reemplazo = None
        categoria_actual = None
        
        for categoria, grupos in resultado['grupos_por_categoria'].items():
            for grupo in grupos:
                if grupo['id'] == grupo_origen:
                    categoria_actual = categoria
                    for pareja in grupo['parejas']:
                        if pareja['id'] == pareja_id:
                            pareja_movida = pareja
                            grupo['parejas'].remove(pareja)
                            break
                
                if grupo['id'] == grupo_destino and categoria_actual:
                    if len(grupo['parejas']) > 0:
                        pareja_reemplazo = grupo['parejas'][0]
                        grupo['parejas'].remove(pareja_reemplazo)
                    if pareja_movida:
                        grupo['parejas'].append(pareja_movida)
        
        if pareja_movida and pareja_reemplazo:
            for categoria, grupos in resultado['grupos_por_categoria'].items():
                for grupo in grupos:
                    if grupo['id'] == grupo_origen:
                        grupo['parejas'].append(pareja_reemplazo)
                        break
        
        session['resultado_algoritmo'] = resultado
        session.modified = True
        
        mensaje = f"Pareja intercambiada correctamente"
        if pareja_reemplazo:
            mensaje = f"Intercambio exitoso: {pareja_movida['nombre']} ↔ {pareja_reemplazo['nombre']}"
        
        return jsonify({
            'success': True,
            'mensaje': mensaje
        })
    except Exception as e:
        return jsonify({'error': f'Error al intercambiar: {str(e)}'}), 500


@api_bp.route('/ejecutar-algoritmo', methods=['POST'])
def ejecutar_algoritmo():
    """Ejecuta el algoritmo de generación de grupos para el torneo."""
    parejas_data = session.get('parejas', [])
    
    if not parejas_data:
        return jsonify({'error': 'No hay parejas cargadas'}), 400
    
    try:
        parejas_obj = [Pareja.from_dict(p) for p in parejas_data]
        
        algoritmo = AlgoritmoGrupos(parejas=parejas_obj, num_canchas=NUM_CANCHAS_DEFAULT)
        resultado_obj = algoritmo.ejecutar()
        
        resultado = serializar_resultado(resultado_obj, NUM_CANCHAS_DEFAULT)
        
        session['resultado_algoritmo'] = resultado
        session['num_canchas'] = NUM_CANCHAS_DEFAULT
        session.modified = True
        
        return jsonify({
            'success': True,
            'mensaje': '✅ Grupos generados exitosamente',
            'resultado': resultado
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al ejecutar algoritmo: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


def serializar_resultado(resultado, num_canchas):
    """Convierte el resultado del algoritmo a formato JSON serializable."""
    grupos_dict = {}
    canchas_asignadas = {}
    
    for categoria, grupos in resultado.grupos_por_categoria.items():
        grupos_dict[categoria] = []
        
        for grupo in grupos:
            franja = grupo.franja_horaria
            if franja:
                if franja not in canchas_asignadas:
                    canchas_asignadas[franja] = 0
                cancha_num = (canchas_asignadas[franja] % num_canchas) + 1
                canchas_asignadas[franja] += 1
            else:
                cancha_num = None
            
            grupos_dict[categoria].append({
                'id': grupo.id,
                'parejas': [p.to_dict() for p in grupo.parejas],
                'partidos': [
                    {'pareja1': p1.nombre, 'pareja2': p2.nombre}
                    for p1, p2 in grupo.partidos
                ],
                'franja_horaria': grupo.franja_horaria,
                'cancha': cancha_num,
                'score': grupo.score_compatibilidad
            })
    
    calendario_builder = CalendarioBuilder(num_canchas)
    calendario = calendario_builder.organizar_partidos(resultado)
    
    return {
        'grupos_por_categoria': grupos_dict,
        'estadisticas': resultado.estadisticas,
        'parejas_sin_asignar': [p.to_dict() for p in resultado.parejas_sin_asignar],
        'calendario': calendario
    }


@api_bp.route('/parejas-no-asignadas/<categoria>', methods=['GET'])
def obtener_parejas_no_asignadas(categoria):
    """Obtiene las parejas no asignadas de una categoría específica."""
    resultado_data = session.get('resultado_algoritmo')
    if not resultado_data:
        return jsonify({'error': 'No hay resultados del algoritmo'}), 404
    
    parejas_no_asignadas = resultado_data.get('parejas_sin_asignar', [])
    
    # Filtrar por categoría
    parejas_categoria = [
        pareja for pareja in parejas_no_asignadas 
        if pareja.get('categoria') == categoria
    ]
    
    return jsonify({
        'success': True,
        'parejas': parejas_categoria,
        'total': len(parejas_categoria)
    })


@api_bp.route('/asignar-pareja-a-grupo', methods=['POST'])
def asignar_pareja_a_grupo():
    """Asigna una pareja no asignada a un grupo, opcionalmente reemplazando otra."""
    data = request.json
    pareja_id = data.get('pareja_id')
    grupo_id = data.get('grupo_id')
    pareja_a_remover_id = data.get('pareja_a_remover_id')  # Opcional
    categoria = data.get('categoria')
    
    if not all([pareja_id, grupo_id, categoria]):
        return jsonify({'error': 'Faltan parámetros requeridos'}), 400
    
    resultado_data = session.get('resultado_algoritmo')
    if not resultado_data:
        return jsonify({'error': 'No hay resultados del algoritmo'}), 404
    
    grupos_dict = resultado_data['grupos_por_categoria']
    parejas_sin_asignar = resultado_data.get('parejas_sin_asignar', [])
    
    # Buscar la pareja no asignada
    pareja_a_asignar = None
    for idx, p in enumerate(parejas_sin_asignar):
        if p.get('id') == pareja_id:
            pareja_a_asignar = parejas_sin_asignar.pop(idx)
            break
    
    if not pareja_a_asignar:
        return jsonify({'error': 'Pareja no encontrada en no asignadas'}), 404
    
    # Buscar el grupo
    grupo_encontrado = None
    for grupo in grupos_dict.get(categoria, []):
        if grupo['id'] == grupo_id:
            grupo_encontrado = grupo
            break
    
    if not grupo_encontrado:
        return jsonify({'error': 'Grupo no encontrado'}), 404
    
    # Si hay pareja a remover, quitarla del grupo y agregarla a no asignadas
    if pareja_a_remover_id:
        pareja_removida = None
        for idx, p in enumerate(grupo_encontrado['parejas']):
            if p.get('id') == pareja_a_remover_id:
                pareja_removida = grupo_encontrado['parejas'].pop(idx)
                break
        
        if pareja_removida:
            # Limpiar la posición de grupo antes de agregar a no asignadas
            pareja_removida['posicion_grupo'] = None
            parejas_sin_asignar.append(pareja_removida)
    
    # Si el grupo ya tiene 3 parejas y no se especificó a quién remover
    if len(grupo_encontrado['parejas']) >= 3 and not pareja_a_remover_id:
        # Devolver la pareja a no asignadas
        parejas_sin_asignar.append(pareja_a_asignar)
        return jsonify({
            'error': 'El grupo ya tiene 3 parejas. Debes especificar cuál reemplazar.',
            'grupo_lleno': True,
            'parejas_grupo': grupo_encontrado['parejas']
        }), 400
    
    # Agregar la pareja al grupo
    grupo_encontrado['parejas'].append(pareja_a_asignar)
    
    # Actualizar session
    session['resultado_algoritmo'] = resultado_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': f'✓ Pareja asignada al grupo correctamente'
    })


@api_bp.route('/crear-grupo-manual', methods=['POST'])
def crear_grupo_manual():
    """Crea un nuevo grupo manualmente para una categoría."""
    data = request.json
    categoria = data.get('categoria')
    franja_horaria = data.get('franja_horaria')
    cancha = data.get('cancha')
    
    if not all([categoria, franja_horaria, cancha]):
        return jsonify({'error': 'Faltan parámetros requeridos'}), 400
    
    resultado_data = session.get('resultado_algoritmo')
    if not resultado_data:
        return jsonify({'error': 'No hay resultados del algoritmo'}), 404
    
    grupos_dict = resultado_data['grupos_por_categoria']
    
    # Asegurar que existe la categoría
    if categoria not in grupos_dict:
        grupos_dict[categoria] = []
    
    # Generar nuevo ID único para el grupo
    max_id = 0
    for cat_grupos in grupos_dict.values():
        for grupo in cat_grupos:
            if grupo.get('id', 0) > max_id:
                max_id = grupo['id']
    
    nuevo_id = max_id + 1
    
    # Crear el nuevo grupo
    nuevo_grupo = {
        'id': nuevo_id,
        'franja_horaria': franja_horaria,
        'cancha': cancha,
        'score_compatibilidad': 0.0,
        'parejas': [],
        'partidos': []
    }
    
    grupos_dict[categoria].append(nuevo_grupo)
    
    # Actualizar session
    session['resultado_algoritmo'] = resultado_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': '✓ Grupo creado correctamente',
        'grupo': nuevo_grupo
    })


@api_bp.route('/editar-grupo', methods=['POST'])
def editar_grupo():
    """Edita la franja horaria y cancha de un grupo."""
    data = request.json
    grupo_id = data.get('grupo_id')
    categoria = data.get('categoria')
    franja_horaria = data.get('franja_horaria')
    cancha = data.get('cancha')
    
    if not all([grupo_id, categoria, franja_horaria, cancha]):
        return jsonify({'error': 'Faltan parámetros requeridos'}), 400
    
    resultado_data = session.get('resultado_algoritmo')
    if not resultado_data:
        return jsonify({'error': 'No hay resultados del algoritmo'}), 404
    
    grupos_dict = resultado_data['grupos_por_categoria']
    
    # Buscar el grupo
    grupo_encontrado = None
    for grupo in grupos_dict.get(categoria, []):
        if grupo['id'] == grupo_id:
            grupo_encontrado = grupo
            break
    
    if not grupo_encontrado:
        return jsonify({'error': 'Grupo no encontrado'}), 404
    
    # Actualizar datos del grupo
    grupo_encontrado['franja_horaria'] = franja_horaria
    grupo_encontrado['cancha'] = cancha
    
    # Actualizar session
    session['resultado_algoritmo'] = resultado_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': '✓ Grupo actualizado correctamente'
    })


@api_bp.route('/exportar-google-sheets', methods=['POST'])
def exportar_google_sheets():
    """Exporta el calendario de partidos a Google Sheets."""
    data = request.json
    spreadsheet_id = data.get('spreadsheet_id', '').strip()
    
    if not spreadsheet_id:
        return jsonify({'error': 'Falta el ID del Google Sheet'}), 400
    
    resultado_data = session.get('resultado_algoritmo')
    if not resultado_data:
        return jsonify({'error': 'No hay resultados del algoritmo para exportar'}), 400
    
    credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
    if not os.path.exists(credentials_path):
        return jsonify({'error': 'No se encontraron las credenciales de Google Sheets'}), 500
    
    try:
        resultado = deserializar_resultado(resultado_data)
        
        google_sheets = GoogleSheetsExportCalendario(credentials_path)
        url = google_sheets.exportar_calendario(spreadsheet_id, resultado)
        
        return jsonify({
            'success': True,
            'mensaje': '✅ Calendario exportado exitosamente a Google Sheets',
            'url': url
        })
    except KeyError as e:
        import traceback
        return jsonify({
            'error': f'Error en la estructura de datos: clave faltante {str(e)}',
            'traceback': traceback.format_exc()
        }), 500
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al exportar: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


def deserializar_resultado(resultado_data):
    """Reconstruye el objeto ResultadoAlgoritmo desde datos de sesión."""
    grupos_por_categoria = {}
    
    for categoria, grupos_list in resultado_data['grupos_por_categoria'].items():
        grupos_por_categoria[categoria] = []
        for grupo_dict in grupos_list:
            grupo = Grupo(
                id=grupo_dict['id'],
                categoria=categoria
            )
            grupo.franja_horaria = grupo_dict.get('franja_horaria')
            grupo.score_compatibilidad = grupo_dict.get('score', 0.0)
            
            for pareja_dict in grupo_dict['parejas']:
                pareja = Pareja(
                    id=pareja_dict['id'],
                    nombre=pareja_dict['nombre'],
                    telefono=pareja_dict.get('telefono', 'Sin teléfono'),
                    categoria=pareja_dict['categoria'],
                    franjas_disponibles=pareja_dict.get('franjas_disponibles', [])
                )
                grupo.parejas.append(pareja)
            
            grupo.generar_partidos()
            grupos_por_categoria[categoria].append(grupo)
    
    parejas_sin_asignar = []
    for p in resultado_data.get('parejas_sin_asignar', []):
        pareja = Pareja(
            id=p['id'],
            nombre=p['nombre'],
            telefono=p.get('telefono', 'Sin teléfono'),
            categoria=p['categoria'],
            franjas_disponibles=p.get('franjas_disponibles', [])
        )
        parejas_sin_asignar.append(pareja)
    
    resultado = ResultadoAlgoritmo(
        grupos_por_categoria=grupos_por_categoria,
        parejas_sin_asignar=parejas_sin_asignar,
        calendario=resultado_data.get('calendario', {}),
        estadisticas=resultado_data.get('estadisticas', {})
    )
    
    return resultado


@api_bp.route('/asignar-posicion', methods=['POST'])
def asignar_posicion():
    """Asigna la posición final de una pareja en su grupo."""
    data = request.json
    pareja_id = data.get('pareja_id')
    posicion = data.get('posicion')  # 1, 2, o 3
    categoria = data.get('categoria')
    
    if not all([pareja_id, posicion, categoria]):
        return jsonify({'error': 'Faltan parámetros requeridos'}), 400
    
    try:
        resultado_data = session.get('resultado_algoritmo')
        if not resultado_data:
            return jsonify({'error': 'No hay resultados cargados'}), 400
        
        # Buscar la pareja en los grupos de la categoría
        grupos_categoria = resultado_data['grupos_por_categoria'].get(categoria, [])
        pareja_encontrada = False
        grupo_id = None
        
        for grupo in grupos_categoria:
            for pareja in grupo['parejas']:
                if pareja['id'] == pareja_id:
                    pareja['posicion_grupo'] = posicion
                    pareja_encontrada = True
                    grupo_id = grupo['id']
                    break
            if pareja_encontrada:
                break
        
        if not pareja_encontrada:
            return jsonify({'error': 'Pareja no encontrada'}), 404
        
        # Guardar cambios en sesión
        session['resultado_algoritmo'] = resultado_data
        session.modified = True
        
        # Verificar si ya se pueden generar las finales
        puede_generar = verificar_posiciones_completas(grupos_categoria)
        
        return jsonify({
            'success': True,
            'mensaje': f'✓ Posición {posicion}°',
            'puede_generar_finales': puede_generar
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al asignar posición: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/generar-fixture/<categoria>', methods=['POST'])
def generar_fixture(categoria):
    """Genera el fixture de finales para una categoría."""
    try:
        resultado_data = session.get('resultado_algoritmo')
        if not resultado_data:
            return jsonify({'error': 'No hay resultados cargados'}), 400
        
        # Reconstruir grupos con posiciones
        grupos_data = resultado_data['grupos_por_categoria'].get(categoria, [])
        if not grupos_data:
            return jsonify({'error': f'No hay grupos en categoría {categoria}'}), 404
        
        # Reconstruir objetos Grupo
        grupos_obj = []
        for grupo_dict in grupos_data:
            grupo = Grupo(
                id=grupo_dict['id'],
                categoria=categoria,
                franja_horaria=grupo_dict.get('franja_horaria'),
                score_compatibilidad=grupo_dict.get('score', 0.0)
            )
            
            # Reconstruir parejas con posiciones
            for pareja_dict in grupo_dict['parejas']:
                pareja = Pareja(
                    id=pareja_dict['id'],
                    nombre=pareja_dict['nombre'],
                    telefono=pareja_dict.get('telefono', 'Sin teléfono'),
                    categoria=pareja_dict['categoria'],
                    franjas_disponibles=pareja_dict.get('franjas_disponibles', []),
                    grupo_asignado=grupo_dict['id'],
                    posicion_grupo=PosicionGrupo(pareja_dict['posicion_grupo']) if pareja_dict.get('posicion_grupo') else None
                )
                grupo.parejas.append(pareja)
            
            grupos_obj.append(grupo)
        
        # Generar fixture
        generator = FixtureGenerator(grupos_obj)
        fixture = generator.generar_fixture()
        
        # Guardar fixture en sesión
        if 'fixtures' not in session:
            session['fixtures'] = {}
        session['fixtures'][categoria] = fixture.to_dict()
        session.modified = True
        
        return jsonify({
            'success': True,
            'mensaje': 'Fixture generado exitosamente',
            'fixture': fixture.to_dict()
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al generar fixture: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/obtener-fixture/<categoria>', methods=['GET'])
def obtener_fixture(categoria):
    """Obtiene el fixture de finales para una categoría."""
    try:
        fixtures = session.get('fixtures', {})
        fixture = fixtures.get(categoria)
        
        if not fixture:
            return jsonify({'fixture': None})
        
        return jsonify({
            'success': True,
            'fixture': fixture
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener fixture: {str(e)}'
        }), 500


@api_bp.route('/marcar-ganador', methods=['POST'])
def marcar_ganador():
    """Marca el ganador de un partido de finales."""
    data = request.json
    categoria = data.get('categoria')
    partido_id = data.get('partido_id')
    ganador_id = data.get('ganador_id')
    
    if not all([categoria, partido_id, ganador_id]):
        return jsonify({'error': 'Faltan parámetros requeridos'}), 400
    
    try:
        fixtures = session.get('fixtures', {})
        if categoria not in fixtures:
            return jsonify({'error': 'Fixture no encontrado'}), 404
        
        fixture_data = fixtures[categoria]
        
        # Reconstruir objetos para usar el método de actualización
        resultado_data = session.get('resultado_algoritmo')
        grupos_data = resultado_data['grupos_por_categoria'].get(categoria, [])
        
        # Reconstruir grupos
        grupos_obj = []
        for grupo_dict in grupos_data:
            grupo = Grupo(
                id=grupo_dict['id'],
                categoria=categoria,
                franja_horaria=grupo_dict.get('franja_horaria'),
                score_compatibilidad=grupo_dict.get('score', 0.0)
            )
            
            for pareja_dict in grupo_dict['parejas']:
                pareja = Pareja(
                    id=pareja_dict['id'],
                    nombre=pareja_dict['nombre'],
                    telefono=pareja_dict.get('telefono', 'Sin teléfono'),
                    categoria=pareja_dict['categoria'],
                    franjas_disponibles=pareja_dict.get('franjas_disponibles', []),
                    grupo_asignado=grupo_dict['id'],
                    posicion_grupo=PosicionGrupo(pareja_dict['posicion_grupo']) if pareja_dict.get('posicion_grupo') else None
                )
                grupo.parejas.append(pareja)
            
            grupos_obj.append(grupo)
        
        # CRUCIAL: Reconstruir el fixture DESDE LOS DATOS GUARDADOS, no generar uno nuevo
        # Esto preserva todos los ganadores anteriores
        fixture = FixtureFinales.from_dict(fixture_data, grupos_obj)
        
        # Actualizar con el ganador NUEVO
        fixture = FixtureGenerator.actualizar_fixture_con_ganador(
            fixture,
            partido_id,
            ganador_id
        )
        
        # Guardar en sesión
        fixtures[categoria] = fixture.to_dict()
        session['fixtures'] = fixtures
        session.modified = True
        
        return jsonify({
            'success': True,
            'mensaje': '✓ Ganador confirmado',
            'fixture': fixture.to_dict()
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al marcar ganador: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/calendario-finales', methods=['GET'])
def obtener_calendario_finales():
    """Obtiene el calendario de finales del domingo con los partidos asignados."""
    try:
        fixtures = session.get('fixtures', {})
        
        if not fixtures:
            # Si no hay fixtures, devolver calendario vacío con estructura
            calendario_base = CalendarioFinalesBuilder.generar_calendario_base()
            return jsonify({
                'success': True,
                'calendario': calendario_base,
                'tiene_datos': False
            })
        
        # Poblar calendario con los fixtures actuales
        calendario = CalendarioFinalesBuilder.poblar_calendario_con_fixtures(fixtures)
        
        return jsonify({
            'success': True,
            'calendario': calendario,
            'tiene_datos': True
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al generar calendario de finales: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


def verificar_posiciones_completas(grupos: list) -> bool:
    """Verifica si todas las parejas tienen posiciones asignadas."""
    for grupo in grupos:
        for pareja in grupo['parejas']:
            if not pareja.get('posicion_grupo'):
                return False
    return True
