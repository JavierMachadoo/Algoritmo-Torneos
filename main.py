"""
Aplicación Flask para gestión de torneos de pádel.
Genera grupos optimizados según categorías y disponibilidad horaria.
"""

from flask import Flask, render_template, session, redirect, url_for, flash

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
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    # Configuración básica
    app.secret_key = SECRET_KEY
    app.config['SESSION_PERMANENT'] = False
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
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
        
        return render_template('inicio.html', 
                             parejas=parejas,
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
