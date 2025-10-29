# 🚀 Guía de Instalación y Configuración

## Paso 1: Instalación de Dependencias

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
pip install -r requirements.txt
```

## Paso 2: Configurar Google Sheets API

### 2.1. Crear proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. En el menú lateral, ve a "APIs y servicios" > "Biblioteca"
4. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### 2.2. Crear credenciales

1. En "APIs y servicios" > "Credenciales"
2. Click en "Crear credenciales" > "Cuenta de servicio"
3. Dale un nombre (ej: "torneo-padel-service")
4. Click en "Crear y continuar"
5. En "Rol", selecciona "Editor" (o "Propietario")
6. Click en "Listo"

### 2.3. Descargar archivo de credenciales

1. En la lista de cuentas de servicio, click en la que acabas de crear
2. Ve a la pestaña "Claves"
3. Click en "Agregar clave" > "Crear clave nueva"
4. Selecciona formato **JSON**
5. Se descargará un archivo `.json`
6. **Renombra el archivo a `credentials.json`**
7. **Mueve el archivo a la carpeta `data/` del proyecto**

### 2.4. Compartir tu Google Sheet con la cuenta de servicio

1. Abre el archivo `credentials.json` que descargaste
2. Busca el campo `"client_email"` (algo como: `nombre@proyecto.iam.gserviceaccount.com`)
3. Copia ese email
4. Abre tu Google Sheet (el que tiene las respuestas del formulario)
5. Click en "Compartir" (arriba a la derecha)
6. Pega el email de la cuenta de servicio
7. Dale permisos de **Editor**
8. Click en "Enviar"

## Paso 3: Obtener el ID de tu Google Sheet

1. Abre tu Google Sheet
2. Mira la URL, se ve así:
   ```
   https://docs.google.com/spreadsheets/d/1abc123XYZ456-id-del-sheet/edit
   ```
3. Copia la parte del medio (el ID), en este ejemplo: `1abc123XYZ456-id-del-sheet`
4. Este ID lo usarás en la aplicación para importar datos

## Paso 4: Ejecutar la Aplicación

En PowerShell, ejecuta:

```powershell
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Paso 5: Usar la Aplicación

### 5.1. Conectar con Google Sheets
1. En el sidebar izquierdo, verifica que la ruta a `credentials.json` sea correcta
2. Click en "🔗 Conectar con Google Sheets"
3. Deberías ver "✅ Conectado exitosamente!"

### 5.2. Importar Datos
1. Selecciona "📥 Importar Datos" en el menú principal
2. Ve a la pestaña "📊 Desde Google Sheets"
3. Pega el ID de tu Google Sheet
4. Selecciona la hoja que contiene las respuestas (normalmente "Respuestas de formulario 1")
5. Click en "📥 Importar Datos"

### 5.3. Generar Grupos
1. Selecciona "⚙️ Generar Grupos"
2. Verás un resumen de las parejas por categoría
3. Click en "🚀 EJECUTAR ALGORITMO"
4. ¡Se generarán los grupos automáticamente!

### 5.4. Ver Calendario
1. Selecciona "📅 Calendario"
2. Verás todos los partidos organizados por franja horaria y cancha

### 5.5. Exportar Resultados
1. Selecciona "📤 Exportar"
2. Puedes exportar a:
   - Google Sheets (crea una nueva hoja en tu spreadsheet)
   - JSON/CSV (descarga local)
   - Texto (para copiar y pegar)

## Solución de Problemas Comunes

### Error: "Module not found: streamlit"
```powershell
pip install streamlit
```

### Error: "Credentials file not found"
- Verifica que `credentials.json` esté en la carpeta `data/`
- Verifica que el nombre sea exactamente `credentials.json`

### Error: "Permission denied" al importar
- Asegúrate de haber compartido el Google Sheet con el email de la cuenta de servicio
- Verifica que le diste permisos de Editor

### La aplicación no muestra datos
- Verifica que tu Google Form esté enviando respuestas a una Sheet
- Verifica que los nombres de las columnas contengan las palabras clave:
  - "nombre" o "pareja" para el nombre
  - "tel" o "teléfono" para el teléfono
  - "categor" para la categoría
  - "horario" o "franja" para las franjas horarias

## Estructura de Columnas del Google Form

Tu Google Form debería tener preguntas con estos nombres (aproximados):

1. **Nombre de la pareja** (texto)
2. **Teléfono de contacto** (texto)
3. **Categoría** (opción múltiple: Cuarta, Quinta, Sexta, Séptima)
4. **Franjas horarias disponibles** (casillas de verificación con todas las franjas)

## Contacto y Soporte

Para problemas o preguntas, puedes crear un issue en el repositorio de GitHub.

¡Disfruta organizando tu torneo! 🎾
