"""
Aplicación web para generación de grupos de torneo de pádel.
Interfaz principal con Streamlit.
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
    if 'paso_actual' not in st.session_state:
        st.session_state.paso_actual = 1
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
        
        /* Pasos del proceso */
        .paso-container {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        .paso-container:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .paso-activo {
            border-color: #667eea;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .paso-completado {
            border-color: #4caf50;
            background: #f1f8f4;
        }
        .paso-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .paso-numero {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #667eea;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: bold;
        }
        .paso-completado .paso-numero {
            background: #4caf50;
        }
        .paso-titulo {
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
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
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .grupo-cuarta { border-left-color: #90EE90; }
        .grupo-quinta { border-left-color: #FFD700; }
        .grupo-sexta { border-left-color: #87CEEB; }
        .grupo-septima { border-left-color: #DDA0DD; }
        
        /* Botones grandes */
        .stButton > button {
            width: 100%;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: bold;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        /* Progress bar personalizada */
        .progress-container {
            background: #e0e0e0;
            border-radius: 10px;
            height: 10px;
            margin: 2rem 0;
            overflow: hidden;
        }
        .progress-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.5s ease;
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
        </style>
    """, unsafe_allow_html=True)


def sidebar_configuracion():
    """Sidebar con configuración y opciones."""
    with st.sidebar:
        st.title("⚙️ Configuración")
        
        # Configuración de Google Sheets
        st.subheader("📊 Google Sheets")
        
        credentials_path = st.text_input(
            "Ruta a credentials.json",
            value="data/credentials.json",
            help="Ruta al archivo de credenciales de Google API"
        )
        
        if os.path.exists(credentials_path):
            st.success("✅ Credenciales encontradas")
            
            if st.button("🔗 Conectar con Google Sheets"):
                try:
                    with st.spinner("Conectando..."):
                        manager = GoogleSheetsManager(credentials_path)
                        st.session_state.google_sheets_manager = manager
                        st.success("¡Conectado exitosamente!")
                except Exception as e:
                    st.error(f"Error al conectar: {str(e)}")
        else:
            st.warning("⚠️ Archivo de credenciales no encontrado")
            st.info("📝 Coloca tu archivo credentials.json en la carpeta data/")
        
        st.divider()
        
        # Configuración del torneo
        st.subheader("🎾 Configuración del Torneo")
        
        num_canchas = st.number_input(
            "Número de canchas disponibles",
            min_value=1,
            max_value=4,
            value=2
        )
        
        duracion_partido = st.number_input(
            "Duración de cada partido (horas)",
            min_value=1,
            max_value=3,
            value=1
        )
        
        st.session_state.num_canchas = num_canchas
        st.session_state.duracion_partido = duracion_partido
        
        st.divider()
        
        # Información
        st.subheader("ℹ️ Información")
        st.markdown("""
        **Categorías:**
        - 🟢 Cuarta
        - 🟡 Quinta
        - 🔵 Sexta
        - 🟣 Séptima
        
        **Grupos:** 3 parejas por grupo
        
        **Partidos:** Todos contra todos (3 partidos/grupo)
        """)


def pagina_importar_datos():
    """Página para importar datos desde Google Sheets o manualmente."""
    st.header("📥 Importar Datos")
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Desde Google Sheets", 
        "✍️ Entrada Manual",
        "📁 Desde Archivo"
    ])
    
    # Tab 1: Google Sheets
    with tab1:
        st.subheader("Importar desde Google Sheets")
        
        if not st.session_state.google_sheets_manager:
            st.warning("⚠️ Primero conecta con Google Sheets desde la configuración lateral")
        else:
            spreadsheet_id = st.text_input(
                "ID del Google Spreadsheet",
                help="El ID está en la URL: https://docs.google.com/spreadsheets/d/[ID]/edit"
            )
            
            if spreadsheet_id:
                try:
                    hojas = st.session_state.google_sheets_manager.obtener_hojas_disponibles(spreadsheet_id)
                    hoja_seleccionada = st.selectbox("Selecciona la hoja", hojas)
                    
                    if st.button("📥 Importar Datos"):
                        with st.spinner("Importando datos..."):
                            datos = st.session_state.google_sheets_manager.importar_respuestas_form(
                                spreadsheet_id, 
                                hoja_seleccionada
                            )
                            
                            # Convertir a objetos Pareja
                            parejas = [crear_pareja_desde_dict(d, d['id']) for d in datos]
                            st.session_state.parejas = parejas
                            st.session_state.datos_importados = True
                            
                            st.success(f"✅ {len(parejas)} parejas importadas correctamente")
                            
                            # Mostrar preview
                            st.subheader("Vista previa de datos importados")
                            df = pd.DataFrame([
                                {
                                    'Nombre': p.nombre,
                                    'Categoría': p.categoria,
                                    'Teléfono': p.telefono,
                                    'Franjas': len(p.franjas_disponibles)
                                }
                                for p in parejas
                            ])
                            st.dataframe(df, use_container_width=True)
                            
                except Exception as e:
                    st.error(f"Error al importar: {str(e)}")
    
    # Tab 2: Entrada Manual
    with tab2:
        st.subheader("Agregar Parejas Manualmente")
        
        with st.form("form_pareja_manual"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre de la pareja")
                categoria = st.selectbox("Categoría", CATEGORIAS)
            
            with col2:
                telefono = st.text_input("Teléfono")
            
            st.write("Franjas horarias disponibles:")
            franjas_disponibles = []
            
            col1, col2 = st.columns(2)
            with col1:
                if st.checkbox("Jueves 18:00 a 21:00"):
                    franjas_disponibles.append("Jueves 18:00 a 21:00")
                if st.checkbox("Jueves 20:00 a 23:00"):
                    franjas_disponibles.append("Jueves 20:00 a 23:00")
                if st.checkbox("Viernes 18:00 a 21:00"):
                    franjas_disponibles.append("Viernes 18:00 a 21:00")
                if st.checkbox("Viernes 21:00 a 00:00"):
                    franjas_disponibles.append("Viernes 21:00 a 00:00")
            
            with col2:
                if st.checkbox("Sábado 9:00 a 12:00"):
                    franjas_disponibles.append("Sábado 9:00 a 12:00")
                if st.checkbox("Sábado 12:00 a 15:00"):
                    franjas_disponibles.append("Sábado 12:00 a 15:00")
                if st.checkbox("Sábado 16:00 a 19:00"):
                    franjas_disponibles.append("Sábado 16:00 a 19:00")
                if st.checkbox("Sábado 19:00 a 22:00"):
                    franjas_disponibles.append("Sábado 19:00 a 22:00")
            
            submitted = st.form_submit_button("➕ Agregar Pareja")
            
            if submitted and nombre and categoria:
                nueva_pareja = Pareja(
                    id=len(st.session_state.parejas) + 1,
                    nombre=nombre,
                    telefono=telefono,
                    categoria=categoria,
                    franjas_disponibles=franjas_disponibles
                )
                st.session_state.parejas.append(nueva_pareja)
                st.success(f"✅ Pareja '{nombre}' agregada")
                st.rerun()
        
        # Mostrar parejas agregadas
        if st.session_state.parejas:
            st.subheader(f"Parejas agregadas ({len(st.session_state.parejas)})")
            
            for i, pareja in enumerate(st.session_state.parejas):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{pareja.nombre}**")
                with col2:
                    st.write(f"{COLORES_CATEGORIA.get(pareja.categoria, '⚪')} {pareja.categoria}")
                with col3:
                    st.write(f"📞 {pareja.telefono}")
                with col4:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.parejas.pop(i)
                        st.rerun()
    
    # Tab 3: Desde Archivo
    with tab3:
        st.subheader("Importar desde archivo CSV o JSON")
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo",
            type=['csv', 'json']
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    # Procesar CSV
                    st.info("Funcionalidad CSV en desarrollo")
                elif uploaded_file.name.endswith('.json'):
                    import json
                    datos = json.load(uploaded_file)
                    st.info("Funcionalidad JSON en desarrollo")
            except Exception as e:
                st.error(f"Error al cargar archivo: {str(e)}")


def pagina_generar_grupos():
    """Página para ejecutar el algoritmo y generar grupos."""
    st.header("⚙️ Generar Grupos")
    
    if not st.session_state.parejas:
        st.warning("⚠️ No hay parejas cargadas. Ve a la página 'Importar Datos' primero.")
        return
    
    # Resumen de datos
    st.subheader("📊 Resumen de Parejas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    parejas_por_cat = {}
    for cat in CATEGORIAS:
        parejas_por_cat[cat] = len([p for p in st.session_state.parejas if p.categoria == cat])
    
    with col1:
        st.metric("🟢 Cuarta", parejas_por_cat.get("Cuarta", 0))
    with col2:
        st.metric("🟡 Quinta", parejas_por_cat.get("Quinta", 0))
    with col3:
        st.metric("🔵 Sexta", parejas_por_cat.get("Sexta", 0))
    with col4:
        st.metric("🟣 Séptima", parejas_por_cat.get("Séptima", 0))
    
    st.divider()
    
    # Botón para ejecutar algoritmo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 EJECUTAR ALGORITMO", type="primary", use_container_width=True):
            with st.spinner("🔄 Ejecutando algoritmo de formación de grupos..."):
                try:
                    # Ejecutar algoritmo
                    algoritmo = AlgoritmoGrupos(
                        parejas=st.session_state.parejas,
                        num_canchas=st.session_state.get('num_canchas', 2)
                    )
                    resultado = algoritmo.ejecutar()
                    st.session_state.resultado_algoritmo = resultado
                    
                    st.success("✅ ¡Grupos generados exitosamente!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error al generar grupos: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Mostrar resultados si existen
    if st.session_state.resultado_algoritmo:
        st.divider()
        mostrar_resultados(st.session_state.resultado_algoritmo)


def mostrar_resultados(resultado):
    """Muestra los resultados del algoritmo."""
    st.header("📋 Resultados")
    
    # Estadísticas generales
    stats = resultado.estadisticas
    
    st.subheader("📊 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parejas", stats['total_parejas'])
    with col2:
        st.metric("Parejas Asignadas", stats['parejas_asignadas'])
    with col3:
        st.metric("Sin Asignar", stats['parejas_sin_asignar'])
    with col4:
        st.metric("% Asignación", f"{stats['porcentaje_asignacion']:.1f}%")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Grupos", stats['total_grupos'])
    with col2:
        st.metric("Compatibilidad Perfecta", stats['grupos_compatibilidad_perfecta'])
    with col3:
        st.metric("Compatibilidad Parcial", stats['grupos_compatibilidad_parcial'])
    
    st.divider()
    
    # Mostrar grupos por categoría
    st.subheader("👥 Grupos Formados")
    
    for categoria in CATEGORIAS:
        if categoria not in resultado.grupos_por_categoria:
            continue
        
        grupos = resultado.grupos_por_categoria[categoria]
        if not grupos:
            continue
        
        emoji = COLORES_CATEGORIA.get(categoria, "⚪")
        
        with st.expander(f"{emoji} **{categoria}** - {len(grupos)} grupos", expanded=True):
            for grupo in grupos:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Grupo {grupo.id}**")
                    for i, pareja in enumerate(grupo.parejas, 1):
                        st.write(f"  {i}. {pareja.nombre} - 📞 {pareja.telefono}")
                
                with col2:
                    st.write(f"**Franja:**")
                    st.write(grupo.franja_horaria or "Por coordinar")
                    st.write(f"**Score:** {grupo.score_compatibilidad:.1f}/3.0")
                
                st.markdown("**Partidos:**")
                for idx, (p1, p2) in enumerate(grupo.partidos, 1):
                    st.write(f"  Partido {idx}: {p1.nombre} vs {p2.nombre}")
                
                st.divider()
    
    # Parejas sin asignar
    if resultado.parejas_sin_asignar:
        st.subheader("⚠️ Parejas Sin Grupo Asignado")
        st.warning("Las siguientes parejas no pudieron ser asignadas a un grupo. Por favor coordinar manualmente.")
        
        for pareja in resultado.parejas_sin_asignar:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.write(f"**{pareja.nombre}**")
                    st.write(f"{COLORES_CATEGORIA.get(pareja.categoria, '⚪')} {pareja.categoria}")
                
                with col2:
                    st.write(f"📞 {pareja.telefono}")
                
                with col3:
                    st.write("**Disponibilidad:**")
                    if pareja.franjas_disponibles:
                        for franja in pareja.franjas_disponibles:
                            st.write(f"  • {franja}")
                    else:
                        st.write("Sin franjas especificadas")
                
                st.divider()


def pagina_calendario():
    """Página para ver el calendario de partidos."""
    st.header("📅 Calendario de Partidos")
    
    if not st.session_state.resultado_algoritmo:
        st.warning("⚠️ Primero genera los grupos en la página 'Generar Grupos'")
        return
    
    resultado = st.session_state.resultado_algoritmo
    generador = GeneradorCalendario(
        duracion_partido_horas=st.session_state.get('duracion_partido', 1)
    )
    
    # Generar calendario detallado
    calendario = generador.generar_calendario_detallado(resultado)
    
    # Mostrar calendario por franja horaria
    for franja in sorted(calendario.keys()):
        partidos = calendario[franja]
        
        if not partidos:
            continue
        
        st.subheader(f"📅 {franja}")
        
        # Separar por cancha
        partidos_cancha_1 = [p for p in partidos if p['cancha'] == 1]
        partidos_cancha_2 = [p for p in partidos if p['cancha'] == 2]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏟️ Cancha 1")
            for partido in sorted(partidos_cancha_1, key=lambda x: x.get('hora_inicio_num', 0)):
                with st.container():
                    st.write(f"**{partido.get('hora_inicio_str', '')} - {partido.get('hora_fin_str', '')}**")
                    st.write(f"{partido['color']} {partido['categoria']} - Grupo {partido['grupo_id']}")
                    st.write(f"{partido['pareja1']} vs {partido['pareja2']}")
                    st.divider()
        
        with col2:
            st.markdown("### 🏟️ Cancha 2")
            for partido in sorted(partidos_cancha_2, key=lambda x: x.get('hora_inicio_num', 0)):
                with st.container():
                    st.write(f"**{partido.get('hora_inicio_str', '')} - {partido.get('hora_fin_str', '')}**")
                    st.write(f"{partido['color']} {partido['categoria']} - Grupo {partido['grupo_id']}")
                    st.write(f"{partido['pareja1']} vs {partido['pareja2']}")
                    st.divider()
        
        st.markdown("---")
    
    # Opción de descargar calendario en texto
    st.subheader("📥 Descargar Calendario")
    
    texto_calendario = generador.exportar_calendario_texto(resultado)
    
    st.download_button(
        label="📄 Descargar como TXT",
        data=texto_calendario,
        file_name=f"calendario_torneo_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )


def pagina_exportar():
    """Página para exportar resultados."""
    st.header("📤 Exportar Resultados")
    
    if not st.session_state.resultado_algoritmo:
        st.warning("⚠️ Primero genera los grupos en la página 'Generar Grupos'")
        return
    
    resultado = st.session_state.resultado_algoritmo
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Google Sheets",
        "📁 Archivos Locales",
        "📋 Copiar Texto"
    ])
    
    # Tab 1: Google Sheets
    with tab1:
        st.subheader("Exportar a Google Sheets")
        
        if not st.session_state.google_sheets_manager:
            st.warning("⚠️ Primero conecta con Google Sheets desde la configuración lateral")
        else:
            spreadsheet_id = st.text_input(
                "ID del Google Spreadsheet (donde exportar)",
                help="Puedes usar el mismo del formulario u otro diferente"
            )
            
            nombre_hoja = st.text_input(
                "Nombre de la nueva hoja",
                value=f"Grupos_Torneo_{datetime.now().strftime('%Y%m%d_%H%M')}"
            )
            
            if st.button("📤 Exportar a Google Sheets"):
                if spreadsheet_id:
                    try:
                        with st.spinner("Exportando..."):
                            url = st.session_state.google_sheets_manager.exportar_grupos(
                                spreadsheet_id,
                                resultado,
                                nombre_hoja
                            )
                            st.success("✅ Exportado exitosamente!")
                            st.markdown(f"[🔗 Abrir Google Sheet]({url})")
                    except Exception as e:
                        st.error(f"Error al exportar: {str(e)}")
                else:
                    st.error("Por favor ingresa el ID del spreadsheet")
    
    # Tab 2: Archivos Locales
    with tab2:
        st.subheader("Descargar archivos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON
            if st.button("📥 Descargar JSON"):
                try:
                    exportador = ExportadorDatos()
                    archivo = f"grupos_torneo_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                    exportador.exportar_json(resultado, archivo)
                    
                    with open(archivo, 'r', encoding='utf-8') as f:
                        st.download_button(
                            "💾 Guardar JSON",
                            data=f.read(),
                            file_name=archivo,
                            mime="application/json"
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            # CSV
            if st.button("📥 Descargar CSV"):
                try:
                    exportador = ExportadorDatos()
                    archivo = f"grupos_torneo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                    exportador.exportar_csv_grupos(resultado, archivo)
                    
                    with open(archivo, 'r', encoding='utf-8') as f:
                        st.download_button(
                            "💾 Guardar CSV",
                            data=f.read(),
                            file_name=archivo,
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Tab 3: Copiar texto
    with tab3:
        st.subheader("Copiar como texto")
        
        generador = GeneradorCalendario()
        texto = generador.exportar_calendario_texto(resultado)
        
        st.text_area("Calendario en texto", texto, height=400)
        
        st.info("💡 Puedes copiar este texto y pegarlo donde necesites")


def main():
    """Función principal de la aplicación con flujo paso a paso."""
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
    
    # Barra de progreso
    total_pasos = 4
    paso_actual = st.session_state.paso_actual
    progreso = (paso_actual / total_pasos) * 100
    
    st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progreso}%"></div>
        </div>
    """, unsafe_allow_html=True)
    
    # Indicadores de pasos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        icono = "✅" if paso_actual > 1 else "1️⃣"
        st.markdown(f"### {icono} Cargar Datos")
        if paso_actual == 1:
            st.markdown("**← Paso Actual**")
    with col2:
        icono = "✅" if paso_actual > 2 else "2️⃣" if paso_actual == 2 else "⚪"
        st.markdown(f"### {icono} Generar Grupos")
        if paso_actual == 2:
            st.markdown("**← Paso Actual**")
    with col3:
        icono = "✅" if paso_actual > 3 else "3️⃣" if paso_actual == 3 else "⚪"
        st.markdown(f"### {icono} Ver Resultados")
        if paso_actual == 3:
            st.markdown("**← Paso Actual**")
    with col4:
        icono = "4️⃣" if paso_actual == 4 else "⚪"
        st.markdown(f"### {icono} Exportar")
        if paso_actual == 4:
            st.markdown("**← Paso Actual**")
    
    st.markdown("---")
    
    # Mostrar el paso correspondiente
    if paso_actual == 1:
        paso_1_cargar_datos()
    elif paso_actual == 2:
        paso_2_generar_grupos()
    elif paso_actual == 3:
        paso_3_ver_resultados()
    elif paso_actual == 4:
        paso_4_exportar()


def paso_1_cargar_datos():
    """PASO 1: Cargar datos de las parejas."""
    st.markdown("""
        <div class="paso-container paso-activo">
            <div class="paso-header">
                <div class="paso-numero">1</div>
                <div class="paso-titulo">Cargar Datos de Parejas</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Mostrar resumen si ya hay datos
    if st.session_state.parejas:
        st.markdown('<div class="alert-success">✅ <strong>Datos cargados correctamente</strong></div>', 
                   unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        total = len(st.session_state.parejas)
        
        with col1:
            st.markdown('<div class="stat-card"><div class="stat-value">{}</div><div class="stat-label">Total Parejas</div></div>'.format(total),
                       unsafe_allow_html=True)
        
        parejas_por_cat = {cat: len([p for p in st.session_state.parejas if p.categoria == cat]) 
                          for cat in CATEGORIAS}
        
        with col2:
            st.markdown('<div class="stat-card"><div class="stat-value">{}</div><div class="stat-label">🟢 Cuarta</div></div>'.format(parejas_por_cat.get("Cuarta", 0)),
                       unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="stat-card"><div class="stat-value">{}</div><div class="stat-label">🟡 Quinta</div></div>'.format(parejas_por_cat.get("Quinta", 0)),
                       unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="stat-card"><div class="stat-value">{}</div><div class="stat-label">🔵 Sexta / 🟣 Séptima</div></div>'.format(
                parejas_por_cat.get("Sexta", 0) + parejas_por_cat.get("Séptima", 0)),
                       unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("📝 Modificar datos", use_container_width=True):
                st.session_state.parejas = []
                st.rerun()
        with col2:
            if st.button("➡️ Siguiente Paso", type="primary", use_container_width=True):
                st.session_state.paso_actual = 2
                st.rerun()
    
    # Opciones de carga
    st.subheader("Selecciona cómo cargar los datos:")
    
    tab1, tab2, tab3 = st.tabs(["📁 Importar CSV", "📊 Google Sheets", "✍️ Entrada Manual"])
    
    with tab1:
        cargar_desde_csv()
    
    with tab2:
        cargar_desde_google_sheets()
    
    with tab3:
        entrada_manual()


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
            import io
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


def paso_2_generar_grupos():
    """PASO 2: Generar grupos con el algoritmo."""
    st.markdown("""
        <div class="paso-container paso-activo">
            <div class="paso-header">
                <div class="paso-numero">2</div>
                <div class="paso-titulo">Generar Grupos Automáticamente</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botón para volver
    if st.button("← Volver a cargar datos"):
        st.session_state.paso_actual = 1
        st.rerun()
    
    st.markdown("---")
    
    # Configuración
    st.subheader("⚙️ Configuración del Torneo")
    
    col1, col2 = st.columns(2)
    with col1:
        num_canchas = st.number_input(
            "Número de canchas disponibles",
            min_value=1,
            max_value=4,
            value=2,
            help="Cantidad de canchas que se pueden usar simultáneamente"
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
    
    # Resumen pre-algoritmo
    st.subheader("📊 Resumen de Parejas Cargadas")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total = len(st.session_state.parejas)
    parejas_por_cat = {cat: len([p for p in st.session_state.parejas if p.categoria == cat]) 
                       for cat in CATEGORIAS}
    
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("🟢 Cuarta", parejas_por_cat.get("Cuarta", 0))
    with col3:
        st.metric("🟡 Quinta", parejas_por_cat.get("Quinta", 0))
    with col4:
        st.metric("🔵 Sexta", parejas_por_cat.get("Sexta", 0))
    with col5:
        st.metric("🟣 Séptima", parejas_por_cat.get("Séptima", 0))
    
    st.markdown("---")
    
    # Botón principal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 EJECUTAR ALGORITMO", type="primary", use_container_width=True, 
                    help="Genera los grupos óptimos automáticamente"):
            with st.spinner("⏳ Ejecutando algoritmo inteligente..."):
                try:
                    algoritmo = AlgoritmoGrupos(
                        parejas=st.session_state.parejas,
                        num_canchas=num_canchas
                    )
                    resultado = algoritmo.ejecutar()
                    st.session_state.resultado_algoritmo = resultado
                    st.session_state.paso_actual = 3
                    st.success("✅ ¡Grupos generados exitosamente!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Ver detalles del error"):
                        st.code(traceback.format_exc())


def paso_3_ver_resultados():
    """PASO 3: Visualizar resultados del algoritmo."""
    st.markdown("""
        <div class="paso-container paso-activo">
            <div class="paso-header">
                <div class="paso-numero">3</div>
                <div class="paso-titulo">Resultados y Grupos Generados</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    resultado = st.session_state.resultado_algoritmo
    
    # Botones de navegación
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Volver a generar", use_container_width=True):
            st.session_state.paso_actual = 2
            st.rerun()
    with col2:
        if st.button("Exportar Resultados →", type="primary", use_container_width=True):
            st.session_state.paso_actual = 4
            st.rerun()
    
    st.markdown("---")
    
    # Estadísticas principales
    stats = resultado.estadisticas
    
    st.subheader("📊 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{stats['parejas_asignadas']}</div>
                <div class="stat-label">Parejas Asignadas</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem;">de {stats['total_parejas']} total</div>
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
    
    # Mostrar grupos por categoría
    st.subheader("👥 Grupos Formados por Categoría")
    
    tabs = st.tabs(["🟢 Cuarta", "🟡 Quinta", "🔵 Sexta", "🟣 Séptima", "⚠️ Sin Asignar"])
    
    for idx, categoria in enumerate(CATEGORIAS):
        with tabs[idx]:
            if categoria not in resultado.grupos_por_categoria or not resultado.grupos_por_categoria[categoria]:
                st.info(f"No hay grupos formados en la categoría {categoria}")
                continue
            
            grupos = resultado.grupos_por_categoria[categoria]
            
            for grupo in grupos:
                # Determinar clase CSS según categoría
                clase_css = {
                    "Cuarta": "grupo-cuarta",
                    "Quinta": "grupo-quinta",
                    "Sexta": "grupo-sexta",
                    "Séptima": "grupo-septima"
                }.get(categoria, "")
                
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"### Grupo {grupo.id}")
                    with col2:
                        score_emoji = "✅" if grupo.score_compatibilidad >= 3.0 else "⚠️"
                        st.markdown(f"**{score_emoji} Score: {grupo.score_compatibilidad:.1f}/3.0**")
                    with col3:
                        st.markdown(f"**{grupo.franja_horaria or 'Por coordinar'}**")
                    
                    st.markdown(f'<div class="grupo-card {clase_css}">', unsafe_allow_html=True)
                    
                    st.write("**Parejas:**")
                    for i, pareja in enumerate(grupo.parejas, 1):
                        st.write(f"{i}. {pareja.nombre} - 📞 {pareja.telefono}")
                    
                    st.write("**Partidos:**")
                    for idx, (p1, p2) in enumerate(grupo.partidos, 1):
                        st.write(f"Partido {idx}: {p1.nombre} vs {p2.nombre}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("---")
    
    # Parejas sin asignar
    with tabs[4]:
        if resultado.parejas_sin_asignar:
            st.warning(f"⚠️ {len(resultado.parejas_sin_asignar)} parejas no pudieron ser asignadas")
            st.info("💡 Estas parejas necesitan coordinación manual para encontrar horarios compatibles")
            
            for pareja in resultado.parejas_sin_asignar:
                with st.expander(f"{COLORES_CATEGORIA.get(pareja.categoria, '⚪')} {pareja.nombre}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Categoría:** {pareja.categoria}")
                        st.write(f"**Teléfono:** {pareja.telefono}")
                    with col2:
                        st.write("**Franjas disponibles:**")
                        if pareja.franjas_disponibles:
                            for franja in pareja.franjas_disponibles:
                                st.write(f"• {franja}")
                        else:
                            st.write("Sin franjas especificadas")
        else:
            st.success("🎉 ¡Excelente! Todas las parejas fueron asignadas a un grupo")


def paso_4_exportar():
    """PASO 4: Exportar resultados."""
    st.markdown("""
        <div class="paso-container paso-activo">
            <div class="paso-header">
                <div class="paso-numero">4</div>
                <div class="paso-titulo">Exportar Resultados</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Volver a resultados"):
        st.session_state.paso_actual = 3
        st.rerun()
    
    st.markdown("---")
    
    resultado = st.session_state.resultado_algoritmo
    
    st.subheader("📤 Opciones de Exportación")
    
    tab1, tab2, tab3 = st.tabs(["📊 Google Sheets", "📁 Descargar Archivos", "📋 Copiar Texto"])
    
    with tab1:
        exportar_google_sheets(resultado)
    
    with tab2:
        exportar_archivos(resultado)
    
    with tab3:
        exportar_texto(resultado)


def exportar_google_sheets(resultado):
    """Exportar a Google Sheets."""
    st.markdown('<div class="alert-info">📊 Exporta los grupos directamente a una hoja de Google Sheets</div>',
               unsafe_allow_html=True)
    
    if not st.session_state.google_sheets_manager:
        st.warning("⚠️ Primero debes conectar con Google Sheets (vuelve al Paso 1)")
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
            import json
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


if __name__ == "__main__":
    main()
