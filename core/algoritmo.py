from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import itertools

from core.models import Pareja, Grupo, ResultadoAlgoritmo
from config import CATEGORIAS, EMOJI_CATEGORIA


class AlgoritmoGrupos:
    def __init__(self, parejas: List[Pareja], num_canchas: int = 2):
        self.parejas = parejas
        self.num_canchas = num_canchas
        self.contador_grupos = 0
    
    def ejecutar(self) -> ResultadoAlgoritmo:
        parejas_por_categoria = self._separar_por_categoria()
        grupos_por_categoria = {}
        parejas_sin_asignar_total = []
        
        for categoria, parejas_cat in parejas_por_categoria.items():
            grupos, sin_asignar = self._formar_grupos_categoria(parejas_cat, categoria)
            grupos_por_categoria[categoria] = grupos
            parejas_sin_asignar_total.extend(sin_asignar)
        
        calendario = self._generar_calendario(grupos_por_categoria)
        estadisticas = self._calcular_estadisticas(grupos_por_categoria, parejas_sin_asignar_total)
        
        return ResultadoAlgoritmo(
            grupos_por_categoria=grupos_por_categoria,
            parejas_sin_asignar=parejas_sin_asignar_total,
            calendario=calendario,
            estadisticas=estadisticas
        )
    
    def _separar_por_categoria(self) -> Dict[str, List[Pareja]]:
        parejas_por_cat = defaultdict(list)
        for pareja in self.parejas:
            if pareja.categoria in CATEGORIAS:
                parejas_por_cat[pareja.categoria].append(pareja)
        return dict(parejas_por_cat)
    
    def _formar_grupos_categoria(self, parejas: List[Pareja], categoria: str) -> Tuple[List[Grupo], List[Pareja]]:
        if len(parejas) < 3:
            return [], list(parejas)
        
        grupos_formados = []
        parejas_disponibles = set(parejas)
        
        while len(parejas_disponibles) >= 3:
            mejor_grupo = None
            mejor_score = -1
            mejor_franja = None
            
            for combo in itertools.combinations(parejas_disponibles, 3):
                score, franja = self._calcular_compatibilidad(list(combo))
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_grupo = combo
                    mejor_franja = franja
            
            if mejor_grupo and mejor_score > 0:
                grupo = self._crear_grupo(list(mejor_grupo), categoria, mejor_franja, mejor_score)
                grupos_formados.append(grupo)
                
                for pareja in mejor_grupo:
                    parejas_disponibles.remove(pareja)
            else:
                break
        
        parejas_sin_asignar = list(parejas_disponibles)
        return grupos_formados, parejas_sin_asignar
    
    def _calcular_compatibilidad(self, parejas: List[Pareja]) -> Tuple[float, Optional[str]]:
        if len(parejas) != 3:
            return 0.0, None
        
        franjas_p1 = set(parejas[0].franjas_disponibles)
        franjas_p2 = set(parejas[1].franjas_disponibles)
        franjas_p3 = set(parejas[2].franjas_disponibles)
        
        franjas_comunes_todas = franjas_p1 & franjas_p2 & franjas_p3
        
        if franjas_comunes_todas:
            return 3.0, list(franjas_comunes_todas)[0]
        
        franjas_p1_p2 = franjas_p1 & franjas_p2
        franjas_p1_p3 = franjas_p1 & franjas_p3
        franjas_p2_p3 = franjas_p2 & franjas_p3
        
        if franjas_p1_p2:
            return 2.0, list(franjas_p1_p2)[0]
        if franjas_p1_p3:
            return 2.0, list(franjas_p1_p3)[0]
        if franjas_p2_p3:
            return 2.0, list(franjas_p2_p3)[0]
        
        return 0.0, None
    
    def _crear_grupo(self, parejas: List[Pareja], categoria: str, 
                     franja: Optional[str], score: float) -> Grupo:
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
        calendario = defaultdict(list)
        grupos_por_franja = defaultdict(list)
        
        for categoria, grupos in grupos_por_categoria.items():
            for grupo in grupos:
                if grupo.franja_horaria:
                    grupos_por_franja[grupo.franja_horaria].append(grupo)
        
        for franja, grupos in grupos_por_franja.items():
            for i, grupo in enumerate(grupos):
                cancha = (i % self.num_canchas) + 1
                
                for idx_partido, (pareja1, pareja2) in enumerate(grupo.partidos):
                    calendario[franja].append({
                        "franja": franja,
                        "categoria": grupo.categoria,
                        "color": EMOJI_CATEGORIA.get(grupo.categoria, "⚪"),
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
        total_parejas = len(self.parejas)
        total_asignadas = total_parejas - len(parejas_sin_asignar)
        total_grupos = sum(len(grupos) for grupos in grupos_por_categoria.values())
        
        grupos_por_cat = {cat: len(grupos) for cat, grupos in grupos_por_categoria.items()}
        parejas_por_cat = defaultdict(int)
        
        for grupo_list in grupos_por_categoria.values():
            for grupo in grupo_list:
                parejas_por_cat[grupo.categoria] += len(grupo.parejas)
        
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
