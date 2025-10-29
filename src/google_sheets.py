"""
Integración con Google Sheets para importar y exportar datos.
Maneja la conexión con Google Forms (via Sheets) y exportación de resultados.
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime


class GoogleSheetsManager:
    """
    Gestor de conexión y operaciones con Google Sheets.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, credentials_path: str):
        """
        Inicializa la conexión con Google Sheets.
        
        Args:
            credentials_path: Ruta al archivo credentials.json
        """
        self.credentials_path = credentials_path
        self.client = None
        self._conectar()
    
    def _conectar(self):
        """Establece la conexión con Google Sheets API."""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(creds)
        except Exception as e:
            raise ConnectionError(f"Error al conectar con Google Sheets: {str(e)}")
    
    def importar_respuestas_form(self, spreadsheet_id: str, hoja: str = None) -> List[Dict]:
        """
        Importa las respuestas del Google Form desde una Google Sheet.
        
        Args:
            spreadsheet_id: ID de la Google Sheet (de la URL)
            hoja: Nombre de la hoja a leer (por defecto la primera)
        
        Returns:
            Lista de diccionarios con los datos de cada pareja
        """
        try:
            # Abrir el spreadsheet
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Obtener la hoja
            if hoja:
                worksheet = spreadsheet.worksheet(hoja)
            else:
                worksheet = spreadsheet.sheet1
            
            # Obtener todos los datos
            datos = worksheet.get_all_records()
            
            # Procesar y normalizar los datos
            parejas_procesadas = []
            for idx, fila in enumerate(datos, start=1):
                pareja = self._procesar_fila_form(fila, idx)
                if pareja:
                    parejas_procesadas.append(pareja)
            
            return parejas_procesadas
            
        except Exception as e:
            raise Exception(f"Error al importar datos: {str(e)}")
    
    def _procesar_fila_form(self, fila: Dict, id: int) -> Optional[Dict]:
        """
        Procesa una fila del formulario y la convierte al formato esperado.
        
        Mapeo de columnas del Google Form:
        - Timestamp (automático de Forms)
        - Nombre de la pareja (texto libre)
        - Teléfono (número)
        - Categoría (radio button)
        - Franjas horarias (checkboxes múltiples)
        """
        try:
            # Buscar columnas (pueden tener nombres variados)
            nombre = None
            telefono = None
            categoria = None
            franjas = []
            
            # Procesar cada columna del formulario
            for key, value in fila.items():
                key_lower = key.lower()
                
                # Nombre de la pareja
                if 'nombre' in key_lower or 'pareja' in key_lower:
                    nombre = str(value).strip()
                
                # Teléfono
                elif 'tel' in key_lower or 'teléfono' in key_lower or 'telefono' in key_lower:
                    telefono = str(value).strip()
                
                # Categoría
                elif 'categor' in key_lower:
                    categoria = str(value).strip().title()
                
                # Franjas horarias (pueden venir en múltiples formatos)
                elif 'horario' in key_lower or 'franja' in key_lower or 'preferencia' in key_lower:
                    # Si es una columna con múltiples valores separados por coma
                    if isinstance(value, str) and value:
                        # Puede venir como "Jueves 18:00 a 21:00, Viernes 18:00 a 21:00"
                        franjas_str = [f.strip() for f in value.split(',')]
                        franjas.extend(franjas_str)
            
            # Si no encontramos franjas en una sola columna, buscar columnas individuales
            if not franjas:
                franjas = self._extraer_franjas_individuales(fila)
            
            # Validar que tenemos los datos mínimos
            if not nombre or not categoria:
                return None
            
            return {
                'id': id,
                'nombre': nombre,
                'telefono': telefono or 'Sin teléfono',
                'categoria': categoria,
                'franjas_horarias': franjas
            }
            
        except Exception as e:
            print(f"Error procesando fila {id}: {str(e)}")
            return None
    
    def _extraer_franjas_individuales(self, fila: Dict) -> List[str]:
        """
        Extrae franjas horarias cuando vienen como columnas separadas (checkboxes).
        Busca columnas que contengan los horarios específicos.
        """
        franjas = []
        
        # Lista de franjas posibles
        franjas_posibles = [
            "Jueves 18:00 a 21:00",
            "Jueves 20:00 a 23:00",
            "Viernes 18:00 a 21:00",
            "Viernes 21:00 a 00:00",
            "Sábado 9:00 a 12:00",
            "Sábado 12:00 a 15:00",
            "Sábado 16:00 a 19:00",
            "Sábado 19:00 a 22:00"
        ]
        
        for key, value in fila.items():
            # Si la columna contiene una franja horaria y está marcada
            for franja in franjas_posibles:
                if franja in key and value:
                    franjas.append(franja)
                    break
        
        return franjas
    
    def exportar_grupos(self, spreadsheet_id: str, resultado_algoritmo, 
                       nombre_hoja: str = None) -> str:
        """
        Exporta los grupos generados a una nueva hoja de Google Sheets.
        
        Args:
            spreadsheet_id: ID del spreadsheet donde exportar
            resultado_algoritmo: ResultadoAlgoritmo del algoritmo
            nombre_hoja: Nombre de la nueva hoja (por defecto con timestamp)
        
        Returns:
            URL de la hoja creada
        """
        try:
            # Abrir el spreadsheet
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Nombre de la hoja
            if not nombre_hoja:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                nombre_hoja = f"Grupos_Torneo_{timestamp}"
            
            # Crear nueva hoja
            try:
                worksheet = spreadsheet.add_worksheet(
                    title=nombre_hoja,
                    rows=1000,
                    cols=20
                )
            except Exception:
                # Si ya existe, usar esa
                worksheet = spreadsheet.worksheet(nombre_hoja)
                worksheet.clear()
            
            # Preparar datos para exportar
            self._escribir_grupos_en_hoja(worksheet, resultado_algoritmo)
            
            # Aplicar formato
            self._aplicar_formato(worksheet, resultado_algoritmo)
            
            return spreadsheet.url
            
        except Exception as e:
            raise Exception(f"Error al exportar grupos: {str(e)}")
    
    def _escribir_grupos_en_hoja(self, worksheet, resultado_algoritmo):
        """Escribe los datos de grupos en la hoja."""
        fila_actual = 1
        
        # Título principal
        worksheet.update_cell(fila_actual, 1, "🎾 TORNEO DE PÁDEL - GRUPOS Y CALENDARIO")
        worksheet.update_cell(fila_actual + 1, 1, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        fila_actual += 3
        
        # Estadísticas
        stats = resultado_algoritmo.estadisticas
        worksheet.update_cell(fila_actual, 1, "📊 ESTADÍSTICAS")
        fila_actual += 1
        worksheet.update_cell(fila_actual, 1, f"Total parejas: {stats['total_parejas']}")
        fila_actual += 1
        worksheet.update_cell(fila_actual, 1, f"Parejas asignadas: {stats['parejas_asignadas']} ({stats['porcentaje_asignacion']:.1f}%)")
        fila_actual += 1
        worksheet.update_cell(fila_actual, 1, f"Parejas sin asignar: {stats['parejas_sin_asignar']}")
        fila_actual += 1
        worksheet.update_cell(fila_actual, 1, f"Total grupos: {stats['total_grupos']}")
        fila_actual += 3
        
        # Grupos por categoría
        colores_emoji = {
            "Cuarta": "🟢",
            "Quinta": "🟡",
            "Sexta": "🔵",
            "Séptima": "🟣"
        }
        
        for categoria in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
            if categoria not in resultado_algoritmo.grupos_por_categoria:
                continue
            
            grupos = resultado_algoritmo.grupos_por_categoria[categoria]
            if not grupos:
                continue
            
            # Título de categoría
            emoji = colores_emoji.get(categoria, "⚪")
            worksheet.update_cell(fila_actual, 1, f"{emoji} CATEGORÍA {categoria.upper()}")
            fila_actual += 1
            
            # Encabezados
            headers = ["Grupo", "Pareja 1", "Pareja 2", "Pareja 3", "Franja Horaria", "Cancha"]
            for col, header in enumerate(headers, start=1):
                worksheet.update_cell(fila_actual, col, header)
            fila_actual += 1
            
            # Datos de grupos
            for grupo in grupos:
                parejas_nombres = [p.nombre for p in grupo.parejas]
                while len(parejas_nombres) < 3:
                    parejas_nombres.append("-")
                
                # Buscar cancha en calendario
                cancha = self._buscar_cancha_grupo(grupo, resultado_algoritmo.calendario)
                
                row_data = [
                    f"Grupo {grupo.id}",
                    parejas_nombres[0],
                    parejas_nombres[1],
                    parejas_nombres[2],
                    grupo.franja_horaria or "Por coordinar",
                    f"Cancha {cancha}" if cancha else "Por asignar"
                ]
                
                for col, data in enumerate(row_data, start=1):
                    worksheet.update_cell(fila_actual, col, data)
                fila_actual += 1
            
            fila_actual += 2
        
        # Parejas sin asignar
        if resultado_algoritmo.parejas_sin_asignar:
            worksheet.update_cell(fila_actual, 1, "⚠️ PAREJAS SIN GRUPO ASIGNADO")
            fila_actual += 1
            worksheet.update_cell(fila_actual, 1, "Por favor coordinar manualmente")
            fila_actual += 1
            
            headers = ["Pareja", "Categoría", "Teléfono", "Franjas Disponibles"]
            for col, header in enumerate(headers, start=1):
                worksheet.update_cell(fila_actual, col, header)
            fila_actual += 1
            
            for pareja in resultado_algoritmo.parejas_sin_asignar:
                franjas_str = ", ".join(pareja.franjas_disponibles) if pareja.franjas_disponibles else "Ninguna"
                row_data = [
                    pareja.nombre,
                    pareja.categoria,
                    pareja.telefono,
                    franjas_str
                ]
                
                for col, data in enumerate(row_data, start=1):
                    worksheet.update_cell(fila_actual, col, data)
                fila_actual += 1
    
    def _buscar_cancha_grupo(self, grupo, calendario) -> Optional[int]:
        """Busca el número de cancha asignado a un grupo en el calendario."""
        for franja, partidos in calendario.items():
            for partido in partidos:
                if partido['grupo_id'] == grupo.id:
                    return partido['cancha']
        return None
    
    def _aplicar_formato(self, worksheet, resultado_algoritmo):
        """Aplica formato de colores y estilos a la hoja."""
        # Formato básico de encabezados en negrita
        # (Google Sheets API tiene limitaciones, formato básico por ahora)
        pass
    
    def crear_spreadsheet_nuevo(self, nombre: str) -> str:
        """
        Crea un nuevo Google Spreadsheet.
        
        Args:
            nombre: Nombre del nuevo spreadsheet
        
        Returns:
            ID del spreadsheet creado
        """
        try:
            spreadsheet = self.client.create(nombre)
            return spreadsheet.id
        except Exception as e:
            raise Exception(f"Error al crear spreadsheet: {str(e)}")
    
    def obtener_hojas_disponibles(self, spreadsheet_id: str) -> List[str]:
        """
        Obtiene la lista de hojas disponibles en un spreadsheet.
        
        Args:
            spreadsheet_id: ID del spreadsheet
        
        Returns:
            Lista de nombres de hojas
        """
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            return [worksheet.title for worksheet in spreadsheet.worksheets()]
        except Exception as e:
            raise Exception(f"Error al obtener hojas: {str(e)}")
