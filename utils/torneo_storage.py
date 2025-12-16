"""
Sistema de almacenamiento persistente para torneos.
Guarda cada torneo en un archivo JSON individual.
"""

import json
from pathlib import Path
from datetime import datetime
import uuid
from typing import Dict, List, Optional


class TorneoStorage:
    """Gestiona el almacenamiento persistente de torneos en archivos JSON."""
    
    TORNEOS_DIR = Path('data/torneos')
    
    def __init__(self):
        """Inicializa el directorio de torneos."""
        self.TORNEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    def crear_torneo(self, nombre: str = None) -> str:
        """
        Crea un nuevo torneo y retorna su ID.
        
        Args:
            nombre: Nombre del torneo. Si no se proporciona, se genera automáticamente.
        
        Returns:
            ID único del torneo creado.
        """
        torneo_id = str(uuid.uuid4())[:8]
        
        if not nombre:
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            nombre = f"Torneo {fecha}"
        
        torneo = {
            'id': torneo_id,
            'nombre': nombre,
            'fecha_creacion': datetime.now().isoformat(),
            'fecha_modificacion': datetime.now().isoformat(),
            'parejas': [],
            'resultado_algoritmo': None,
            'num_canchas': 2,
            'estado': 'creando'  # creando, grupos_generados, con_finales, completado
        }
        
        self.guardar(torneo_id, torneo)
        return torneo_id
    
    def guardar(self, torneo_id: str, datos: Dict) -> None:
        """
        Guarda los datos de un torneo.
        
        Args:
            torneo_id: ID del torneo
            datos: Diccionario con todos los datos del torneo
        """
        datos['fecha_modificacion'] = datetime.now().isoformat()
        archivo = self.TORNEOS_DIR / f'{torneo_id}.json'
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    
    def cargar(self, torneo_id: str) -> Optional[Dict]:
        """
        Carga los datos de un torneo.
        
        Args:
            torneo_id: ID del torneo
        
        Returns:
            Diccionario con los datos del torneo o None si no existe.
        """
        archivo = self.TORNEOS_DIR / f'{torneo_id}.json'
        
        if not archivo.exists():
            return None
        
        try:
            with open(archivo, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar torneo {torneo_id}: {e}")
            return None
    
    def listar_todos(self) -> List[Dict]:
        """
        Lista todos los torneos disponibles.
        
        Returns:
            Lista de diccionarios con información resumida de cada torneo.
        """
        torneos = []
        
        for archivo in self.TORNEOS_DIR.glob('*.json'):
            try:
                with open(archivo, encoding='utf-8') as f:
                    torneo = json.load(f)
                    
                    torneos.append({
                        'id': torneo.get('id', archivo.stem),
                        'nombre': torneo.get('nombre', 'Sin nombre'),
                        'fecha_creacion': torneo.get('fecha_creacion'),
                        'fecha_modificacion': torneo.get('fecha_modificacion'),
                        'num_parejas': len(torneo.get('parejas', [])),
                        'estado': torneo.get('estado', 'desconocido')
                    })
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error al leer {archivo}: {e}")
                continue
        
        # Ordenar por fecha de modificación (más reciente primero)
        return sorted(torneos, key=lambda x: x.get('fecha_modificacion', ''), reverse=True)
    
    def eliminar(self, torneo_id: str) -> bool:
        """
        Elimina un torneo.
        
        Args:
            torneo_id: ID del torneo a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existía.
        """
        archivo = self.TORNEOS_DIR / f'{torneo_id}.json'
        
        if archivo.exists():
            archivo.unlink()
            return True
        
        return False
    
    def duplicar(self, torneo_id: str, nuevo_nombre: str = None) -> Optional[str]:
        """
        Crea una copia de un torneo existente.
        
        Args:
            torneo_id: ID del torneo a duplicar
            nuevo_nombre: Nombre para el nuevo torneo
        
        Returns:
            ID del nuevo torneo o None si falló.
        """
        torneo_original = self.cargar(torneo_id)
        
        if not torneo_original:
            return None
        
        nuevo_id = str(uuid.uuid4())[:8]
        
        if not nuevo_nombre:
            nuevo_nombre = f"{torneo_original['nombre']} (Copia)"
        
        nuevo_torneo = torneo_original.copy()
        nuevo_torneo['id'] = nuevo_id
        nuevo_torneo['nombre'] = nuevo_nombre
        nuevo_torneo['fecha_creacion'] = datetime.now().isoformat()
        nuevo_torneo['estado'] = 'creando'
        
        self.guardar(nuevo_id, nuevo_torneo)
        return nuevo_id
    
    def actualizar_nombre(self, torneo_id: str, nuevo_nombre: str) -> bool:
        """
        Actualiza el nombre de un torneo.
        
        Args:
            torneo_id: ID del torneo
            nuevo_nombre: Nuevo nombre
        
        Returns:
            True si se actualizó correctamente, False si no existe.
        """
        torneo = self.cargar(torneo_id)
        
        if not torneo:
            return False
        
        torneo['nombre'] = nuevo_nombre
        self.guardar(torneo_id, torneo)
        return True
    
    def exportar_backup(self, torneo_id: str, ruta_destino: Path) -> bool:
        """
        Crea un backup de un torneo en la ubicación especificada.
        
        Args:
            torneo_id: ID del torneo
            ruta_destino: Ruta donde guardar el backup
        
        Returns:
            True si se creó el backup correctamente.
        """
        import shutil
        
        archivo_origen = self.TORNEOS_DIR / f'{torneo_id}.json'
        
        if not archivo_origen.exists():
            return False
        
        try:
            shutil.copy2(archivo_origen, ruta_destino)
            return True
        except IOError:
            return False


# Instancia global para usar en toda la aplicación
storage = TorneoStorage()
