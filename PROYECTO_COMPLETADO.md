# 🎾 Proyecto Completado - Generador de Grupos para Torneo de Pádel

## ✅ Estado del Proyecto

**TODO FUNCIONANDO CORRECTAMENTE** ✨

El algoritmo logró **100% de asignación** con **compatibilidad perfecta (3.0/3.0)** en todos los grupos!

---

## 📁 Archivos Creados

### Core del Proyecto
- ✅ `src/algoritmo.py` - Algoritmo principal de formación de grupos
- ✅ `src/google_sheets.py` - Integración con Google Sheets  
- ✅ `src/calendario.py` - Generación de calendarios
- ✅ `src/exportar.py` - Exportación a múltiples formatos
- ✅ `app.py` - Aplicación web Streamlit

### Configuración
- ✅ `requirements.txt` - Dependencias Python
- ✅ `.gitignore` - Archivos ignorados en git
- ✅ `.env.example` - Ejemplo de configuración

### Documentación
- ✅ `README.md` - Documentación principal
- ✅ `INSTALACION.md` - Guía paso a paso de instalación
- ✅ `LICENSE` - Licencia MIT

### Testing
- ✅ `test_algoritmo.py` - Script de prueba con datos de ejemplo

---

## 🚀 Cómo Empezar

### 1. Probar el Algoritmo (SIN Google Sheets)

```powershell
python test_algoritmo.py
```

Ya lo probamos y funciona perfectamente! ✅

### 2. Configurar Google Sheets (para uso real)

Sigue la guía completa en `INSTALACION.md`. Resumen rápido:

1. **Google Cloud Console**
   - Crea proyecto
   - Habilita Google Sheets API + Drive API
   - Crea cuenta de servicio
   - Descarga `credentials.json`
   - Colócalo en carpeta `data/`

2. **Compartir tu Google Sheet**
   - Comparte con el email de la cuenta de servicio
   - Dale permisos de Editor

### 3. Ejecutar la Aplicación Web

```powershell
streamlit run app.py
```

Se abrirá en tu navegador en `http://localhost:8501`

---

## 🎯 Funcionalidades Implementadas

### ✅ Algoritmo Inteligente
- Formación de grupos de 3 parejas
- Sistema de scoring de compatibilidad horaria (0.0 - 3.0)
- Optimización greedy para maximizar compatibilidad
- Separación automática por categorías (4ta, 5ta, 6ta, 7ma)
- Gestión de 2 canchas simultáneas
- Identificación de parejas sin grupo compatible

### ✅ Integración Google Sheets
- Importación automática desde Google Forms
- Exportación con formato y colores
- Procesamiento flexible de columnas del formulario
- Mapeo automático de datos

### ✅ Aplicación Web (Streamlit)
- **Importar Datos**: Desde Google Sheets, manual, o archivo
- **Generar Grupos**: Ejecuta algoritmo con un click
- **Visualizar Resultados**: Por categoría con colores
- **Ver Calendario**: Organizado por franja horaria y cancha
- **Exportar**: A Google Sheets, JSON, CSV, o texto

### ✅ Calendario Inteligente
- Asignación de horarios específicos (ej: 12:00-13:00)
- Distribución en 2 canchas
- 3 partidos por grupo (todos vs todos)
- Export en múltiples formatos

---

## 📊 Resultados del Test

Con 18 parejas de ejemplo:
- ✅ **100% de asignación** (18/18 parejas)
- ✅ **6 grupos formados** (2 por Cuarta y Quinta, 1 por Sexta y Séptima)
- ✅ **Compatibilidad perfecta** en todos los grupos (3.0/3.0)
- ✅ **0 parejas sin asignar**

---

## 🎨 Características Visuales

### Colores por Categoría
- 🟢 **Verde** - Cuarta
- 🟡 **Amarillo** - Quinta  
- 🔵 **Celeste** - Sexta
- 🟣 **Morado** - Séptima

### Interfaz Streamlit
- Navegación intuitiva por pestañas
- Sidebar con configuración
- Estadísticas en tiempo real
- Métricas visuales
- Grupos expandibles

---

## 📝 Estructura de Datos del Google Form

El formulario debe tener estos campos (nombres aproximados):

1. **Nombre de la pareja** (texto libre)
   - Ejemplo: "Juan Pérez / María López"

2. **Teléfono** (texto o número)
   - Ejemplo: "099123456"

3. **Categoría** (radio buttons)
   - Opciones: Cuarta, Quinta, Sexta, Séptima

4. **Franjas horarias** (checkboxes múltiples)
   - Jueves 18:00 a 21:00
   - Jueves 20:00 a 23:00
   - Viernes 18:00 a 21:00
   - Viernes 21:00 a 00:00
   - Sábado 9:00 a 12:00
   - Sábado 12:00 a 15:00
   - Sábado 16:00 a 19:00
   - Sábado 19:00 a 22:00

---

## 🔧 Tecnologías Utilizadas

- **Python 3.13**
- **Streamlit** - Framework web
- **Pandas** - Manejo de datos
- **gspread** - API de Google Sheets
- **Google Auth** - Autenticación
- **Plotly** - Visualizaciones (preparado para futuro)

---

## 🎓 Lógica del Algoritmo

### Paso 1: Separación por Categoría
Divide las parejas en 4 listas según su categoría.

### Paso 2: Formación de Grupos (Greedy)
Para cada categoría:
1. Evalúa todas las combinaciones posibles de 3 parejas
2. Calcula score de compatibilidad:
   - **3.0** = Las 3 coinciden en al menos 1 franja ✅
   - **2.0** = Solo 2 coinciden ⚠️
   - **0.0** = No hay compatibilidad ❌
3. Selecciona el mejor grupo (mayor score)
4. Remueve parejas usadas
5. Repite hasta que no haya más grupos compatibles

### Paso 3: Generación de Calendario
- Agrupa partidos por franja horaria
- Asigna cancha 1 y 2 alternadamente
- Calcula horarios específicos (1 hora por partido)
- Genera los 3 partidos de cada grupo

### Paso 4: Identificación de Conflictos
Parejas sin grupo quedan en lista separada con:
- Nombre y categoría
- Teléfono de contacto
- Franjas disponibles
→ Para coordinación manual

---

## 🎯 Próximos Pasos (Opcionales)

Algunas ideas para mejorar:

1. **Edición Manual de Grupos**
   - Drag & drop de parejas entre grupos
   - Reasignación de franjas horarias

2. **Visualizaciones**
   - Gráficos con Plotly
   - Distribución de compatibilidad
   - Timeline visual del torneo

3. **Notificaciones**
   - Envío automático de WhatsApp/Email
   - Con horarios y canchas asignadas

4. **Base de Datos**
   - Guardar histórico de torneos
   - Estadísticas de parejas

5. **Fase Final**
   - Generación automática de cuadros finales
   - Tracking de resultados

---

## 💡 Notas Importantes

### Compatibilidad Parcial (Score 2.0)
Si un grupo tiene score 2.0:
- Solo 2 de las 3 parejas coinciden en horario
- La tercera pareja deberá jugar fuera de su disponibilidad preferida
- Se marca en el resultado para coordinación

### Parejas Sin Asignar
Cuando quedan parejas sin grupo:
- El algoritmo priorizó calidad sobre cantidad
- Mejor tener grupos compatibles que forzar asignaciones malas
- Lista disponible para gestión manual

### Uso de 2 Canchas
- Categorías diferentes pueden jugar simultáneamente
- Grupos de la misma categoría también (si hay muchos)
- Optimiza el uso del tiempo disponible

---

## 🤝 Soporte

Para dudas o problemas:
1. Revisa `INSTALACION.md`
2. Ejecuta `python test_algoritmo.py` para verificar
3. Abre un issue en GitHub

---

## 📄 Licencia

MIT License - Uso libre y modificable

---

**¡Proyecto listo para usar! 🎾✨**

Creado con ❤️ para organizar torneos de pádel de forma inteligente.
