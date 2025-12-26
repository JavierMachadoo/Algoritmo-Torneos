"""
Sistema de almacenamiento persistente simplificado.
Mantiene un solo torneo activo con persistencia.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class TorneoStorage:
    """Gestiona el almacenamiento persistente de un único torneo."""
    
    TORNEOS_DIR = Path('data/torneos')
    TORNEO_ACTUAL_FILE = TORNEOS_DIR / 'torneo_actual.json'
    
    def __init__(self):
        """Inicializa el directorio de torneos."""
        self.TORNEOS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Crear torneo por defecto si no existe
        if not self.TORNEO_ACTUAL_FILE.exists():
            self._crear_torneo_default()
    
    def _crear_torneo_default(self) -> None:
        """Crea el torneo por defecto."""
        torneo = {
            'nombre': f"Torneo {datetime.now().strftime('%d/%m/%Y')}",
            'fecha_creacion': datetime.now().isoformat(),
            'fecha_modificacion': datetime.now().isoformat(),
            'parejas': [],
            'resultado_algoritmo': None,
            'num_canchas': 2,
            'estado': 'creando'
        }
        self.guardar(torneo)
    
    def guardar(self, datos: Dict) -> None:
        """
        Guarda los datos del torneo actual.
        
        Args:
            datos: Diccionario con todos los datos del torneo
        """
        datos['fecha_modificacion'] = datetime.now().isoformat()
        
        with open(self.TORNEO_ACTUAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    
    def cargar(self) -> Dict:
        """
        Carga los datos del torneo actual.
        
        Returns:
            Diccionario con los datos del torneo.
        """
        if not self.TORNEO_ACTUAL_FILE.exists():
            self._crear_torneo_default()
        
        try:
            with open(self.TORNEO_ACTUAL_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar torneo: {e}")
            self._crear_torneo_default()
            return self.cargar()
    
    def limpiar(self) -> None:
        """Limpia todos los datos del torneo actual manteniendo la estructura."""
        torneo = self.cargar()
        torneo['parejas'] = []
        torneo['resultado_algoritmo'] = None
        torneo['estado'] = 'creando'
        self.guardar(torneo)
    
    def actualizar_nombre(self, nuevo_nombre: str) -> bool:
        """
        Actualiza el nombre del torneo actual.
        
        Args:
            nuevo_nombre: Nuevo nombre para el torneo
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            torneo = self.cargar()
            torneo['nombre'] = nuevo_nombre
            self.guardar(torneo)
            return True
        except Exception as e:
            print(f"Error al actualizar nombre: {e}")
            return False


# Instancia global
storage = TorneoStorage()
