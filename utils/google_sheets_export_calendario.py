import gspread
from google.oauth2.service_account import Credentials
from typing import Optional
from datetime import datetime

from config import GOOGLE_SHEETS_SCOPES, EMOJI_CATEGORIA


class GoogleSheetsExportCalendario:
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
    
    def exportar_calendario(self, spreadsheet_id: str, resultado_algoritmo, nombre_hoja: str = None) -> str:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        
        if not nombre_hoja:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_hoja = f"Calendario_{timestamp}"
        
        try:
            worksheet = spreadsheet.add_worksheet(title=nombre_hoja, rows=200, cols=12)
        except:
            worksheet = spreadsheet.worksheet(nombre_hoja)
            worksheet.clear()
        
        self._escribir_calendario(worksheet, resultado_algoritmo)
        return spreadsheet.url
    
    def _escribir_calendario(self, worksheet, resultado_algoritmo):
        datos = []
        formatos = []  # Lista para guardar formato de cada celda
        
        # Título
        datos.append(["TORNEO LAGOMAR PÁDEL CLUB"])
        formatos.append([{'backgroundColor': {'red': 0.12, 'green': 0.31, 'blue': 0.47}, 
                         'textFormat': {'bold': True, 'fontSize': 18, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                         'horizontalAlignment': 'CENTER'}])
        datos.append([])
        formatos.append([{}])
        
        # Organizar por días
        calendario = resultado_algoritmo.calendario
        dias_orden = ['Jueves', 'Viernes', 'Sábado']
        
        for dia in dias_orden:
            if dia not in calendario or not calendario[dia]:
                continue
            
            # Encabezado del día (rojo con texto cursiva)
            datos.append([dia.upper()])
            formatos.append([{'backgroundColor': {'red': 1, 'green': 0, 'blue': 0},
                            'textFormat': {'bold': True, 'italic': True, 'fontSize': 14},
                            'horizontalAlignment': 'CENTER'}])
            
            # Encabezados de columnas (verde claro con negritas)
            datos.append(["HORA", "SERIE", "CANCHA 1", "RESULTADOS", "", "", 
                         "HORA", "SERIE", "CANCHA 2", "RESULTADOS", "", ""])
            header_format = {'backgroundColor': {'red': 0.56, 'green': 0.77, 'blue': 0.49},
                           'textFormat': {'bold': True, 'italic': True, 'fontSize': 12},
                           'horizontalAlignment': 'CENTER'}
            formatos.append([header_format] * 12)
            
            # Obtener todas las franjas horarias del día
            franjas = sorted(calendario[dia].keys())
            
            for franja in franjas:
                hora = franja.split()[1] if ' ' in franja else franja
                canchas = calendario[dia][franja]
                
                # Determinar si hay partidos en esta franja
                tiene_partido_c1 = len(canchas) > 0 and canchas[0]
                tiene_partido_c2 = len(canchas) > 1 and canchas[1]
                
                # Fila 1: Hora y primer partido de cada cancha
                fila1 = [hora]
                formato_fila1 = []
                
                # Formato hora
                if tiene_partido_c1 or tiene_partido_c2:
                    formato_hora = {'textFormat': {'bold': True}}
                else:
                    formato_hora = {'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                formato_fila1.append(formato_hora)
                
                # Cancha 1
                if tiene_partido_c1:
                    partido1 = canchas[0]
                    categoria = partido1.get('categoria', '')
                    color_bg = self._get_color_categoria(categoria)
                    serie = f"{self._get_numero_categoria(categoria)}{self._get_letra_grupo(partido1.get('grupo_id', 0))}"
                    fila1.extend([serie, partido1.get('pareja1', ''), "", "", ""])
                    formato_fila1.extend([
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},  # SERIE
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},  # Pareja
                        {'backgroundColor': color_bg},  # Resultado 1
                        {'backgroundColor': color_bg},  # Resultado 2
                        {'backgroundColor': color_bg}   # Resultado 3
                    ])
                else:
                    fila1.extend(["", "", "", "", ""])
                    gray_bg = {'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                    formato_fila1.extend([gray_bg] * 5)
                
                # Hora repetida para cancha 2
                fila1.append(hora)
                formato_fila1.append(formato_hora)
                
                # Cancha 2
                if tiene_partido_c2:
                    partido2 = canchas[1]
                    categoria = partido2.get('categoria', '')
                    color_bg = self._get_color_categoria(categoria)
                    serie = f"{self._get_numero_categoria(categoria)}{self._get_letra_grupo(partido2.get('grupo_id', 0))}"
                    fila1.extend([serie, partido2.get('pareja1', ''), "", "", ""])
                    formato_fila1.extend([
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg}
                    ])
                else:
                    fila1.extend(["", "", "", "", ""])
                    gray_bg = {'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                    formato_fila1.extend([gray_bg] * 5)
                
                datos.append(fila1)
                formatos.append(formato_fila1)
                
                # Fila 2: Pareja 2 de cada cancha
                fila2 = [""]
                formato_fila2 = [{}]
                
                # Cancha 1
                if tiene_partido_c1:
                    color_bg = self._get_color_categoria(canchas[0].get('categoria', ''))
                    fila2.extend(["", canchas[0].get('pareja2', ''), "", "", ""])
                    formato_fila2.extend([
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg}
                    ])
                else:
                    fila2.extend(["", "", "", "", ""])
                    gray_bg = {'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                    formato_fila2.extend([gray_bg] * 5)
                
                fila2.append("")
                formato_fila2.append({})
                
                # Cancha 2
                if tiene_partido_c2:
                    color_bg = self._get_color_categoria(canchas[1].get('categoria', ''))
                    fila2.extend(["", canchas[1].get('pareja2', ''), "", "", ""])
                    formato_fila2.extend([
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg, 'textFormat': {'bold': True}},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg},
                        {'backgroundColor': color_bg}
                    ])
                else:
                    fila2.extend(["", "", "", "", ""])
                    gray_bg = {'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                    formato_fila2.extend([gray_bg] * 5)
                
                datos.append(fila2)
                formatos.append(formato_fila2)
            
            # Línea en blanco entre días
            datos.append([])
            formatos.append([{}])
        
        # Escribir todos los datos de una vez
        worksheet.update('A1', datos)
        
        # Aplicar formatos
        self._aplicar_formatos(worksheet, formatos)
    
    def _aplicar_formatos(self, worksheet, formatos):
        """Aplica formatos de color y estilo a las celdas"""
        requests = []
        
        for fila_idx, fila_formatos in enumerate(formatos):
            for col_idx, formato in enumerate(fila_formatos):
                if formato:
                    cell_format = {
                        'repeatCell': {
                            'range': {
                                'sheetId': worksheet.id,
                                'startRowIndex': fila_idx,
                                'endRowIndex': fila_idx + 1,
                                'startColumnIndex': col_idx,
                                'endColumnIndex': col_idx + 1
                            },
                            'cell': {
                                'userEnteredFormat': formato
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                        }
                    }
                    requests.append(cell_format)
        
        if requests:
            body = {'requests': requests}
            worksheet.spreadsheet.batch_update(body)
    
    def _get_color_categoria(self, categoria):
        """Retorna el color RGB de la categoría"""
        colores = {
            'Cuarta': {'red': 0, 'green': 1, 'blue': 0},      # Verde lima
            'Quinta': {'red': 1, 'green': 1, 'blue': 0},      # Amarillo
            'Sexta': {'red': 0, 'green': 1, 'blue': 1},       # Cyan
            'Séptima': {'red': 1, 'green': 0, 'blue': 1}      # Magenta
        }
        return colores.get(categoria, {'red': 1, 'green': 1, 'blue': 1})
    
    def _get_numero_categoria(self, categoria):
        """Retorna el número de la categoría (4, 5, 6, 7)"""
        mapping = {
            'Cuarta': '4',
            'Quinta': '5',
            'Sexta': '6',
            'Séptima': '7'
        }
        return mapping.get(categoria, '')
    
    def _get_letra_grupo(self, grupo_id):
        """Retorna la letra del grupo basado en el ID"""
        # Los grupos se numeran secuencialmente, convertimos a letras A, B, C, D
        if grupo_id <= 0:
            return 'A'
        letra_index = (grupo_id - 1) % 4
        return chr(65 + letra_index)  # 65 es 'A' en ASCII
