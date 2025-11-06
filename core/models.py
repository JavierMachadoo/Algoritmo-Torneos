from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum


class PosicionGrupo(Enum):
    """Posiciones finales en el grupo"""
    PRIMERO = 1
    SEGUNDO = 2
    TERCERO = 3


class FaseFinal(Enum):
    """Fases de las finales"""
    OCTAVOS = "Octavos de Final"
    CUARTOS = "Cuartos de Final"
    SEMIFINAL = "Semifinal"
    FINAL = "Final"


@dataclass
class Pareja:
    id: int
    nombre: str
    telefono: str
    categoria: str
    franjas_disponibles: List[str]
    grupo_asignado: Optional[int] = None
    posicion_grupo: Optional[PosicionGrupo] = None  # Nueva: posición final en el grupo
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Pareja):
            return self.id == other.id
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'categoria': self.categoria,
            'franjas_disponibles': self.franjas_disponibles,
            'grupo_asignado': self.grupo_asignado,
            'posicion_grupo': self.posicion_grupo.value if self.posicion_grupo else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        posicion = data.get('posicion_grupo')
        return cls(
            id=data['id'],
            nombre=data['nombre'],
            telefono=data.get('telefono', 'Sin teléfono'),
            categoria=data['categoria'],
            franjas_disponibles=data.get('franjas_disponibles', []),
            grupo_asignado=data.get('grupo_asignado'),
            posicion_grupo=PosicionGrupo(posicion) if posicion else None
        )


@dataclass
class Grupo:
    id: int
    categoria: str
    parejas: List[Pareja] = field(default_factory=list)
    franja_horaria: Optional[str] = None
    partidos: List[Tuple[Pareja, Pareja]] = field(default_factory=list)
    score_compatibilidad: float = 0.0
    
    def agregar_pareja(self, pareja: Pareja):
        if len(self.parejas) < 3:
            self.parejas.append(pareja)
            pareja.grupo_asignado = self.id
    
    def esta_completo(self) -> bool:
        return len(self.parejas) == 3
    
    def generar_partidos(self):
        if self.esta_completo():
            self.partidos = [
                (self.parejas[0], self.parejas[1]),
                (self.parejas[0], self.parejas[2]),
                (self.parejas[1], self.parejas[2])
            ]
    
    def to_dict(self):
        return {
            'id': self.id,
            'categoria': self.categoria,
            'parejas': [p.to_dict() for p in self.parejas],
            'franja_horaria': self.franja_horaria,
            'partidos': [
                {'pareja1': p1.nombre, 'pareja2': p2.nombre}
                for p1, p2 in self.partidos
            ],
            'score_compatibilidad': self.score_compatibilidad
        }


@dataclass
class ResultadoAlgoritmo:
    grupos_por_categoria: dict
    parejas_sin_asignar: List[Pareja]
    calendario: dict
    estadisticas: dict


@dataclass
class PartidoFinal:
    """Representa un partido en la fase final"""
    id: str  # Ej: "cuartos_1", "semi_1", "final"
    fase: FaseFinal
    pareja1: Optional[Pareja] = None
    pareja2: Optional[Pareja] = None
    ganador: Optional[Pareja] = None
    numero_partido: int = 1  # Número del partido dentro de la fase
    
    def to_dict(self):
        return {
            'id': self.id,
            'fase': self.fase.value,
            'pareja1': self.pareja1.to_dict() if self.pareja1 else None,
            'pareja2': self.pareja2.to_dict() if self.pareja2 else None,
            'ganador': self.ganador.to_dict() if self.ganador else None,
            'numero_partido': self.numero_partido,
            'esta_completo': self.pareja1 is not None and self.pareja2 is not None,
            'tiene_ganador': self.ganador is not None
        }
    
    @staticmethod
    def from_dict(data: dict, grupos: List['Grupo']) -> 'PartidoFinal':
        """Reconstruye un PartidoFinal desde un diccionario"""
        # Crear un mapa de parejas por ID para búsqueda rápida
        parejas_map = {}
        for grupo in grupos:
            for pareja in grupo.parejas:
                parejas_map[pareja.id] = pareja
        
        def encontrar_pareja(pareja_dict):
            if not pareja_dict:
                return None
            pareja_id = pareja_dict.get('id')
            return parejas_map.get(pareja_id)
        
        return PartidoFinal(
            id=data['id'],
            fase=FaseFinal(data['fase']),
            pareja1=encontrar_pareja(data.get('pareja1')),
            pareja2=encontrar_pareja(data.get('pareja2')),
            ganador=encontrar_pareja(data.get('ganador')),
            numero_partido=data.get('numero_partido', 1)
        )


@dataclass
class FixtureFinales:
    """Fixture completo de finales para una categoría"""
    categoria: str
    octavos: List[PartidoFinal] = field(default_factory=list)
    cuartos: List[PartidoFinal] = field(default_factory=list)
    semifinales: List[PartidoFinal] = field(default_factory=list)
    final: Optional[PartidoFinal] = None
    
    def to_dict(self):
        return {
            'categoria': self.categoria,
            'octavos': [p.to_dict() for p in self.octavos],
            'cuartos': [p.to_dict() for p in self.cuartos],
            'semifinales': [p.to_dict() for p in self.semifinales],
            'final': self.final.to_dict() if self.final else None
        }
    
    @staticmethod
    def from_dict(data: dict, grupos: List['Grupo']) -> 'FixtureFinales':
        """Reconstruye un FixtureFinales desde un diccionario"""
        fixture = FixtureFinales(categoria=data['categoria'])
        
        # Reconstruir cada lista de partidos
        fixture.octavos = [
            PartidoFinal.from_dict(p, grupos) for p in data.get('octavos', [])
        ]
        fixture.cuartos = [
            PartidoFinal.from_dict(p, grupos) for p in data.get('cuartos', [])
        ]
        fixture.semifinales = [
            PartidoFinal.from_dict(p, grupos) for p in data.get('semifinales', [])
        ]
        
        if data.get('final'):
            fixture.final = PartidoFinal.from_dict(data['final'], grupos)
        
        return fixture

