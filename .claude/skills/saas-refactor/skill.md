# Skill: SaaS Refactor

### Metadata
- **Name:** `saas-refactor`
- **Description:** Migración a arquitectura SaaS multi-tenant
- **Trigger:** Mencionar "SaaS", "multi-tenant", "Supabase"
- **Scope:** `root`

## 🎯 Objetivo
Guiar la migración del sistema actual (single-tenant para un club) hacia una arquitectura SaaS multi-tenant usando Supabase como backend.

## 🔔 Triggers de Auto-invocación
El agente debe activar esta skill cuando detecte:
- Usuario menciona: "SaaS", "multi-tenant", "varios clubes", "Supabase"
- Usuario habla de: "parametrizar", "configuración por club", "múltiples organizadores"
- Se menciona: "registro público", "base de datos", "migración"

## 📊 Estado Actual vs Estado Objetivo

### Estado Actual (Single-Tenant)
```
┌─────────────────────────────────────┐
│       Club de Pádel "El Raqueta"    │
│                                      │
│  ┌────────────────────────────┐     │
│  │  main.py (Flask)            │     │
│  └──────────┬─────────────────┘     │
│             │                        │
│  ┌──────────▼─────────────────┐     │
│  │  torneo_storage.py (JSON)   │     │
│  │  data/torneos/torneo_actual │     │
│  │         .json                │     │
│  └────────────────────────────┘     │
│                                      │
│  - Categorías hardcoded             │
│  - Franjas hardcoded                │
│  - Sin autenticación real           │
│  - Datos en filesystem              │
└─────────────────────────────────────┘
```

### Estado Objetivo (Multi-Tenant SaaS)
```
┌─────────────────────────────────────────────────────────┐
│                  SaaS Platform                          │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Club A   │  │ Club B   │  │ Club C   │  ...        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │                     │
│       └─────────────┴─────────────┘                     │
│                     │                                    │
│          ┌──────────▼──────────┐                        │
│          │   Flask API (JWT)    │                        │
│          └──────────┬──────────┘                        │
│                     │                                    │
│          ┌──────────▼──────────────┐                    │
│          │   Supabase (PostgreSQL)  │                    │
│          │   - Row Level Security   │                    │
│          │   - Multi-tenant schema  │                    │
│          └────────────────────────┘                     │
│                                                          │
│  - Configuración por tenant                             │
│  - Registro público                                     │
│  - Dashboard de gestión                                 │
│  - API REST completa                                    │
└─────────────────────────────────────────────────────────┘
```

## 🗄️ Diseño de Base de Datos

### Schema Multi-Tenant

```sql
-- TABLA: clubs (tenants)
CREATE TABLE clubs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    configuracion JSONB DEFAULT '{}'::jsonb
);

-- TABLA: users (organizadores y jugadores)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255),
    rol VARCHAR(50) DEFAULT 'jugador', -- 'admin', 'organizador', 'jugador'
    club_id UUID REFERENCES clubs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLA: torneos
CREATE TABLE torneos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    club_id UUID REFERENCES clubs(id) ON DELETE CASCADE,
    organizador_id UUID REFERENCES users(id),
    estado VARCHAR(50) DEFAULT 'borrador', -- 'borrador', 'activo', 'finalizado'
    fecha_inicio DATE,
    fecha_fin DATE,
    configuracion JSONB DEFAULT '{}'::jsonb, -- categorias, franjas personalizadas
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLA: parejas
CREATE TABLE parejas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    torneo_id UUID REFERENCES torneos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL, -- "Juan/Pedro"
    telefono VARCHAR(50),
    categoria VARCHAR(50) NOT NULL,
    franjas_disponibles TEXT[] DEFAULT ARRAY[]::TEXT[],
    user_id UUID REFERENCES users(id), -- Opcional: si la pareja tiene cuenta
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLA: grupos
CREATE TABLE grupos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    torneo_id UUID REFERENCES torneos(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    franja_comun VARCHAR(100),
    score DECIMAL(3,1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLA: grupos_parejas (relación muchos a muchos)
CREATE TABLE grupos_parejas (
    grupo_id UUID REFERENCES grupos(id) ON DELETE CASCADE,
    pareja_id UUID REFERENCES parejas(id) ON DELETE CASCADE,
    PRIMARY KEY (grupo_id, pareja_id)
);

-- TABLA: partidos
CREATE TABLE partidos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grupo_id UUID REFERENCES grupos(id) ON DELETE CASCADE,
    pareja_1_id UUID REFERENCES parejas(id),
    pareja_2_id UUID REFERENCES parejas(id),
    fase VARCHAR(50) DEFAULT 'grupos', -- 'grupos', 'final', 'semifinal'
    franja VARCHAR(100),
    cancha INTEGER,
    resultado_pareja_1 INTEGER,
    resultado_pareja_2 INTEGER,
    completado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES
CREATE INDEX idx_torneos_club ON torneos(club_id);
CREATE INDEX idx_parejas_torneo ON parejas(torneo_id);
CREATE INDEX idx_grupos_torneo ON grupos(torneo_id);
CREATE INDEX idx_partidos_grupo ON partidos(grupo_id);
```

### Row Level Security (RLS)

```sql
-- Habilitar RLS
ALTER TABLE torneos ENABLE ROW LEVEL SECURITY;
ALTER TABLE parejas ENABLE ROW LEVEL SECURITY;
ALTER TABLE grupos ENABLE ROW LEVEL SECURITY;
ALTER TABLE partidos ENABLE ROW LEVEL SECURITY;

-- Política: Los usuarios solo ven datos de su club
CREATE POLICY "Users can view own club torneos" ON torneos
    FOR SELECT
    USING (club_id IN (
        SELECT club_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can insert own club torneos" ON torneos
    FOR INSERT
    WITH CHECK (club_id IN (
        SELECT club_id FROM users WHERE id = auth.uid()
    ));

-- Similar para parejas, grupos, partidos...
```

## 🔄 Plan de Migración

### Fase 1: Abstracción de Storage
**Objetivo:** Preparar código para cambiar de JSON a DB sin romper nada

```python
# ANTES (utils/torneo_storage.py)
class TorneoStorage:
    def guardar(self, datos: Dict) -> None:
        with open('data/torneos/torneo_actual.json', 'w') as f:
            json.dump(datos, f)
    
    def cargar(self) -> Dict:
        with open('data/torneos/torneo_actual.json', 'r') as f:
            return json.load(f)

# DESPUÉS (utils/torneo_storage.py)
from abc import ABC, abstractmethod

class IStorageAdapter(ABC):
    @abstractmethod
    def guardar_torneo(self, torneo_id: str, datos: Dict) -> None:
        pass
    
    @abstractmethod
    def cargar_torneo(self, torneo_id: str) -> Dict:
        pass

class JSONStorageAdapter(IStorageAdapter):
    """Implementación actual con JSON"""
    def guardar_torneo(self, torneo_id: str, datos: Dict) -> None:
        # ... lógica actual ...
        pass

class SupabaseStorageAdapter(IStorageAdapter):
    """Nueva implementación con Supabase"""
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def guardar_torneo(self, torneo_id: str, datos: Dict) -> None:
        # Guardar en Supabase
        self.client.table('torneos').upsert({
            'id': torneo_id,
            'configuracion': datos
        }).execute()
    
    def cargar_torneo(self, torneo_id: str) -> Dict:
        response = self.client.table('torneos')\
            .select('*')\
            .eq('id', torneo_id)\
            .single()\
            .execute()
        return response.data
```

### Fase 2: Configuración Dinámica
**Objetivo:** Parametrizar CATEGORIAS y FRANJAS_HORARIAS

```python
# ANTES (config/settings.py)
CATEGORIAS = ["Cuarta", "Quinta", "Sexta", "Séptima"]
FRANJAS_HORARIAS = [
    "Jueves 18:00",
    "Viernes 18:00",
    # ... hardcoded
]

# DESPUÉS
class ConfiguracionTorneo:
    """Configuración almacenada en DB por club"""
    
    @staticmethod
    def get_categorias(club_id: str) -> List[str]:
        """Obtener categorías configuradas para el club"""
        config = supabase.table('clubs')\
            .select('configuracion')\
            .eq('id', club_id)\
            .single()\
            .execute()
        
        return config.data.get('categorias', [
            "Cuarta", "Quinta", "Sexta", "Séptima"
        ])
    
    @staticmethod
    def get_franjas_horarias(club_id: str) -> List[str]:
        """Obtener franjas configuradas para el club"""
        config = supabase.table('clubs')\
            .select('configuracion')\
            .eq('id', club_id)\
            .single()\
            .execute()
        
        return config.data.get('franjas_horarias', [
            # Defaults
        ])
```

### Fase 3: Autenticación Real
**Objetivo:** Reemplazar auth hardcoded por Supabase Auth

```python
# ANTES (utils/jwt_handler.py)
def generate_token(self, data: dict) -> str:
    """JWT con datos del torneo incluidos"""
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=2),
        'resultado_data': data  # ❌ Datos en token
    }
    return jwt.encode(payload, self.secret_key)

# DESPUÉS
from supabase import create_client

class AuthService:
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def login(self, email: str, password: str) -> Dict:
        """Login con Supabase Auth"""
        response = self.client.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        return {
            'access_token': response.session.access_token,
            'user': response.user
        }
    
    def register(self, email: str, password: str, club_id: str) -> Dict:
        """Registro de nuevo usuario"""
        response = self.client.auth.sign_up({
            'email': email,
            'password': password,
            'data': {
                'club_id': club_id
            }
        })
        return response
```

### Fase 4: API Multi-Tenant
**Objetivo:** Todas las queries filtradas por `club_id`

```python
# ANTES
@api_bp.route('/parejas', methods=['GET'])
@require_auth
@with_resultado_data
def listar_parejas(resultado_data):
    return jsonify(resultado_data['parejas'])

# DESPUÉS
@api_bp.route('/parejas', methods=['GET'])
@require_auth
def listar_parejas():
    user = get_current_user()  # Del token de Supabase
    club_id = user['club_id']
    torneo_id = request.args.get('torneo_id')
    
    # Supabase automáticamente filtra por RLS
    response = supabase.table('parejas')\
        .select('*')\
        .eq('torneo_id', torneo_id)\
        .execute()
    
    return jsonify(response.data)
```

### Fase 5: Dashboard Multi-Torneo
**Objetivo:** UI para gestionar múltiples torneos

```python
@web_bp.route('/dashboard')
@require_auth
def dashboard():
    user = get_current_user()
    
    torneos = supabase.table('torneos')\
        .select('*')\
        .eq('club_id', user['club_id'])\
        .order('created_at', desc=True)\
        .execute()
    
    return render_template('dashboard.html', 
                          torneos=torneos.data,
                          user=user)
```

## 📋 Checklist de Migración

### Backend
- [ ] Instalar Supabase SDK: `pip install supabase`
- [ ] Crear interfaz `IStorageAdapter`
- [ ] Implementar `SupabaseStorageAdapter`
- [ ] Migrar configuraciones a JSONB en DB
- [ ] Reemplazar JWT custom por Supabase Auth
- [ ] Añadir `club_id` a todas las queries
- [ ] Implementar RLS policies
- [ ] Crear endpoint `/api/registro`
- [ ] Migrar datos JSON existentes a Supabase

### Frontend
- [ ] Actualizar login para usar Supabase Auth
- [ ] Crear página de registro
- [ ] Añadir selector de torneo en dashboard
- [ ] Actualizar todas las API calls con `torneo_id`
- [ ] Guardar token de Supabase en localStorage

### Testing
- [ ] Tests con base de datos de prueba
- [ ] Tests de RLS (verificar aislamiento entre tenants)
- [ ] Tests de migración de datos

## 🚀 Nuevas Funcionalidades SaaS

### 1. Registro Público de Clubes
```python
@api_bp.route('/registro/club', methods=['POST'])
def registrar_club():
    """Permite a nuevos clubes registrarse"""
    data = request.json
    
    # Crear club
    club = supabase.table('clubs').insert({
        'nombre': data['nombre_club'],
        'slug': slugify(data['nombre_club']),
        'configuracion': {
            'categorias': ['Cuarta', 'Quinta', 'Sexta', 'Séptima'],
            'franjas_horarias': DEFAULT_FRANJAS
        }
    }).execute()
    
    # Crear usuario admin
    user = supabase.auth.sign_up({
        'email': data['email'],
        'password': data['password']
    })
    
    # Asignar club al usuario
    supabase.table('users').update({
        'club_id': club.data['id'],
        'rol': 'admin'
    }).eq('id', user.id).execute()
    
    return jsonify({'message': 'Club creado exitosamente'})
```

### 2. Plantillas de Configuración
```python
PLANTILLAS_TORNEO = {
    'weekend_league': {
        'nombre': 'Liga de Fin de Semana',
        'categorias': ['A', 'B', 'C'],
        'franjas_horarias': [
            'Sábado 09:00', 'Sábado 14:00', 
            'Domingo 09:00', 'Domingo 14:00'
        ]
    },
    'padel_club': {
        'nombre': 'Torneo de Club Tradicional',
        'categorias': ['Primera', 'Segunda', 'Tercera', 'Cuarta'],
        'franjas_horarias': DEFAULT_FRANJAS
    }
}

@api_bp.route('/torneos/crear-desde-plantilla', methods=['POST'])
def crear_desde_plantilla():
    plantilla_id = request.json['plantilla']
    plantilla = PLANTILLAS_TORNEO[plantilla_id]
    
    # Crear torneo con configuración predefinida
    # ...
```

### 3. Estadísticas Multi-Torneo
```python
@api_bp.route('/estadisticas/club', methods=['GET'])
def estadisticas_club():
    user = get_current_user()
    
    stats = supabase.rpc('calcular_estadisticas_club', {
        'p_club_id': user['club_id']
    }).execute()
    
    return jsonify({
        'total_torneos': stats.data['total_torneos'],
        'total_parejas': stats.data['total_parejas'],
        'promedio_grupos_por_torneo': stats.data['avg_grupos'],
        'categorias_mas_populares': stats.data['top_categorias']
    })
```

## 🔐 Seguridad Multi-Tenant

### Verificación de Tenant en Middleware
```python
@api_bp.before_request
def verify_tenant():
    """Asegura que todas las requests incluyan club_id correcto"""
    if request.method != 'OPTIONS':
        user = get_current_user()
        
        # Verificar que el recurso pertenece al club del usuario
        if 'torneo_id' in request.view_args:
            torneo = supabase.table('torneos')\
                .select('club_id')\
                .eq('id', request.view_args['torneo_id'])\
                .single()\
                .execute()
            
            if torneo.data['club_id'] != user['club_id']:
                return jsonify({'error': 'Acceso denegado'}), 403
```

## 📊 Variables de Entorno (.env)

```bash
# ANTES
SECRET_KEY=tu-clave-secreta
ADMIN_USERNAME=admin
ADMIN_PASSWORD=torneopadel2026

# DESPUÉS
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-role-key  # Solo para operaciones admin
SECRET_KEY=tu-clave-secreta  # Opcional, Supabase maneja JWT
```

## 🔗 Referencias

- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Multi-tenant Architecture](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [Supabase Auth](https://supabase.com/docs/guides/auth)
