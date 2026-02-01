# Arquitectura de Agentes IA - Algoritmo-Torneos

## 🎯 Objetivo

Implementar una arquitectura escalable y mantenible para múltiples agentes de IA, siguiendo el modelo de **"fuente de verdad única"** con symlinks (inspirado en Prowler Cloud).

## 🏗️ Arquitectura Final

```
Algoritmo-Torneos/
│
├── agents.md                    # 📄 Archivo MAESTRO (fuente de verdad)
│                                #    - Contexto del proyecto
│                                #    - Tabla de skills auto-generada
│
├── skills/                      # 📁 Skills centralizadas (fuente de verdad)
│   ├── git-atomic-commits/
│   │   └── skill.md            #    - Metadata + Documentación completa
│   ├── python-flask-mvc/
│   │   └── skill.md
│   └── saas-refactor/
│       └── skill.md
│
├── .claude/                     # 🤖 Agente Claude
│   ├── claude.md               #    - Copia de agents.md (auto-generada)
│   └── skills/                 #    - SYMLINK → /skills
│
├── .copilot/                    # 🤖 Agente GitHub Copilot
│   ├── copilot.md              #    - Copia de agents.md (auto-generada)
│   └── skills/                 #    - SYMLINK → /skills
│
├── .gemini/                     # 🤖 Agente Google Gemini
│   ├── gemini.md               #    - Copia de agents.md (auto-generada)
│   └── skills/                 #    - SYMLINK → /skills
│
├── .cursor/                     # 🤖 Agente Cursor
│   ├── cursor.md               #    - Copia de agents.md (auto-generada)
│   └── skills/                 #    - SYMLINK → /skills
│
├── setup.sh / setup.bat         # 🔧 Script de configuración inicial
│                                #    - Crea carpetas de agentes
│                                #    - Crea symlinks a /skills
│                                #    - Copia agents.md → {agente}.md
│
└── sync.sh / sync.bat           # 🔄 Script de sincronización
                                 #    - Lee metadata de cada skill
                                 #    - Actualiza tabla en agents.md
                                 #    - Propaga a todos los agentes
```

## 🔑 Principios de Diseño

### 1. Fuente de Verdad Única (Single Source of Truth)
- **Skills:** Solo existen en `/skills/[nombre-skill]/skill.md`
- **Contexto maestro:** Solo en `/agents.md`
- **No hay copias físicas** de skills en carpetas de agentes

### 2. Symlinks para Escalabilidad
- Cada agente tiene un symlink (junction en Windows) hacia `/skills`
- Cambios en skills se propagan automáticamente a todos los agentes
- Sin duplicación = Sin inconsistencias

### 3. Automatización Total
- `setup.sh/bat`: Configuración inicial en segundos
- `sync.sh/bat`: Sincronización automática de metadata
- Sin intervención manual = Sin errores humanos

### 4. Metadata como Contrato
Cada skill define su metadata:
```markdown
### Metadata
- **Name:** `nombre-skill`
- **Description:** Breve descripción
- **Trigger:** Cuándo activarse automáticamente
- **Scope:** `root` | `backend` | `frontend` | etc.
```

Los scripts leen esta metadata y generan automáticamente las tablas de auto-invocación.

## 📋 Workflow de Uso

### Configuración Inicial (Una sola vez)

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

**Resultado:**
- Crea carpetas `.claude/`, `.copilot/`, `.gemini/`, `.cursor/`
- Crea symlinks a `/skills` en cada carpeta
- Copia `agents.md` a cada agente renombrándolo

### Agregar una Nueva Skill

1. **Crear carpeta:**
   ```bash
   mkdir skills/nueva-skill
   ```

2. **Crear `skill.md` con metadata:**
   ```markdown
   # Skill: Nueva Skill

   ### Metadata
   - **Name:** `nueva-skill`
   - **Description:** Descripción corta
   - **Trigger:** Cuándo activar
   - **Scope:** `general`

   ## Contenido de la skill...
   ```

3. **Sincronizar:**
   ```bash
   # Windows
   sync.bat

   # Linux/Mac
   ./sync.sh
   ```

**Resultado:**
- Tabla de skills actualizada automáticamente en todos los agentes

### Modificar una Skill Existente

1. Editar `/skills/[nombre-skill]/skill.md`
2. Si cambias metadata, ejecutar `sync.sh/bat`
3. Los cambios se propagan automáticamente (por symlinks)

### Agregar Soporte para Nuevo Agente

1. **Editar `setup.sh/bat`:**
   Agregar el nuevo agente al array:
   ```bash
   AGENTS=("claude" "copilot" "gemini" "cursor" "nuevo-agente")
   ```

2. **Ejecutar setup:**
   ```bash
   ./setup.sh  # o setup.bat
   ```

3. **Listo!** El nuevo agente ya tiene acceso a todas las skills.

## 🔄 Sincronización de Metadata

### Cómo Funciona `sync.sh/bat`

1. **Escanea** `/skills/*/skill.md`
2. **Extrae** metadata de cada skill (regex patterns)
3. **Genera** tabla markdown con formato:
   ```markdown
   <!-- SKILLS_TABLE_START -->
   | Trigger | Skill | Scope | Descripción |
   |---------|-------|-------|-------------|
   | ... | ... | ... | ... |
   <!-- SKILLS_TABLE_END -->
   ```
4. **Reemplaza** contenido entre marcadores en `agents.md`
5. **Propaga** a cada archivo de agente (`.claude/claude.md`, etc.)

### Marcadores en agents.md

```markdown
## 🤖 Skills del Proyecto

<!-- SKILLS_TABLE_START -->
<!-- Esta sección se auto-genera con sync.sh -->
<!-- NO editar manualmente -->
<!-- SKILLS_TABLE_END -->
```

## 📊 Estadísticas de la Arquitectura

### Líneas de Código
- `agents.md`: **155 líneas** (< 500 límite) ✅
- `setup.sh`: ~150 líneas
- `sync.sh`: ~120 líneas
- Total scripts: < 300 líneas

### Reducción de Duplicación
- **Antes:** 3 copias de cada skill (claude, copilot, gemini) = 9 archivos
- **Después:** 1 skill centralizada + symlinks = 3 archivos
- **Ahorro:** 67% menos archivos redundantes

### Mantenibilidad
- **Actualizar skill:** 1 archivo editado → ∞ agentes actualizados
- **Agregar skill:** Crear 1 archivo + ejecutar sync → Todos los agentes la ven
- **Agregar agente:** Editar 1 línea en setup + ejecutar → Totalmente configurado

## 🚀 Ventajas del Sistema

### ✅ Escalabilidad
- Agregar nuevos agentes: < 1 minuto
- Agregar nuevas skills: < 5 minutos
- Sin límite en cantidad de agentes/skills

### ✅ Consistencia
- Imposible tener versiones desincronizadas
- Un cambio = propagación instantánea
- Metadata como contrato formal

### ✅ Mantenibilidad
- Código DRY (Don't Repeat Yourself)
- Scripts automatizados y testeables
- Documentación auto-generada

### ✅ Onboarding Rápido
- Nuevo desarrollador ejecuta `setup.sh` → listo
- Documentación centralizada en agents.md
- Skills con metadata clara

## 🔐 Compatibilidad

### Windows
- Usa **Junction Points** (no requiere admin si falla symlink)
- Scripts `.bat` nativos de cmd
- PowerShell para parsing avanzado

### Linux/Mac
- Usa **symlinks** estándar (`ln -s`)
- Scripts `.sh` con bash
- Compatible con Git Bash en Windows

### Git
- Symlinks/junctions **NO** se commitean como archivos
- Git rastrea el link, no el contenido
- `.gitignore` configurado para archivos generados

## 📝 Buenas Prácticas

### Para Skills
1. **Metadata obligatoria** al inicio del `skill.md`
2. **Documentación completa:** triggers, ejemplos, anti-patrones
3. **Scope específico:** root, backend, frontend, etc.
4. **Triggers claros:** Palabras clave o patrones de código

### Para Agentes
1. **No editar** archivos en carpetas de agentes directamente
2. **Siempre modificar** `/skills/` o `agents.md`
3. **Ejecutar sync** después de cambios en metadata
4. **Validar** que symlinks funcionan (Git status limpio)

### Para el Proyecto
1. **agents.md < 500 líneas** (contexto condensado)
2. **Skills independientes** (bajo acoplamiento)
3. **Scripts idempotentes** (ejecutar múltiples veces = mismo resultado)
4. **Documentación actualizada** (este archivo!)

## 🐛 Troubleshooting

### "Symlinks no funcionan en Windows"
**Solución:** Ejecutar `setup.bat` como Administrador. Si persiste, usa Junction Points (el script lo hace automáticamente).

### "Tabla de skills no se actualiza"
**Solución:** 
1. Verificar que metadata esté en formato correcto
2. Ejecutar `sync.sh/bat` manualmente
3. Revisar logs de PowerShell para errores

### "Git muestra cambios en .claude/skills/"
**Solución:** 
1. Los symlinks no deben causar cambios
2. Verificar `.gitignore` incluye archivos generados
3. Ejecutar `git status` - si ve carpeta completa, recrear symlink

### "Skill nueva no aparece en agentes"
**Checklist:**
- [ ] Archivo en `/skills/[nombre]/skill.md`
- [ ] Metadata presente en formato correcto
- [ ] Ejecutado `sync.sh/bat`
- [ ] Verificado que marcadores están en agents.md

## 🔮 Roadmap Futuro

### Fase 2: Validación Automática
- Script `validate.sh` que verifica:
  - Metadata presente en todas las skills
  - agents.md < 500 líneas
  - Symlinks intactos
  - Formato markdown correcto

### Fase 3: CI/CD Integration
- GitHub Action que ejecuta `sync.sh` en cada commit
- Auto-commit de tablas actualizadas
- Tests de integridad de skills

### Fase 4: Skill Manager CLI
```bash
skill create nombre-skill --scope backend
skill list
skill validate nombre-skill
skill sync
```

## 📚 Referencias

- **Prowler Cloud:** Inspiración para arquitectura de symlinks
- **Single Source of Truth:** Principio DRY aplicado a documentación
- **Conventional Commits:** Formato de metadata similar a conventional commits

---

**Última actualización:** 2026-02-01  
**Arquitecto:** Sistema refactorizado para escalabilidad y mantenibilidad  
**Estado:** ✅ Producción - Arquitectura estable
