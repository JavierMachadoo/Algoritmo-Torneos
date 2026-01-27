"""
Cancha Validator - Validación de disponibilidad de canchas y solapamientos horarios.
Following refactor:flask early return pattern for validation.
"""
from typing import Dict, List, Optional, Tuple
import logging

from config import FRANJAS_HORARIAS, FRANJAS_MAPPING

logger = logging.getLogger(__name__)


class CanchaValidator:
    """
    Validador para disponibilidad de canchas y detección de solapamientos horarios.
    
    Elimina código duplicado que aparece 3+ veces en parejas.py.
    Implementa patrón de validación temprana (early returns) de refactor:flask.
    """
    
    @staticmethod
    def check_availability(
        grupos_dict: Dict[str, List[Dict]], 
        franja_horaria: str, 
        cancha: str,
        exclude_grupo_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si una cancha está disponible en una franja horaria específica.
        
        Early return pattern: Retorna inmediatamente al detectar conflicto.
        
        Args:
            grupos_dict: Diccionario de grupos por categoría
            franja_horaria: Franja horaria a verificar (ej: "Jueves 18:00")
            cancha: Número de cancha como string
            exclude_grupo_id: ID de grupo a excluir de la validación (para ediciones)
            
        Returns:
            Tuple (is_available, error_message)
            - (True, None) si está disponible
            - (False, "mensaje de error") si está ocupada
            
        Examples:
            >>> is_available, error = CanchaValidator.check_availability(
            ...     grupos_dict, "Jueves 18:00", "1"
            ... )
            >>> if not is_available:
            ...     return jsonify({'error': error}), 400
        """
        # Early return: Validar que la franja horaria sea válida
        if franja_horaria not in FRANJAS_HORARIAS:
            return False, f'Franja horaria inválida: {franja_horaria}'
        
        # Verificar ocupación directa
        for categoria, grupos in grupos_dict.items():
            for grupo in grupos:
                # Skip excluded group (para ediciones)
                if exclude_grupo_id and grupo.get('id') == exclude_grupo_id:
                    continue
                
                # Early return: Cancha ocupada en esa franja exacta
                if (grupo.get('franja_horaria') == franja_horaria and 
                    str(grupo.get('cancha')) == str(cancha)):
                    error_msg = (
                        f'La Cancha {cancha} ya está ocupada en {franja_horaria} '
                        f'por un grupo de {categoria}'
                    )
                    logger.warning(error_msg)
                    return False, error_msg
        
        # Cancha disponible
        return True, None
    
    @staticmethod
    def check_overlap(
        grupos_dict: Dict[str, List[Dict]], 
        franja_horaria: str, 
        cancha: str,
        exclude_grupo_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si hay solapamiento horario en una cancha.
        
        Detecta conflictos cuando dos franjas comparten horas (ej: Jueves 18:00 y 20:00
        comparten las 20:00).
        
        Early return pattern: Retorna al primer solapamiento detectado.
        
        Args:
            grupos_dict: Diccionario de grupos por categoría
            franja_horaria: Franja horaria a verificar
            cancha: Número de cancha como string
            exclude_grupo_id: ID de grupo a excluir de la validación
            
        Returns:
            Tuple (no_overlap, error_message)
            - (True, None) si no hay solapamiento
            - (False, "mensaje detallado") si hay conflicto
            
        Examples:
            >>> no_overlap, error = CanchaValidator.check_overlap(
            ...     grupos_dict, "Jueves 20:00", "1"
            ... )
            >>> if not no_overlap:
            ...     return jsonify({'error': error}), 400
        """
        # Early return: Franja no reconocida
        if franja_horaria not in FRANJAS_MAPPING:
            return False, f'Franja horaria no reconocida: {franja_horaria}'
        
        # Obtener horas que ocupa la nueva franja
        horas_nueva_franja = FRANJAS_MAPPING[franja_horaria]
        
        # Verificar solapamientos con grupos existentes
        for categoria, grupos in grupos_dict.items():
            for grupo in grupos:
                # Skip excluded group
                if exclude_grupo_id and grupo.get('id') == exclude_grupo_id:
                    continue
                
                # Solo verificar grupos en la misma cancha
                if str(grupo.get('cancha')) != str(cancha):
                    continue
                
                franja_existente = grupo.get('franja_horaria')
                if not franja_existente or franja_existente not in FRANJAS_MAPPING:
                    continue
                
                # Calcular intersección de horas
                horas_existente = FRANJAS_MAPPING[franja_existente]
                horas_conflicto = set(horas_nueva_franja) & set(horas_existente)
                
                # Early return: Hay solapamiento
                if horas_conflicto:
                    error_msg = (
                        f'Conflicto: La Cancha {cancha} tiene un solapamiento horario '
                        f'con {franja_existente} (grupo de {categoria}) '
                        f'en las horas: {", ".join(sorted(horas_conflicto))}'
                    )
                    logger.warning(error_msg)
                    return False, error_msg
        
        # No hay solapamiento
        return True, None
    
    @staticmethod
    def validate_franja_cancha(
        grupos_dict: Dict[str, List[Dict]], 
        franja_horaria: str, 
        cancha: str,
        exclude_grupo_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validación completa: disponibilidad + solapamiento.
        
        Combina check_availability() y check_overlap() en una sola llamada.
        Usa early returns para máxima eficiencia.
        
        Args:
            grupos_dict: Diccionario de grupos por categoría
            franja_horaria: Franja horaria a validar
            cancha: Número de cancha como string
            exclude_grupo_id: ID de grupo a excluir (para ediciones)
            
        Returns:
            Tuple (is_valid, error_message)
            - (True, None) si la combinación es válida
            - (False, "mensaje de error") si hay algún problema
            
        Examples:
            >>> # Uso en rutas - patrón completo
            >>> is_valid, error = CanchaValidator.validate_franja_cancha(
            ...     grupos_dict, franja_horaria, cancha
            ... )
            >>> if not is_valid:
            ...     return jsonify({'error': error}), 400
            >>> 
            >>> # Continuar con lógica de negocio...
        """
        # Early return: Parámetros básicos inválidos
        if not franja_horaria or not cancha:
            return False, 'Franja horaria y cancha son requeridos'
        
        # Early return: Verificar disponibilidad directa
        is_available, error_msg = CanchaValidator.check_availability(
            grupos_dict, franja_horaria, cancha, exclude_grupo_id
        )
        if not is_available:
            return False, error_msg
        
        # Early return: Verificar solapamientos
        no_overlap, error_msg = CanchaValidator.check_overlap(
            grupos_dict, franja_horaria, cancha, exclude_grupo_id
        )
        if not no_overlap:
            return False, error_msg
        
        # Validación exitosa
        logger.debug(
            f'Cancha {cancha} disponible para {franja_horaria} '
            f'(exclude_grupo_id={exclude_grupo_id})'
        )
        return True, None
    
    @staticmethod
    def get_disponibilidad_canchas(
        grupos_dict: Dict[str, List[Dict]], 
        num_canchas: int
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Obtiene disponibilidad completa de todas las canchas en todas las franjas.
        
        Genera un mapa de disponibilidad útil para UI y validaciones.
        
        Args:
            grupos_dict: Diccionario de grupos por categoría
            num_canchas: Número total de canchas disponibles
            
        Returns:
            Dict con estructura:
            {
                'Jueves 18:00': {
                    '1': {'disponible': True, 'ocupada_por': None, 'solapamiento': None},
                    '2': {'disponible': False, 'ocupada_por': 'Cuarta', 'solapamiento': {...}}
                },
                ...
            }
            
        Examples:
            >>> disponibilidad = CanchaValidator.get_disponibilidad_canchas(
            ...     grupos_dict, num_canchas=2
            ... )
            >>> if not disponibilidad['Jueves 18:00']['1']['disponible']:
            ...     print("Cancha 1 no disponible en Jueves 18:00")
        """
        # Construir mapa de franjas ocupadas por cancha
        franjas_ocupadas = {}
        for categoria, grupos in grupos_dict.items():
            for grupo in grupos:
                franja = grupo.get('franja_horaria')
                cancha = str(grupo.get('cancha'))
                
                if franja and cancha:
                    if franja not in franjas_ocupadas:
                        franjas_ocupadas[franja] = {}
                    franjas_ocupadas[franja][cancha] = categoria
        
        # Construir disponibilidad por franja y cancha
        disponibilidad = {}
        for franja in FRANJAS_HORARIAS:
            disponibilidad[franja] = {}
            
            for cancha_num in range(1, num_canchas + 1):
                cancha_str = str(cancha_num)
                
                # Verificar ocupación directa
                ocupada_directa = (
                    franja in franjas_ocupadas and 
                    cancha_str in franjas_ocupadas[franja]
                )
                categoria_ocupante = franjas_ocupadas.get(franja, {}).get(cancha_str)
                
                # Verificar solapamientos
                solapamiento = None
                if franja in FRANJAS_MAPPING:
                    horas_franja = FRANJAS_MAPPING[franja]
                    
                    for otra_franja, cat_por_cancha in franjas_ocupadas.items():
                        # Skip misma franja y canchas diferentes
                        if otra_franja == franja or cancha_str not in cat_por_cancha:
                            continue
                        
                        if otra_franja in FRANJAS_MAPPING:
                            horas_otra = FRANJAS_MAPPING[otra_franja]
                            horas_comunes = set(horas_franja) & set(horas_otra)
                            
                            if horas_comunes:
                                solapamiento = {
                                    'franja': otra_franja,
                                    'categoria': cat_por_cancha[cancha_str],
                                    'horas_conflicto': sorted(list(horas_comunes))
                                }
                                break
                
                disponibilidad[franja][cancha_str] = {
                    'disponible': not ocupada_directa,
                    'ocupada_por': categoria_ocupante,
                    'solapamiento': solapamiento
                }
        
        return disponibilidad
    
    @staticmethod
    def validate_franja_exists(franja_horaria: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que una franja horaria sea válida.
        
        Early return pattern para validación simple.
        
        Args:
            franja_horaria: Franja a validar
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not franja_horaria:
            return False, 'Franja horaria es requerida'
        
        if franja_horaria not in FRANJAS_HORARIAS:
            return False, (
                f'Franja horaria inválida: {franja_horaria}. '
                f'Franjas válidas: {", ".join(FRANJAS_HORARIAS)}'
            )
        
        return True, None
