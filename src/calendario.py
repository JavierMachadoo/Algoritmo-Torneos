"""
Generación de calendario de partidos y exportación.
"""

from typing import Dict, List
from datetime import datetime, timedelta
from src.algoritmo import Grupo, ResultadoAlgoritmo


class GeneradorCalendario:
    """
    Genera calendarios detallados de partidos con horarios y canchas.
    """
    
    def __init__(self, duracion_partido_horas: int = 1):
        """
        Inicializa el generador de calendario.
        
        Args:
            duracion_partido_horas: Duración de cada partido en horas
        """
        self.duracion_partido = duracion_partido_horas
    
    def generar_calendario_detallado(self, resultado: ResultadoAlgoritmo) -> Dict:
        """
        Genera un calendario detallado con todos los partidos organizados.
        
        Args:
            resultado: Resultado del algoritmo con grupos formados
        
        Returns:
            Diccionario con calendario estructurado por franja horaria
        """
        calendario_detallado = {}
        
        for franja, partidos in resultado.calendario.items():
            # Agrupar partidos por grupo
            partidos_por_grupo = {}
            for partido in partidos:
                grupo_id = partido['grupo_id']
                if grupo_id not in partidos_por_grupo:
                    partidos_por_grupo[grupo_id] = []
                partidos_por_grupo[grupo_id].append(partido)
            
            # Calcular horarios específicos para cada partido
            calendario_detallado[franja] = self._calcular_horarios_partidos(
                franja, partidos_por_grupo
            )
        
        return calendario_detallado
    
    def _calcular_horarios_partidos(self, franja: str, 
                                    partidos_por_grupo: Dict) -> List[Dict]:
        """
        Calcula horarios específicos para los partidos de una franja.
        
        Ejemplo: Si la franja es "Sábado 12:00 a 15:00"
        Partido 1: 12:00 - 13:00
        Partido 2: 13:00 - 14:00
        Partido 3: 14:00 - 15:00
        """
        partidos_con_horario = []
        hora_inicio = self._extraer_hora_inicio(franja)
        
        for grupo_id, partidos in partidos_por_grupo.items():
            # Los 3 partidos del grupo se juegan consecutivamente
            hora_actual = hora_inicio
            
            for partido in sorted(partidos, key=lambda x: x['partido_num']):
                hora_fin = hora_actual + self.duracion_partido
                
                partido_detallado = {
                    **partido,
                    'hora_inicio_num': hora_actual,
                    'hora_fin_num': hora_fin,
                    'hora_inicio_str': self._formato_hora(hora_actual),
                    'hora_fin_str': self._formato_hora(hora_fin)
                }
                partidos_con_horario.append(partido_detallado)
                
                hora_actual = hora_fin
        
        return partidos_con_horario
    
    def _extraer_hora_inicio(self, franja: str) -> int:
        """
        Extrae la hora de inicio de una franja horaria.
        
        Ejemplo: "Sábado 12:00 a 15:00" -> 12
        """
        try:
            # Buscar el primer número seguido de :00
            import re
            match = re.search(r'(\d+):00', franja)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0
    
    def _formato_hora(self, hora: int) -> str:
        """Formatea una hora numérica a string."""
        return f"{hora:02d}:00"
    
    def exportar_calendario_texto(self, resultado: ResultadoAlgoritmo) -> str:
        """
        Exporta el calendario en formato texto legible.
        
        Returns:
            String con el calendario formateado
        """
        calendario = self.generar_calendario_detallado(resultado)
        
        texto = "🎾 CALENDARIO DE PARTIDOS - TORNEO DE PÁDEL\n"
        texto += "=" * 60 + "\n\n"
        
        for franja in sorted(calendario.keys()):
            partidos = calendario[franja]
            
            if not partidos:
                continue
            
            texto += f"\n📅 {franja}\n"
            texto += "-" * 60 + "\n"
            
            # Agrupar por cancha
            partidos_cancha_1 = [p for p in partidos if p['cancha'] == 1]
            partidos_cancha_2 = [p for p in partidos if p['cancha'] == 2]
            
            if partidos_cancha_1:
                texto += "\n🏟️  CANCHA 1:\n"
                for partido in sorted(partidos_cancha_1, key=lambda x: x['hora_inicio_num']):
                    texto += self._formato_partido_texto(partido)
            
            if partidos_cancha_2:
                texto += "\n🏟️  CANCHA 2:\n"
                for partido in sorted(partidos_cancha_2, key=lambda x: x['hora_inicio_num']):
                    texto += self._formato_partido_texto(partido)
            
            texto += "\n"
        
        # Parejas sin asignar
        if resultado.parejas_sin_asignar:
            texto += "\n⚠️  PAREJAS SIN GRUPO ASIGNADO\n"
            texto += "=" * 60 + "\n"
            texto += "Por favor coordinar manualmente:\n\n"
            
            for pareja in resultado.parejas_sin_asignar:
                texto += f"  • {pareja.nombre} ({pareja.categoria})\n"
                texto += f"    Tel: {pareja.telefono}\n"
                if pareja.franjas_disponibles:
                    texto += f"    Disponible: {', '.join(pareja.franjas_disponibles)}\n"
                texto += "\n"
        
        return texto
    
    def _formato_partido_texto(self, partido: Dict) -> str:
        """Formatea un partido para mostrar en texto."""
        return (
            f"  {partido['hora_inicio_str']} - {partido['hora_fin_str']} | "
            f"{partido['color']} {partido['categoria']} | "
            f"Grupo {partido['grupo_id']} - Partido {partido['partido_num']}\n"
            f"    {partido['pareja1']} vs {partido['pareja2']}\n"
        )
    
    def generar_estadisticas_visuales(self, resultado: ResultadoAlgoritmo) -> Dict:
        """
        Genera datos para visualizaciones (gráficos).
        
        Returns:
            Diccionario con datos para gráficos
        """
        stats = resultado.estadisticas
        
        return {
            'parejas': {
                'asignadas': stats['parejas_asignadas'],
                'sin_asignar': stats['parejas_sin_asignar']
            },
            'grupos_por_categoria': stats['grupos_por_categoria'],
            'parejas_por_categoria': stats['parejas_por_categoria'],
            'compatibilidad': {
                'perfecta': stats['grupos_compatibilidad_perfecta'],
                'parcial': stats['grupos_compatibilidad_parcial']
            }
        }
