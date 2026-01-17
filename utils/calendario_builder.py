from typing import Dict
from config import HORARIOS_POR_DIA


class CalendarioBuilder:
    def __init__(self, num_canchas: int = 2):
        self.num_canchas = num_canchas
    
    def construir_calendario_vacio(self) -> Dict:
        calendario = {}
        for dia, horas in HORARIOS_POR_DIA.items():
            calendario[dia] = {hora: [None] * self.num_canchas for hora in horas}
        return calendario
    
    def organizar_partidos(self, resultado_algoritmo, canchas_por_grupo=None) -> Dict:
        """Organiza los partidos en el calendario.
        
        Args:
            resultado_algoritmo: Resultado del algoritmo con los grupos
            canchas_por_grupo: Dict opcional con {grupo_id: numero_cancha}
        """
        calendario = self.construir_calendario_vacio()
        franjas_a_horas = self._mapear_franjas_a_horas()
        
        for categoria, grupos in resultado_algoritmo.grupos_por_categoria.items():
            for grupo in grupos:
                if not grupo.franja_horaria:
                    continue
                
                # Obtener la cancha asignada al grupo si existe
                cancha_asignada = None
                if canchas_por_grupo and grupo.id in canchas_por_grupo:
                    cancha_asignada = canchas_por_grupo[grupo.id]
                
                self._asignar_partidos_grupo(calendario, grupo, categoria, franjas_a_horas, cancha_asignada)
        
        return calendario
    
    def _mapear_franjas_a_horas(self) -> Dict:
        return {
            'Jueves 18:00': ('Jueves', ['18:00', '19:00', '20:00']),
            'Jueves 20:00': ('Jueves', ['20:00', '21:00', '22:00']),
            'Viernes 18:00': ('Viernes', ['18:00', '19:00', '20:00']),
            'Viernes 21:00': ('Viernes', ['21:00', '22:00', '23:00']),
            'Sábado 09:00': ('Sábado', ['09:00', '10:00', '11:00']),
            'Sábado 9:00': ('Sábado', ['09:00', '10:00', '11:00']),
            'Sábado 12:00': ('Sábado', ['12:00', '13:00', '14:00']),
            'Sábado 16:00': ('Sábado', ['16:00', '17:00', '18:00']),
            'Sábado 19:00': ('Sábado', ['19:00', '20:00', '21:00']),
        }
    
    def _asignar_partidos_grupo(self, calendario, grupo, categoria, franjas_a_horas, cancha_asignada=None):
        franja_grupo = grupo.franja_horaria
        
        for franja_key, (dia, horas_disponibles) in franjas_a_horas.items():
            if franja_key in franja_grupo:
                hora_idx = 0
                for partido_num, (p1, p2) in enumerate(grupo.partidos):
                    if hora_idx >= len(horas_disponibles):
                        break
                    
                    hora = horas_disponibles[hora_idx]
                    
                    # Usar la cancha asignada si existe, sino buscar una libre
                    if cancha_asignada is not None:
                        cancha_idx = int(cancha_asignada) - 1  # Convertir de 1-indexed a 0-indexed
                    else:
                        cancha_idx = self._buscar_cancha_libre(calendario[dia][hora])
                    
                    if cancha_idx is not None and cancha_idx < self.num_canchas:
                        partido = {
                            'categoria': categoria,
                            'grupo_id': grupo.id,
                            'pareja1': p1.nombre,
                            'pareja2': p2.nombre
                        }
                        calendario[dia][hora][cancha_idx] = partido
                        hora_idx += 1
                
                break
    
    def _buscar_cancha_libre(self, canchas) -> int:
        for idx, cancha in enumerate(canchas):
            if cancha is None:
                return idx
        return None
