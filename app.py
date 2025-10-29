"""
Aplicación Flask para generación de grupos de torneo de pádel.
Diseño moderno con Bootstrap 5.
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from flask_session import Session
import pandas as pd
import os
from datetime import datetime
import json

# Importar módulos propios
from src.algoritmo import (
    AlgoritmoGrupos, 
    Pareja,
    CATEGORIAS,
    COLORES_CATEGORIA,
    FRANJAS_HORARIAS
)
from src.google_sheets import GoogleSheetsManager
from src.calendario import GeneradorCalendario
from src.exportar import ExportadorDatos

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura_aqui_123'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Asegurar que exista la carpeta de uploads
UPLOAD_FOLDER = 'data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
def inicio():
    """Página de inicio."""
    return render_template('inicio.html')


@app.route('/datos')
def datos():
    """Página de carga de datos."""
    parejas = session.get('parejas', [])
    stats = calcular_estadisticas(parejas)
    return render_template('datos.html', 
                         parejas=parejas, 
                         stats=stats,
                         categorias=CATEGORIAS,
                         franjas=FRANJAS_HORARIAS)


@app.route('/resultados')
def resultados():
    """Página de resultados."""
    resultado = session.get('resultado_algoritmo')
    
    if not resultado:
        flash('Primero debes ejecutar el algoritmo', 'warning')
        return redirect(url_for('datos'))
    
    return render_template('resultados.html', 
                         resultado=resultado,
                         categorias=CATEGORIAS,
                         colores=COLORES_CATEGORIA)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/cargar-csv', methods=['POST'])
def cargar_csv():
    """Carga un archivo CSV."""
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['archivo']
    
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'El archivo debe ser CSV'}), 400
    
    try:
        # Leer CSV
        df = pd.read_csv(file)
        parejas = procesar_dataframe(df)
        
        # Guardar en sesión
        session['parejas'] = parejas
        session.modified = True
        
        return jsonify({
            'success': True,
            'mensaje': f'✅ {len(parejas)} parejas cargadas correctamente',
            'parejas': parejas
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar CSV: {str(e)}'}), 500


@app.route('/api/agregar-pareja', methods=['POST'])
def agregar_pareja():
    """Agrega una pareja manualmente."""
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


@app.route('/api/eliminar-pareja/<int:pareja_id>', methods=['DELETE'])
def eliminar_pareja(pareja_id):
    """Elimina una pareja."""
    parejas = session.get('parejas', [])
    
    # Buscar y eliminar
    parejas = [p for p in parejas if p['id'] != pareja_id]
    
    session['parejas'] = parejas
    session.modified = True
    
    return jsonify({
        'success': True,
        'mensaje': 'Pareja eliminada correctamente'
    })


@app.route('/api/limpiar-datos', methods=['POST'])
def limpiar_datos():
    """Limpia todos los datos."""
    session.clear()
    return jsonify({
        'success': True,
        'mensaje': 'Datos limpiados correctamente'
    })


@app.route('/api/ejecutar-algoritmo', methods=['POST'])
def ejecutar_algoritmo():
    """Ejecuta el algoritmo de generación de grupos."""
    parejas_data = session.get('parejas', [])
    
    if not parejas_data:
        return jsonify({'error': 'No hay parejas cargadas'}), 400
    
    try:
        # Configuración
        num_canchas = request.json.get('num_canchas', 2)
        duracion_partido = request.json.get('duracion_partido', 1)
        
        # Convertir a objetos Pareja
        parejas_obj = [
            Pareja(
                id=p['id'],
                nombre=p['nombre'],
                telefono=p['telefono'],
                categoria=p['categoria'],
                franjas_disponibles=p['franjas_disponibles']
            )
            for p in parejas_data
        ]
        
        # Ejecutar algoritmo
        algoritmo = AlgoritmoGrupos(
            parejas=parejas_obj,
            num_canchas=num_canchas
        )
        resultado_obj = algoritmo.ejecutar()
        
        # Convertir a dict serializable
        resultado = convertir_resultado_a_dict(resultado_obj)
        
        # Guardar en sesión
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


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def procesar_dataframe(df: pd.DataFrame) -> list:
    """Convierte un DataFrame en lista de parejas."""
    parejas = []
    
    for idx, fila in df.iterrows():
        nombre = None
        telefono = None
        categoria = None
        franjas = []
        
        for key, value in fila.items():
            key_lower = key.lower()
            
            if 'nombre' in key_lower or 'pareja' in key_lower:
                nombre = str(value).strip()
            elif 'tel' in key_lower or 'teléfono' in key_lower:
                telefono = str(value).strip()
            elif 'categor' in key_lower:
                categoria = str(value).strip().title()
            elif any(franja in key for franja in FRANJAS_HORARIAS):
                if pd.notna(value) and str(value).strip():
                    for franja in FRANJAS_HORARIAS:
                        if franja in key:
                            franjas.append(franja)
                            break
        
        if nombre and categoria:
            parejas.append({
                'id': len(parejas) + 1,
                'nombre': nombre,
                'telefono': telefono or 'Sin teléfono',
                'categoria': categoria,
                'franjas_disponibles': franjas
            })
    
    return parejas


def calcular_estadisticas(parejas: list) -> dict:
    """Calcula estadísticas de las parejas."""
    stats = {
        'total': len(parejas),
        'por_categoria': {cat: 0 for cat in CATEGORIAS}
    }
    
    for pareja in parejas:
        cat = pareja.get('categoria', '')
        if cat in stats['por_categoria']:
            stats['por_categoria'][cat] += 1
    
    return stats


def convertir_resultado_a_dict(resultado) -> dict:
    """Convierte el resultado del algoritmo a diccionario."""
    grupos_dict = {}
    
    # Contador de canchas por franja horaria
    canchas_asignadas = {}  # {franja: contador}
    num_canchas = session.get('num_canchas', 2)
    
    for categoria, grupos in resultado.grupos_por_categoria.items():
        grupos_dict[categoria] = []
        
        for grupo in grupos:
            # Asignar cancha basado en la franja horaria
            franja = grupo.franja_horaria
            if franja:
                if franja not in canchas_asignadas:
                    canchas_asignadas[franja] = 0
                
                # Asignar cancha (rotar entre las disponibles)
                cancha_num = (canchas_asignadas[franja] % num_canchas) + 1
                canchas_asignadas[franja] += 1
            else:
                cancha_num = None
            
            grupos_dict[categoria].append({
                'id': grupo.id,
                'parejas': [
                    {
                        'nombre': p.nombre,
                        'telefono': p.telefono,
                        'categoria': p.categoria,
                        'franjas': p.franjas_disponibles
                    }
                    for p in grupo.parejas
                ],
                'partidos': [
                    {'pareja1': p1.nombre, 'pareja2': p2.nombre}
                    for p1, p2 in grupo.partidos
                ],
                'franja_horaria': grupo.franja_horaria,
                'cancha': cancha_num,
                'score': grupo.score_compatibilidad
            })
    
    # Organizar calendario
    calendario = organizar_calendario(resultado)
    
    return {
        'grupos_por_categoria': grupos_dict,
        'estadisticas': resultado.estadisticas,
        'parejas_sin_asignar': [
            {
                'nombre': p.nombre,
                'telefono': p.telefono,
                'categoria': p.categoria,
                'franjas': p.franjas_disponibles
            }
            for p in resultado.parejas_sin_asignar
        ],
        'calendario': calendario
    }


def organizar_calendario(resultado) -> dict:
    """Organiza los partidos en un calendario por días y horas individuales."""
    # Calendario fijo con 2 canchas por HORA (no por franja)
    calendario = {
        'Jueves': {
            '18:00': [None, None],
            '19:00': [None, None],
            '20:00': [None, None],
            '21:00': [None, None],
            '22:00': [None, None],
        },
        'Viernes': {
            '18:00': [None, None],
            '19:00': [None, None],
            '20:00': [None, None],
            '21:00': [None, None],
            '22:00': [None, None],
            '23:00': [None, None],
        },
        'Sábado': {
            '09:00': [None, None],
            '10:00': [None, None],
            '11:00': [None, None],
            '12:00': [None, None],
            '13:00': [None, None],
            '14:00': [None, None],
            '16:00': [None, None],
            '17:00': [None, None],
            '18:00': [None, None],
            '19:00': [None, None],
            '20:00': [None, None],
            '21:00': [None, None],
        }
    }
    
    # Mapeo de franjas a días y lista de horas dentro de esa franja
    franjas_a_horas = {
        'Jueves 18:00': ('Jueves', ['18:00', '19:00', '20:00']),
        'Jueves 20:00': ('Jueves', ['20:00', '21:00', '22:00']),
        'Viernes 18:00': ('Viernes', ['18:00', '19:00', '20:00']),
        'Viernes 21:00': ('Viernes', ['21:00', '22:00', '23:00']),
        'Sábado 09:00': ('Sábado', ['09:00', '10:00', '11:00']),
        'Sábado 9:00': ('Sábado', ['09:00', '10:00', '11:00']),
        'Sábado 12:00': ('Sábado', ['12:00', '13:00', '14:00']),
        'Sábado 16:00': ('Sábado', ['16:00', '17:00', '18:00']),
        'Sábado 19:00': ('Sábado', ['19:00', '20:00', '21:00']),
    }
    
    # Recorrer todos los grupos y asignar a las canchas
    for categoria, grupos in resultado.grupos_por_categoria.items():
        for grupo in grupos:
            if not grupo.franja_horaria:
                continue
            
            franja_grupo = grupo.franja_horaria
            print(f"DEBUG: Procesando grupo {grupo.id} de {categoria} con franja: '{franja_grupo}'")
            print(f"  Partidos en el grupo: {len(grupo.partidos)}")
            
            # Buscar coincidencia en el mapeo
            encontrado = False
            for franja_key, (dia, horas_disponibles) in franjas_a_horas.items():
                if franja_key in franja_grupo:
                    # Este grupo tiene múltiples partidos (todos contra todos)
                    # Distribuirlos en las horas disponibles de la franja
                    
                    hora_idx = 0
                    for partido_num, (p1, p2) in enumerate(grupo.partidos):
                        # Rotar entre las horas disponibles
                        if hora_idx >= len(horas_disponibles):
                            print(f"  -> ADVERTENCIA: Más partidos que horas disponibles")
                            break
                        
                        hora = horas_disponibles[hora_idx]
                        
                        # Buscar cancha libre en esa hora
                        cancha_idx = None
                        if calendario[dia][hora][0] is None:
                            cancha_idx = 0
                        elif calendario[dia][hora][1] is None:
                            cancha_idx = 1
                        else:
                            print(f"  -> ADVERTENCIA: Ambas canchas ocupadas en {dia} {hora}")
                            hora_idx += 1
                            continue
                        
                        # Crear el partido
                        partido = {
                            'categoria': categoria,
                            'grupo_id': grupo.id,
                            'pareja1': p1.nombre,
                            'pareja2': p2.nombre
                        }
                        
                        # Asignar a la cancha
                        calendario[dia][hora][cancha_idx] = partido
                        print(f"  -> Partido {partido_num + 1}: {dia} {hora} Cancha {cancha_idx + 1}")
                        
                        # Siguiente hora para el próximo partido
                        hora_idx += 1
                    
                    encontrado = True
                    break
            
            if not encontrado:
                print(f"  -> NO ENCONTRADO en el mapeo")
    
    print(f"\nDEBUG: Calendario final:")
    for dia, horas in calendario.items():
        print(f"  {dia}:")
        for hora, canchas in horas.items():
            ocupadas = sum(1 for c in canchas if c is not None)
            if ocupadas > 0:
                print(f"    {hora}: {ocupadas}/2 canchas ocupadas")
    
    return calendario


# ============================================================================
# EJECUTAR APLICACIÓN
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
