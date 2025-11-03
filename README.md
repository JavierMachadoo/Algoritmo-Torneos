# 🎾 Algoritmo de Torneos de Pádel

Aplicación web para generar grupos y calendarios de torneos de pádel basándose en disponibilidad horaria.

## 📋 Características

- Importación automática desde Google Forms
- Algoritmo inteligente de formación de grupos por categoría y horarios
- Interfaz visual para revisar y editar grupos
- Exportación a Google Sheets con formato y colores
- Gestión de 2 canchas simultáneas
- 4 categorías: Cuarta (🟢), Quinta (🟡), Sexta (🔵), Séptima (🟣)

## 🚀 Instalación

### Requisitos previos
- Python 3.8 o superior
- Cuenta de Google (para integración con Sheets)

### Pasos de instalación

1. Clona el repositorio:
```bash
git clone https://github.com/JavierMachadoo/Algoritmo-Torneos.git
cd Algoritmo-Torneos
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las credenciales de Google Sheets:
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un proyecto nuevo
   - Habilita la API de Google Sheets
   - Descarga las credenciales y guárdalas en `data/credentials.json`

4. Ejecuta la aplicación:
```bash
python main.py
```

## 📖 Uso

1. **Importar datos**: Conecta tu Google Form con la app
2. **Ejecutar algoritmo**: Genera grupos automáticamente
3. **Revisar y editar**: Ajusta grupos manualmente si es necesario
4. **Exportar**: Genera el calendario en Google Sheets

## 🏗️ Estructura del Proyecto

```
Algoritmo-Torneos/
├── app.py                  # Aplicación principal Streamlit
├── src/
│   ├── google_sheets.py    # Integración con Google Sheets
│   ├── algoritmo.py        # Algoritmo de formación de grupos
│   ├── calendario.py       # Generación de calendario
│   └── exportar.py         # Exportación a Google Sheets
├── data/
│   └── credentials.json    # Credenciales de Google (no incluido)
└── requirements.txt        # Dependencias Python
```

## 🧮 Lógica del Algoritmo

1. **Separación por categoría**: Divide parejas en 4ta, 5ta, 6ta y 7ma
2. **Formación de grupos**: Agrupa 3 parejas con máxima coincidencia horaria
3. **Asignación de canchas**: Optimiza uso de 2 canchas simultáneas
4. **Identificación de conflictos**: Lista parejas sin grupo asignado

## 📝 Formato de Datos

El Google Form debe tener estos campos:
- Nombre de la pareja (nombres y apellidos)
- Teléfono de contacto
- Categoría (Cuarta/Quinta/Sexta/Séptima)
- Franjas horarias disponibles (múltiple selección)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor abre un issue primero para discutir cambios mayores.

## 📄 Licencia

MIT License - ver LICENSE para más detalles
