# Algoritmo-Torneos

proyecto Flask para generar grupos y calendario de partidos de pádel según disponibilidad y categoría.

## ¿Qué es?
Una pequeña aplicación web (Flask) que:
- Administra parejas por categoría y franjas horarias.
- Forma grupos optimizados (tripletas) según compatibilidad de horarios.
- Genera un calendario asignando partidos por franja y canchas.

## Tecnologías
- Python
- Flask
- Flask-Session
- pandas
- gspread / Google Auth  (para exportar a Google Sheets)

## Estructura principal
- `main.py` — factory de la app Flask, rutas principales y arranque.
- `api/` — endpoints (API) para manipular parejas y ejecutar acciones desde la UI.
- `web/` — assets y templates (HTML, JS, CSS). Interfaz de usuario.
- `core/algoritmo.py` — lógica central que forma grupos y genera el calendario.
- `core/models.py` — modelos ligeros (Pareja, Grupo, Resultado).
- `data/` — ejemplos y subidas.
- `credentials.json` — credenciales de Google (si usas exportación a Sheets).

## Cómo funciona el algoritmo (alto nivel)
- Se separan las parejas por categoría.
- Para cada categoría: se generan grupos de 3 iterando sobre combinaciones posibles.
  - Se calcula una "compatibilidad" en base a franjas horarias:
    - Score 3.0 = las 3 parejas comparten una franja (mejor caso).
    - Score 2.0 = al menos una intersección entre dos parejas (caso parcial).
    - Score 0.0 = sin intersección relevante.
  - Se elige la combinación con mayor score, se crea el grupo y se elimina de la bolsa de disponibles.
  - Se repite hasta que queden menos de 3 parejas.
- Se generan los partidos por grupo y se arma un calendario asignando canchas de forma round-robin por franja.

Resultado esperado: grupos con máxima compatibilidad horaria posible y un calendario por franja/cancha.

## Instalación y ejecución (Windows / PowerShell)
1. Clona o copia el repositorio:

```powershell
git clone <tu-repo-url>
cd Algoritmo-Torneos
```

2. Crea y activa un entorno virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Instala dependencias:

```powershell
pip install -r requirements.txt
```

4. Verifica que `credentials.json` esté en la raíz si quieres usar Google Sheets (opcional). Si no la tienes, la exportación quedará deshabilitada.

5. Ejecuta la aplicación (modo desarrollo):

```powershell
python main.py
```

6. Abre en navegador: http://127.0.0.1:5000

- Ve a `/datos` para cargar parejas y ejecutar el algoritmo desde la UI.
- Luego `/resultados` para ver grupos y calendario.

## Notas operativas y recomendaciones
- El algoritmo es determinista respecto a la selección de combinaciones pero puede quedar con parejas sin asignar (cuando quedan <3 o no existe compatibilidad). Es intencional; esas parejas quedan pendientes para revisión manual.
- Para producción: desplegar detrás de un servidor WSGI (gunicorn/uvicorn) y usar un almacenamiento de sesiones persistente si no quieres perder datos.
- Google Sheets: necesitas `credentials.json` y habilitar la API en un proyecto de Google Cloud.

## Troubleshooting rápido
- Si al abrir `/resultados` aparece vacío, asegúrate de haber ejecutado el algoritmo desde `/datos` y de que `session['resultado_algoritmo']` esté presente (la app guarda el resultado en sesión en memoria).
- Errores de dependencias: revisa la versión de Python y reinstala el `requirements.txt` en un entorno limpio.

## Licencia y contacto
- Proyecto personal. Para dudas o mejoras, revisa el código en `core/algoritmo.py` o abre un issue en el repositorio.

¡Listo! 🟢  (Archivo `README.md` creado en la raíz del proyecto.)
