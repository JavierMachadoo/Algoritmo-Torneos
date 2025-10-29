"""
Exportación de datos a diferentes formatos.
"""

import json
from typing import Dict, List
from src.algoritmo import ResultadoAlgoritmo, Pareja, Grupo


class ExportadorDatos:
    """
    Exporta los resultados del algoritmo a diferentes formatos.
    """
    
    @staticmethod
    def exportar_json(resultado: ResultadoAlgoritmo, archivo: str):
        """
        Exporta el resultado a un archivo JSON.
        
        Args:
            resultado: ResultadoAlgoritmo a exportar
            archivo: Ruta del archivo de salida
        """
        datos = {
            'fecha_generacion': None,  # Se puede agregar timestamp
            'estadisticas': resultado.estadisticas,
            'grupos': ExportadorDatos._grupos_a_dict(resultado.grupos_por_categoria),
            'parejas_sin_asignar': ExportadorDatos._parejas_a_dict(resultado.parejas_sin_asignar),
            'calendario': resultado.calendario
        }
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _grupos_a_dict(grupos_por_categoria: Dict[str, List[Grupo]]) -> Dict:
        """Convierte grupos a diccionario serializable."""
        resultado = {}
        
        for categoria, grupos in grupos_por_categoria.items():
            resultado[categoria] = [
                {
                    'id': grupo.id,
                    'categoria': grupo.categoria,
                    'franja_horaria': grupo.franja_horaria,
                    'score_compatibilidad': grupo.score_compatibilidad,
                    'parejas': [
                        {
                            'id': p.id,
                            'nombre': p.nombre,
                            'telefono': p.telefono,
                            'categoria': p.categoria
                        }
                        for p in grupo.parejas
                    ],
                    'partidos': [
                        {
                            'pareja1': p1.nombre,
                            'pareja2': p2.nombre
                        }
                        for p1, p2 in grupo.partidos
                    ]
                }
                for grupo in grupos
            ]
        
        return resultado
    
    @staticmethod
    def _parejas_a_dict(parejas: List[Pareja]) -> List[Dict]:
        """Convierte parejas a diccionario serializable."""
        return [
            {
                'id': p.id,
                'nombre': p.nombre,
                'telefono': p.telefono,
                'categoria': p.categoria,
                'franjas_disponibles': p.franjas_disponibles
            }
            for p in parejas
        ]
    
    @staticmethod
    def exportar_csv_grupos(resultado: ResultadoAlgoritmo, archivo: str):
        """
        Exporta los grupos a un archivo CSV.
        
        Args:
            resultado: ResultadoAlgoritmo a exportar
            archivo: Ruta del archivo CSV de salida
        """
        import csv
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'Grupo ID', 'Categoría', 'Franja Horaria', 
                'Pareja 1', 'Pareja 2', 'Pareja 3', 
                'Teléfono 1', 'Teléfono 2', 'Teléfono 3',
                'Score Compatibilidad'
            ])
            
            # Datos
            for categoria, grupos in resultado.grupos_por_categoria.items():
                for grupo in grupos:
                    parejas = grupo.parejas + [None] * (3 - len(grupo.parejas))
                    
                    writer.writerow([
                        grupo.id,
                        grupo.categoria,
                        grupo.franja_horaria or 'Por coordinar',
                        parejas[0].nombre if parejas[0] else '-',
                        parejas[1].nombre if parejas[1] else '-',
                        parejas[2].nombre if parejas[2] else '-',
                        parejas[0].telefono if parejas[0] else '-',
                        parejas[1].telefono if parejas[1] else '-',
                        parejas[2].telefono if parejas[2] else '-',
                        grupo.score_compatibilidad
                    ])
    
    @staticmethod
    def exportar_csv_parejas_sin_asignar(resultado: ResultadoAlgoritmo, archivo: str):
        """
        Exporta las parejas sin asignar a un archivo CSV.
        
        Args:
            resultado: ResultadoAlgoritmo a exportar
            archivo: Ruta del archivo CSV de salida
        """
        import csv
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'Nombre', 'Categoría', 'Teléfono', 'Franjas Disponibles'
            ])
            
            # Datos
            for pareja in resultado.parejas_sin_asignar:
                franjas = ', '.join(pareja.franjas_disponibles) if pareja.franjas_disponibles else 'Ninguna'
                writer.writerow([
                    pareja.nombre,
                    pareja.categoria,
                    pareja.telefono,
                    franjas
                ])
