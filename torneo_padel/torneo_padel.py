"""
Aplicación web para generación de grupos de torneo de pádel con Reflex.
Diseño moderno y flexible.
"""

import reflex as rx
from typing import List, Dict, Optional
import pandas as pd
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


# ============================================================================
# ESTADO DE LA APLICACIÓN
# ============================================================================

class State(rx.State):
    """Estado global de la aplicación."""
    
    # Datos
    parejas: List[Dict] = []
    resultado_algoritmo: Optional[Dict] = None
    
    # Configuración
    num_canchas: int = 2
    duracion_partido: int = 1
    
    # UI
    pagina_actual: str = "inicio"  # inicio, datos, resultados
    tab_activo: str = "csv"  # csv, google, manual
    categoria_activa: str = "Cuarta"
    
    # Formulario manual
    form_nombre: str = ""
    form_telefono: str = ""
    form_categoria: str = "Cuarta"
    form_franjas: List[str] = []
    
    # Mensajes
    mensaje: str = ""
    mensaje_tipo: str = "info"  # info, success, error, warning
    
    # Archivo cargado
    archivo_csv: str = ""
    
    # Setters explícitos
    def set_form_nombre(self, valor: str):
        self.form_nombre = valor
    
    def set_form_telefono(self, valor: str):
        self.form_telefono = valor
    
    def set_form_categoria(self, valor: str):
        self.form_categoria = valor
    
    def set_num_canchas(self, valor: int):
        self.num_canchas = valor
    
    def set_duracion_partido(self, valor: int):
        self.duracion_partido = valor
    
    @rx.var
    def total_parejas(self) -> int:
        """Retorna el total de parejas cargadas."""
        return len(self.parejas)
    
    @rx.var
    def parejas_por_categoria(self) -> Dict[str, int]:
        """Cuenta parejas por categoría."""
        conteo = {cat: 0 for cat in CATEGORIAS}
        for pareja in self.parejas:
            cat = pareja.get("categoria", "")
            if cat in conteo:
                conteo[cat] += 1
        return conteo
    
    @rx.var
    def tiene_datos(self) -> bool:
        """Verifica si hay datos cargados."""
        return len(self.parejas) > 0
    
    @rx.var
    def tiene_resultados(self) -> bool:
        """Verifica si hay resultados del algoritmo."""
        return self.resultado_algoritmo is not None
    
    def ir_a_pagina(self, pagina: str):
        """Navega a una página específica."""
        self.pagina_actual = pagina
    
    def cambiar_tab(self, tab: str):
        """Cambia el tab activo."""
        self.tab_activo = tab
    
    def cambiar_categoria(self, categoria: str):
        """Cambia la categoría activa en resultados."""
        self.categoria_activa = categoria
    
    def agregar_pareja_manual(self):
        """Agrega una pareja manualmente."""
        if not self.form_nombre:
            self.mostrar_mensaje("El nombre es obligatorio", "error")
            return
        
        if not self.form_franjas:
            self.mostrar_mensaje("Selecciona al menos una franja horaria", "error")
            return
        
        nueva_pareja = {
            "id": len(self.parejas) + 1,
            "nombre": self.form_nombre,
            "telefono": self.form_telefono or "Sin teléfono",
            "categoria": self.form_categoria,
            "franjas_disponibles": self.form_franjas.copy()
        }
        
        self.parejas.append(nueva_pareja)
        self.mostrar_mensaje(f"Pareja '{self.form_nombre}' agregada correctamente", "success")
        
        # Limpiar formulario
        self.form_nombre = ""
        self.form_telefono = ""
        self.form_franjas = []
    
    def eliminar_pareja(self, index: int):
        """Elimina una pareja."""
        if 0 <= index < len(self.parejas):
            del self.parejas[index]
            self.mostrar_mensaje("Pareja eliminada", "success")
    
    def toggle_franja(self, franja: str):
        """Activa/desactiva una franja horaria."""
        if franja in self.form_franjas:
            self.form_franjas.remove(franja)
        else:
            self.form_franjas.append(franja)
    
    async def procesar_csv(self, files: List[rx.UploadFile]):
        """Procesa el archivo CSV cargado."""
        if not files:
            self.mostrar_mensaje("No se seleccionó ningún archivo", "error")
            return
        
        try:
            file = files[0]
            content = await file.read()
            
            # Guardar temporalmente
            import io
            df = pd.read_csv(io.BytesIO(content))
            
            # Procesar DataFrame
            parejas_nuevas = self.procesar_dataframe(df)
            self.parejas = parejas_nuevas
            
            self.mostrar_mensaje(f"✅ {len(parejas_nuevas)} parejas cargadas correctamente", "success")
            
        except Exception as e:
            self.mostrar_mensaje(f"Error al procesar CSV: {str(e)}", "error")
    
    def procesar_dataframe(self, df: pd.DataFrame) -> List[Dict]:
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
                    "id": idx + 1,
                    "nombre": nombre,
                    "telefono": telefono or "Sin teléfono",
                    "categoria": categoria,
                    "franjas_disponibles": franjas
                })
        
        return parejas
    
    def ejecutar_algoritmo(self):
        """Ejecuta el algoritmo de generación de grupos."""
        if not self.parejas:
            self.mostrar_mensaje("Primero debes cargar las parejas", "error")
            return
        
        try:
            # Convertir dict a objetos Pareja
            parejas_obj = [
                Pareja(
                    id=p["id"],
                    nombre=p["nombre"],
                    telefono=p["telefono"],
                    categoria=p["categoria"],
                    franjas_disponibles=p["franjas_disponibles"]
                )
                for p in self.parejas
            ]
            
            # Ejecutar algoritmo
            algoritmo = AlgoritmoGrupos(
                parejas=parejas_obj,
                num_canchas=self.num_canchas
            )
            resultado = algoritmo.ejecutar()
            
            # Convertir resultado a dict serializable
            self.resultado_algoritmo = self.resultado_a_dict(resultado)
            
            self.mostrar_mensaje("✅ Grupos generados exitosamente", "success")
            self.ir_a_pagina("resultados")
            
        except Exception as e:
            self.mostrar_mensaje(f"Error al ejecutar algoritmo: {str(e)}", "error")
    
    def resultado_a_dict(self, resultado) -> Dict:
        """Convierte el resultado del algoritmo a diccionario."""
        grupos_dict = {}
        
        for categoria, grupos in resultado.grupos_por_categoria.items():
            grupos_dict[categoria] = [
                {
                    "id": grupo.id,
                    "parejas": [
                        {
                            "nombre": p.nombre,
                            "telefono": p.telefono,
                            "categoria": p.categoria,
                            "franjas": p.franjas_disponibles
                        }
                        for p in grupo.parejas
                    ],
                    "partidos": [
                        {"pareja1": p1.nombre, "pareja2": p2.nombre}
                        for p1, p2 in grupo.partidos
                    ],
                    "franja_horaria": grupo.franja_horaria,
                    "score": grupo.score_compatibilidad
                }
                for grupo in grupos
            ]
        
        return {
            "grupos_por_categoria": grupos_dict,
            "estadisticas": resultado.estadisticas,
            "parejas_sin_asignar": [
                {
                    "nombre": p.nombre,
                    "telefono": p.telefono,
                    "categoria": p.categoria,
                    "franjas": p.franjas_disponibles
                }
                for p in resultado.parejas_sin_asignar
            ]
        }
    
    def mostrar_mensaje(self, texto: str, tipo: str = "info"):
        """Muestra un mensaje al usuario."""
        self.mensaje = texto
        self.mensaje_tipo = tipo
    
    def limpiar_datos(self):
        """Limpia todos los datos."""
        self.parejas = []
        self.resultado_algoritmo = None
        self.mostrar_mensaje("Datos limpiados", "info")
        self.ir_a_pagina("inicio")


# ============================================================================
# COMPONENTES DE UI
# ============================================================================

def navbar() -> rx.Component:
    """Barra de navegación superior."""
    return rx.box(
        rx.hstack(
            rx.heading("🎾 Torneo de Pádel", size="7", color="white"),
            rx.spacer(),
            rx.button(
                "Inicio",
                on_click=State.ir_a_pagina("inicio"),
                variant="ghost",
                color_scheme="gray",
                display=rx.cond(State.pagina_actual != "inicio", "block", "none")
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding="1.5rem",
        box_shadow="0 2px 4px rgba(0,0,0,0.1)",
    )


def mensaje_alerta() -> rx.Component:
    """Muestra mensajes al usuario."""
    return rx.cond(
        State.mensaje != "",
        rx.callout(
            State.mensaje,
            icon="info",
            color_scheme=rx.cond(
                State.mensaje_tipo == "success", "green",
                rx.cond(State.mensaje_tipo == "error", "red",
                       rx.cond(State.mensaje_tipo == "warning", "orange", "blue"))
            ),
            margin_top="1rem",
            margin_bottom="1rem",
        ),
    )


def stat_card(valor: rx.Var, etiqueta: str, icono: str = "📊") -> rx.Component:
    """Tarjeta de estadística."""
    return rx.card(
        rx.vstack(
            rx.text(icono, font_size="2rem"),
            rx.heading(valor, size="8", color="white"),
            rx.text(etiqueta, size="2", color="white", opacity=0.9),
            align="center",
            spacing="2",
        ),
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding="1.5rem",
        border_radius="10px",
        box_shadow="0 2px 4px rgba(0,0,0,0.1)",
    )


# ============================================================================
# PÁGINAS
# ============================================================================

def pagina_inicio() -> rx.Component:
    """Página de inicio."""
    return rx.center(
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.heading("🎾 Generador de Grupos", size="9", text_align="center"),
                    rx.text(
                        "Sistema inteligente de formación de grupos por compatibilidad horaria",
                        size="4",
                        text_align="center",
                        color="gray",
                    ),
                    spacing="2",
                ),
                padding="2rem",
                width="100%",
            ),
            
            # Paso a paso
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("📥", font_size="3rem"),
                        rx.heading("1. Ingresar Datos", size="5"),
                        rx.text("Carga las parejas desde CSV o manualmente", text_align="center"),
                        align="center",
                        spacing="2",
                    ),
                    padding="2rem",
                ),
                rx.card(
                    rx.vstack(
                        rx.text("🤖", font_size="3rem"),
                        rx.heading("2. Ejecutar Algoritmo", size="5"),
                        rx.text("El sistema genera grupos compatibles", text_align="center"),
                        align="center",
                        spacing="2",
                    ),
                    padding="2rem",
                ),
                rx.card(
                    rx.vstack(
                        rx.text("📊", font_size="3rem"),
                        rx.heading("3. Ver Resultados", size="5"),
                        rx.text("Consulta grupos y calendario", text_align="center"),
                        align="center",
                        spacing="2",
                    ),
                    padding="2rem",
                ),
                spacing="4",
                width="100%",
            ),
            
            # Botón principal
            rx.button(
                "📥 INGRESAR DATOS",
                on_click=State.ir_a_pagina("datos"),
                size="4",
                variant="solid",
                color_scheme="purple",
                width="300px",
                cursor="pointer",
            ),
            
            spacing="6",
            max_width="1200px",
            padding="2rem",
        ),
        width="100%",
    )


def pagina_datos() -> rx.Component:
    """Página de carga de datos."""
    return rx.vstack(
        # Header
        rx.heading("📊 Cargar Datos de Parejas", size="8"),
        
        mensaje_alerta(),
        
        # Tabs de opciones
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("📁 CSV", value="csv"),
                rx.tabs.trigger("✍️ Manual", value="manual"),
            ),
            
            rx.tabs.content(
                tab_csv(),
                value="csv",
            ),
            
            rx.tabs.content(
                tab_manual(),
                value="manual",
            ),
            
            default_value="csv",
            width="100%",
        ),
        
        # Mostrar datos si hay
        rx.cond(
            State.tiene_datos,
            rx.vstack(
                rx.divider(),
                
                # Estadísticas
                rx.heading("📈 Resumen", size="6"),
                rx.hstack(
                    stat_card(State.total_parejas, "Total Parejas", "👥"),
                    stat_card(State.parejas_por_categoria["Cuarta"], "Cuarta", "🟢"),
                    stat_card(State.parejas_por_categoria["Quinta"], "Quinta", "🟡"),
                    stat_card(State.parejas_por_categoria["Sexta"], "Sexta", "🔵"),
                    stat_card(State.parejas_por_categoria["Séptima"], "Séptima", "🟣"),
                    spacing="4",
                    width="100%",
                ),
                
                # Tabla de parejas
                rx.heading("📋 Parejas Cargadas", size="6", margin_top="2rem"),
                lista_parejas(),
                
                # Configuración
                rx.heading("⚙️ Configuración", size="6", margin_top="2rem"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Número de canchas:", font_weight="bold"),
                        rx.input(
                            value=State.num_canchas.to(str),
                            on_change=lambda v: State.set_num_canchas(int(v) if v.isdigit() else 2),
                            type="number",
                            min="1",
                            max="4",
                        ),
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Duración partido (horas):", font_weight="bold"),
                        rx.input(
                            value=State.duracion_partido.to(str),
                            on_change=lambda v: State.set_duracion_partido(int(v) if v.isdigit() else 1),
                            type="number",
                            min="1",
                            max="3",
                        ),
                        align="start",
                    ),
                    spacing="6",
                ),
                
                # Botón ejecutar
                rx.button(
                    "🚀 EJECUTAR ALGORITMO",
                    on_click=State.ejecutar_algoritmo,
                    size="4",
                    variant="solid",
                    color_scheme="green",
                    width="300px",
                    cursor="pointer",
                    margin_top="2rem",
                ),
                
                spacing="4",
                width="100%",
            ),
        ),
        
        spacing="4",
        max_width="1200px",
        padding="2rem",
        width="100%",
    )


def tab_csv() -> rx.Component:
    """Tab para cargar CSV."""
    return rx.vstack(
        rx.callout(
            "📄 Carga un archivo CSV con las respuestas del formulario",
            icon="info",
            color_scheme="blue",
        ),
        
        rx.upload(
            rx.vstack(
                rx.button("Seleccionar archivo CSV", size="3"),
                rx.text("Arrastra el archivo aquí o haz clic para seleccionar", size="2", color="gray"),
            ),
            accept={".csv": ["text/csv"]},
            max_files=1,
            on_drop=State.procesar_csv(rx.upload_files()),
        ),
        
        spacing="4",
        padding="2rem",
    )


def tab_manual() -> rx.Component:
    """Tab para entrada manual."""
    return rx.vstack(
        rx.callout(
            "✍️ Ingresa las parejas manualmente una por una",
            icon="info",
            color_scheme="blue",
        ),
        
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Nombre de la pareja *", font_weight="bold"),
                        rx.input(
                            placeholder="Ej: Juan Pérez / María López",
                            value=State.form_nombre,
                            on_change=State.set_form_nombre,
                            width="100%",
                        ),
                        align="start",
                        width="50%",
                    ),
                    rx.vstack(
                        rx.text("Teléfono", font_weight="bold"),
                        rx.input(
                            placeholder="Ej: 099123456",
                            value=State.form_telefono,
                            on_change=State.set_form_telefono,
                            width="100%",
                        ),
                        align="start",
                        width="50%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Categoría *", font_weight="bold"),
                    rx.select(
                        CATEGORIAS,
                        value=State.form_categoria,
                        on_change=State.set_form_categoria,
                    ),
                    align="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Franjas horarias disponibles *", font_weight="bold"),
                    rx.text("Selecciona todas las franjas en las que pueden jugar", size="2", color="gray"),
                    rx.vstack(
                        *[
                            rx.checkbox(
                                franja,
                                checked=State.form_franjas.contains(franja),
                                on_change=lambda: State.toggle_franja(franja),
                            )
                            for franja in FRANJAS_HORARIAS
                        ],
                        align="start",
                    ),
                    align="start",
                    width="100%",
                ),
                
                rx.button(
                    "➕ Agregar Pareja",
                    on_click=State.agregar_pareja_manual,
                    size="3",
                    color_scheme="purple",
                    cursor="pointer",
                ),
                
                spacing="4",
                width="100%",
            ),
        ),
        
        spacing="4",
        padding="2rem",
    )


def lista_parejas() -> rx.Component:
    """Lista las parejas cargadas."""
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(
                State.parejas,
                lambda pareja, idx: rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(pareja["nombre"], font_weight="bold", font_size="1.1rem"),
                            rx.text(f"📞 {pareja['telefono']}", size="2", color="gray"),
                            rx.text(f"🏷️ {pareja['categoria']}", size="2"),
                            align="start",
                        ),
                        rx.spacer(),
                        rx.button(
                            "🗑️",
                            on_click=lambda: State.eliminar_pareja(idx),
                            variant="ghost",
                            color_scheme="red",
                            cursor="pointer",
                        ),
                        width="100%",
                        align="center",
                    ),
                ),
            ),
            spacing="2",
        ),
        height="400px",
        width="100%",
    )


def pagina_resultados() -> rx.Component:
    """Página de resultados."""
    return rx.vstack(
        # Header
        rx.heading("🏆 Resultados del Torneo", size="8"),
        
        # Navegación
        rx.hstack(
            rx.button(
                "← Volver a datos",
                on_click=State.ir_a_pagina("datos"),
                variant="outline",
            ),
            rx.button(
                "🔄 Ejecutar de nuevo",
                on_click=lambda: [State.set_resultado_algoritmo(None), State.ir_a_pagina("datos")],
                variant="outline",
            ),
            spacing="2",
        ),
        
        mensaje_alerta(),
        
        # Estadísticas
        rx.cond(
            State.tiene_resultados,
            rx.vstack(
                rx.hstack(
                    stat_card(
                        f"{State.resultado_algoritmo['estadisticas']['parejas_asignadas']}/{State.resultado_algoritmo['estadisticas']['total_parejas']}",
                        "Parejas Asignadas",
                        "✅"
                    ),
                    stat_card(
                        f"{State.resultado_algoritmo['estadisticas']['porcentaje_asignacion']:.0f}%",
                        "Tasa de Asignación",
                        "📊"
                    ),
                    stat_card(
                        State.resultado_algoritmo['estadisticas']['total_grupos'],
                        "Grupos Formados",
                        "👥"
                    ),
                    stat_card(
                        f"{State.resultado_algoritmo['estadisticas']['score_compatibilidad_promedio']:.2f}/3.0",
                        "Calidad Promedio",
                        "⭐"
                    ),
                    spacing="4",
                    width="100%",
                ),
                
                # Tabs de categorías
                rx.divider(margin_y="2rem"),
                tabs_resultados(),
                
                spacing="4",
                width="100%",
            ),
        ),
        
        spacing="4",
        max_width="1200px",
        padding="2rem",
        width="100%",
    )


def tabs_resultados() -> rx.Component:
    """Tabs con resultados por categoría."""
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("🟢 Cuarta", value="Cuarta"),
            rx.tabs.trigger("🟡 Quinta", value="Quinta"),
            rx.tabs.trigger("🔵 Sexta", value="Sexta"),
            rx.tabs.trigger("🟣 Séptima", value="Séptima"),
            rx.tabs.trigger("📅 Calendario", value="calendario"),
        ),
        
        rx.tabs.content(
            mostrar_grupos_categoria("Cuarta"),
            value="Cuarta",
        ),
        rx.tabs.content(
            mostrar_grupos_categoria("Quinta"),
            value="Quinta",
        ),
        rx.tabs.content(
            mostrar_grupos_categoria("Sexta"),
            value="Sexta",
        ),
        rx.tabs.content(
            mostrar_grupos_categoria("Séptima"),
            value="Séptima",
        ),
        rx.tabs.content(
            mostrar_calendario(),
            value="calendario",
        ),
        
        default_value="Cuarta",
        width="100%",
    )


def mostrar_grupos_categoria(categoria: str) -> rx.Component:
    """Muestra los grupos de una categoría."""
    return rx.scroll_area(
        rx.vstack(
            rx.cond(
                State.resultado_algoritmo["grupos_por_categoria"][categoria].length() > 0,
                rx.vstack(
                    rx.foreach(
                        State.resultado_algoritmo["grupos_por_categoria"][categoria],
                        lambda grupo: grupo_card(grupo, categoria),
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.callout(
                    f"No hay grupos formados en la categoría {categoria}",
                    icon="info",
                    color_scheme="blue",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        height="600px",
        width="100%",
    )


def grupo_card(grupo: rx.Var, categoria: str) -> rx.Component:
    """Tarjeta de un grupo."""
    
    # Color según categoría
    border_color = {
        "Cuarta": "#90EE90",
        "Quinta": "#FFD700",
        "Sexta": "#87CEEB",
        "Séptima": "#DDA0DD"
    }.get(categoria, "#E0E0E0")
    
    bg_color = {
        "Cuarta": "#f0fff0",
        "Quinta": "#fffef0",
        "Sexta": "#f0f8ff",
        "Séptima": "#fff0ff"
    }.get(categoria, "#FFFFFF")
    
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(f"Grupo {grupo['id']}", size="6"),
                rx.spacer(),
                rx.badge(
                    f"Score: {grupo['score']:.1f}/3.0",
                    color_scheme="green" if grupo['score'] >= 3.0 else "yellow",
                ),
                width="100%",
                align="center",
            ),
            
            # Franja horaria
            rx.cond(
                grupo['franja_horaria'] != "",
                rx.text(f"🕐 {grupo['franja_horaria']}", font_weight="bold"),
            ),
            
            rx.divider(),
            
            # Parejas
            rx.text("👥 Parejas:", font_weight="bold", size="4"),
            rx.vstack(
                rx.foreach(
                    grupo["parejas"],
                    lambda pareja, idx: rx.box(
                        rx.vstack(
                            rx.text(f"{idx + 1}. {pareja['nombre']}", font_weight="bold"),
                            rx.text(f"📞 {pareja['telefono']}", size="2", color="gray"),
                            rx.text(f"🕐 Horarios: {', '.join(pareja['franjas'])}", size="2"),
                            align="start",
                        ),
                        padding="0.5rem",
                        background="rgba(255,255,255,0.5)",
                        border_radius="5px",
                    ),
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            
            rx.divider(),
            
            # Partidos
            rx.text("🏆 Partidos:", font_weight="bold", size="4"),
            rx.vstack(
                rx.foreach(
                    grupo["partidos"],
                    lambda partido, idx: rx.text(
                        f"• Partido {idx + 1}: {partido['pareja1']} vs {partido['pareja2']}",
                        size="2",
                    ),
                ),
                align="start",
            ),
            
            spacing="3",
            align="start",
            width="100%",
        ),
        border_left=f"5px solid {border_color}",
        background=bg_color,
        padding="1.5rem",
    )


def mostrar_calendario() -> rx.Component:
    """Muestra el calendario general."""
    return rx.vstack(
        rx.heading("📅 Calendario de Partidos", size="6"),
        rx.callout(
            "Vista general con organización por días y canchas",
            icon="info",
            color_scheme="blue",
        ),
        
        rx.text("🚧 Calendario en desarrollo - próximamente disponible", size="4", color="gray"),
        
        spacing="4",
        padding="2rem",
    )


# ============================================================================
# APP PRINCIPAL
# ============================================================================

def index() -> rx.Component:
    """Página principal que enruta según el estado."""
    return rx.box(
        navbar(),
        rx.cond(
            State.pagina_actual == "inicio",
            pagina_inicio(),
            rx.cond(
                State.pagina_actual == "datos",
                pagina_datos(),
                rx.cond(
                    State.pagina_actual == "resultados",
                    pagina_resultados(),
                    pagina_inicio(),
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        background="#F5F5F5",
    )


# Crear la app
app = rx.App()
app.add_page(index, route="/", title="Torneo de Pádel")
