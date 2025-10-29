import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime

from config import GOOGLE_SHEETS_SCOPES, FRANJAS_HORARIAS, EMOJI_CATEGORIA


class GoogleSheetsIntegration:
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.client = None
        self._conectar()
    
    def _conectar(self):
        creds = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=GOOGLE_SHEETS_SCOPES
        )
        self.client = gspread.authorize(creds)
    
    def importar_respuestas(self, spreadsheet_id: str, hoja: str = None) -> List[Dict]:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(hoja) if hoja else spreadsheet.sheet1
        
        datos = worksheet.get_all_records()
        parejas_procesadas = []
        
        for idx, fila in enumerate(datos, start=1):
            pareja = self._procesar_fila_form(fila, idx)
            if pareja:
                parejas_procesadas.append(pareja)
        
        return parejas_procesadas
    
    def _procesar_fila_form(self, fila: Dict, id: int) -> Optional[Dict]:
        nombre = None
        telefono = None
        categoria = None
        franjas = []
        
        for key, value in fila.items():
            key_lower = key.lower()
            
            if 'nombre' in key_lower or 'pareja' in key_lower:
                nombre = str(value).strip()
            elif 'tel' in key_lower or 'teléfono' in key_lower or 'telefono' in key_lower:
                telefono = str(value).strip()
            elif 'categor' in key_lower:
                categoria = str(value).strip().title()
            elif 'horario' in key_lower or 'franja' in key_lower or 'preferencia' in key_lower:
                if isinstance(value, str) and value:
                    franjas_str = [f.strip() for f in value.split(',')]
                    franjas.extend(franjas_str)
        
        if not franjas:
            franjas = self._extraer_franjas_individuales(fila)
        
        if not nombre or not categoria:
            return None
        
        return {
            'id': id,
            'nombre': nombre,
            'telefono': telefono or 'Sin teléfono',
            'categoria': categoria,
            'franjas_horarias': franjas
        }
    
    def _extraer_franjas_individuales(self, fila: Dict) -> List[str]:
        franjas = []
        for key, value in fila.items():
            for franja in FRANJAS_HORARIAS:
                if franja in key and value:
                    franjas.append(franja)
                    break
        return franjas
    
    def exportar_grupos(self, spreadsheet_id: str, resultado_algoritmo, nombre_hoja: str = None) -> str:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        
        if not nombre_hoja:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_hoja = f"Grupos_Torneo_{timestamp}"
        
        try:
            worksheet = spreadsheet.add_worksheet(title=nombre_hoja, rows=1000, cols=20)
        except:
            worksheet = spreadsheet.worksheet(nombre_hoja)
            worksheet.clear()
        
        self._escribir_grupos_en_hoja(worksheet, resultado_algoritmo)
        return spreadsheet.url
    
    def _escribir_grupos_en_hoja(self, worksheet, resultado_algoritmo):
        fila_actual = 1
        
        worksheet.update_cell(fila_actual, 1, "🎾 TORNEO DE PÁDEL - GRUPOS Y CALENDARIO")
        worksheet.update_cell(fila_actual + 1, 1, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        fila_actual += 3
        
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
        
        for categoria in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
            if categoria not in resultado_algoritmo.grupos_por_categoria:
                continue
            
            grupos = resultado_algoritmo.grupos_por_categoria[categoria]
            if not grupos:
                continue
            
            emoji = EMOJI_CATEGORIA.get(categoria, "⚪")
            worksheet.update_cell(fila_actual, 1, f"{emoji} CATEGORÍA {categoria.upper()}")
            fila_actual += 1
            
            headers = ["Grupo", "Pareja 1", "Pareja 2", "Pareja 3", "Franja Horaria", "Cancha"]
            for col, header in enumerate(headers, start=1):
                worksheet.update_cell(fila_actual, col, header)
            fila_actual += 1
            
            for grupo in grupos:
                parejas_nombres = [p.nombre for p in grupo.parejas]
                while len(parejas_nombres) < 3:
                    parejas_nombres.append("-")
                
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
                row_data = [pareja.nombre, pareja.categoria, pareja.telefono, franjas_str]
                
                for col, data in enumerate(row_data, start=1):
                    worksheet.update_cell(fila_actual, col, data)
                fila_actual += 1
    
    def _buscar_cancha_grupo(self, grupo, calendario) -> Optional[int]:
        for franja, partidos in calendario.items():
            for partido in partidos:
                if partido['grupo_id'] == grupo.id:
                    return partido['cancha']
        return None
    
    def crear_spreadsheet(self, nombre: str) -> str:
        spreadsheet = self.client.create(nombre)
        return spreadsheet.id
    
    def obtener_hojas(self, spreadsheet_id: str) -> List[str]:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        return [worksheet.title for worksheet in spreadsheet.worksheets()]
