"""
Aplicación Flask para gestión de torneos de pádel.
Genera grupos optimizados según categorías y disponibilidad horaria.
"""

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_session import Session
import os
import shutil

from config import (
    SECRET_KEY, 
    SESSION_TYPE, 
    CATEGORIAS, 
    FRANJAS_HORARIAS, 
    EMOJI_CATEGORIA, 
    COLORES_CATEGORIA
)
from api import api_bp


def crear_app():
    """Factory para crear y configurar la aplicación Flask."""
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    # Configuración básica
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = SESSION_TYPE
    app.config['SESSION_PERMANENT'] = False
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    Session(app)
    
    # Headers anti-cache para desarrollo (fuerza recarga siempre)
    @app.after_request
    def add_no_cache_headers(response):
        if app.debug:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Last-Modified'] = 'Mon, 01 Jan 2024 00:00:00 GMT'
        return response
    
    # Registrar blueprints
    app.register_blueprint(api_bp)
    
    # Rutas principales
    @app.route('/')
    def inicio():
        """Página de inicio del sistema."""
        return render_template('inicio.html')
    
    @app.route('/datos')
    def datos():
        """Página de gestión de parejas."""
        parejas = session.get('parejas', [])
        stats = _calcular_estadisticas(parejas)
        return render_template('datos.html', 
                             parejas=parejas, 
                             stats=stats,
                             categorias=CATEGORIAS,
                             franjas=FRANJAS_HORARIAS)
    
    @app.route('/resultados')
    def resultados():
        """Página de visualización de grupos generados."""
        resultado = session.get('resultado_algoritmo')
        
        if not resultado:
            flash('Primero debes ejecutar el algoritmo', 'warning')
            return redirect(url_for('datos'))
        
        return render_template('resultados.html', 
                             resultado=resultado,
                             categorias=CATEGORIAS,
                             colores=COLORES_CATEGORIA,
                             emojis=EMOJI_CATEGORIA)
    
    return app


def _calcular_estadisticas(parejas):
    """Calcula estadísticas básicas de las parejas cargadas."""
    stats = {
        'total': len(parejas),
        'por_categoria': {cat: 0 for cat in CATEGORIAS}
    }
    
    for pareja in parejas:
        cat = pareja.get('categoria', '')
        if cat in stats['por_categoria']:
            stats['por_categoria'][cat] += 1
    
    return stats


def _limpiar_sesiones_antiguas():
    """Elimina archivos de sesión antiguos al iniciar en modo desarrollo."""
    session_dir = 'flask_session'
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        print(f"✓ Sesiones antiguas eliminadas de {session_dir}/")


if __name__ == '__main__':
    _limpiar_sesiones_antiguas()
    
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
