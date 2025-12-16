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
    
    # Rutas principales
    @app.route('/')
    def inicio():
        """Página de inicio del sistema."""
        torneos = storage.listar_todos()
        torneo_actual_id = session.get('torneo_actual')
        torneo_actual = None
        
        if torneo_actual_id:
            torneo_actual = storage.cargar(torneo_actual_id)
        
        return render_template('inicio.html', 
                             torneos=torneos,
                             torneo_actual=torneo_actual)
    
    @app.route('/datos')
    def datos():
        """Página de gestión de parejas."""
        # Asegurar que hay un torneo activo
        torneo_id = session.get('torneo_actual')
        if not torneo_id:
            # Crear torneo automáticamente si no existe
            torneo_id = storage.crear_torneo()
            session['torneo_actual'] = torneo_id
            session['parejas'] = []
            session.modified = True
        
        parejas = session.get('parejas', [])
        stats = _calcular_estadisticas(parejas)
        
        # Obtener info del torneo
        torneo = storage.cargar(torneo_id)
        
        return render_template('datos.html', 
                             parejas=parejas, 
                             stats=stats,
                             categorias=CATEGORIAS,
                             franjas=FRANJAS_HORARIAS,
                             torneo=torneo)
    
    @app.route('/resultados')
    def resultados():
        """Página de visualización de grupos generados."""
        resultado = session.get('resultado_algoritmo')
        
        if not resultado:
            flash('Primero debes ejecutar el algoritmo', 'warning')
            return redirect(url_for('datos'))
        
        # Obtener info del torneo
        torneo_id = session.get('torneo_actual')
        torneo = storage.cargar(torneo_id) if torneo_id else None
        
        return render_template('resultados.html', 
                             resultado=resultado,
                             categorias=CATEGORIAS,
                             colores=COLORES_CATEGORIA,
                             emojis=EMOJI_CATEGORIA,
                             torneo=torneo)
    
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


if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
