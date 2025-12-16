"""
Script de prueba para verificar el sistema de almacenamiento.
"""

from utils.torneo_storage import storage

def test_storage():
    print("🧪 Probando sistema de almacenamiento...\n")
    
    # 1. Crear torneo
    print("1️⃣ Creando torneo...")
    torneo_id = storage.crear_torneo("Torneo de Prueba")
    print(f"   ✅ Torneo creado con ID: {torneo_id}\n")
    
    # 2. Cargar torneo
    print("2️⃣ Cargando torneo...")
    torneo = storage.cargar(torneo_id)
    print(f"   ✅ Torneo cargado: {torneo['nombre']}")
    print(f"   📊 Estado: {torneo['estado']}")
    print(f"   📅 Fecha: {torneo['fecha_creacion']}\n")
    
    # 3. Modificar y guardar
    print("3️⃣ Agregando datos...")
    torneo['parejas'] = [
        {
            'id': 1,
            'nombre': 'Pareja Test 1',
            'telefono': '099123456',
            'categoria': 'Cuarta',
            'franjas_disponibles': ['Jueves 18:00', 'Sábado 12:00']
        },
        {
            'id': 2,
            'nombre': 'Pareja Test 2',
            'telefono': '099654321',
            'categoria': 'Quinta',
            'franjas_disponibles': ['Viernes 18:00']
        }
    ]
    storage.guardar(torneo_id, torneo)
    print(f"   ✅ {len(torneo['parejas'])} parejas agregadas\n")
    
    # 4. Verificar guardado
    print("4️⃣ Verificando persistencia...")
    torneo_recargado = storage.cargar(torneo_id)
    print(f"   ✅ Parejas persistidas: {len(torneo_recargado['parejas'])}")
    for p in torneo_recargado['parejas']:
        print(f"      - {p['nombre']} ({p['categoria']})\n")
    
    # 5. Listar todos
    print("5️⃣ Listando todos los torneos...")
    torneos = storage.listar_todos()
    print(f"   ✅ Total de torneos: {len(torneos)}")
    for t in torneos:
        print(f"      - {t['nombre']} ({t['num_parejas']} parejas)\n")
    
    # 6. Limpiar test
    print("6️⃣ Limpiando torneo de prueba...")
    storage.eliminar(torneo_id)
    print(f"   ✅ Torneo eliminado\n")
    
    print("✅ ¡Todas las pruebas pasaron correctamente!\n")
    print("🎉 El sistema de almacenamiento está funcionando perfectamente.")
    print("📁 Los torneos se guardan en: data/torneos/")

if __name__ == '__main__':
    try:
        test_storage()
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
