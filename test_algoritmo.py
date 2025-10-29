"""
Script de prueba del algoritmo con datos de ejemplo.
Ejecuta: python test_algoritmo.py
"""

from src.algoritmo import AlgoritmoGrupos, Pareja, COLORES_CATEGORIA
from src.calendario import GeneradorCalendario

# Datos de ejemplo
parejas_ejemplo = [
    # Categoría Cuarta
    Pareja(1, "Juan Pérez / María López", "099123456", "Cuarta", 
           ["Sábado 9:00 a 12:00", "Sábado 12:00 a 15:00"]),
    Pareja(2, "Carlos Gómez / Ana Martínez", "099234567", "Cuarta", 
           ["Sábado 9:00 a 12:00", "Sábado 16:00 a 19:00"]),
    Pareja(3, "Pedro Rodríguez / Laura Fernández", "099345678", "Cuarta", 
           ["Sábado 9:00 a 12:00", "Viernes 18:00 a 21:00"]),
    Pareja(4, "Luis García / Carmen Sánchez", "099456789", "Cuarta", 
           ["Sábado 12:00 a 15:00", "Sábado 16:00 a 19:00"]),
    Pareja(5, "Miguel Torres / Isabel Ramírez", "099567890", "Cuarta", 
           ["Sábado 12:00 a 15:00", "Viernes 18:00 a 21:00"]),
    Pareja(6, "Jorge Castro / Patricia Morales", "099678901", "Cuarta", 
           ["Sábado 12:00 a 15:00", "Sábado 19:00 a 22:00"]),
    
    # Categoría Quinta
    Pareja(7, "Roberto Silva / Daniela Vargas", "099789012", "Quinta", 
           ["Viernes 18:00 a 21:00", "Sábado 16:00 a 19:00"]),
    Pareja(8, "Fernando Díaz / Lucía Herrera", "099890123", "Quinta", 
           ["Viernes 18:00 a 21:00", "Sábado 16:00 a 19:00"]),
    Pareja(9, "Ricardo Méndez / Sofía Reyes", "099901234", "Quinta", 
           ["Viernes 18:00 a 21:00", "Sábado 19:00 a 22:00"]),
    Pareja(10, "Andrés Ortiz / Valentina Cruz", "099012345", "Quinta", 
           ["Sábado 16:00 a 19:00", "Sábado 19:00 a 22:00"]),
    Pareja(11, "Diego Romero / Camila Jiménez", "099123457", "Quinta", 
           ["Sábado 16:00 a 19:00", "Jueves 18:00 a 21:00"]),
    Pareja(12, "Pablo Navarro / Victoria Ruiz", "099234568", "Quinta", 
           ["Sábado 16:00 a 19:00", "Jueves 20:00 a 23:00"]),
    
    # Categoría Sexta
    Pareja(13, "Martín Flores / Gabriela Molina", "099345679", "Sexta", 
           ["Jueves 18:00 a 21:00", "Viernes 21:00 a 00:00"]),
    Pareja(14, "Javier Vega / Andrea Gil", "099456780", "Sexta", 
           ["Jueves 18:00 a 21:00", "Viernes 21:00 a 00:00"]),
    Pareja(15, "Sebastián Peña / Carolina Mendoza", "099567891", "Sexta", 
           ["Jueves 18:00 a 21:00", "Sábado 9:00 a 12:00"]),
    
    # Categoría Séptima  
    Pareja(16, "Mateo Ríos / Martina Campos", "099678902", "Séptima", 
           ["Jueves 20:00 a 23:00", "Viernes 21:00 a 00:00"]),
    Pareja(17, "Lucas Fuentes / Emma Paredes", "099789013", "Séptima", 
           ["Jueves 20:00 a 23:00", "Viernes 21:00 a 00:00"]),
    Pareja(18, "Santiago Ibarra / Olivia Cortés", "099890124", "Séptima", 
           ["Jueves 20:00 a 23:00", "Sábado 19:00 a 22:00"]),
]


def test_algoritmo():
    """Prueba el algoritmo con datos de ejemplo."""
    print("=" * 80)
    print("🎾 TEST DEL ALGORITMO DE GRUPOS - TORNEO DE PÁDEL")
    print("=" * 80)
    print()
    
    # Mostrar parejas de entrada
    print(f"📋 Total de parejas: {len(parejas_ejemplo)}")
    print()
    
    for cat in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
        count = len([p for p in parejas_ejemplo if p.categoria == cat])
        emoji = COLORES_CATEGORIA.get(cat, "⚪")
        print(f"  {emoji} {cat}: {count} parejas")
    
    print()
    print("-" * 80)
    print("🚀 Ejecutando algoritmo...")
    print("-" * 80)
    print()
    
    # Ejecutar algoritmo
    algoritmo = AlgoritmoGrupos(parejas=parejas_ejemplo, num_canchas=2)
    resultado = algoritmo.ejecutar()
    
    # Mostrar estadísticas
    stats = resultado.estadisticas
    
    print("📊 ESTADÍSTICAS:")
    print(f"  • Parejas asignadas: {stats['parejas_asignadas']} de {stats['total_parejas']} ({stats['porcentaje_asignacion']:.1f}%)")
    print(f"  • Parejas sin asignar: {stats['parejas_sin_asignar']}")
    print(f"  • Total grupos formados: {stats['total_grupos']}")
    print(f"  • Grupos con compatibilidad perfecta (3.0): {stats['grupos_compatibilidad_perfecta']}")
    print(f"  • Grupos con compatibilidad parcial (2.0): {stats['grupos_compatibilidad_parcial']}")
    print(f"  • Score promedio: {stats['score_compatibilidad_promedio']:.2f}/3.0")
    print()
    
    # Mostrar grupos por categoría
    print("=" * 80)
    print("👥 GRUPOS FORMADOS")
    print("=" * 80)
    print()
    
    for categoria in ["Cuarta", "Quinta", "Sexta", "Séptima"]:
        if categoria not in resultado.grupos_por_categoria:
            continue
        
        grupos = resultado.grupos_por_categoria[categoria]
        if not grupos:
            continue
        
        emoji = COLORES_CATEGORIA.get(categoria, "⚪")
        print(f"{emoji} CATEGORÍA {categoria.upper()} - {len(grupos)} grupos")
        print("-" * 80)
        
        for grupo in grupos:
            print(f"\n  Grupo {grupo.id}:")
            print(f"  Franja horaria: {grupo.franja_horaria or 'Por coordinar'}")
            print(f"  Score: {grupo.score_compatibilidad:.1f}/3.0")
            print(f"  Parejas:")
            
            for i, pareja in enumerate(grupo.parejas, 1):
                print(f"    {i}. {pareja.nombre}")
                print(f"       Tel: {pareja.telefono}")
                print(f"       Disponibilidad: {', '.join(pareja.franjas_disponibles)}")
            
            print(f"  Partidos:")
            for idx, (p1, p2) in enumerate(grupo.partidos, 1):
                print(f"    Partido {idx}: {p1.nombre} vs {p2.nombre}")
        
        print()
    
    # Parejas sin asignar
    if resultado.parejas_sin_asignar:
        print("=" * 80)
        print("⚠️  PAREJAS SIN GRUPO ASIGNADO")
        print("=" * 80)
        print()
        
        for pareja in resultado.parejas_sin_asignar:
            emoji = COLORES_CATEGORIA.get(pareja.categoria, "⚪")
            print(f"  • {pareja.nombre} ({emoji} {pareja.categoria})")
            print(f"    Tel: {pareja.telefono}")
            print(f"    Disponibilidad: {', '.join(pareja.franjas_disponibles) if pareja.franjas_disponibles else 'Sin especificar'}")
            print()
    
    # Calendario
    print("=" * 80)
    print("📅 CALENDARIO DE PARTIDOS")
    print("=" * 80)
    print()
    
    generador = GeneradorCalendario(duracion_partido_horas=1)
    texto_calendario = generador.exportar_calendario_texto(resultado)
    print(texto_calendario)
    
    print("=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    test_algoritmo()
