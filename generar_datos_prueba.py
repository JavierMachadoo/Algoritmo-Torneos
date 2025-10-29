"""
Genera datos de prueba en formato CSV para simular Google Forms.
"""

import csv
from datetime import datetime, timedelta
import random

# Franjas horarias
FRANJAS = [
    "Jueves 18:00 a 21:00",
    "Jueves 20:00 a 23:00",
    "Viernes 18:00 a 21:00",
    "Viernes 21:00 a 00:00",
    "Sábado 9:00 a 12:00",
    "Sábado 12:00 a 15:00",
    "Sábado 16:00 a 19:00",
    "Sábado 19:00 a 22:00"
]

# Datos de parejas
parejas_data = [
    # Cuarta (12 parejas)
    ("Juan Pérez / María López", "099123456", "Cuarta", [4, 5]),
    ("Carlos Gómez / Ana Martínez", "099234567", "Cuarta", [4, 6]),
    ("Pedro Rodríguez / Laura Fernández", "099345678", "Cuarta", [2, 4]),
    ("Luis García / Carmen Sánchez", "099456789", "Cuarta", [5, 6]),
    ("Miguel Torres / Isabel Ramírez", "099567890", "Cuarta", [2, 5]),
    ("Jorge Castro / Patricia Morales", "099678901", "Cuarta", [5, 7]),
    ("Alejandro Ruiz / Sofía Díaz", "099789012", "Cuarta", [4, 5]),
    ("Daniel Herrera / Valentina Cruz", "099890123", "Cuarta", [5, 6, 7]),
    ("Andrés Moreno / Camila Rojas", "099901234", "Cuarta", [4, 6]),
    ("Sebastián Vargas / Lucía Méndez", "099012345", "Cuarta", [1, 6, 7]),
    ("Mateo Ortiz / Emma Jiménez", "099123457", "Cuarta", [0, 7]),
    ("Gabriel Silva / Victoria Ramos", "099234568", "Cuarta", [2, 3]),
    
    # Quinta (14 parejas)
    ("Roberto Navarro / Andrea Gil", "099345679", "Quinta", [2, 6]),
    ("Fernando Vega / Daniela Flores", "099456780", "Quinta", [2, 6]),
    ("Ricardo Peña / Carolina Castro", "099567891", "Quinta", [2, 7]),
    ("Diego Romero / Martina Molina", "099678902", "Quinta", [6, 7]),
    ("Pablo Ríos / Gabriela Mendoza", "099789013", "Quinta", [0, 6]),
    ("Lucas Fuentes / Olivia Paredes", "099890124", "Quinta", [0, 6]),
    ("Santiago Ibarra / Isabella Cortés", "099901235", "Quinta", [1, 6, 7]),
    ("Nicolás Campos / Emilia Reyes", "099012346", "Quinta", [5, 6]),
    ("Joaquín León / Renata Medina", "099123458", "Quinta", [2, 3]),
    ("Tomás Guzmán / Julia Soto", "099234569", "Quinta", [2, 4]),
    ("Maximiliano Cruz / Valentina Torres", "099345680", "Quinta", [3, 4, 5]),
    ("Benjamín Arias / Luciana Prieto", "099456781", "Quinta", [4, 5]),
    ("Emilio Mora / Antonella Aguilar", "099567892", "Quinta", [1, 3]),
    ("Matías Delgado / Mía Cabrera", "099678903", "Quinta", [0, 1, 6]),
    
    # Sexta (12 parejas)
    ("Javier Serrano / Constanza Paz", "099789014", "Sexta", [0]),
    ("Martín Blanco / Delfina Núñez", "099890125", "Sexta", [0, 6]),
    ("Ignacio Guerrero / Pilar Domínguez", "099901236", "Sexta", [0, 3]),
    ("Facundo Miranda / Alma Carrillo", "099012347", "Sexta", [1, 6, 7]),
    ("Valentín Ponce / Nina Márquez", "099123459", "Sexta", [1, 2, 3]),
    ("Thiago Espinoza / Jazmín Ríos", "099234570", "Sexta", [2, 3]),
    ("Lautaro Benítez / Catalina Vera", "099345681", "Sexta", [3, 4]),
    ("Bruno Villalba / Julieta Peralta", "099456782", "Sexta", [4, 5]),
    ("Alejo Cáceres / Renata Acosta", "099567893", "Sexta", [4, 6]),
    ("Ian Maldonado / Luna Ferreira", "099678904", "Sexta", [5, 6]),
    ("Ezequiel Sosa / Abril Sandoval", "099789015", "Sexta", [5, 7]),
    ("Bautista Rojas / Lola Montero", "099890126", "Sexta", [6, 7]),
    ("Agustín Figueroa / Helena Bustos", "099901237", "Sexta", [6, 7]),
    
    # Séptima (10 parejas)
    ("Felipe Bravo / Clara Vidal", "099012348", "Séptima", [1, 3]),
    ("Lorenzo Suárez / Martina Campos", "099123460", "Séptima", [1, 3]),
    ("Francisco Rivas / Emilia Santos", "099234571", "Séptima", [1, 7]),
    ("Simón Robles / Sofia Luna", "099345682", "Séptima", [6, 7]),
    ("Manuel Gallardo / Elena Riveros", "099456783", "Séptima", [6, 7]),
    ("Vicente Valdez / Paula Cortés", "099567894", "Séptima", [3, 4]),
    ("Rodrigo Lagos / Isidora Leiva", "099678905", "Séptima", [4, 5]),
    ("Esteban Muñoz / Florencia Parra", "099789016", "Séptima", [4, 6]),
    ("Cristóbal Tapia / Magdalena Bravo", "099890127", "Séptima", [5, 6]),
    ("Gonzalo Moya / Antonia Rubio", "099901238", "Séptima", [2, 3]),
]


def generar_csv():
    """Genera el archivo CSV con datos de prueba."""
    # Fecha base
    fecha_base = datetime(2025, 10, 15, 8, 0, 0)
    
    with open('data/datos_prueba.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Encabezados
        headers = ['Marca temporal', 'Nombre de la pareja', 'Teléfono de contacto', 'Categoría']
        headers.extend(FRANJAS)
        writer.writerow(headers)
        
        # Datos
        for idx, (nombre, telefono, categoria, indices_franjas) in enumerate(parejas_data):
            # Timestamp incremental
            timestamp = fecha_base + timedelta(hours=idx * 1.5)
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Crear fila
            fila = [timestamp_str, nombre, telefono, categoria]
            
            # Agregar franjas (marcar con el nombre de la franja si está seleccionada)
            for i, franja in enumerate(FRANJAS):
                if i in indices_franjas:
                    fila.append(franja)
                else:
                    fila.append('')
            
            writer.writerow(fila)
    
    print(f"✅ Archivo CSV generado: data/datos_prueba.csv")
    print(f"📊 Total de parejas: {len(parejas_data)}")
    
    # Estadísticas
    por_categoria = {}
    for _, _, cat, _ in parejas_data:
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
    
    print("\nDistribución por categoría:")
    for cat, count in sorted(por_categoria.items()):
        print(f"  {cat}: {count} parejas")


if __name__ == "__main__":
    generar_csv()
