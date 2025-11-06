"""
Builder para el calendario de finales del domingo.
Define horarios fijos para cada fase y categoría.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class SlotFinal:
    """Representa un slot de partido en el calendario de finales"""
    categoria: str  # "Cuarta", "Quinta", "Sexta", "Séptima"
    fase: str  # "Cuartos", "Semifinal", "Final"
    numero_partido: int  # 1, 2, 3, 4 (para identificar cuál cuarto/semi)
    

class CalendarioFinalesBuilder:
    """
    Construye el calendario de finales del domingo con horarios predefinidos.
    
    Basado en el formato del torneo:
    - Categorías: 4ta, 5ta, 6ta, 7ma
    - Fases: Cuartos (4 partidos), Semifinales (2 partidos), Final (1 partido)
    """
    
    # Horarios disponibles el domingo
    HORARIOS_DOMINGO = [
        "09:00", "10:00", "11:00", "12:00", "13:00", "14:00",
        "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"
    ]
    
    # Estructura del calendario: hora -> (cancha1, cancha2)
    ESTRUCTURA_CALENDARIO = {
        # Mañana: Cuartos de Final
        "09:00": (
            SlotFinal("Quinta", "Cuartos", 1),
            SlotFinal("Quinta", "Cuartos", 2)
        ),
        "10:00": (
            SlotFinal("Quinta", "Cuartos", 3),
            SlotFinal("Quinta", "Cuartos", 4)
        ),
        "11:00": (
            SlotFinal("Séptima", "Cuartos", 1),
            SlotFinal("Séptima", "Cuartos", 2)
        ),
        "12:00": (
            SlotFinal("Séptima", "Cuartos", 3),
            SlotFinal("Séptima", "Cuartos", 4)
        ),
        
        # Mediodía: Semifinales y más Cuartos
        "13:00": (
            SlotFinal("Quinta", "Semifinal", 1),
            SlotFinal("Sexta", "Cuartos", 1)
        ),
        "14:00": (
            SlotFinal("Séptima", "Semifinal", 1),
            SlotFinal("Sexta", "Cuartos", 2)
        ),
        "15:00": (
            SlotFinal("Quinta", "Semifinal", 2),
            SlotFinal("Sexta", "Cuartos", 3)
        ),
        
        # Tarde: Más Semifinales y Cuartos de 4ta
        "16:00": (
            SlotFinal("Séptima", "Semifinal", 2),
            SlotFinal("Sexta", "Cuartos", 4)
        ),
        "17:00": (
            SlotFinal("Cuarta", "Cuartos", 1),
            SlotFinal("Cuarta", "Cuartos", 2)
        ),
        "18:00": (
            SlotFinal("Cuarta", "Cuartos", 3),
            SlotFinal("Cuarta", "Cuartos", 4)
        ),
        
        # Noche: Semifinales de 4ta y 6ta
        "19:00": (
            SlotFinal("Sexta", "Semifinal", 1),
            SlotFinal("Sexta", "Semifinal", 2)
        ),
        "20:00": (
            SlotFinal("Cuarta", "Semifinal", 1),
            SlotFinal("Cuarta", "Semifinal", 2)
        ),
        
        # Finales
        "21:00": (
            SlotFinal("Quinta", "Final", 1),
            SlotFinal("Séptima", "Final", 1)
        ),
        "22:00": (
            SlotFinal("Cuarta", "Final", 1),
            SlotFinal("Sexta", "Final", 1)
        ),
    }
    
    @staticmethod
    def generar_calendario_base() -> Dict[str, Dict[int, SlotFinal]]:
        """
        Genera la estructura base del calendario de finales.
        
        Returns:
            Dict con estructura: {"09:00": {1: SlotFinal, 2: SlotFinal}, ...}
        """
        calendario = {}
        
        for hora, (slot_cancha1, slot_cancha2) in CalendarioFinalesBuilder.ESTRUCTURA_CALENDARIO.items():
            calendario[hora] = {
                1: slot_cancha1,
                2: slot_cancha2
            }
        
        return calendario
    
    @staticmethod
    def obtener_slot_para_partido(categoria: str, fase: str, numero_partido: int) -> Tuple[str, int]:
        """
        Encuentra el horario y cancha asignados a un partido específico.
        
        Args:
            categoria: "Cuarta", "Quinta", "Sexta", "Séptima"
            fase: "Cuartos", "Semifinal", "Final"
            numero_partido: 1, 2, 3, 4
        
        Returns:
            Tupla (hora, cancha) ej: ("09:00", 1)
        """
        for hora, (slot_cancha1, slot_cancha2) in CalendarioFinalesBuilder.ESTRUCTURA_CALENDARIO.items():
            if (slot_cancha1.categoria == categoria and 
                slot_cancha1.fase == fase and 
                slot_cancha1.numero_partido == numero_partido):
                return (hora, 1)
            
            if (slot_cancha2.categoria == categoria and 
                slot_cancha2.fase == fase and 
                slot_cancha2.numero_partido == numero_partido):
                return (hora, 2)
        
        return None
    
    @staticmethod
    def poblar_calendario_con_fixtures(fixtures_dict: dict) -> Dict[str, Dict[int, dict]]:
        """
        Puebla el calendario base con los partidos reales de los fixtures.
        
        Args:
            fixtures_dict: Diccionario con fixtures por categoría
                          {"Cuarta": fixture_dict, "Quinta": fixture_dict, ...}
        
        Returns:
            Calendario poblado con información de partidos
        """
        calendario = {}
        
        # Inicializar calendario vacío
        for hora in CalendarioFinalesBuilder.HORARIOS_DOMINGO:
            calendario[hora] = {1: None, 2: None}
        
        # Mapeo de nombres de categoría
        categoria_map = {
            "Cuarta": "Cuarta",
            "Quinta": "Quinta",
            "Sexta": "Sexta",
            "Séptima": "Séptima"
        }
        
        # Mapeo de fases
        fase_map = {
            "CUARTOS": "Cuartos",
            "SEMIFINAL": "Semifinal",
            "FINAL": "Final"
        }
        
        # Procesar cada categoría
        for categoria_key, fixture_data in fixtures_dict.items():
            if not fixture_data:
                continue
            
            categoria_nombre = categoria_map.get(categoria_key, categoria_key)
            
            # Procesar cuartos
            for idx, partido in enumerate(fixture_data.get('cuartos', []), 1):
                slot_info = CalendarioFinalesBuilder.obtener_slot_para_partido(
                    categoria_nombre, "Cuartos", idx
                )
                if slot_info:
                    hora, cancha = slot_info
                    calendario[hora][cancha] = {
                        'categoria': categoria_key,
                        'fase': 'Cuartos',
                        'numero_partido': idx,
                        'partido_id': partido.get('id'),
                        'pareja1': partido.get('pareja1', {}).get('nombre') if partido.get('pareja1') else 'Por definir',
                        'pareja2': partido.get('pareja2', {}).get('nombre') if partido.get('pareja2') else 'Por definir',
                        'tiene_ganador': partido.get('tiene_ganador', False),
                        'ganador': partido.get('ganador', {}).get('nombre') if partido.get('ganador') else None
                    }
            
            # Procesar semifinales
            for idx, partido in enumerate(fixture_data.get('semifinales', []), 1):
                slot_info = CalendarioFinalesBuilder.obtener_slot_para_partido(
                    categoria_nombre, "Semifinal", idx
                )
                if slot_info:
                    hora, cancha = slot_info
                    calendario[hora][cancha] = {
                        'categoria': categoria_key,
                        'fase': 'Semifinal',
                        'numero_partido': idx,
                        'partido_id': partido.get('id'),
                        'pareja1': partido.get('pareja1', {}).get('nombre') if partido.get('pareja1') else 'Por definir',
                        'pareja2': partido.get('pareja2', {}).get('nombre') if partido.get('pareja2') else 'Por definir',
                        'tiene_ganador': partido.get('tiene_ganador', False),
                        'ganador': partido.get('ganador', {}).get('nombre') if partido.get('ganador') else None
                    }
            
            # Procesar final
            if fixture_data.get('final'):
                partido = fixture_data['final']
                slot_info = CalendarioFinalesBuilder.obtener_slot_para_partido(
                    categoria_nombre, "Final", 1
                )
                if slot_info:
                    hora, cancha = slot_info
                    calendario[hora][cancha] = {
                        'categoria': categoria_key,
                        'fase': 'Final',
                        'numero_partido': 1,
                        'partido_id': partido.get('id'),
                        'pareja1': partido.get('pareja1', {}).get('nombre') if partido.get('pareja1') else 'Por definir',
                        'pareja2': partido.get('pareja2', {}).get('nombre') if partido.get('pareja2') else 'Por definir',
                        'tiene_ganador': partido.get('tiene_ganador', False),
                        'ganador': partido.get('ganador', {}).get('nombre') if partido.get('ganador') else None
                    }
        
        return calendario
