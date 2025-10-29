"""
Script para probar el algoritmo importando datos desde CSV.
Simula la importación desde Google Forms.
"""

import pandas as pd
from src.algoritmo import AlgoritmoGrupos, Pareja, COLORES_CATEGORIA
from src.calendario import GeneradorCalendario

# Franjas horarias disponibles
FRANJAS_COLUMNAS = [
    "Jueves 18:00 a 21:00",
    "Jueves 20:00 a 23:00",
    "Viernes 18:00 a 21:00",
    "Viernes 21:00 a 00:00",
    "Sábado 9:00 a 12:00",
    "Sábado 12:00 a 15:00",
    "Sábado 16:00 a 19:00",
    "Sábado 19:00 a 22:00"
]


def importar_csv(archivo_csv: str):
    """
    Importa datos desde un CSV que simula las respuestas de Google Forms.
    
    Args:
        archivo_csv: Ruta al archivo CSV
    
    Returns:
        Lista de objetos Pareja
    """
    print(f"📥 Importando datos desde: {archivo_csv}")
    
    # Leer CSV
    df = pd.read_csv(archivo_csv)
    
    parejas = []
    
    for idx, fila in df.iterrows():
        # Extraer datos básicos
        nombre = fila["Nombre de la pareja"]
        telefono = fila["Teléfono de contacto"]
        categoria = fila["Categoría"]
        
        # Extraer franjas horarias seleccionadas
        franjas_disponibles = []
        for franja in FRANJAS_COLUMNAS:
            if pd.notna(fila.get(franja)) and str(fila.get(franja)).strip():
                franjas_disponibles.append(franja)
        
        # Crear objeto Pareja
        pareja = Pareja(
            id=idx + 1,
            nombre=nombre,
            telefono=str(telefono),
            categoria=categoria,
            franjas_disponibles=franjas_disponibles
        )
        
        parejas.append(pareja)
    
    print(f"✅ {len(parejas)} parejas importadas correctamente\n")
    return parejas


def test_csv():
    """Prueba el algoritmo con datos importados desde CSV."""
    print("=" * 80)
    print("🎾 TEST CON DATOS IMPORTADOS - TORNEO DE PÁDEL")
    print("=" * 80)
    print()
    
    # Importar datos
    parejas = importar_csv("data/datos_prueba.csv")
    
    # Mostrar resumen de datos importados
    print("📋 DATOS IMPORTADOS:")
    print()
    
    parejas_por_cat = {}
    for cat in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
        count = len([p for p in parejas if p.categoria == cat])
        parejas_por_cat[cat] = count
        emoji = COLORES_CATEGORIA.get(cat, "⚪")
        print(f"  {emoji} {cat}: {count} parejas")
    
    print()
    print("-" * 80)
    print("🚀 Ejecutando algoritmo...")
    print("-" * 80)
    print()
    
    # Ejecutar algoritmo
    algoritmo = AlgoritmoGrupos(parejas=parejas, num_canchas=2)
    resultado = algoritmo.ejecutar()
    
    # Mostrar estadísticas
    stats = resultado.estadisticas
    
    print("📊 ESTADÍSTICAS:")
    print(f"  • Total parejas: {stats['total_parejas']}")
    print(f"  • Parejas asignadas: {stats['parejas_asignadas']} ({stats['porcentaje_asignacion']:.1f}%)")
    print(f"  • Parejas sin asignar: {stats['parejas_sin_asignar']}")
    print(f"  • Total grupos: {stats['total_grupos']}")
    print()
    
    print("  Grupos por categoría:")
    for cat, count in stats['grupos_por_categoria'].items():
        emoji = COLORES_CATEGORIA.get(cat, "⚪")
        print(f"    {emoji} {cat}: {count} grupos")
    
    print()
    print(f"  • Grupos con compatibilidad perfecta (3.0): {stats['grupos_compatibilidad_perfecta']}")
    print(f"  • Grupos con compatibilidad parcial (2.0): {stats['grupos_compatibilidad_parcial']}")
    print(f"  • Score promedio: {stats['score_compatibilidad_promedio']:.2f}/3.0")
    print()
    
    # Mostrar grupos formados (resumen)
    print("=" * 80)
    print("👥 GRUPOS FORMADOS (Resumen)")
    print("=" * 80)
    print()
    
    for categoria in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
        if categoria not in resultado.grupos_por_categoria:
            continue
        
        grupos = resultado.grupos_por_categoria[categoria]
        if not grupos:
            continue
        
        emoji = COLORES_CATEGORIA.get(categoria, "⚪")
        print(f"{emoji} {categoria.upper()}: {len(grupos)} grupos")
        
        for grupo in grupos:
            parejas_str = " / ".join([p.nombre.split(" / ")[0] for p in grupo.parejas])
            score_emoji = "✅" if grupo.score_compatibilidad >= 3.0 else "⚠️" if grupo.score_compatibilidad >= 2.0 else "❌"
            print(f"  Grupo {grupo.id}: {parejas_str}... {score_emoji} Score: {grupo.score_compatibilidad:.1f}")
            print(f"    └─ Horario: {grupo.franja_horaria or 'Por coordinar'}")
        
        print()
    
    # Parejas sin asignar
    if resultado.parejas_sin_asignar:
        print("=" * 80)
        print(f"⚠️  PAREJAS SIN GRUPO ASIGNADO ({len(resultado.parejas_sin_asignar)})")
        print("=" * 80)
        print()
        
        for pareja in resultado.parejas_sin_asignar:
            emoji = COLORES_CATEGORIA.get(pareja.categoria, "⚪")
            print(f"  • {pareja.nombre} ({emoji} {pareja.categoria})")
            print(f"    Tel: {pareja.telefono}")
            franjas_str = ", ".join(pareja.franjas_disponibles) if pareja.franjas_disponibles else "Sin especificar"
            print(f"    Disponibilidad: {franjas_str}")
            print()
    else:
        print("=" * 80)
        print("✅ ¡TODAS LAS PAREJAS FUERON ASIGNADAS!")
        print("=" * 80)
        print()
    
    # Resumen de calendario
    print("=" * 80)
    print("📅 RESUMEN DE CALENDARIO")
    print("=" * 80)
    print()
    
    calendario = resultado.calendario
    
    print(f"Total de franjas horarias utilizadas: {len(calendario)}")
    print()
    
    for franja in sorted(calendario.keys()):
        partidos = calendario[franja]
        canchas_usadas = len(set([p['cancha'] for p in partidos]))
        categorias = set([p['categoria'] for p in partidos])
        
        print(f"  📅 {franja}")
        print(f"     Canchas: {canchas_usadas} | Categorías: {', '.join(categorias)} | Partidos: {len(partidos)}")
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)
    print()
    
    # Resumen final
    print("📈 RESUMEN FINAL:")
    print(f"  ✅ Eficiencia de asignación: {stats['porcentaje_asignacion']:.1f}%")
    print(f"  ✅ Calidad promedio de grupos: {stats['score_compatibilidad_promedio']:.2f}/3.0")
    print(f"  ✅ Grupos perfectos: {stats['grupos_compatibilidad_perfecta']}/{stats['total_grupos']}")
    
    if stats['parejas_sin_asignar'] == 0:
        print("\n  🎉 ¡ALGORITMO PERFECTO! Todas las parejas asignadas.")
    elif stats['porcentaje_asignacion'] >= 90:
        print("\n  👍 Excelente resultado. Coordinación manual mínima requerida.")
    elif stats['porcentaje_asignacion'] >= 75:
        print("\n  👌 Buen resultado. Algunas parejas requieren coordinación manual.")
    else:
        print("\n  ⚠️  Muchas parejas sin asignar. Considerar ajustar horarios.")
    
    print()


if __name__ == "__main__":
    test_csv()
