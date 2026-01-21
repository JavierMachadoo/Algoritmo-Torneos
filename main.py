"""
Aplicación Flask para gestión de torneos de pádel.
Genera grupos optimizados según categorías y disponibilidad horaria.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import os
import logging

from config import (
    SECRET_KEY, 
    CATEGORIAS, 
    FRANJAS_HORARIAS, 
    EMOJI_CATEGORIA, 
    COLORES_CATEGORIA
)
from config.settings import BASE_DIR
from api import api_bp
from api.routes.finales import finales_bp
from utils.torneo_storage import storage
from utils.jwt_handler import JWTHandler


def crear_app():
    """Factory para crear y configurar la aplicación Flask."""
    # Configure logging - solo consola, sin archivo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    # Configuración básica
    app.secret_key = SECRET_KEY
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Inicializar JWT handler
    jwt_handler = JWTHandler(SECRET_KEY, expiration_hours=24)
    app.jwt_handler = jwt_handler  # Hacer accesible en toda la app
    
    # Registrar blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(finales_bp)
    
    # Helper para obtener datos del token o storage
    def obtener_datos_torneo():
        """Obtiene datos del torneo desde storage.
        El token JWT solo valida la sesión, no almacena datos."""
        # Siempre cargar desde storage
        torneo = storage.cargar()
        return {
            'parejas': torneo.get('parejas', []),
            'resultado_algoritmo': torneo.get('resultado_algoritmo'),
            'num_canchas': torneo.get('num_canchas', 2)
        }
    
    # Middleware: Asegurar que siempre haya un token
    @app.before_request
    def asegurar_token():
        """Asegura que cada request tenga un token válido."""
        # Skip para archivos estáticos
        if request.path.startswith('/static/'):
            return
        
        token = jwt_handler.obtener_token_desde_request()
        
        # Si no hay token o es inválido, crear uno nuevo
        if not token or not jwt_handler.verificar_token(token):
            import time
            data = {
                'session_id': 'torneo_session',
                'timestamp': int(time.time())
            }
            # El token se enviará en la respuesta
            request.token_data = data
    
    # Rutas principales
    @app.route('/')
    def inicio():
        """Página de inicio - Carga de datos."""
        datos = obtener_datos_torneo()
        parejas = datos.get('parejas', [])
        resultado = datos.get('resultado_algoritmo')
        torneo = storage.cargar()
        
        # Enriquecer parejas con información de asignación
        parejas_enriquecidas = []
        for pareja in parejas:
            pareja_info = pareja.copy()
            pareja_info['grupo_asignado'] = None
            pareja_info['franja_asignada'] = None
            pareja_info['esta_asignada'] = False
            pareja_info['fuera_de_horario'] = False
            
            # Si hay resultado del algoritmo, buscar asignación
            if resultado:
                for categoria, grupos in resultado.get('grupos_por_categoria', {}).items():
                    for grupo in grupos:
                        for p in grupo.get('parejas', []):
                            if p['id'] == pareja['id']:
                                pareja_info['grupo_asignado'] = grupo['id']
                                pareja_info['franja_asignada'] = grupo.get('franja_horaria')
                                pareja_info['esta_asignada'] = True
                                
                                # Verificar si está fuera de horario
                                franja_asignada = grupo.get('franja_horaria')
                                if franja_asignada:
                                    franjas_disponibles = pareja.get('franjas_disponibles', [])
                                    if franja_asignada not in franjas_disponibles:
                                        pareja_info['fuera_de_horario'] = True
                                break
                        if pareja_info['esta_asignada']:
                            break
                    if pareja_info['esta_asignada']:
                        break
            
            parejas_enriquecidas.append(pareja_info)
        
        # Ordenar parejas por categoría
        orden_categorias = ['Cuarta', 'Quinta', 'Sexta', 'Séptima']
        parejas_ordenadas = sorted(parejas_enriquecidas, 
                                  key=lambda p: orden_categorias.index(p.get('categoria', 'Cuarta')))
        
        # Obtener datos actuales para el header
        datos_actuales = obtener_datos_torneo()
        resultado_actual = datos_actuales.get('resultado_algoritmo')
        
        response = make_response(render_template('inicio.html', 
                             parejas=parejas_ordenadas,
                             resultado=resultado,
                             torneo=torneo,
                             categorias=CATEGORIAS,
                             franjas=FRANJAS_HORARIAS))
        
        # Si hay datos nuevos del token, actualizar la cookie
        if hasattr(request, 'token_data'):
            nuevo_token = jwt_handler.generar_token(request.token_data)
            response.set_cookie('token', nuevo_token, 
                              httponly=True, 
                              samesite='Lax',
                              max_age=60*60*24)
        
        return response
    
    @app.route('/resultados')
    def resultados():
        """Página de resultados - Visualización de grupos generados."""
        datos = obtener_datos_torneo()
        resultado = datos.get('resultado_algoritmo')
        
        if not resultado:
            flash('Primero debes generar los grupos', 'warning')
            return redirect(url_for('inicio'))
        
        torneo = storage.cargar()
        
        response = make_response(render_template('resultados.html', 
                             resultado=resultado,
                             categorias=CATEGORIAS,
                             colores=COLORES_CATEGORIA,
                             emojis=EMOJI_CATEGORIA,
                             torneo=torneo))
        
        # Actualizar token si es necesario
        if hasattr(request, 'token_data'):
            nuevo_token = jwt_handler.generar_token(request.token_data)
            response.set_cookie('token', nuevo_token, 
                              httponly=True, 
                              samesite='Lax',
                              max_age=60*60*24)
        
        return response
    
    @app.route('/finales')
    def finales():
        """Página de visualización de finales y calendario del domingo."""
        datos = obtener_datos_torneo()
        resultado = datos.get('resultado_algoritmo')
        
        if not resultado:
            flash('Primero debes generar los grupos', 'warning')
            return redirect(url_for('inicio'))
        
        torneo = storage.cargar()
        fixtures = torneo.get('fixtures_finales', {})
        
        response = make_response(render_template('finales.html',
                             fixtures=fixtures,
                             categorias=CATEGORIAS,
                             colores=COLORES_CATEGORIA,
                             emojis=EMOJI_CATEGORIA,
                             resultado=resultado,
                             torneo=torneo))
        
        # Actualizar token si es necesario
        if hasattr(request, 'token_data'):
            nuevo_token = jwt_handler.generar_token(request.token_data)
            response.set_cookie('token', nuevo_token, 
                              httponly=True, 
                              samesite='Lax',
                              max_age=60*60*24)
        
        return response
    
    return app


if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
