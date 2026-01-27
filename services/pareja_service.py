"""
ParejaService - Business logic for pareja operations.
Following refactor:flask service layer patterns (lines 230-330).

Pure business logic with no Flask dependencies (no request, no jsonify).
All methods are static and raise custom exceptions for error cases.
"""
from typing import Dict, List, Any, Optional
from services.exceptions import (
    ParejaValidationError,
    ParejaNotFoundError,
    ResultadoAlgoritmoNotFoundError
)


class ParejaService:
    """Service layer for pareja-related business logic."""
    
    @staticmethod
    def add(
        datos_actuales: Dict[str, Any],
        nombre: str,
        telefono: str,
        categoria: str,
        franjas: List[str],
        desde_resultados: bool = False
    ) -> Dict[str, Any]:
        """
        Add a new pareja to the tournament.
        
        Args:
            datos_actuales: Current tournament data
            nombre: Pareja name
            telefono: Contact phone number
            categoria: Tournament category
            franjas: List of available time slots
            desde_resultados: Whether adding from results view (triggers stats recalc)
        
        Returns:
            Dict with the created pareja data
        
        Raises:
            ParejaValidationError: If validation fails (missing name or franjas)
        """
        # Validation
        if not nombre or not nombre.strip():
            raise ParejaValidationError('El nombre es obligatorio')
        
        if not franjas or len(franjas) == 0:
            raise ParejaValidationError('Debe seleccionar al menos una franja horaria')
        
        # Get parejas list
        parejas = datos_actuales.get('parejas', [])
        
        # Generate new ID
        max_id = max([p['id'] for p in parejas], default=0)
        nuevo_id = max_id + 1
        
        # Create pareja dict
        nueva_pareja = {
            'id': nuevo_id,
            'nombre': nombre.strip(),
            'telefono': telefono,
            'categoria': categoria,
            'franjas_disponibles': franjas
        }
        
        # Add to parejas list
        parejas.append(nueva_pareja)
        datos_actuales['parejas'] = parejas
        
        # If there's a resultado_algoritmo, add to parejas_sin_asignar
        resultado_data = datos_actuales.get('resultado_algoritmo')
        if resultado_data:
            # Add to parejas no asignadas
            parejas_sin_asignar = resultado_data.get('parejas_sin_asignar', [])
            parejas_sin_asignar.append(nueva_pareja)
            resultado_data['parejas_sin_asignar'] = parejas_sin_asignar
            
            # Only recalculate stats if adding from results view
            if desde_resultados:
                # Import here to avoid circular dependency
                from api.routes.parejas import recalcular_estadisticas
                resultado_data['estadisticas'] = recalcular_estadisticas(resultado_data)
            
            datos_actuales['resultado_algoritmo'] = resultado_data
        
        return nueva_pareja
    
    @staticmethod
    def delete(
        datos_actuales: Dict[str, Any],
        pareja_id: int
    ) -> Dict[str, Any]:
        """
        Delete a pareja from the tournament completely.
        
        Args:
            datos_actuales: Current tournament data
            pareja_id: ID of the pareja to delete
        
        Returns:
            Dict with success status and statistics if applicable
        
        Raises:
            ParejaValidationError: If pareja_id is not provided
        """
        if pareja_id is None:
            raise ParejaValidationError('El ID de la pareja es obligatorio')
        
        # Import helpers here to avoid circular dependency
        from api.routes.parejas import (
            recalcular_score_grupo,
            regenerar_calendario,
            recalcular_estadisticas
        )
        
        # 1. Delete from base parejas list
        parejas = datos_actuales.get('parejas', [])
        parejas = [p for p in parejas if p['id'] != pareja_id]
        datos_actuales['parejas'] = parejas
        
        # 2. If resultado_algoritmo exists, delete from grupos and no asignadas
        resultado_data = datos_actuales.get('resultado_algoritmo')
        if resultado_data:
            # Delete from grupos
            grupos_dict = resultado_data['grupos_por_categoria']
            for cat, grupos in grupos_dict.items():
                for grupo in grupos:
                    parejas_grupo = grupo.get('parejas', [])
                    grupo['parejas'] = [p for p in parejas_grupo if p.get('id') != pareja_id]
                    # Recalculate score if deleted from group
                    if len(grupo['parejas']) != len(parejas_grupo):
                        recalcular_score_grupo(grupo)
            
            # Delete from no asignadas
            parejas_sin_asignar = resultado_data.get('parejas_sin_asignar', [])
            resultado_data['parejas_sin_asignar'] = [
                p for p in parejas_sin_asignar if p.get('id') != pareja_id
            ]
            
            # Regenerate calendar and statistics
            regenerar_calendario(resultado_data)
            resultado_data['estadisticas'] = recalcular_estadisticas(resultado_data)
            datos_actuales['resultado_algoritmo'] = resultado_data
        
        return {
            'success': True,
            'mensaje': 'Pareja eliminada correctamente'
        }
    
    @staticmethod
    def update(
        datos_actuales: Dict[str, Any],
        pareja_id: int,
        nombre: str,
        telefono: str,
        categoria: str,
        franjas: List[str]
    ) -> Dict[str, Any]:
        """
        Update an existing pareja.
        
        Args:
            datos_actuales: Current tournament data
            pareja_id: ID of the pareja to update
            nombre: New name
            telefono: New phone number
            categoria: New category
            franjas: New available time slots
        
        Returns:
            Dict with success status and update message
        
        Raises:
            ParejaValidationError: If validation fails
            ResultadoAlgoritmoNotFoundError: If resultado_algoritmo is not available
            ParejaNotFoundError: If pareja is not found in grupos or parejas_sin_asignar
        """
        # Validation
        if not nombre or not nombre.strip():
            raise ParejaValidationError('El nombre es obligatorio')
        
        if not franjas or len(franjas) == 0:
            raise ParejaValidationError('Debe seleccionar al menos una franja horaria')
        
        # Import helpers here to avoid circular dependency
        from api.routes.parejas import (
            recalcular_score_grupo,
            regenerar_calendario
        )
        
        resultado_data = datos_actuales.get('resultado_algoritmo')
        if not resultado_data:
            raise ResultadoAlgoritmoNotFoundError('No hay resultados del algoritmo')
        
        grupos_dict = resultado_data['grupos_por_categoria']
        parejas_sin_asignar = resultado_data.get('parejas_sin_asignar', [])
        
        # Find pareja in grupos or parejas_sin_asignar
        pareja_encontrada = None
        grupo_contenedor = None
        categoria_original = None
        
        # Search in grupos
        for cat, grupos in grupos_dict.items():
            for grupo in grupos:
                for pareja in grupo.get('parejas', []):
                    if pareja.get('id') == pareja_id:
                        pareja_encontrada = pareja
                        grupo_contenedor = grupo
                        categoria_original = cat
                        break
                if pareja_encontrada:
                    break
            if pareja_encontrada:
                break
        
        # Search in no asignadas if not found
        if not pareja_encontrada:
            for pareja in parejas_sin_asignar:
                if pareja.get('id') == pareja_id:
                    pareja_encontrada = pareja
                    categoria_original = pareja.get('categoria')
                    break
        
        if not pareja_encontrada:
            raise ParejaNotFoundError('Pareja no encontrada')
        
        # Check if category changed
        cambio_categoria = categoria_original != categoria
        
        # If category changed, move to parejas_sin_asignar
        if cambio_categoria and grupo_contenedor:
            grupo_contenedor['parejas'] = [
                p for p in grupo_contenedor.get('parejas', [])
                if p.get('id') != pareja_id
            ]
            pareja_encontrada['posicion_grupo'] = None
            parejas_sin_asignar.append(pareja_encontrada)
            recalcular_score_grupo(grupo_contenedor)
            grupo_contenedor = None
        
        # Update pareja data
        pareja_encontrada['nombre'] = nombre.strip()
        pareja_encontrada['telefono'] = telefono
        pareja_encontrada['categoria'] = categoria
        pareja_encontrada['franjas_disponibles'] = franjas
        
        # Update in base parejas list
        parejas_base = datos_actuales.get('parejas', [])
        pareja_actualizada_en_base = False
        
        for pareja_base in parejas_base:
            if pareja_base['id'] == pareja_id:
                pareja_base['nombre'] = nombre
                pareja_base['telefono'] = telefono
                pareja_base['categoria'] = categoria
                pareja_base['franjas_disponibles'] = franjas
                pareja_actualizada_en_base = True
                break
        
        # If not exists in base list, add it (prevent inconsistencies)
        if not pareja_actualizada_en_base:
            parejas_base.append({
                'id': pareja_id,
                'nombre': nombre,
                'telefono': telefono,
                'categoria': categoria,
                'franjas_disponibles': franjas
            })
        
        datos_actuales['parejas'] = parejas_base
        
        # If pareja is in a group and franjas changed, recalculate score
        if grupo_contenedor and not cambio_categoria:
            recalcular_score_grupo(grupo_contenedor)
        
        # Regenerate full calendar
        regenerar_calendario(resultado_data)
        datos_actuales['resultado_algoritmo'] = resultado_data
        
        # Build success message
        mensaje = '✓ Pareja actualizada correctamente'
        if cambio_categoria:
            mensaje += ' (movida a parejas no asignadas por cambio de categoría)'
        
        return {
            'success': True,
            'mensaje': mensaje
        }
    
    @staticmethod
    def remove_from_group(
        datos_actuales: Dict[str, Any],
        pareja_id: int
    ) -> Dict[str, Any]:
        """
        Remove a pareja from its group and return it to parejas_sin_asignar.
        
        Args:
            datos_actuales: Current tournament data
            pareja_id: ID of the pareja to remove
        
        Returns:
            Dict with success status, message, and updated statistics
        
        Raises:
            ParejaValidationError: If pareja_id is not provided
            ResultadoAlgoritmoNotFoundError: If resultado_algoritmo is not available
            ParejaNotFoundError: If pareja is not found in any group
        """
        if not pareja_id:
            raise ParejaValidationError('Falta pareja_id')
        
        resultado_data = datos_actuales.get('resultado_algoritmo')
        if not resultado_data:
            raise ResultadoAlgoritmoNotFoundError('No hay resultados del algoritmo')
        
        # Import helpers here to avoid circular dependency
        from api.routes.parejas import (
            recalcular_score_grupo,
            regenerar_calendario,
            recalcular_estadisticas
        )
        
        grupos_dict = resultado_data['grupos_por_categoria']
        parejas_sin_asignar = resultado_data.get('parejas_sin_asignar', [])
        
        # Search for pareja in grupos
        pareja_encontrada = None
        grupo_contenedor = None
        
        for cat, grupos in grupos_dict.items():
            for grupo in grupos:
                for idx, pareja in enumerate(grupo.get('parejas', [])):
                    if pareja.get('id') == pareja_id:
                        pareja_encontrada = grupo['parejas'].pop(idx)
                        grupo_contenedor = grupo
                        break
                if pareja_encontrada:
                    break
            if pareja_encontrada:
                break
        
        if not pareja_encontrada:
            raise ParejaNotFoundError('Pareja no encontrada en ningún grupo')
        
        # Clean group position before adding to no asignadas
        pareja_encontrada['posicion_grupo'] = None
        
        # Add to parejas no asignadas
        parejas_sin_asignar.append(pareja_encontrada)
        
        # Recalculate score of affected group
        recalcular_score_grupo(grupo_contenedor)
        
        # Regenerate full calendar
        regenerar_calendario(resultado_data)
        
        # Recalculate global statistics
        estadisticas = recalcular_estadisticas(resultado_data)
        
        # Update data
        datos_actuales['resultado_algoritmo'] = resultado_data
        
        return {
            'success': True,
            'mensaje': '✓ Pareja removida del grupo y devuelta a no asignadas',
            'estadisticas': estadisticas
        }
