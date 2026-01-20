import pandas as pd
import re
from typing import List, Dict, Set
from config import FRANJAS_HORARIAS


class CSVProcessor:
    @staticmethod
    def _extraer_hora_inicio(texto: str) -> str:
        """
        Extrae la hora de inicio de un texto con formato 'Día HH:MM a HH:MM' o 'Día H:MM'.
        Normaliza la hora con cero a la izquierda si es necesario.
        Retorna formato 'Día HH:MM'.
        Ejemplo: 'Sábado 9:00 a 12:00' -> 'Sábado 09:00'
        Ejemplo: 'Sábado 12:00 a 15:00' -> 'Sábado 12:00'
        """
        # Buscar patrón: Día seguido de hora (1 o 2 dígitos) : minutos
        match = re.search(r'(\w+)\s+(\d{1,2}):(\d{2})', texto)
        if match:
            dia = match.group(1)
            hora = match.group(2).zfill(2)  # Agregar cero a la izquierda si es necesario
            minutos = match.group(3)
            return f"{dia} {hora}:{minutos}"
        return texto.strip()
    
    @staticmethod
    def _extraer_franjas_de_texto(texto: str) -> List[str]:
        """
        Extrae todas las franjas horarias de un texto que puede contener múltiples horarios
        separados por punto y coma (;) o saltos de línea.
        
        Ejemplo: "Jueves 20:00 a 23:00;Viernes 21:00 a 00:00;Sábado 9:00 a 12:00"
        Retorna: ["Jueves 20:00", "Viernes 21:00", "Sábado 09:00"]
        """
        franjas_encontradas = []
        
        # Separar por punto y coma o salto de línea
        segmentos = re.split(r'[;\n]', texto)
        
        for segmento in segmentos:
            segmento = segmento.strip()
            if not segmento:
                continue
            
            # Extraer hora de inicio del segmento
            hora_inicio = CSVProcessor._extraer_hora_inicio(segmento)
            
            # Buscar coincidencia con franjas conocidas
            for franja_base in FRANJAS_HORARIAS:
                if hora_inicio == franja_base or franja_base in hora_inicio:
                    if franja_base not in franjas_encontradas:
                        franjas_encontradas.append(franja_base)
                    break
        
        return franjas_encontradas
    
    @staticmethod
    def procesar_dataframe(df: pd.DataFrame) -> List[Dict]:
        parejas = []
        
        for idx, fila in df.iterrows():
            nombre = None
            telefono = None
            categoria = None
            franjas = []
            
            for key, value in fila.items():
                key_lower = key.lower()
                
                # Detectar columna de nombre (puede incluir "nombre", "pareja", etc.)
                if 'nombre' in key_lower or 'pareja' in key_lower:
                    if pd.notna(value):
                        nombre = str(value).strip()
                
                # Detectar teléfono con múltiples variantes
                elif any(palabra in key_lower for palabra in ['tel', 'teléfono', 'telefono', 'phone', 'celular', 'contacto']):
                    if pd.notna(value):
                        telefono_str = str(value).strip()
                        # Eliminar espacios y caracteres no numéricos excepto + al inicio
                        if telefono_str and telefono_str not in ['nan', 'NaN', '']:
                            telefono = telefono_str
                
                # Detectar categoría
                elif 'categor' in key_lower:
                    if pd.notna(value):
                        categoria = str(value).strip().title()
                
                # Detectar franjas horarias
                # Puede ser en columnas separadas O en una sola columna con punto y coma
                elif any(palabra in key_lower for palabra in ['horario', 'franja', 'disponib', 'hora']):
                    if pd.notna(value):
                        valor_str = str(value).strip()
                        if valor_str and valor_str not in ['nan', 'NaN', '']:
                            # Si el valor contiene punto y coma, procesarlo como múltiples franjas
                            if ';' in valor_str:
                                franjas_extraidas = CSVProcessor._extraer_franjas_de_texto(valor_str)
                                franjas.extend([f for f in franjas_extraidas if f not in franjas])
                            else:
                                # Procesamiento individual
                                hora_inicio = CSVProcessor._extraer_hora_inicio(valor_str)
                                for franja_base in FRANJAS_HORARIAS:
                                    if hora_inicio == franja_base or franja_base in hora_inicio:
                                        if franja_base not in franjas:
                                            franjas.append(franja_base)
                                        break
                else:
                    # Detectar franjas en columnas tipo checkbox (columna = horario, valor = horario si está marcado)
                    if pd.notna(value) and str(value).strip():
                        valor_str = str(value).strip()
                        if valor_str not in ['nan', 'NaN', '']:
                            # Intentar extraer franja de la columna o del valor
                            # Si el valor contiene múltiples franjas con punto y coma
                            if ';' in valor_str:
                                franjas_extraidas = CSVProcessor._extraer_franjas_de_texto(valor_str)
                                franjas.extend([f for f in franjas_extraidas if f not in franjas])
                            else:
                                # Buscar en el nombre de la columna
                                hora_inicio = CSVProcessor._extraer_hora_inicio(key)
                                for franja_base in FRANJAS_HORARIAS:
                                    if hora_inicio == franja_base or franja_base in key:
                                        if franja_base not in franjas:
                                            franjas.append(franja_base)
                                        break
                                
                                # Si no encontró en la columna, buscar en el valor
                                if not franjas or franja_base not in franjas:
                                    hora_inicio = CSVProcessor._extraer_hora_inicio(valor_str)
                                    for franja_base in FRANJAS_HORARIAS:
                                        if hora_inicio == franja_base or franja_base in valor_str:
                                            if franja_base not in franjas:
                                                franjas.append(franja_base)
                                            break
            
            # Validar que tengamos los datos mínimos
            if nombre and categoria:
                parejas.append({
                    'categoria': categoria,
                    'franjas_disponibles': franjas,
                    'id': len(parejas) + 1,
                    'nombre': nombre,
                    'telefono': telefono or 'Sin teléfono'
                })
        
        return parejas
    
    @staticmethod
    def validar_archivo(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx'}
