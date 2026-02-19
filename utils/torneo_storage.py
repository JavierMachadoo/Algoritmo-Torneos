"""
Sistema de almacenamiento persistente del torneo activo.

En producción (Render, Railway, etc.) usa Supabase para persistencia real.
En desarrollo local, cae a JSON si no hay variables de Supabase configuradas.

Variables de entorno requeridas para Supabase:
    SUPABASE_URL       → URL del proyecto Supabase
    SUPABASE_ANON_KEY  → clave anon/public del proyecto
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Directorio base del proyecto (dos niveles arriba de este archivo)
_BASE_DIR = Path(__file__).resolve().parent.parent

# ── Detectar si Supabase está disponible ──────────────────────────────────────
_SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
_SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', '').strip()
_USE_SUPABASE = bool(_SUPABASE_URL and _SUPABASE_KEY)

if _USE_SUPABASE:
    try:
        from supabase import create_client, Client as SupabaseClient
    except ImportError:
        logger.warning('supabase package no instalado. Usando almacenamiento JSON.')
        _USE_SUPABASE = False

# ─────────────────────────────────────────────────────────────────────────────


class TorneoStorage:
    """Gestiona el almacenamiento persistente de un único torneo.

    Backend:
        - Supabase (JSONB)  → cuando SUPABASE_URL y SUPABASE_ANON_KEY están definidas
        - JSON local        → fallback para desarrollo sin Supabase
    """

    # Paths locales (solo se usan si no hay Supabase)
    _TORNEOS_DIR: Path = _BASE_DIR / 'data' / 'torneos'
    _TORNEO_FILE: Path = _TORNEOS_DIR / 'torneo_actual.json'

    # Nombre de la tabla en Supabase
    _TABLE = 'torneo_actual'

    def __init__(self) -> None:
        if _USE_SUPABASE:
            self._sb: SupabaseClient = create_client(_SUPABASE_URL, _SUPABASE_KEY)
            logger.info('TorneoStorage: usando Supabase')
        else:
            self._TORNEOS_DIR.mkdir(parents=True, exist_ok=True)
            if not self._TORNEO_FILE.exists():
                self._crear_torneo_default()
            logger.info('TorneoStorage: usando JSON local (%s)', self._TORNEO_FILE)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _torneo_vacio(self) -> Dict:
        """Devuelve la estructura de un torneo nuevo."""
        now = datetime.now().isoformat()
        return {
            'nombre': f"Torneo {datetime.now().strftime('%d/%m/%Y')}",
            'fecha_creacion': now,
            'fecha_modificacion': now,
            'parejas': [],
            'resultado_algoritmo': None,
            'num_canchas': 2,
            'estado': 'creando',
        }

    def _crear_torneo_default(self) -> None:
        self.guardar(self._torneo_vacio())

    # ── API pública ───────────────────────────────────────────────────────────

    def guardar(self, datos: Dict) -> None:
        """Persiste el diccionario completo del torneo."""
        datos['fecha_modificacion'] = datetime.now().isoformat()

        if _USE_SUPABASE:
            self._sb.table(self._TABLE).upsert(
                {'id': 1, 'datos': datos}
            ).execute()
        else:
            with open(self._TORNEO_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)

    def cargar(self) -> Dict:
        """Carga y devuelve el diccionario completo del torneo."""
        if _USE_SUPABASE:
            try:
                resp = self._sb.table(self._TABLE).select('datos').eq('id', 1).execute()
                if resp.data:
                    return resp.data[0]['datos']
            except Exception as e:
                logger.error('Error al cargar desde Supabase: %s', e)

            # Primera ejecución: no hay fila todavía
            default = self._torneo_vacio()
            self.guardar(default)
            return default

        # ── JSON local ────────────────────────────────────────────────────────
        if not self._TORNEO_FILE.exists():
            self._crear_torneo_default()

        try:
            with open(self._TORNEO_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error('Error al cargar torneo JSON: %s', e)
            self._crear_torneo_default()
            return self.cargar()

    def limpiar(self) -> None:
        """Reinicia el torneo manteniendo nombre y fecha de creación."""
        torneo = self.cargar()
        torneo['parejas'] = []
        torneo['resultado_algoritmo'] = None
        torneo['fixtures_finales'] = {}
        torneo['estado'] = 'creando'
        self.guardar(torneo)

    def actualizar_nombre(self, nuevo_nombre: str) -> bool:
        """Actualiza el nombre del torneo. Devuelve True si tuvo éxito."""
        try:
            torneo = self.cargar()
            torneo['nombre'] = nuevo_nombre
            self.guardar(torneo)
            return True
        except Exception as e:
            logger.error('Error al actualizar nombre: %s', e)
            return False


# Instancia global compartida por todos los módulos
storage = TorneoStorage()
