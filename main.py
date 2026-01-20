"""
Aplicación Flask para gestión de torneos de pádel.
Genera grupos optimizados según categorías y disponibilidad horaria.
"""

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_session import Session
import os
import logging

from config import (
    SECRET_KEY, 
    CATEGORIAS, 
    FRANJAS_HORARIAS, 
    EMOJI_CATEGORIA, 
    COLORES_CATEGORIA
)
from api import api_bp
from utils.torneo_storage import storage


def crear_app():
    """Factory para crear y configurar la aplicación Flask."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    # Configuración básica
    app.secret_key = SECRET_KEY
    
    # Configuración de sesiones del lado del servidor
    app.config['SESSION_TYPE'] = 'filesystem'  # Guardar sesiones en archivos
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True  # Firmar cookies de sesión para seguridad
    app.config['SESSION_KEY_PREFIX'] = 'torneo_'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Crear directorio de sesiones si no existe
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Inicializar Flask-Session
    Session(app)
    
    # Registrar blueprints
    app.register_blueprint(api_bp)
    
    # Middleware: Sincronizar sesión con almacenamiento
    @app.before_request
    def cargar_torneo():
        """Carga el torneo actual en la sesión si no está cargado."""
        if 'parejas' not in session:
            torneo = storage.cargar()
            session['parejas'] = torneo.get('parejas', [])
            session['resultado_algoritmo'] = torneo.get('resultado_algoritmo')
            session['num_canchas'] = torneo.get('num_canchas', 2)
            session.modified = True
    
    # Rutas principales
    @app.route('/')
    def inicio():
        """Página de inicio - Carga de datos."""
        parejas = session.get('parejas', [])
        resultado = session.get('resultado_algoritmo')
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
        
        return render_template('inicio.html', 
                             parejas=parejas_ordenadas,
                             resultado=resultado,
                             torneo=torneo,
                             categorias=CATEGORIAS,
                             franjas=FRANJAS_HORARIAS)
    
    @app.route('/datos')
    def datos():
        """Redirige a inicio - ya no se usa esta página."""
        return redirect(url_for('inicio'))
    
    @app.route('/resultados')
    def resultados():
        """Página de visualización de grupos generados."""
        resultado = session.get('resultado_algoritmo')
        
        if not resultado:
            flash('Primero debes generar los grupos', 'warning')
            return redirect(url_for('inicio'))
        
        torneo = storage.cargar()
        
        return render_template('resultados.html', 
                             resultado=resultado,
                             categorias=CATEGORIAS,
                             colores=COLORES_CATEGORIA,
                             emojis=EMOJI_CATEGORIA,
                             torneo=torneo)
    
    return app


if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
