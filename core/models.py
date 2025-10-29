from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Pareja:
    id: int
    nombre: str
    telefono: str
    categoria: str
    franjas_disponibles: List[str]
    grupo_asignado: Optional[int] = None
    
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
            'grupo_asignado': self.grupo_asignado
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data['id'],
            nombre=data['nombre'],
            telefono=data.get('telefono', 'Sin teléfono'),
            categoria=data['categoria'],
            franjas_disponibles=data.get('franjas_disponibles', [])
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
