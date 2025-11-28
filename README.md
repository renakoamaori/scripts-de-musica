
# 🎵 Repositorio de Herramientas para Gestión Musical

Monorepo de utilidades prácticas diseñadas para optimizar el almacenamiento de tu colección musical y obtener información valiosa sobre tus hábitos de escucha. Ideal para usuarios que buscan **gestión eficiente** y **ahorro de espacio** sin comprometer calidad.

---

## 📋 Tabla de Contenidos

- [Herramientas Disponibles](#️-herramientas-disponibles)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Requisitos del Sistema](#️-requisitos-del-sistema)

---

## 🛠️ Herramientas Disponibles

### 1. 🔄 Optimizador de Audio a MP3

**Ubicación:** `CONVERTIR_MUSICA_A_MP3/audiomp3.py`

Reduce significativamente el peso de bibliotecas musicales en formatos lossless (FLAC/WAV) convirtiéndolas a MP3 de alta calidad (320kbps), ideal para dispositivos portátiles o liberar espacio en disco.

#### Funcionalidades Clave:

- **Soporte Multiformato:** Procesa recursivamente FLAC, WAV, OGG y M4A
- **Conversión Inteligente:** Utiliza `ffmpeg` para generar MP3 a 320kbps preservando metadatos originales
- **Gestión Automática:** Copia portadas e imágenes; omite archivos ya procesados para reanudar tareas interrumpidas
- **Alto Rendimiento:** Procesamiento paralelo mediante `ThreadPoolExecutor` (multithreading)
- **Interfaz Dual:**
    - **Modo GUI:** Interfaz gráfica moderna con `PyQt6` para selección visual de carpetas
    - **Modo CLI:** Argumentos de línea de comandos para automatización y servidores
- **Logging Avanzado:** Reportes detallados en JSON (resumen y errores) en carpeta `logs`

---

### 2. 📊 Analizador de Biblioteca Musical

**Ubicación:** `METADATOS_MUSICA/audioanalysis.py`

Herramienta de escaneo profundo para comprender la composición de tu biblioteca musical y obtener insights personalizados.

#### Funcionalidades Clave:

- **Extracción Completa:** Usa `mutagen` para leer tags (Artista, Álbum, Género, Año) y calcular duración/bitrate real
- **Estadísticas Detalladas:** 
    - Tiempo total de escucha
    - Bitrate promedio de la colección
    - Conteo de artistas únicos
    - Género predominante
- **Análisis con IA:** Integración con Google Gemini (vía `google-genai`) para generar perfiles de oyente personalizados y análisis de calidad/coherencia
- **Exportación Organizada:** Data cruda y resúmenes en JSON, organizados por fecha en carpetas dedicadas

---

## 📁 Estructura del Proyecto

```
scripts-de-musica/
├── CONVERTIR_MUSICA_A_MP3/
│   ├── audiomp3.py
│   ├── requirements.txt
│   ├── .venv/
│   └── logs/
└── METADATOS_MUSICA/
        ├── audioanalysis.py
        ├── requirements.txt
        ├── .env
        ├── .venv/
        └── summary/
```

---

## 🚀 Instalación

Cada herramienta es **independiente** y mantiene su propio entorno virtual.

### Optimizador de Audio a MP3

```bash
cd scripts-de-musica/CONVERTIR_MUSICA_A_MP3
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Analizador de Biblioteca

```bash
cd scripts-de-musica/METADATOS_MUSICA
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 💻 Uso

### Optimizador de Audio a MP3

**Modo GUI (Interfaz Gráfica):**
```bash
python audiomp3.py
```

**Modo CLI (Línea de Comandos):**
```bash
python audiomp3.py --input_dir /ruta/origen --output_dir /ruta/destino
```

### Analizador de Biblioteca

```bash
python audioanalysis.py --music_dir /ruta/a/biblioteca
```

---

## ⚙️ Requisitos del Sistema

### Dependencias Externas

- **FFmpeg:** Requerido para el Optimizador de Audio
    - **Linux:**
        - **Debian/Ubuntu:** `sudo apt install ffmpeg`
        - **Arch/Manjaro:** `sudo pacman -S ffmpeg`
        - **Fedora/RHEL:** `sudo dnf install ffmpeg`
        - **Otras distros:** Consultar repositorio de tu distribución
    - **macOS:** `brew install ffmpeg`
    - **Windows:** Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html)

### Variables de Entorno (Analizador)

Crear archivo `.env` en `METADATOS_MUSICA/`:

```env
GEMINI_API_KEY=tu_clave_api_aqui
```

Obtén tu clave API en [Google AI Studio](https://makersuite.google.com/app/apikey).

---

## 📝 Notas

- Ambas herramientas pueden ejecutarse de forma independiente
- Los logs y outputs se organizan automáticamente por fecha
- La conversión a MP3 preserva la estructura de carpetas original

---

## 📜 Licencia

Este repositorio está diseñado para **uso personal y educativo**. Las herramientas están disponibles libremente para optimizar y analizar tu colección musical privada, así como para fines de aprendizaje en procesamiento de audio y análisis de metadatos.

**Restricciones:**
- No está permitido el uso comercial sin autorización expresa
- Respeta los derechos de autor del contenido musical que proceses
- El autor no se responsabiliza por el uso indebido de las herramientas

---
