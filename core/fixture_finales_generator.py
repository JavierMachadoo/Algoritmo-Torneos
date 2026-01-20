"""
Módulo para generar el fixture de finales basado en las posiciones de grupo.
"""

from typing import List, Dict, Optional
from core.models import Grupo, FixtureFinales, PartidoFinal, FaseFinal, PosicionGrupo
import logging

logger = logging.getLogger(__name__)


class GeneradorFixtureFinales:
    """Genera el fixture de finales para una categoría basándose en las posiciones de los grupos"""
    
    @staticmethod
    def contar_grupos_completos(grupos: List[Grupo]) -> int:
        """Cuenta cuántos grupos tienen todos sus resultados completos"""
        return sum(1 for grupo in grupos if grupo.todos_resultados_completos())
    
    @staticmethod
    def obtener_clasificados_por_posicion(grupos: List[Grupo]) -> Dict[int, List]:
        """
        Obtiene las parejas clasificadas agrupadas por posición.
        Retorna: {1: [primeros], 2: [segundos], 3: [terceros]}
        Solo incluye parejas de grupos con resultados completos.
        """
        from core.clasificacion import CalculadorClasificacion
        
        clasificados = {1: [], 2: [], 3: []}
        
        for grupo in grupos:
            if not grupo.todos_resultados_completos():
                continue
            
            # Calcular posiciones del grupo
            posiciones = CalculadorClasificacion.asignar_posiciones(grupo)
            
            # Agrupar parejas por posición
            for pareja in grupo.parejas:
                if pareja.id in posiciones:
                    posicion = posiciones[pareja.id].value
                    pareja.posicion_grupo = posiciones[pareja.id]
                    clasificados[posicion].append({
                        'pareja': pareja,
                        'grupo_id': grupo.id
                    })
        
        return clasificados
    
    @staticmethod
    def generar_fixture(categoria: str, grupos: List[Grupo]) -> Optional[FixtureFinales]:
        """
        Genera el fixture de finales para una categoría.
        
        IMPORTANTE: Genera SIEMPRE la estructura de llaves, incluso si no hay clasificados.
        Las llaves se llenan automáticamente cuando se completan los grupos.
        
        Lógica de generación basada en número de grupos:
        - 8+ grupos: Octavos (8 partidos) → Cuartos (4) → Semis (2) → Final (1)
        - 4-7 grupos: Cuartos (4 partidos) → Semis (2) → Final (1)
        - 2-3 grupos: Semis (2 partidos) → Final (1)
        
        Criterio de enfrentamientos:
        - Se enfrentan parejas de diferentes grupos
        - Prioridad: 1° vs 2°, luego pueden entrar los 3° si es necesario
        """
        if not grupos:
            logger.warning(f"No hay grupos para la categoría {categoria}")
            # Retornar estructura vacía con semifinales por defecto
            return GeneradorFixtureFinales._generar_solo_semifinales(categoria, {1: [], 2: [], 3: []})
        
        grupos_categoria = [g for g in grupos if g.categoria == categoria]
        num_grupos = len(grupos_categoria)
        grupos_completos = GeneradorFixtureFinales.contar_grupos_completos(grupos_categoria)
        
        logger.info(f"Generando fixture para {categoria}: {num_grupos} grupos, {grupos_completos} completos")
        
        # Obtener clasificados por posición (puede estar vacío)
        clasificados = GeneradorFixtureFinales.obtener_clasificados_por_posicion(grupos_categoria)
        
        fixture = FixtureFinales(categoria=categoria)
        
        # Generar fixture según número de grupos (SIEMPRE se genera la estructura)
        if num_grupos >= 8:
            fixture = GeneradorFixtureFinales._generar_con_octavos(categoria, clasificados)
        elif num_grupos >= 4:
            fixture = GeneradorFixtureFinales._generar_con_cuartos(categoria, clasificados)
        else:
            fixture = GeneradorFixtureFinales._generar_solo_semifinales(categoria, clasificados)
        
        return fixture
    
    @staticmethod
    def _generar_con_octavos(categoria: str, clasificados: Dict) -> FixtureFinales:
        """Genera fixture con octavos (8 grupos)"""
        fixture = FixtureFinales(categoria=categoria)
        
        primeros = clasificados[1]
        segundos = clasificados[2]
        
        # Crear 8 partidos de octavos
        for i in range(8):
            partido_id = f"{categoria}_octavos_{i+1}"
            partido = PartidoFinal(
                id=partido_id,
                fase=FaseFinal.OCTAVOS,
                numero_partido=i+1
            )
            
            # Asignar parejas si están disponibles
            if i < len(primeros):
                partido.pareja1 = primeros[i]['pareja']
            if i < len(segundos):
                partido.pareja2 = segundos[i]['pareja']
            
            fixture.octavos.append(partido)
        
        # Crear estructura de cuartos (vacíos por ahora)
        for i in range(4):
            partido_id = f"{categoria}_cuartos_{i+1}"
            fixture.cuartos.append(PartidoFinal(
                id=partido_id,
                fase=FaseFinal.CUARTOS,
                numero_partido=i+1
            ))
        
        # Crear estructura de semifinales
        for i in range(2):
            partido_id = f"{categoria}_semi_{i+1}"
            fixture.semifinales.append(PartidoFinal(
                id=partido_id,
                fase=FaseFinal.SEMIFINAL,
                numero_partido=i+1
            ))
        
        # Crear final
        fixture.final = PartidoFinal(
            id=f"{categoria}_final",
            fase=FaseFinal.FINAL,
            numero_partido=1
        )
        
        return fixture
    
    @staticmethod
    def _generar_con_cuartos(categoria: str, clasificados: Dict) -> FixtureFinales:
        """Genera fixture con cuartos (4 grupos)"""
        fixture = FixtureFinales(categoria=categoria)
        
        primeros = clasificados[1]
        segundos = clasificados[2]
        
        # Crear 4 partidos de cuartos
        for i in range(4):
            partido_id = f"{categoria}_cuartos_{i+1}"
            partido = PartidoFinal(
                id=partido_id,
                fase=FaseFinal.CUARTOS,
                numero_partido=i+1
            )
            
            # Asignar parejas si están disponibles
            if i < len(primeros):
                partido.pareja1 = primeros[i]['pareja']
            if i < len(segundos):
                partido.pareja2 = segundos[i]['pareja']
            
            fixture.cuartos.append(partido)
        
        # Crear estructura de semifinales
        for i in range(2):
            partido_id = f"{categoria}_semi_{i+1}"
            fixture.semifinales.append(PartidoFinal(
                id=partido_id,
                fase=FaseFinal.SEMIFINAL,
                numero_partido=i+1
            ))
        
        # Crear final
        fixture.final = PartidoFinal(
            id=f"{categoria}_final",
            fase=FaseFinal.FINAL,
            numero_partido=1
        )
        
        return fixture
    
    @staticmethod
    def _generar_solo_semifinales(categoria: str, clasificados: Dict) -> FixtureFinales:
        """Genera fixture solo con semifinales (2-3 grupos)"""
        fixture = FixtureFinales(categoria=categoria)
        
        primeros = clasificados[1]
        segundos = clasificados[2]
        
        # Crear 2 semifinales
        for i in range(2):
            partido_id = f"{categoria}_semi_{i+1}"
            partido = PartidoFinal(
                id=partido_id,
                fase=FaseFinal.SEMIFINAL,
                numero_partido=i+1
            )
            
            # Asignar parejas si están disponibles
            if i < len(primeros):
                partido.pareja1 = primeros[i]['pareja']
            if i < len(segundos):
                partido.pareja2 = segundos[i]['pareja']
            
            fixture.semifinales.append(partido)
        
        # Crear final
        fixture.final = PartidoFinal(
            id=f"{categoria}_final",
            fase=FaseFinal.FINAL,
            numero_partido=1
        )
        
        return fixture
    
    @staticmethod
    def actualizar_ganador_partido(fixture: FixtureFinales, partido_id: str, ganador_id: int):
        """
        Actualiza el ganador de un partido y propaga al siguiente nivel.
        """
        # Buscar el partido en todas las fases
        partido_encontrado = None
        fase_actual = None
        
        # Buscar en octavos
        for partido in fixture.octavos:
            if partido.id == partido_id:
                partido_encontrado = partido
                fase_actual = FaseFinal.OCTAVOS
                break
        
        # Buscar en cuartos
        if not partido_encontrado:
            for partido in fixture.cuartos:
                if partido.id == partido_id:
                    partido_encontrado = partido
                    fase_actual = FaseFinal.CUARTOS
                    break
        
        # Buscar en semifinales
        if not partido_encontrado:
            for partido in fixture.semifinales:
                if partido.id == partido_id:
                    partido_encontrado = partido
                    fase_actual = FaseFinal.SEMIFINAL
                    break
        
        # Buscar en final
        if not partido_encontrado and fixture.final and fixture.final.id == partido_id:
            partido_encontrado = fixture.final
            fase_actual = FaseFinal.FINAL
        
        if not partido_encontrado:
            logger.error(f"Partido {partido_id} no encontrado en el fixture")
            return False
        
        # Asignar ganador
        if partido_encontrado.pareja1 and partido_encontrado.pareja1.id == ganador_id:
            partido_encontrado.ganador = partido_encontrado.pareja1
        elif partido_encontrado.pareja2 and partido_encontrado.pareja2.id == ganador_id:
            partido_encontrado.ganador = partido_encontrado.pareja2
        else:
            logger.error(f"Ganador ID {ganador_id} no es parte del partido {partido_id}")
            return False
        
        # Propagar al siguiente nivel
        GeneradorFixtureFinales._propagar_ganador(fixture, partido_encontrado, fase_actual)
        
        return True
    
    @staticmethod
    def _propagar_ganador(fixture: FixtureFinales, partido: PartidoFinal, fase: FaseFinal):
        """Propaga el ganador de un partido al siguiente nivel"""
        if not partido.ganador:
            return
        
        num_partido = partido.numero_partido
        ganador = partido.ganador
        
        if fase == FaseFinal.OCTAVOS:
            # Octavos → Cuartos
            # Partidos 1 y 2 → Cuarto 1
            # Partidos 3 y 4 → Cuarto 2
            # Partidos 5 y 6 → Cuarto 3
            # Partidos 7 y 8 → Cuarto 4
            idx_cuarto = (num_partido - 1) // 2
            if idx_cuarto < len(fixture.cuartos):
                cuarto = fixture.cuartos[idx_cuarto]
                if num_partido % 2 == 1:
                    cuarto.pareja1 = ganador
                else:
                    cuarto.pareja2 = ganador
        
        elif fase == FaseFinal.CUARTOS:
            # Cuartos → Semifinales
            # Partidos 1 y 2 → Semi 1
            # Partidos 3 y 4 → Semi 2
            idx_semi = (num_partido - 1) // 2
            if idx_semi < len(fixture.semifinales):
                semi = fixture.semifinales[idx_semi]
                if num_partido % 2 == 1:
                    semi.pareja1 = ganador
                else:
                    semi.pareja2 = ganador
        
        elif fase == FaseFinal.SEMIFINAL:
            # Semifinales → Final
            if fixture.final:
                if num_partido == 1:
                    fixture.final.pareja1 = ganador
                else:
                    fixture.final.pareja2 = ganador
