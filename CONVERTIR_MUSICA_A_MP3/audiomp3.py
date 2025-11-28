"""
Script para conversión masiva de audio y organización de archivos.

Procesa recursivamente todos los archivos en un directorio de entrada, convirtiendo 
archivos de audio (FLAC, WAV, OGG, M4A) al formato MP3 a 320 kbps mientras preserva 
los metadatos originales. Los archivos que no son de audio (imágenes, documentos, 
letras) se copian sin modificaciones. La estructura de carpetas original se replica 
en el directorio de salida.

* Características:
    * Procesamiento paralelo mediante múltiples hilos para mayor rendimiento
    * Barra de progreso con tiempo estimado de finalización
    * Omisión automática de archivos ya procesados
    * Registro detallado de conversiones, copias y errores en formato JSON
"""

# Primero importo las librerías necesarias
import os # Para operaciones del sistema
import shutil # Para copiar archivos
import subprocess # Para llamar a ffmpeg
import json # Para manejar archivos JSON
import time # Para medir tiempos
from pathlib import Path # Para manejar rutas de archivos
from concurrent.futures import ThreadPoolExecutor, as_completed # Para procesamiento paralelo
import argparse # Para manejar argumentos de línea de comandos
from typing import Literal # Para manejar argumentos de línea de comandos
from datetime import datetime # Para manejar fechas y horas

BASE_DIR = Path(__file__).resolve().parent # Directorio base del script
LOGS_DIR = BASE_DIR / "logs" # Directorio para logs

# -------------------- Configuración --------------------
AUDIO_FORMATS = {".flac", ".wav", ".ogg", ".m4a"} # Formatos de audio a convertir

timestamp = datetime.now().strftime("%d%m%Y_%H%M%S") # formato en ddmmyyyy_hhmmss.
ERROR_LOG = LOGS_DIR / f"log_errors_{timestamp}.json" # Archivo de log para errores
SUMMARY_LOG = LOGS_DIR / f"log_summary_{timestamp}.json" # Archivo de log para resumen

CPU_CORES = os.cpu_count() or 2 # Número de núcleos de CPU para procesamiento paralelo (predeterminado a 2 si no se puede determinar)

# -------------------- Funciones --------------------
def convert_or_copy(file_path: Path, input_dir: Path, output_dir: Path) -> tuple[Literal["converted", "copied", "skipped", "error"], Path | tuple[Path, str]]:
    """
    Convierte un archivo de audio a MP3 y copia otros archivos.
    """
    rel_path = file_path.relative_to(input_dir) # Ruta relativa del archivo
    out_file = output_dir / rel_path # Ruta de salida correspondiente
    out_file.parent.mkdir(parents=True, exist_ok=True) # Crear directorios si no existen
    ext = file_path.suffix.lower() # Extensión del archivo

    # Intentar convertir o copiar el archivo
    try:
        # Convertir si es un formato de audio
        if ext in AUDIO_FORMATS:
            # Cambiar la extensión a .mp3
            out_file = out_file.with_suffix(".mp3")
            # Omitir si el archivo ya existe
            if out_file.exists():
                return "skipped", out_file # Archivo ya procesado
            
            # CONFIGURACIÓN PARA WINDOWS: Ocultar ventana de consola
            startupinfo = None # Inicializar variable
            if os.name == 'nt':
                # Configurar para ocultar la ventana de consola en Windows
                startupinfo = subprocess.STARTUPINFO() # Crear objeto STARTUPINFO
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # Establecer bandera para ocultar ventana

            # Ejecutar ffmpeg para convertir el archivo
            result = subprocess.run(
                ["ffmpeg", "-i", str(file_path), "-b:a", "320k", "-map_metadata", "0", str(out_file), "-y"], # Comando ffmpeg
                capture_output=True, # Capturar salida
                text=True, # Salida como texto
                encoding="utf-8", # Codificación UTF-8
                errors="replace", # Reemplazar errores de codificación
                startupinfo=startupinfo # Usar configuración para ocultar ventana en Windows
            )
            # Si hay un error en la conversión, registrar el error
            if result.returncode != 0 or "error" in result.stderr.lower():
                raise RuntimeError(result.stderr) # Lanzar excepción con el error
            return "converted", out_file # Retornar éxito de conversión
        # Copiar otros archivos
        else:
            # Omitir si el archivo ya existe
            if not out_file.exists():
                shutil.copy2(file_path, out_file) # Copiar archivo preservando metadatos
            return "copied", out_file # Retornar éxito de copia
    # Manejar excepciones y registrar errores
    except Exception as e:
        return "error", (file_path, str(e)) # Retornar error con detalles

# -------------------- Main --------------------

# Script normal.
def main_script(input_dir: Path, output_dir: Path) -> None:
    """
    Función principal para procesar todos los archivos en el directorio de entrada.
    1. Recopila todos los archivos en el directorio de entrada.
    2. Procesa cada archivo en paralelo, convirtiendo o copiando según corresponda.
    3. Muestra una barra de progreso con velocidad y ETA.
    4. Guarda logs de errores y un resumen al finalizar.
    5. Imprime la ubicación de los archivos procesados y los logs.
    """

    #importo las librerías necesarias
    try:
        from tqdm import tqdm # Para la barra de progreso
    except ImportError:
        print("Error: Necesitas instalar 'tqdm' para usar el modo consola.")
        return
    
    # Recopilar todos los archivos de todos los álbumes
    all_files = [f for f in input_dir.rglob("*") if f.is_file()] # Lista de todos los archivos
    total_files = len(all_files) # Contar el total de archivos

    if total_files == 0:
        print("No se encontraron archivos para procesar en el directorio de entrada.")
        return

    all_results = {"converted": [], "copied": [], "error": []} # Diccionario para almacenar resultados
    errores = [] # Lista para almacenar errores

    start_time = time.time() # Tiempo de inicio

    # Procesamiento paralelo de archivos
    with ThreadPoolExecutor(max_workers=CPU_CORES) as executor:
        futures = {executor.submit(convert_or_copy, f, input_dir, output_dir): f for f in all_files} # Enviar tareas al executor

        # Barra de progreso con tqdm
        with tqdm(total=total_files, desc="Procesando archivos", dynamic_ncols=True) as pbar:
            # Iterar sobre los resultados a medida que se completan
            for future in as_completed(futures):
                status, result_data = future.result() # Obtener resultado de la tarea
                # Actualizar resultados según el estado
                if status == "error":
                    f_path, error_msg = result_data if isinstance(result_data, tuple) else (result_data, "Error desconocido")
                    all_results["error"].append({"file": f_path.name, "error": error_msg})
                    errores.append({"file": f_path.name, "error": error_msg}) # Agregar a la lista de errores
                else:
                    all_results[status].append(str(result_data)) # Agregar archivo a la lista correspondiente

                # Actualizar barra de progreso
                pbar.update(1)
                elapsed = time.time() - start_time # Tiempo
                speed = pbar.n / elapsed if elapsed > 0 else 0 # Velocidad en archivos por segundo
                remaining = total_files - pbar.n # Archivos restantes
                eta = remaining / speed if speed > 0 else 0 # Tiempo estimado restante
                # Actualizar información en la barra de progreso
                pbar.set_postfix({"Velocidad_t/s": f"{speed:.2f}", "ETA": f"{int(eta//60):02d}:{int(eta%60):02d}"})

    # Calcular tiempos y totales
    elapsed_total = time.time() - start_time
    total_tracks = len(all_results["converted"]) + len(all_results["copied"]) + len(all_results["error"]) # Total de archivos procesados

    LOGS_DIR.mkdir(parents=True, exist_ok=True) # Crear directorio de logs si no existe

    # Guardar errores
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        json.dump(errores, f, indent=2, ensure_ascii=False) # Guardar errores en JSON

    # Guardar resumen
    with open(SUMMARY_LOG, "w", encoding="utf-8") as f:
        summary = {
            "converted": all_results["converted"],
            "copied": all_results["copied"],
            "failed": all_results["error"],
            "total_files_processed": total_tracks,
            "total_time_sec": int(elapsed_total),
            "average_speed_tracks_per_sec": round(total_tracks / elapsed_total, 2) if elapsed_total > 0 else 0
        }
        json.dump(summary, f, indent=2, ensure_ascii=False) # Guardar resumen en JSON

    print(f"\nProceso completado. Archivos en: {output_dir}")
    print(f"Resumen guardado en: {SUMMARY_LOG}")
    print(f"Errores guardados en: {ERROR_LOG}")

# Script con GUI:
def main_with_gui() -> None:
    """
    Función principal para procesar todos los archivos en el directorio de entrada con GUI.
    Similar a la función main(), pero con una interfaz gráfica hecha en PyQt6.
    """
    # primero se importan las librerías necesarias para la GUI
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QProgressBar
        from PyQt6.QtCore import QThread, pyqtSignal
    except ImportError:
        print("Error: Necesitas instalar 'PyQt6' para usar la interfaz gráfica.")
        return

    # Clase para el hilo de procesamiento
    class WorkerThread(QThread):
        progress = pyqtSignal(int) # Señal para actualizar progreso
        log = pyqtSignal(str) # Señal para enviar logs
        finished = pyqtSignal() # Señal para indicar finalización

        # Constructor
        def __init__(self, input_dir, output_dir):
            super().__init__() # Inicializar QThread
            self.input_dir = Path(input_dir) # Directorio de entrada
            self.output_dir = Path(output_dir) # Directorio de salida

        # Método para ejecutar el hilo
        def run(self):
            # Recopilar todos los archivos de todos los álbumes
            all_files = [f for f in self.input_dir.rglob("*") if f.is_file()] # Lista de todos los archivos
            total_files = len(all_files) # Contar el total de archivos

            if total_files == 0:
                self.log.emit("No se encontraron archivos para procesar en el directorio de entrada.")
                self.finished.emit()
                return

            start_time = time.time() # Tiempo de inicio
            errores = [] # Lista para almacenar errores

            # Procesamiento paralelo de archivos
            with ThreadPoolExecutor(max_workers=CPU_CORES) as executor:
                futures = {executor.submit(convert_or_copy, f, self.input_dir, self.output_dir): f for f in all_files} # Enviar tareas al executor

                # Iterar sobre los resultados a medida que se completan
                for i, future in enumerate(as_completed(futures)):
                    status, result_data = future.result() # Obtener resultado de la tarea
                    # Enviar logs según el estado
                    if status == "error":
                        f_path, error_msg = result_data if isinstance(result_data, tuple) else (result_data, "Unknown error")
                        self.log.emit(f"Error al procesar {f_path.name}: {error_msg}") # Enviar log de error
                        errores.append({"file": f_path.name, "error": error_msg})

                    else:
                        if isinstance(result_data, Path):
                            msg = f"Convertido: {result_data.name}" if status == "converted" else f"Copiado: {result_data.name}"
                            self.log.emit(msg) # Enviar log de éxito
                        else:
                            self.log.emit(f"Error desconocido con el archivo.") # Enviar log de error desconocido

                    self.progress.emit(int((i + 1) / total_files * 100)) # Actualizar progreso

            elapsed_total = time.time() - start_time # Tiempo total
            self.log.emit(f"Proceso completado en {int(elapsed_total)} segundos.") # Enviar log de finalización

            LOGS_DIR.mkdir(parents=True, exist_ok=True) # Crear directorio de logs si no existe

            #crear archivo de log de errores
            with open(ERROR_LOG, "w", encoding="utf-8") as f:
                json.dump(errores, f, indent=2, ensure_ascii=False) # Guardar errores en JSON
            self.log.emit(f"Errores guardados en: {ERROR_LOG}") # Indicar ubicación del log de errores

            #crear archivo de log de resumen
            with open(SUMMARY_LOG, "w", encoding="utf-8") as f:
                summary = {
                    "failed": errores,
                    "total_files_processed": total_files,
                    "total_time_sec": int(elapsed_total),
                    "average_speed_tracks_per_sec": round(total_files / elapsed_total, 2) if elapsed_total > 0 else 0
                }
                json.dump(summary, f, indent=2, ensure_ascii=False) # Guardar resumen en JSON

            self.finished.emit() # Emitir señal de finalización
        
    # Clase para la ventana principal
    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Conversión Masiva de Audio a MP3")
            self.setGeometry(100, 100, 600, 400)

            main_layout = QVBoxLayout()

            self.input_button = QPushButton("Seleccionar Directorio de Entrada")
            self.input_button.clicked.connect(self.select_input_directory)
            main_layout.addWidget(self.input_button)

            self.output_button = QPushButton("Seleccionar Directorio de Salida")
            self.output_button.clicked.connect(self.select_output_directory)
            main_layout.addWidget(self.output_button)

            self.start_button = QPushButton("Iniciar Procesamiento")
            self.start_button.clicked.connect(self.start_processing)
            main_layout.addWidget(self.start_button)

            self.progress_bar = QProgressBar()
            main_layout.addWidget(self.progress_bar)

            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            main_layout.addWidget(self.log_text)

            self.setLayout(main_layout)

            self.input_dir = ""
            self.output_dir = ""
            self.worker_thread = None

        def select_input_directory(self):
            dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Entrada")
            if dir_path:
                self.input_dir = dir_path
                self.log_text.append(f"Directorio de entrada seleccionado: {dir_path}")

        def select_output_directory(self):
            dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Salida")
            if dir_path:
                self.output_dir = dir_path
                self.log_text.append(f"Directorio de salida seleccionado: {dir_path}")

        def start_processing(self):
            if not self.input_dir or not self.output_dir:
                self.log_text.append("Por favor, seleccione ambos directorios antes de iniciar.")
                return

            self.worker_thread = WorkerThread(self.input_dir, self.output_dir)
            self.worker_thread.progress.connect(self.update_progress)
            self.worker_thread.log.connect(self.append_log)
            self.worker_thread.finished.connect(self.processing_finished)
            self.worker_thread.start()
            self.log_text.append("Procesamiento iniciado...")

        def update_progress(self, value):
            self.progress_bar.setValue(value)

        def append_log(self, message):
            self.log_text.append(message)

        def processing_finished(self):
            self.log_text.append("Procesamiento finalizado.")
    
    import sys # Importar sys para la aplicación GUI
    # Iniciar la aplicación GUI
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#main
def main() -> None:
    """
    Función principal para decidir si ejecutar el script normal o con GUI.
    Parametros:
        - gui: Booleano que indica si se debe usar la GUI o no.
        - input_dir: Directorio de entrada si no se usa GUI.
        - output_dir: Directorio de salida si no se usa GUI.
    """
    parser = argparse.ArgumentParser(description="Conversión masiva de audio y organización de archivos.") # Configurar el parser de argumentos
    parser.add_argument("--gui", action="store_true", help="Usar interfaz gráfica.") # Argumento para usar GUI
    parser.add_argument("--input_dir", type=str, nargs="?", help="Directorio de entrada con archivos a procesar.") # Argumento para el directorio de entrada
    parser.add_argument("--output_dir", type=str, nargs="?", help="Directorio de salida para archivos procesados.") # Argumento para el directorio de salida
    args = parser.parse_args() # Parsear los argumentos

    # Si existe el argumento --gui, ejecutar con GUI
    if args.gui:
        main_with_gui() # Ejecutar con GUI
    # Sino, ejecutar el script normal
    else:
        if not args.input_dir or not args.output_dir:
            print("Error: Debe proporcionar los directorios de entrada y salida cuando no se usa la GUI.")
            return
        input_dir = Path(args.input_dir).resolve() # Define el directorio de entrada
        output_dir = Path(args.output_dir).resolve() # Define el directorio de salida

        if not input_dir.is_dir():
            print(f"Error: El directorio de entrada '{input_dir}' no existe o no es un directorio válido.")
            return
        
        main_script(input_dir, output_dir) # Ejecutar el script normal


if __name__ == "__main__":
    main()
