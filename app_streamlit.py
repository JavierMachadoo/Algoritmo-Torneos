"""
Aplicación web mejorada para generación de grupos de torneo de pádel.
Interfaz paso a paso con Streamlit.
"""

import streamlit as st
import pandas as pd
from typing import Optional
import os
from datetime import datetime

# Importar módulos propios
from src.algoritmo import (
    AlgoritmoGrupos, 
    crear_pareja_desde_dict, 
    Pareja,
    CATEGORIAS,
    COLORES_CATEGORIA,
    FRANJAS_HORARIAS
)
from src.google_sheets import GoogleSheetsManager
from src.calendario import GeneradorCalendario
from src.exportar import ExportadorDatos


# Configuración de la página
st.set_page_config(
    page_title="Torneo de Pádel - Generador de Grupos",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def inicializar_session_state():
    """Inicializa variables de estado de la sesión."""
    if 'parejas' not in st.session_state:
        st.session_state.parejas = []
    if 'resultado_algoritmo' not in st.session_state:
        st.session_state.resultado_algoritmo = None
    if 'google_sheets_manager' not in st.session_state:
        st.session_state.google_sheets_manager = None
    if 'pagina' not in st.session_state:
        st.session_state.pagina = 'inicio'  # 'inicio', 'datos_cargados', 'resultados'
    if 'num_canchas' not in st.session_state:
        st.session_state.num_canchas = 2
    if 'duracion_partido' not in st.session_state:
        st.session_state.duracion_partido = 1


def cargar_css_personalizado():
    """Carga estilos CSS personalizados."""
    st.markdown("""
        <style>
        /* Header principal */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: bold;
        }
        .main-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Cards de estadísticas */
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            margin: 0.5rem 0;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        /* Grupos */
        .grupo-card {
            background: white;
            border-left: 5px solid;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .grupo-cuarta { border-left-color: #90EE90; background: #f0fff0; }
        .grupo-quinta { border-left-color: #FFD700; background: #fffef0; }
        .grupo-sexta { border-left-color: #87CEEB; background: #f0f8ff; }
        .grupo-septima { border-left-color: #DDA0DD; background: #fff0ff; }
        
        .grupo-header {
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ddd;
        }
        
        .pareja-info {
            margin: 0.8rem 0;
            padding: 0.8rem;
            background: rgba(255,255,255,0.5);
            border-radius: 5px;
        }
        
        .pareja-nombre {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .pareja-detalle {
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.3rem;
        }
        
        /* Calendario visual */
        .calendario-grid {
            display: grid;
            grid-template-columns: 100px repeat(3, 1fr);
            gap: 10px;
            margin: 1rem 0;
        }
        
        .calendario-header {
            background: #667eea;
            color: white;
            padding: 1rem;
            text-align: center;
            font-weight: bold;
            border-radius: 8px;
        }
        
        .calendario-cell {
            padding: 0.8rem;
            border-radius: 8px;
            min-height: 100px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .partido-bloque {
            padding: 0.8rem;
            margin: 0.3rem 0;
            border-radius: 5px;
            font-size: 0.85rem;
            border-left: 4px solid;
        }
        
        .partido-cuarta { 
            background: #90EE90; 
            border-left-color: #228B22;
            color: #004d00;
        }
        .partido-quinta { 
            background: #FFD700; 
            border-left-color: #B8860B;
            color: #664d00;
        }
        .partido-sexta { 
            background: #87CEEB; 
            border-left-color: #4682B4;
            color: #003d66;
        }
        .partido-septima { 
            background: #DDA0DD; 
            border-left-color: #9370DB;
            color: #4d004d;
        }
        
        /* Alertas personalizadas */
        .alert-info {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .alert-success {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .alert-warning {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        /* Tabla de datos */
        .dataframe {
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    """Función principal de la aplicación."""
    # Inicializar
    inicializar_session_state()
    cargar_css_personalizado()
    
    # Header principal
    st.markdown("""
        <div class="main-header">
            <h1>🎾 Generador de Grupos - Torneo de Pádel</h1>
            <p>Sistema inteligente de formación de grupos por compatibilidad horaria</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Enrutamiento según página
    if st.session_state.pagina == 'inicio':
        pagina_inicio()
    elif st.session_state.pagina == 'datos_cargados':
        pagina_datos_cargados()
    elif st.session_state.pagina == 'resultados':
        pagina_resultados()


def pagina_inicio():
    """Página principal con botón para ingresar datos."""
    st.title("¡Bienvenido!")
    
    st.markdown("""
        <div class="alert-info">
            <h3>📋 Sistema de Generación de Grupos</h3>
            <p>Este sistema te ayudará a crear grupos óptimos para tu torneo de pádel,
            considerando las categorías y disponibilidad horaria de cada pareja.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 ¿Cómo funciona?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem;">📥</div>
                <h4>1. Ingresar Datos</h4>
                <p>Carga las parejas desde CSV, Google Sheets o manualmente</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem;">🤖</div>
                <h4>2. Ejecutar Algoritmo</h4>
                <p>El sistema genera grupos compatibles automáticamente</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem;">📊</div>
                <h4>3. Ver Resultados</h4>
                <p>Consulta los grupos y el calendario de partidos</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Botón principal grande
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 INGRESAR DATOS", type="primary", use_container_width=True, 
                    key="btn_ingresar", help="Comienza cargando los datos de las parejas"):
            st.session_state.pagina = 'datos_cargados'
            st.rerun()


def pagina_datos_cargados():
    """Página que muestra los datos cargados y botón para ejecutar algoritmo."""
    st.title("📊 Datos Cargados")
    
    # Botón para volver
    if st.button("← Volver a cargar más datos"):
        st.session_state.pagina = 'inicio'
        st.rerun()
    
    st.markdown("---")
    
    # Si no hay datos cargados, mostrar interfaz de carga
    if not st.session_state.parejas:
        mostrar_interfaz_carga()
        return
    
    # Estadísticas generales
    st.subheader("📈 Resumen General")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total = len(st.session_state.parejas)
    parejas_por_cat = {cat: len([p for p in st.session_state.parejas if p.categoria == cat]) 
                       for cat in CATEGORIAS}
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Parejas</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{parejas_por_cat.get("Cuarta", 0)}</div>
                <div class="stat-label">🟢 Cuarta</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{parejas_por_cat.get("Quinta", 0)}</div>
                <div class="stat-label">🟡 Quinta</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{parejas_por_cat.get("Sexta", 0)}</div>
                <div class="stat-label">🔵 Sexta</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{parejas_por_cat.get("Séptima", 0)}</div>
                <div class="stat-label"> Séptima</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabla de datos
    st.subheader("📋 Listado Completo de Parejas")
    
    # Crear DataFrame para mostrar
    datos_tabla = []
    for pareja in st.session_state.parejas:
        datos_tabla.append({
            'Nombre': pareja.nombre,
            'Teléfono': pareja.telefono,
            'Categoría': pareja.categoria,
            'Horarios Disponibles': ', '.join(pareja.franjas_disponibles) if pareja.franjas_disponibles else 'No especificado'
        })
    
    df = pd.DataFrame(datos_tabla)
    st.dataframe(df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Configuración y botón de ejecutar
    st.subheader("⚙️ Configuración del Algoritmo")
    
    col1, col2 = st.columns(2)
    with col1:
        num_canchas = st.number_input(
            "Número de canchas disponibles",
            min_value=1,
            max_value=4,
            value=2
        )
        st.session_state.num_canchas = num_canchas
    
    with col2:
        duracion = st.number_input(
            "Duración de cada partido (horas)",
            min_value=1,
            max_value=3,
            value=1
        )
        st.session_state.duracion_partido = duracion
    
    st.markdown("---")
    
    # Botón grande para ejecutar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 EJECUTAR ALGORITMO", type="primary", use_container_width=True,
                    key="btn_ejecutar", help="Genera los grupos óptimos"):
            with st.spinner("⏳ Generando grupos óptimos..."):
                try:
                    algoritmo = AlgoritmoGrupos(
                        parejas=st.session_state.parejas,
                        num_canchas=num_canchas
                    )
                    resultado = algoritmo.ejecutar()
                    st.session_state.resultado_algoritmo = resultado
                    st.session_state.pagina = 'resultados'
                    st.success("✅ ¡Grupos generados exitosamente!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al ejecutar el algoritmo: {str(e)}")
                    import traceback
                    with st.expander("Ver detalles del error"):
                        st.code(traceback.format_exc())


def mostrar_interfaz_carga():
    """Muestra la interfaz para cargar datos."""
    st.subheader("Selecciona cómo cargar los datos:")
    
    tab1, tab2, tab3 = st.tabs(["📁 Importar CSV", "📊 Google Sheets", "✍️ Entrada Manual"])
    
    with tab1:
        cargar_desde_csv()
    
    with tab2:
        cargar_desde_google_sheets()
    
    with tab3:
        entrada_manual()


def pagina_resultados():
    """Página de resultados con tabs por categoría y calendario general."""
    st.title("🏆 Resultados del Torneo")
    
    resultado = st.session_state.resultado_algoritmo
    
    # Botones de navegación
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button("← Volver a datos", use_container_width=True):
            st.session_state.pagina = 'datos_cargados'
            st.rerun()
    with col2:
        if st.button("🔄 Ejecutar de nuevo", use_container_width=True):
            st.session_state.resultado_algoritmo = None
            st.session_state.pagina = 'datos_cargados'
            st.rerun()
    with col3:
        if st.button("📤 Exportar", use_container_width=True, type="primary"):
            mostrar_opciones_exportacion(resultado)
    
    st.markdown("---")
    
    # Estadísticas generales
    stats = resultado.estadisticas
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{stats['parejas_asignadas']}/{stats['total_parejas']}</div>
                <div class="stat-label">Parejas Asignadas</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{stats['porcentaje_asignacion']:.0f}%</div>
                <div class="stat-label">Tasa de Asignación</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{stats['total_grupos']}</div>
                <div class="stat-label">Grupos Formados</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{stats['score_compatibilidad_promedio']:.2f}/3.0</div>
                <div class="stat-label">Calidad Promedio</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Crear tabs: una por categoría + una general
    categorias_con_grupos = [cat for cat in CATEGORIAS if cat in resultado.grupos_por_categoria 
                             and resultado.grupos_por_categoria[cat]]
    
    tabs_nombres = [f"{COLORES_CATEGORIA.get(cat, '⚪')} {cat}" for cat in categorias_con_grupos]
    tabs_nombres.append("📅 Calendario General")
    
    tabs = st.tabs(tabs_nombres)
    
    # Mostrar grupos por categoría
    for idx, categoria in enumerate(categorias_con_grupos):
        with tabs[idx]:
            mostrar_grupos_categoria(categoria, resultado.grupos_por_categoria[categoria])
    
    # Tab de calendario general
    with tabs[-1]:
        mostrar_calendario_general(resultado)


def cargar_desde_csv():
    """Interfaz para cargar desde archivo CSV."""
    st.markdown('<div class="alert-info">📄 Carga un archivo CSV con las respuestas del formulario</div>', 
               unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Selecciona el archivo CSV",
        type=['csv'],
        help="El archivo debe tener las columnas: Nombre, Teléfono, Categoría, y franjas horarias"
    )
    
    if uploaded_file:
        try:
            # Leer CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Archivo cargado: {len(df)} filas encontradas")
            
            # Preview
            with st.expander("👁️ Vista previa de datos"):
                st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("✅ Confirmar y cargar parejas", type="primary", use_container_width=True):
                parejas = procesar_csv_a_parejas(df)
                st.session_state.parejas = parejas
                st.success(f"🎉 {len(parejas)} parejas cargadas correctamente!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")


def procesar_csv_a_parejas(df):
    """Procesa un DataFrame y lo convierte a lista de Parejas."""
    parejas = []
    
    for idx, fila in df.iterrows():
        # Extraer datos básicos
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
                    # Buscar qué franja es
                    for franja in FRANJAS_HORARIAS:
                        if franja in key:
                            franjas.append(franja)
                            break
        
        if nombre and categoria:
            pareja = Pareja(
                id=idx + 1,
                nombre=nombre,
                telefono=telefono or "Sin teléfono",
                categoria=categoria,
                franjas_disponibles=franjas
            )
            parejas.append(pareja)
    
    return parejas


def cargar_desde_google_sheets():
    """Interfaz para cargar desde Google Sheets."""
    st.markdown('<div class="alert-info">📊 Conecta con Google Sheets para importar datos automáticamente</div>', 
               unsafe_allow_html=True)
    
    st.warning("⚠️ Requiere configuración previa de Google Cloud API. Ver INSTALACION.md")
    
    credentials_path = st.text_input(
        "Ruta al archivo credentials.json",
        value="data/credentials.json"
    )
    
    if os.path.exists(credentials_path):
        st.success("✅ Archivo de credenciales encontrado")
        
        if st.button("🔗 Conectar con Google Sheets"):
            try:
                with st.spinner("Conectando..."):
                    manager = GoogleSheetsManager(credentials_path)
                    st.session_state.google_sheets_manager = manager
                    st.success("¡Conectado exitosamente!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        if st.session_state.google_sheets_manager:
            spreadsheet_id = st.text_input(
                "ID del Google Spreadsheet",
                help="Está en la URL del Google Sheet"
            )
            
            if spreadsheet_id:
                try:
                    hojas = st.session_state.google_sheets_manager.obtener_hojas_disponibles(spreadsheet_id)
                    hoja = st.selectbox("Selecciona la hoja", hojas)
                    
                    if st.button("📥 Importar datos", type="primary"):
                        with st.spinner("Importando..."):
                            datos = st.session_state.google_sheets_manager.importar_respuestas_form(
                                spreadsheet_id, hoja
                            )
                            parejas = [crear_pareja_desde_dict(d, d['id']) for d in datos]
                            st.session_state.parejas = parejas
                            st.success(f"✅ {len(parejas)} parejas importadas!")
                            st.balloons()
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.error("❌ Archivo de credenciales no encontrado")


def entrada_manual():
    """Interfaz para entrada manual de parejas."""
    st.markdown('<div class="alert-info">✍️ Ingresa las parejas manualmente una por una</div>', 
               unsafe_allow_html=True)
    
    with st.form("form_agregar_pareja", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre de la pareja *", placeholder="Ej: Juan Pérez / María López")
            categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        with col2:
            telefono = st.text_input("Teléfono", placeholder="Ej: 099123456")
        
        st.write("**Franjas horarias disponibles:**")
        franjas_seleccionadas = st.multiselect(
            "Selecciona todas las franjas en las que pueden jugar",
            FRANJAS_HORARIAS,
            help="Selecciona al menos 2 franjas horarias"
        )
        
        submitted = st.form_submit_button("➕ Agregar Pareja", use_container_width=True, type="primary")
        
        if submitted:
            if not nombre:
                st.error("❌ El nombre es obligatorio")
            elif not franjas_seleccionadas:
                st.error("❌ Selecciona al menos una franja horaria")
            else:
                nueva_pareja = Pareja(
                    id=len(st.session_state.parejas) + 1,
                    nombre=nombre,
                    telefono=telefono or "Sin teléfono",
                    categoria=categoria,
                    franjas_disponibles=franjas_seleccionadas
                )
                st.session_state.parejas.append(nueva_pareja)
                st.success(f"✅ Pareja '{nombre}' agregada correctamente")
                st.rerun()
    
    # Lista de parejas agregadas
    if st.session_state.parejas:
        st.markdown("---")
        st.subheader(f"Parejas agregadas ({len(st.session_state.parejas)})")
        
        for i, pareja in enumerate(st.session_state.parejas):
            with st.expander(f"{COLORES_CATEGORIA.get(pareja.categoria, '⚪')} {pareja.nombre}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Categoría:** {pareja.categoria}")
                with col2:
                    st.write(f"**Teléfono:** {pareja.telefono}")
                with col3:
                    if st.button("🗑️ Eliminar", key=f"del_{i}"):
                        st.session_state.parejas.pop(i)
                        st.rerun()
                
                st.write(f"**Franjas:** {', '.join(pareja.franjas_disponibles) if pareja.franjas_disponibles else 'Ninguna'}")


def exportar_google_sheets(resultado):
    """Exportar a Google Sheets."""
    st.markdown('<div class="alert-info">📊 Exporta los grupos directamente a una hoja de Google Sheets</div>',
               unsafe_allow_html=True)
    
    if not st.session_state.google_sheets_manager:
        st.warning("⚠️ Primero debes conectar con Google Sheets en el paso de carga de datos")
        return
    
    spreadsheet_id = st.text_input(
        "ID del Google Spreadsheet (destino)",
        help="Puede ser el mismo del formulario u otro diferente"
    )
    
    nombre_hoja = st.text_input(
        "Nombre de la nueva hoja",
        value=f"Grupos_Torneo_{datetime.now().strftime('%Y%m%d_%H%M')}"
    )
    
    if st.button("📤 Exportar a Google Sheets", type="primary", use_container_width=True):
        if not spreadsheet_id:
            st.error("❌ Ingresa el ID del spreadsheet")
            return
        
        try:
            with st.spinner("Exportando..."):
                url = st.session_state.google_sheets_manager.exportar_grupos(
                    spreadsheet_id,
                    resultado,
                    nombre_hoja
                )
                st.success("✅ ¡Exportado exitosamente!")
                st.markdown(f"[🔗 Abrir Google Sheet]({url})")
                st.balloons()
        except Exception as e:
            st.error(f"❌ Error al exportar: {str(e)}")


def exportar_archivos(resultado):
    """Descargar archivos locales."""
    st.markdown('<div class="alert-info">📁 Descarga los resultados en diferentes formatos</div>',
               unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV
        try:
            exportador = ExportadorDatos()
            archivo_csv = f"grupos_torneo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            exportador.exportar_csv_grupos(resultado, archivo_csv)
            
            with open(archivo_csv, 'rb') as f:
                st.download_button(
                    "📥 Descargar CSV",
                    data=f.read(),
                    file_name=archivo_csv,
                    mime="text/csv",
                    use_container_width=True
                )
        except:
            pass
    
    with col2:
        # JSON
        try:
            exportador = ExportadorDatos()
            archivo_json = f"grupos_torneo_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            exportador.exportar_json(resultado, archivo_json)
            
            with open(archivo_json, 'r', encoding='utf-8') as f:
                st.download_button(
                    "📥 Descargar JSON",
                    data=f.read(),
                    file_name=archivo_json,
                    mime="application/json",
                    use_container_width=True
                )
        except:
            pass
    
    with col3:
        # TXT (calendario)
        generador = GeneradorCalendario()
        texto = generador.exportar_calendario_texto(resultado)
        
        st.download_button(
            "📥 Descargar TXT",
            data=texto,
            file_name=f"calendario_torneo_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )


def exportar_texto(resultado):
    """Copiar como texto."""
    st.markdown('<div class="alert-info">📋 Copia el texto para compartir por WhatsApp, email, etc.</div>',
               unsafe_allow_html=True)
    
    generador = GeneradorCalendario()
    texto = generador.exportar_calendario_texto(resultado)
    
    st.text_area("Calendario en texto", texto, height=400)
    
    st.info("💡 Selecciona todo el texto (Ctrl+A) y cópialo (Ctrl+C)")


def mostrar_grupos_categoria(categoria: str, grupos: list):
    """Muestra los grupos de una categoría específica."""
    st.subheader(f"Grupos de {categoria}")
    
    if not grupos:
        st.info(f"No hay grupos formados en la categoría {categoria}")
        return
    
    st.markdown(f"**{len(grupos)} grupos formados**")
    st.markdown("---")
    
    # Determinar clase CSS según categoría
    clase_css = {
        "Cuarta": "grupo-cuarta",
        "Quinta": "grupo-quinta",
        "Sexta": "grupo-sexta",
        "Séptima": "grupo-septima"
    }.get(categoria, "")
    
    for grupo in grupos:
        st.markdown(f'<div class="grupo-card {clase_css}">', unsafe_allow_html=True)
        
        # Header del grupo
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<div class="grupo-header">Grupo {grupo.id}</div>', unsafe_allow_html=True)
        with col2:
            score_emoji = "🟢" if grupo.score_compatibilidad >= 3.0 else "🟡" if grupo.score_compatibilidad >= 2.0 else "🔴"
            st.markdown(f"**{score_emoji} Score: {grupo.score_compatibilidad:.1f}/3.0**")
        
        # Información de horario
        if grupo.franja_horaria:
            st.markdown(f"**🕐 Horario del Grupo:** {grupo.franja_horaria}")
        
        st.markdown("---")
        
        # Parejas del grupo
        st.markdown("**👥 Parejas:**")
        for i, pareja in enumerate(grupo.parejas, 1):
            st.markdown(f'<div class="pareja-info">', unsafe_allow_html=True)
            st.markdown(f'<div class="pareja-nombre">{i}. {pareja.nombre}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pareja-detalle">📞 Teléfono: {pareja.telefono}</div>', unsafe_allow_html=True)
            
            # Mostrar horarios disponibles de cada pareja
            if pareja.franjas_disponibles:
                horarios_str = ", ".join(pareja.franjas_disponibles)
                st.markdown(f'<div class="pareja-detalle">🕐 Horarios elegidos: {horarios_str}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="pareja-detalle">🕐 Sin horarios especificados</div>', 
                           unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Partidos del grupo
        st.markdown("**🏆 Partidos (todos contra todos):**")
        for idx, (p1, p2) in enumerate(grupo.partidos, 1):
            st.markdown(f"• Partido {idx}: **{p1.nombre}** vs **{p2.nombre}**")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


def mostrar_calendario_general(resultado):
    """Muestra el calendario general con las 2 canchas y los días."""
    st.subheader("📅 Calendario de Partidos - Vista General")
    
    st.markdown('<div class="alert-info">📌 Este calendario muestra la organización de partidos en las canchas disponibles</div>',
               unsafe_allow_html=True)
    
    # Organizar partidos por día y franja horaria
    partidos_organizados = organizar_partidos_por_dia(resultado)
    
    if not partidos_organizados:
        st.warning("No hay partidos programados con horarios específicos")
        return
    
    # Días de la semana
    dias = ['Jueves', 'Viernes', 'Sábado']
    
    for dia in dias:
        if dia not in partidos_organizados or not partidos_organizados[dia]:
            continue
        
        st.markdown(f"### 📆 {dia}")
        
        # Crear columnas: hora + canchas
        col_hora, col_cancha1, col_cancha2 = st.columns([1, 3, 3])
        
        with col_hora:
            st.markdown("**Horario**")
        with col_cancha1:
            st.markdown("**🏟️ Cancha 1**")
        with col_cancha2:
            st.markdown("**🏟️ Cancha 2**")
        
        # Obtener todas las franjas horarias únicas del día
        franjas_dia = sorted(partidos_organizados[dia].keys())
        
        for franja in franjas_dia:
            col_hora, col_cancha1, col_cancha2 = st.columns([1, 3, 3])
            
            with col_hora:
                st.markdown(f"**{franja}**")
            
            partidos_franja = partidos_organizados[dia][franja]
            
            # Distribuir en canchas (máximo 2)
            with col_cancha1:
                if len(partidos_franja) > 0:
                    mostrar_partido_en_calendario(partidos_franja[0])
                else:
                    st.markdown("—")
            
            with col_cancha2:
                if len(partidos_franja) > 1:
                    mostrar_partido_en_calendario(partidos_franja[1])
                else:
                    st.markdown("—")
        
        st.markdown("---")


def organizar_partidos_por_dia(resultado):
    """Organiza los partidos por día y franja horaria."""
    partidos_por_dia = {
        'Jueves': {},
        'Viernes': {},
        'Sábado': {}
    }
    
    # Mapeo de franjas a días
    franjas_a_dia = {
        'Jueves 18:00-21:00': ('Jueves', '18:00-21:00'),
        'Jueves 20:00-23:00': ('Jueves', '20:00-23:00'),
        'Viernes 18:00-21:00': ('Viernes', '18:00-21:00'),
        'Viernes 21:00-00:00': ('Viernes', '21:00-00:00'),
        'Sábado 09:00-12:00': ('Sábado', '09:00-12:00'),
        'Sábado 12:00-15:00': ('Sábado', '12:00-15:00'),
        'Sábado 16:00-19:00': ('Sábado', '16:00-19:00'),
        'Sábado 19:00-22:00': ('Sábado', '19:00-22:00'),
    }
    
    # Recorrer todos los grupos
    for categoria, grupos in resultado.grupos_por_categoria.items():
        for grupo in grupos:
            if not grupo.franja_horaria:
                continue
            
            # Buscar en qué día y franja cae
            for franja_completa, (dia, franja_hora) in franjas_a_dia.items():
                if franja_completa in grupo.franja_horaria or grupo.franja_horaria in franja_completa:
                    if franja_hora not in partidos_por_dia[dia]:
                        partidos_por_dia[dia][franja_hora] = []
                    
                    # Agregar todos los partidos del grupo
                    for p1, p2 in grupo.partidos:
                        partidos_por_dia[dia][franja_hora].append({
                            'categoria': categoria,
                            'grupo_id': grupo.id,
                            'pareja1': p1.nombre,
                            'pareja2': p2.nombre,
                            'partido': f"{p1.nombre} vs {p2.nombre}"
                        })
                    break
    
    return partidos_por_dia


def mostrar_partido_en_calendario(partido_info):
    """Muestra un partido en el calendario con el color de su categoría."""
    categoria = partido_info['categoria']
    
    # Determinar clase CSS según categoría
    clase_partido = {
        "Cuarta": "partido-cuarta",
        "Quinta": "partido-quinta",
        "Sexta": "partido-sexta",
        "Séptima": "partido-septima"
    }.get(categoria, "")
    
    st.markdown(f"""
        <div class="partido-bloque {clase_partido}">
            <div style="font-weight: bold; margin-bottom: 0.3rem;">
                {COLORES_CATEGORIA.get(categoria, '⚪')} {categoria}
            </div>
            <div style="font-size: 0.8rem;">
                Grupo {partido_info['grupo_id']}
            </div>
            <div style="margin-top: 0.3rem;">
                {partido_info['partido']}
            </div>
        </div>
    """, unsafe_allow_html=True)


def mostrar_opciones_exportacion(resultado):
    """Muestra las opciones de exportación en un expander."""
    with st.expander("📤 Opciones de Exportación", expanded=True):
        tab1, tab2, tab3 = st.tabs(["📊 Google Sheets", "📁 Descargar Archivos", "📋 Copiar Texto"])
        
        with tab1:
            exportar_google_sheets(resultado)
        
        with tab2:
            exportar_archivos(resultado)
        
        with tab3:
            exportar_texto(resultado)


if __name__ == "__main__":
    main()
