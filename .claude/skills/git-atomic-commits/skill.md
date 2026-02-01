# Skill: Git Atomic Commits

### Metadata 
- **Name:** `git-atomic-commits`
- **Description:** Commits semánticos y atómicos
- **Trigger:** Usuario dice "commit", "listo", "terminé"
- **Scope:** `root`

## 🎯 Objetivo
Ayudar a crear commits atómicos siguiendo convenciones semánticas para mantener un historial de Git limpio y comprensible.

## 🔔 Triggers de Auto-invocación
El agente debe activar esta skill cuando detecte:
- Usuario dice: "commit", "listo", "terminé", "ya acabé"
- Usuario solicita: "commitea esto", "guarda los cambios"
- Después de completar una tarea auto-contenida

## 📋 Reglas de Commits

### Formato Estándar
```
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer opcional]
```

### Tipos Permitidos
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `refactor`: Cambio de código que no añade funcionalidad ni corrige bugs
- `style`: Cambios de formato (espacios, punto y coma, etc.)
- `docs`: Cambios en documentación
- `test`: Añadir o modificar tests
- `chore`: Cambios en build, CI, dependencias

### Scopes del Proyecto
- `algoritmo`: core/algoritmo.py
- `clasificacion`: core/clasificacion.py
- `finales`: core/fixture_finales_generator.py, api/routes/finales.py
- `parejas`: api/routes/parejas.py, services/pareja_service.py
- `storage`: utils/torneo_storage.py
- `validators`: validators/*
- `decorators`: decorators/*
- `web`: templates, static
- `api`: api/routes
- `config`: config/settings.py

## ✅ Ejemplos Buenos

```bash
feat(parejas): agregar endpoint POST /api/parejas
fix(algoritmo): corregir cálculo de compatibilidad para grupos de 3
refactor(storage): extraer lógica de persistencia a clase TorneoStorage
style(web): ajustar responsive en mobile para tabla de grupos
docs(readme): actualizar instrucciones de instalación
```

## ❌ Ejemplos Malos

```bash
# ❌ Demasiado amplio
git commit -m "Implementar finales"

# ❌ Sin scope
git commit -m "feat: agregar cosas"

# ❌ Sin tipo
git commit -m "cambios en algoritmo"

# ❌ Múltiples cambios no relacionados
git commit -m "feat: agregar endpoint + fix bug + actualizar css"
```

## 🔄 Workflow del Agente

Cuando se invoca esta skill:

1. **Analizar cambios realizados**
   ```bash
   git status
   git diff
   ```

2. **Identificar scope afectado**
   - ¿Qué módulo se modificó?
   - ¿Es un cambio auto-contenido?

3. **Determinar tipo de commit**
   - ¿Añade funcionalidad? → `feat`
   - ¿Corrige error? → `fix`
   - ¿Reorganiza código? → `refactor`

4. **Proponer mensaje**
   ```
   Sugerencia de commit:
   feat(parejas): agregar validación de teléfono en ParejaService
   ```

5. **Preguntar si hay múltiples commits**
   Si hay cambios en diferentes scopes:
   ```
   Detecté cambios en:
   - api/routes/parejas.py (feat)
   - core/algoritmo.py (fix)
   
   ¿Quieres hacer 2 commits separados?
   ```

## 🎓 Principios

### Un Commit = Una Idea
Cada commit debe poder revertirse independientemente sin romper otros cambios.

### Descripción Clara
El mensaje debe explicar **qué** y **por qué**, no **cómo**.

```bash
# ✅ BIEN
feat(algoritmo): usar backtracking para optimizar distribución de grupos

# ❌ MAL
feat(algoritmo): agregar for loop y if statement
```

### Tamaño Adecuado
- **Muy pequeño:** `fix(algoritmo): agregar espacio` ❌
- **Muy grande:** `feat: implementar sistema completo de finales` ❌
- **Perfecto:** `feat(finales): agregar endpoint GET /api/finales/clasificacion` ✅

## 🚫 Anti-patrones a Evitar

1. **Mega-commits**
   ```bash
   # ❌ NO
   git commit -m "work in progress"
   git commit -m "changes"
   git commit -m "update"
   ```

2. **Commits de debugging**
   ```bash
   # ❌ NO
   git commit -m "fix: intento 1"
   git commit -m "fix: intento 2"
   git commit -m "fix: ahora sí funciona"
   # ✅ Hacer squash antes de push
   ```

3. **Mezclar concerns**
   ```bash
   # ❌ NO
   git commit -m "feat(parejas): add endpoint + fix(algoritmo): bug + style(web): css"
   # ✅ Dividir en 3 commits
   ```

## 📝 Checklist Pre-commit

Antes de hacer commit, verificar:

- [ ] ¿El código funciona?
- [ ] ¿Sigue los patrones del proyecto? (MVC, Service Layer)
- [ ] ¿El mensaje es claro y específico?
- [ ] ¿Es un cambio auto-contenido?
- [ ] ¿Incluye solo archivos relevantes?

## 🔗 Referencias

- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
