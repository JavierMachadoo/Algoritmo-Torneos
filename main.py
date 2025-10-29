from flask import Flask, render_template, session, redirect, url_for, flash
from flask_session import Session

from config import SECRET_KEY, SESSION_TYPE, CATEGORIAS, FRANJAS_HORARIAS, EMOJI_CATEGORIA, COLORES_CATEGORIA
from api import api_bp


def crear_app():
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = SESSION_TYPE
    Session(app)
    
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def inicio():
        return render_template('inicio.html')
    
    @app.route('/datos')
    def datos():
        parejas = session.get('parejas', [])
        stats = calcular_estadisticas(parejas)
        return render_template('datos.html', 
                             parejas=parejas, 
                             stats=stats,
                             categorias=CATEGORIAS,
                             franjas=FRANJAS_HORARIAS)
    
    @app.route('/resultados')
    def resultados():
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


def calcular_estadisticas(parejas):
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
