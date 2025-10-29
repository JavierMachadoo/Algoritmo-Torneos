"""
Algoritmo de formación de grupos para torneos de pádel.
Agrupa parejas por categoría y compatibilidad de horarios.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import itertools


# Definición de franjas horarias disponibles
FRANJAS_HORARIAS = [
    "Jueves 18:00 a 21:00",
    "Jueves 20:00 a 23:00",
    "Viernes 18:00 a 21:00",
    "Viernes 21:00 a 00:00",
    "Sábado 9:00 a 12:00",
    "Sábado 12:00 a 15:00",
    "Sábado 16:00 a 19:00",
    "Sábado 19:00 a 22:00"
]

# Categorías disponibles
CATEGORIAS = ["Cuarta", "Quinta", "Sexta", "Séptima"]

# Colores por categoría para visualización
COLORES_CATEGORIA = {
    "Cuarta": "🟢",
    "Quinta": "🟡",
    "Sexta": "🔵",
    "Séptima": "🟣"
}


@dataclass
class Pareja:
    """Representa una pareja de jugadores."""
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


@dataclass
class Grupo:
    """Representa un grupo de 3 parejas."""
    id: int
    categoria: str
    parejas: List[Pareja] = field(default_factory=list)
    franja_horaria: Optional[str] = None
    partidos: List[Tuple[Pareja, Pareja]] = field(default_factory=list)
    score_compatibilidad: float = 0.0
    
    def agregar_pareja(self, pareja: Pareja):
        """Agrega una pareja al grupo."""
        if len(self.parejas) < 3:
            self.parejas.append(pareja)
            pareja.grupo_asignado = self.id
    
    def esta_completo(self) -> bool:
        """Verifica si el grupo tiene 3 parejas."""
        return len(self.parejas) == 3
    
    def generar_partidos(self):
        """Genera los 3 partidos del grupo (todos contra todos)."""
        if self.esta_completo():
            self.partidos = [
                (self.parejas[0], self.parejas[1]),
                (self.parejas[0], self.parejas[2]),
                (self.parejas[1], self.parejas[2])
            ]


@dataclass
class ResultadoAlgoritmo:
    """Resultado del algoritmo de formación de grupos."""
    grupos_por_categoria: Dict[str, List[Grupo]]
    parejas_sin_asignar: List[Pareja]
    calendario: Dict[str, List[Dict]]
    estadisticas: Dict


class AlgoritmoGrupos:
    """
    Algoritmo para formar grupos de 3 parejas con máxima compatibilidad horaria.
    """
    
    def __init__(self, parejas: List[Pareja], num_canchas: int = 2):
        self.parejas = parejas
        self.num_canchas = num_canchas
        self.grupos: List[Grupo] = []
        self.parejas_sin_asignar: List[Pareja] = []
        self.contador_grupos = 0
    
    def ejecutar(self) -> ResultadoAlgoritmo:
        """
        Ejecuta el algoritmo completo de formación de grupos.
        
        Returns:
            ResultadoAlgoritmo con grupos formados y estadísticas
        """
        # 1. Separar parejas por categoría
        parejas_por_categoria = self._separar_por_categoria()
        
        # 2. Formar grupos por cada categoría
        grupos_por_categoria = {}
        parejas_sin_asignar_total = []
        
        for categoria, parejas_cat in parejas_por_categoria.items():
            grupos, sin_asignar = self._formar_grupos_categoria(parejas_cat, categoria)
            grupos_por_categoria[categoria] = grupos
            parejas_sin_asignar_total.extend(sin_asignar)
        
        # 3. Generar calendario con asignación de canchas
        calendario = self._generar_calendario(grupos_por_categoria)
        
        # 4. Calcular estadísticas
        estadisticas = self._calcular_estadisticas(grupos_por_categoria, parejas_sin_asignar_total)
        
        return ResultadoAlgoritmo(
            grupos_por_categoria=grupos_por_categoria,
            parejas_sin_asignar=parejas_sin_asignar_total,
            calendario=calendario,
            estadisticas=estadisticas
        )
    
    def _separar_por_categoria(self) -> Dict[str, List[Pareja]]:
        """Separa las parejas por categoría."""
        parejas_por_cat = defaultdict(list)
        for pareja in self.parejas:
            if pareja.categoria in CATEGORIAS:
                parejas_por_cat[pareja.categoria].append(pareja)
        return dict(parejas_por_cat)
    
    def _formar_grupos_categoria(self, parejas: List[Pareja], categoria: str) -> Tuple[List[Grupo], List[Pareja]]:
        """
        Forma grupos de 3 parejas para una categoría específica.
        
        Estrategia:
        1. Encuentra todas las combinaciones posibles de 3 parejas
        2. Calcula score de compatibilidad horaria para cada combinación
        3. Selecciona grupos de forma greedy (mejor score primero)
        4. Evita reutilizar parejas ya asignadas
        
        Returns:
            Tupla de (grupos_formados, parejas_sin_asignar)
        """
        if len(parejas) < 3:
            return [], list(parejas)
        
        grupos_formados = []
        parejas_disponibles = set(parejas)
        
        # Generar todas las combinaciones posibles de 3 parejas
        while len(parejas_disponibles) >= 3:
            mejor_grupo = None
            mejor_score = -1
            mejor_franja = None
            
            # Evaluar todas las combinaciones de 3 parejas disponibles
            for combo in itertools.combinations(parejas_disponibles, 3):
                score, franja = self._calcular_compatibilidad(list(combo))
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_grupo = combo
                    mejor_franja = franja
            
            # Si encontramos un grupo con compatibilidad aceptable
            if mejor_grupo and mejor_score > 0:
                grupo = self._crear_grupo(list(mejor_grupo), categoria, mejor_franja, mejor_score)
                grupos_formados.append(grupo)
                
                # Remover parejas asignadas
                for pareja in mejor_grupo:
                    parejas_disponibles.remove(pareja)
            else:
                # No hay más grupos compatibles
                break
        
        # Las parejas restantes no pudieron ser asignadas
        parejas_sin_asignar = list(parejas_disponibles)
        
        return grupos_formados, parejas_sin_asignar
    
    def _calcular_compatibilidad(self, parejas: List[Pareja]) -> Tuple[float, Optional[str]]:
        """
        Calcula el score de compatibilidad horaria entre 3 parejas.
        
        Score:
        - 3.0: Las 3 parejas comparten al menos 1 franja horaria (ÓPTIMO)
        - 2.0: 2 de las 3 parejas comparten franja
        - 0.0: No hay compatibilidad
        
        Returns:
            Tupla de (score, franja_horaria_compartida)
        """
        if len(parejas) != 3:
            return 0.0, None
        
        # Encontrar franjas compartidas por las 3 parejas
        franjas_p1 = set(parejas[0].franjas_disponibles)
        franjas_p2 = set(parejas[1].franjas_disponibles)
        franjas_p3 = set(parejas[2].franjas_disponibles)
        
        # Intersección de las 3
        franjas_comunes_todas = franjas_p1 & franjas_p2 & franjas_p3
        
        if franjas_comunes_todas:
            # Perfecto: las 3 parejas pueden jugar juntas
            return 3.0, list(franjas_comunes_todas)[0]
        
        # Buscar al menos 2 parejas con franja común
        franjas_p1_p2 = franjas_p1 & franjas_p2
        franjas_p1_p3 = franjas_p1 & franjas_p3
        franjas_p2_p3 = franjas_p2 & franjas_p3
        
        if franjas_p1_p2:
            return 2.0, list(franjas_p1_p2)[0]
        if franjas_p1_p3:
            return 2.0, list(franjas_p1_p3)[0]
        if franjas_p2_p3:
            return 2.0, list(franjas_p2_p3)[0]
        
        # No hay compatibilidad
        return 0.0, None
    
    def _crear_grupo(self, parejas: List[Pareja], categoria: str, 
                     franja: Optional[str], score: float) -> Grupo:
        """Crea un nuevo grupo con las parejas dadas."""
        self.contador_grupos += 1
        grupo = Grupo(
            id=self.contador_grupos,
            categoria=categoria,
            franja_horaria=franja,
            score_compatibilidad=score
        )
        
        for pareja in parejas:
            grupo.agregar_pareja(pareja)
        
        grupo.generar_partidos()
        return grupo
    
    def _generar_calendario(self, grupos_por_categoria: Dict[str, List[Grupo]]) -> Dict[str, List[Dict]]:
        """
        Genera el calendario de partidos optimizando el uso de 2 canchas.
        
        Agrupa por franja horaria y asigna canchas.
        """
        calendario = defaultdict(list)
        
        # Agrupar todos los grupos por franja horaria
        grupos_por_franja = defaultdict(list)
        
        for categoria, grupos in grupos_por_categoria.items():
            for grupo in grupos:
                if grupo.franja_horaria:
                    grupos_por_franja[grupo.franja_horaria].append(grupo)
        
        # Crear calendario por franja horaria
        for franja, grupos in grupos_por_franja.items():
            # Asignar canchas (máximo 2 grupos simultáneos)
            for i, grupo in enumerate(grupos):
                cancha = (i % self.num_canchas) + 1
                
                for idx_partido, (pareja1, pareja2) in enumerate(grupo.partidos):
                    calendario[franja].append({
                        "franja": franja,
                        "categoria": grupo.categoria,
                        "color": COLORES_CATEGORIA.get(grupo.categoria, "⚪"),
                        "grupo_id": grupo.id,
                        "cancha": cancha,
                        "partido_num": idx_partido + 1,
                        "pareja1": pareja1.nombre,
                        "pareja2": pareja2.nombre,
                        "score_compatibilidad": grupo.score_compatibilidad
                    })
        
        return dict(calendario)
    
    def _calcular_estadisticas(self, grupos_por_categoria: Dict[str, List[Grupo]], 
                               parejas_sin_asignar: List[Pareja]) -> Dict:
        """Calcula estadísticas del resultado del algoritmo."""
        total_parejas = len(self.parejas)
        total_asignadas = total_parejas - len(parejas_sin_asignar)
        total_grupos = sum(len(grupos) for grupos in grupos_por_categoria.values())
        
        grupos_por_cat = {cat: len(grupos) for cat, grupos in grupos_por_categoria.items()}
        parejas_por_cat = defaultdict(int)
        
        for grupo_list in grupos_por_categoria.values():
            for grupo in grupo_list:
                parejas_por_cat[grupo.categoria] += len(grupo.parejas)
        
        # Calcular compatibilidad promedio
        todos_scores = []
        for grupos in grupos_por_categoria.values():
            for grupo in grupos:
                todos_scores.append(grupo.score_compatibilidad)
        
        score_promedio = sum(todos_scores) / len(todos_scores) if todos_scores else 0
        
        return {
            "total_parejas": total_parejas,
            "parejas_asignadas": total_asignadas,
            "parejas_sin_asignar": len(parejas_sin_asignar),
            "porcentaje_asignacion": (total_asignadas / total_parejas * 100) if total_parejas > 0 else 0,
            "total_grupos": total_grupos,
            "grupos_por_categoria": dict(grupos_por_cat),
            "parejas_por_categoria": dict(parejas_por_cat),
            "score_compatibilidad_promedio": score_promedio,
            "grupos_compatibilidad_perfecta": sum(1 for s in todos_scores if s >= 3.0),
            "grupos_compatibilidad_parcial": sum(1 for s in todos_scores if 2.0 <= s < 3.0)
        }


def crear_pareja_desde_dict(data: Dict, id: int) -> Pareja:
    """
    Crea una instancia de Pareja desde un diccionario de datos.
    
    Args:
        data: Diccionario con los datos de la pareja del formulario
        id: ID único para la pareja
    
    Returns:
        Instancia de Pareja
    """
    return Pareja(
        id=id,
        nombre=data.get("nombre", f"Pareja {id}"),
        telefono=data.get("telefono", ""),
        categoria=data.get("categoria", ""),
        franjas_disponibles=data.get("franjas_horarias", [])
    )
