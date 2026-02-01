# Algoritmo-Torneos - Contexto para Agentes IA

## 📋 Resumen del Proyecto

**Nombre:** Generador de Grupos para Torneos de Pádel  
**Estado:** Sistema funcional para club específico → En evolución hacia SaaS multi-tenant  
**Propósito:** Automatizar la generación de grupos (tripletas) de pádel según categoría, disponibilidad horaria y asignación de canchas.

### Problema que Resuelve
Los organizadores de torneos de pádel necesitan:
1. Agrupar jugadores por nivel (categoría)
2. Formar tripletas que compartan franjas horarias disponibles
3. Asignar automáticamente canchas y generar calendario
4. Gestionar fixture de finales con clasificaciones

### Valor Diferencial
- **Algoritmo optimizado:** Usa backtracking con poda para maximizar compatibilidad horaria
- **Score de compatibilidad:** 3.0 (todas comparten franja), 2.0 (intersección parcial), 0.0 (incompatible)
- **Generación automática de calendario:** Distribuye partidos por franjas y canchas disponibles
- **100% responsive:** Mobile-first para uso en dispositivo del organizador

---

## 🏗️ Stack Tecnológico

**Backend:** Python 3.13, Flask 3.1.2, Pandas 2.2.0+, PyJWT 2.8.0+  
**Frontend:** HTML5 + Jinja2, Bootstrap 5, Vanilla JavaScript  
**Arquitectura:** Monolito modular con Service Layer, JWT stateless, JSON storage (migración a Supabase planificada)

---

## 📁 Arquitectura de Carpetas (Simplificada)

```
Algoritmo-Torneos/
├── main.py                    # Entry point Flask
├── api/routes/               # REST endpoints (parejas, finales)
├── core/                     # Lógica de dominio (algoritmo, modelos)
├── services/                 # Business logic sin Flask
├── utils/                    # Helpers (storage, CSV, JWT)
├── validators/               # Validadores de datos
├── decorators/               # Decoradores API
├── web/templates/            # Frontend Jinja2
├── web/static/               # CSS, JS
└── skills/                   # Skills para agentes IA (ver abajo)
```

---

## 🔑 Conceptos Clave del Dominio

### Modelos de Datos (core/models.py)

**Pareja:** Equipo de 2 jugadores con nombre, categoría, franjas disponibles  
**Grupo:** Tripleta de parejas que jugarán entre sí (score de compatibilidad)  
**ResultadoAlgoritmo:** Grupos por categoría + calendario + estadísticas

### Franjas Horarias
```python
["Jueves 18:00", "Jueves 20:00", "Viernes 18:00", "Viernes 21:00", 
 "Sábado 09:00", "Sábado 12:00", "Sábado 16:00", "Sábado 19:00"]
```

### Categorías
```python
["Cuarta", "Quinta", "Sexta", "Séptima"]
```

---

## 🧮 Algoritmo de Generación de Grupos

**Estrategia:** Backtracking con poda para 2-6 grupos, greedy fallback para más.

**Score de Compatibilidad:**
- `3.0`: Las 3 parejas comparten AL MENOS una franja
- `2.0`: Al menos 2 parejas tienen intersección
- `0.0`: Sin compatibilidad

**Flujo:**
1. Separar parejas por categoría
2. Optimización global (backtracking) o greedy según cantidad
3. Generar calendario round-robin por franja
4. Calcular estadísticas

---

## 🔐 Autenticación y Seguridad

**JWT Handler:** Tokens expiran en 2 horas, auth stateless  
**Flow:** Login → JWT con resultado → API calls con Bearer token  
**Storage:** Datos del torneo en JWT (evita sesiones server-side)

---

## 🚀 Flujo de Trabajo del Usuario

1. **Carga CSV** → AlgoritmoGrupos.ejecutar() → JWT con ResultadoAlgoritmo → Renderiza grupos
2. **Gestión** → Drag & Drop parejas, CRUD grupos (actualiza JWT)
3. **Finales** → Clasificación top 2 → Fixture playoffs → Calendario

---

## 📊 Formato CSV Requerido

```csv
Nombre,Teléfono,Categoría,Jueves 18:00,Jueves 20:00,...
Juan/Pedro,099123456,Cuarta,Sí,No,Sí,...
```

**Validaciones:** Nombre obligatorio (formato "J1/J2"), categoría válida, al menos una franja "Sí"

---

## 🎯 Roadmap hacia SaaS (NewFEATURES.md)

**Objetivo:** Convertir single-tenant → Multi-tenant con Supabase

**Cambios Planificados:**
1. Migrar JSON → PostgreSQL con Row Level Security (RLS)
2. Sistema de registro público (admin/user roles)
3. Multi-tenant: Todas queries filtradas por `club_id`
4. Parametrizar CATEGORIAS/FRANJAS en DB por club
5. Dashboard para gestionar múltiples torneos

---

## 🧩 Patrones de Diseño

### Application Factory (main.py)
```python
def crear_app():
    app = Flask(__name__)
    app.jwt_handler = JWTHandler(SECRET_KEY)
    app.register_blueprint(api_bp)
    return app
```

### Service Layer Pattern
```python
# ✅ CORRECTO: Lógica de negocio sin dependencias Flask
class ParejaService:
    @staticmethod
    def add(datos_actuales, nombre, telefono, categoria, franjas):
        if not nombre:
            raise ParejaValidationError('Nombre obligatorio')
        # ... lógica pura ...
        return nueva_pareja
```

### Decoradores para API
- `@require_auth`: Valida JWT
- `@with_resultado_data`: Extrae datos del JWT
- `@with_storage_sync`: Sincroniza cambios con storage

---

## ⚠️ Anti-patrones a Evitar

❌ **Business Logic en Routes:** Validaciones y lógica deben estar en Service Layer  
❌ **Service con Flask:** No importar `request` o `jsonify` en services  
❌ **Mega-commits:** Commits deben ser atómicos y semánticos  

---

## 📝 Convenciones de Código

**Python:** PEP 8, type hints, docstrings Google style  
**JavaScript:** ES6+, camelCase, Revealing Module Pattern  
**Git:** Prefijos `feat/fix/refactor/style/docs/test`, formato `tipo(scope): descripción`

---

## 🤖 Skills del Proyecto

Las skills están centralizadas en `/skills` y sincronizadas automáticamente con los agentes.

### Auto-invocación de Skills

<!-- SKILLS_TABLE_START -->
| Trigger | Skill | Scope | Descripción |
|---------|-------|-------|-------------|
| Usuario dice "commit", "listo", "terminé" | git-atomic-commits | root | Commits semánticos y atómicos |
| Modificar api/routes/*, crear endpoints | python-flask-mvc | backend | Patrones MVC + Service Layer |
| Mencionar "SaaS", "multi-tenant", "Supabase" | saas-refactor | root | Migración a arquitectura SaaS |
<!-- SKILLS_TABLE_END -->

**Documentación completa:** Ver `./skills/[nombre-skill]/skill.md`

---

## 📚 Referencias Rápidas

**Archivos Críticos:**
- `main.py` - Entry point
- `core/algoritmo.py` - Algoritmo de grupos
- `api/routes/parejas.py` - API principal
- `utils/torneo_storage.py` - Persistencia

**Testing:**
- `generar_datos_prueba.py` - Script de prueba
- `data/datos_prueba.csv` - CSV de ejemplo

---

## 🧠 Cultura del Proyecto

1. **Simplicidad sobre complejidad** - Evitar over-engineering
2. **Mobile-first** - Optimizado para celular
3. **Commits atómicos** - Cada commit auto-explicativo
4. **Separación de concerns** - Service layer sin Flask
5. **Documentación clara** - Docstrings concisos

---

**Última actualización:** Sistema estable en producción. Siguiente fase: Migración a Supabase.
