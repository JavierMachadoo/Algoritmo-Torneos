"""
Ejemplo de uso de decoradores API.
Demuestra cómo los decoradores simplifican el código de las rutas.
"""

# ============================================================
# ANTES: Sin decoradores (código repetitivo)
# ============================================================

# @api_bp.route('/agregar-pareja', methods=['POST'])
# def agregar_pareja():
#     """Versión ANTES - con código boilerplate repetido."""
#     try:
#         # ❌ BOILERPLATE: Fetch datos (se repite 15+ veces)
#         datos_actuales = obtener_datos_desde_token()
#         
#         # Lógica de negocio
#         # ...
#         
#         # ❌ BOILERPLATE: Sincronizar (se repite 20+ veces)
#         sincronizar_con_storage_y_token(datos_actuales)
#         
#         return crear_respuesta_con_token_actualizado({...}, datos_actuales)
#     except Exception as e:
#         logger.error(f"Error: {e}")
#         return jsonify({'error': str(e)}), 500


# ============================================================
# DESPUÉS: Con decoradores (código limpio)
# ============================================================

# @api_bp.route('/agregar-pareja', methods=['POST'])
# @with_storage_sync  # ✅ Auto-sincroniza después de ejecutar
# def agregar_pareja():
#     """Versión DESPUÉS - decorador maneja sincronización automáticamente."""
#     try:
#         datos_actuales = obtener_datos_desde_token()
#         
#         # Solo lógica de negocio
#         # ...
#         
#         # ✅ NO NECESITA sincronizar manualmente
#         return crear_respuesta_con_token_actualizado({...}, datos_actuales)
#     except Exception as e:
#         logger.error(f"Error: {e}")
#         return jsonify({'error': str(e)}), 500


# ============================================================
# CON MÚLTIPLES DECORADORES: Aún más limpio
# ============================================================

# @api_bp.route('/intercambiar-pareja', methods=['POST'])
# @with_resultado_data      # ✅ Valida y provee resultado_data automáticamente
# @with_storage_sync        # ✅ Auto-sincroniza después de ejecutar
# def intercambiar_pareja(resultado_data, datos_actuales):
#     """Versión con 2 decoradores - eliminado TODO el boilerplate."""
#     
#     # ✅ NO NECESITA:
#     #    - obtener_datos_desde_token()
#     #    - validar if not resultado_data
#     #    - sincronizar_con_storage_y_token()
#     
#     # Solo lógica de negocio pura
#     resultado = resultado_data
#     # ...
#     
#     return jsonify({'success': True})


# ============================================================
# BENEFICIOS MEDIBLES
# ============================================================

"""
ANTES del refactoring:
- Archivo parejas.py: 1887 líneas
- Patrón de fetch boilerplate: 15 ocurrencias (5 líneas cada una = 75 líneas)
- Patrón de sync boilerplate: 20 ocurrencias (2 líneas cada una = 40 líneas)
- Total boilerplate: ~115 líneas eliminables

DESPUÉS del refactoring:
- Decoradores reutilizables: 1 archivo (180 líneas)
- Boilerplate eliminado: 115 líneas
- Reducción neta: -115 líneas + mejora en claridad

Cada nueva ruta:
- ANTES: +7-10 líneas de boilerplate
- DESPUÉS: +1 línea (decorador)
"""

# ============================================================
# SIGUIENTE PASO: Validación de categoría
# ============================================================

# @api_bp.route('/obtener-categoria/<categoria>', methods=['GET'])
# @validate_categoria  # ✅ Valida automáticamente categoría
# def obtener_categoria(categoria):
#     """Categoría ya está validada por el decorador."""
#     # categoria garantizado que es válida (Cuarta, Quinta, Sexta, o Séptima)
#     # ...
#     return jsonify({'success': True})
