from flask import Blueprint, request, jsonify, session
import pandas as pd

from core import Pareja, AlgoritmoGrupos
from utils import CSVProcessor, CalendarioBuilder
from config import CATEGORIAS, FRANJAS_HORARIAS

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/cargar-csv', methods=['POST'])
def cargar_csv():
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
    session.clear()
    return jsonify({
        'success': True,
        'mensaje': 'Datos limpiados correctamente'
    })


@api_bp.route('/ejecutar-algoritmo', methods=['POST'])
def ejecutar_algoritmo():
    parejas_data = session.get('parejas', [])
    
    if not parejas_data:
        return jsonify({'error': 'No hay parejas cargadas'}), 400
    
    try:
        num_canchas = request.json.get('num_canchas', 2)
        
        parejas_obj = [Pareja.from_dict(p) for p in parejas_data]
        
        algoritmo = AlgoritmoGrupos(parejas=parejas_obj, num_canchas=num_canchas)
        resultado_obj = algoritmo.ejecutar()
        
        resultado = convertir_resultado_a_dict(resultado_obj, num_canchas)
        
        session['resultado_algoritmo'] = resultado
        session['num_canchas'] = num_canchas
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


def convertir_resultado_a_dict(resultado, num_canchas):
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
