# Plan Actualizado: Sistema Completo con Supabase + Registro Público

Migrar de almacenamiento JSON a Supabase para soportar 50–100+ usuarios con roles, implementar registro público de jugadores, y preparar dos escenarios de deployment según acceso al código web existente.

## Steps

### 1. Configurar Supabase
- Crear proyecto en Supabase (free tier)
- Definir schema:
  - `users` (id, email, password_hash, role, created_at)
  - `torneos`
  - `parejas`
  - `grupos`
  - `partidos`
- Migrar datos desde `torneo_storage.py`

### 2. Integrar Supabase Auth
- Reemplazar lógica de `jwt_handler.py` con Supabase Auth SDK (maneja JWT + refresh tokens automáticamente)
- Configurar Row Level Security (RLS):
  - `role = 'admin'`
  - `role = 'user'`

### 3. Crear sistema de registro
- Desarrollar `web/templates/registro.html` con formulario:
  - email
  - password
  - nombre
  - teléfono
- Crear endpoint `POST /api/registro` que use `supabase.auth.sign_up()`
- Confirmación por email opcional

### 4. Adaptar almacenamiento
- Modificar `torneo_storage.py` para usar Supabase client en lugar de archivos JSON
- Mantener la misma interfaz de métodos para no romper `algoritmo.py` y otros módulos

### 5. Crear rutas públicas
Agregar nuevos endpoints sin autenticación:
- `GET /torneos` → lista de torneos activos
- `GET /torneo/{id}/posiciones` → rankings
- `GET /torneo/{id}/fixture` → calendario

### 6. Desarrollar vistas de jugador
- Templates:
  - `torneos_publico.html`
  - `posiciones_publico.html`
  - `fixture_publico.html`
- Mismo diseño con gradiente
- Sin controles de edición
- Actualización automática desde Supabase

### 7. Deployment según escenario
- **Escenario A (pueden tocar código actual)**  
  Integrar el sistema en el subdirectorio `/torneos` del dominio existente.
- **Escenario B (código inaccesible)**  
  Deployar en Render o Railway, apuntar el dominio completo al repo y replicar una landing institucional básica en `/`.

## Further Considerations

### Supabase RLS (Row Level Security)
- ¿Usuarios solo ven sus propios datos (ej. historial de partidos) o todo es público?
- Recomendación:
  - Público: tablas de torneos y posiciones
  - Privado: datos personales

### Confirmación de email en registro
- ¿Activar email verification de Supabase o permitir acceso inmediato?
- Club cerrado → desactivarla simplifica
- Registro abierto → activarla reduce spam

### Migración de datos existentes
- ¿Hay torneos en `torneo_actual.json` que deban migrarse?
- Crear script de migración antes de hacer el switch definitivo

### Costos futuros
- Free tier: ~200+ usuarios activos/mes
- Plan Pro: USD 25/mes
- Definir si el club puede asumir ese costo o si se necesita un plan de monetización
