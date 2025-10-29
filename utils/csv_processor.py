import pandas as pd
from typing import List, Dict
from config import FRANJAS_HORARIAS


class CSVProcessor:
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
                    'id': len(parejas) + 1,
                    'nombre': nombre,
                    'telefono': telefono or 'Sin teléfono',
                    'categoria': categoria,
                    'franjas_disponibles': franjas
                })
        
        return parejas
    
    @staticmethod
    def validar_archivo(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx'}
