"""
Script para generar un resumen de metadatos de archivos de audio en un directorio específico y opcionalmente usar IA para análisis adicional.
"""

# Importaciones necesarias
import os # Para operaciones del sistema
import argparse # Para manejar argumentos de línea de comandos
from pathlib import Path # Para manejar rutas de archivos
from typing import Optional # Para anotaciones de tipos opcionales

BASE_DIR = Path(__file__).resolve().parent # Directorio base del script
SUMMARY_DIR = BASE_DIR / "summary" # Directorio para los resúmenes

# Función que extrae metadatos de un archivo de audio
def get_audio_metadata(filepath):

    """Extrae metadatos a un archivo de audio usando mutagen."""

    try:
        from mutagen._file import File # Para manejar metadatos de audio
    except ImportError:
        print("Por favor, instála el archivo requirements.txt")
        return None

    # Intentar leer el archivo de audio
    try:
        audio = File(filepath, easy=False) # Cargar con mutagen
        # Si no se pudo leer, retornar None
        if audio is None:
            return None
        
        tags = audio.tags or {} # Obtener etiquetas, manejar None

        # Función auxiliar para obtener el valor de una etiqueta
        def get_tag(keys):

            # Probar varias claves posibles para cada campo
            for key in keys:
                # Verificar si la clave existe en las etiquetas
                if key in tags:
                    # Obtener el valor de la etiqueta
                    val = tags.get(key)
                    # Sí val es un objeto con atributo 'text' (como en ID3), manejarlo
                    if val and hasattr(val, 'text'):
                        # Sí val es una lista, retornar el primer elemento
                        if isinstance(val.text, list) and val.text:
                            return str(val.text[0])
                    # Si val es una lista, retornar el primer elemento
                    elif isinstance(val, list):
                        if val:
                            return str(val[0])
                    # Si val es un valor simple, retornarlo como cadena
                    elif val:
                        return str(val)
            # Si no se encontró ninguna clave, retornar cadena vacía
            return ""

        # Extraer metadatos específicos
        title = get_tag(['title', 'TIT2'])
        artist = get_tag(['artist', 'TPE1'])
        album_artist = get_tag(['albumartist', 'TPE2'])
        album = get_tag(['album', 'TALB'])
        year = get_tag(['date', 'year', 'TDRC', 'TYER'])
        track = get_tag(['tracknumber', 'TRCK'])
        disc = get_tag(['discnumber', 'TPOS'])
        publisher = get_tag(['publisher', 'TPUB'])
        composer = get_tag(['composer', 'TCOM'])
        genre = get_tag(['genre', 'TCON'])

        # Obtener duración y bitrate
        def get_duration_and_bitrate(audio, filepath):
            duration = 0
            bitrate = 0
            #Verificar si audio tiene info y atributos length y bitrate
            if audio.info:
                if hasattr(audio.info, 'length'):
                    duration = audio.info.length # Duración en segundos
                if hasattr(audio.info, 'bitrate'):
                    bitrate = audio.info.bitrate // 1000 # Bitrate en kbps
                #Si el bitrate es 0 pero duración es mayor a 0, estimar bitrate
                if bitrate == 0 and duration > 0:
                    try:
                        file_size = os.path.getsize(filepath) # Tamaño del archivo en bytes
                        bitrate = int((file_size * 8) / (duration * 1000)) # Estimar bitrate en kbps
                    except Exception:
                        bitrate = 0 # Si hay error, dejar en 0
                #Si la duración es 0 pero el bitrate es mayor a 0, estimar duración
                elif duration == 0 and bitrate > 0:
                    try:
                        file_size = os.path.getsize(filepath) # Tamaño del archivo en bytes
                        duration = (file_size * 8) / (bitrate * 1000) # Estimar duración en segundos
                    except Exception:
                        duration = 0 # Si hay error, dejar en 0
                #Si ambos son 0, intentar estimar ambos
                elif duration == 0 and bitrate == 0:
                    try:
                        file_size = os.path.getsize(filepath) # Tamaño del archivo en bytes
                        # Estimar duración y bitrate asumiendo un bitrate promedio de 192 kbps
                        estimated_bitrate = 192
                        duration = (file_size * 8) / (estimated_bitrate * 1000) # Estimar duración en segundos
                        bitrate = estimated_bitrate # Usar bitrate estimado
                    except Exception:
                        duration = 0
                        bitrate = 0 # Si hay error, dejar ambos en 0
            return duration, bitrate

        duration, bitrate = get_duration_and_bitrate(audio, filepath) # Obtener duración y bitrate

        # Función para normalizar campos numéricos (track, disc)
        def normalize_number_field(field):
            #Si el campo es None, retornar cadena vacía
            if not field:
                return ""
            field_str = str(field) # Convertir a cadena

            # Verificar si el campo tiene formato "X/Y"
            if '/' in field_str:
                parts = field_str.split('/') # Dividir por '/'

                # Verificar que ambas partes sean dígitos
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return field_str
            elif field_str.isdigit():
                return field_str
            return ""

        track = normalize_number_field(track) # Normalizar campo track
        disc = normalize_number_field(disc) # Normalizar campo disc

        # Retornar diccionario con metadatos
        return {
            "path": filepath,
            "title": title or "",
            "artist": artist or "",
            "album_artist": album_artist or "",
            "album": album or "",
            "year": year or "",
            "track": track,
            "disc": disc,
            "publisher": publisher or "",
            "composer": composer or "",
            "genre": genre or "",
            "duration": duration,
            "bitrate": bitrate,
        }
    
    # Manejar cualquier excepción y retornar None
    except Exception as e:
        print(f"Error al procesar {filepath}: {e}")
        return None

# Función para convertir segundos a formato legible
def seconds_to_readable(seconds):
    days, rem = divmod(seconds, 86400) # 86400 segundos en un día
    hours, rem = divmod(rem, 3600) # 3600 segundos en una hora
    minutes, _ = divmod(rem, 60) # 60 segundos en un minuto
    parts = [] # Lista para partes del tiempo

    # Construir la cadena legible
    if days > 0: # Agregar días si hay
        parts.append(f"{int(days)} días")
    if hours > 0: # Agregar horas si hay
        parts.append(f"{int(hours)} horas")
    if minutes > 0: # Agregar minutos si hay
        parts.append(f"{int(minutes)} minutos")
    return ", ".join(parts) if parts else "0 minutos" # Retornar cadena legible

# Función para analizar la biblioteca y generar un resumen
def analyze_library(metadata_list, elapsed_time):
    try:
        from collections import Counter # Para contar elementos
        import time # Para medir tiempos
    except ImportError:
        print("No se pudo importar módulos necesarios para el análisis. Asegúrate de tener Python instalado correctamente.")
        return {}

    count = len(metadata_list) # Número total de archivos analizados
    total_duration = sum(m['duration'] for m in metadata_list) # Duración total en segundos
    total_bitrate = sum(m['bitrate'] for m in metadata_list if m['bitrate'] > 0) # Bitrate total
    bitrate_avg = total_bitrate / count if count else 0 # Bitrate promedio
    duration_avg = total_duration / count if count else 0 # Duración promedio

    artists = set(m['artist'] for m in metadata_list if m['artist']) # Artistas únicos
    album_artists = set(m['album_artist'] for m in metadata_list if m['album_artist']) # Artistas de álbum únicos
    albums = set(m['album'] for m in metadata_list if m['album']) # Álbumes únicos

    # Tiempo total para escuchar toda la música
    total_listen_seconds = total_duration # en segundos
    total_listen_readable = seconds_to_readable(total_listen_seconds) # Formatear tiempo total de escucha

    # Género predominante (el más común)
    genres = [m['genre'] for m in metadata_list if m['genre']] # Lista de géneros
    genre_counter = Counter(genres) # Contar ocurrencias de cada género
    genre_predominant = genre_counter.most_common(1)[0][0] if genre_counter else "" # Género más común
    
    # Generar el resumen
    summary = {
        "archivos_analizados": count,
        "tiempo_total_segundos": round(elapsed_time, 2),
        "tiempo_total_formateado": time.strftime("%H:%M:%S", time.gmtime(elapsed_time)),
        "bitrate_promedio_kbps": round(bitrate_avg, 1),
        "duracion_promedio_segundos": round(duration_avg, 2),
        "duracion_promedio_formateada": time.strftime("%M:%S", time.gmtime(duration_avg)),
        "artistas_unicos": len(artists),
        "album_artistas_unicos": len(album_artists),
        "albumes_unicos": len(albums),
        "tiempo_total_escucha": total_listen_readable,
        "genero_predominante": genre_predominant
    }

    return summary # Retornar el resumen generado

# Función principal del script
def main_script(music_dir: str, usar_ia: Optional[bool] = False):
    #Importar módulos necesarios
    import json # Para manejar JSON
    import time # Para medir tiempos
    from datetime import datetime # Para manejar fechas y horas
    from multiprocessing import Pool, cpu_count # Para procesamiento paralelo

    # Intentar importar tqdm
    try:
        from tqdm import tqdm # Para barra de progreso
    except ImportError:
        print("Por favor, instála el archivo requirements.txt")
        return
    
    client = None
    if usar_ia:
        try:
            
            # Importar módulos necesarios para IA
            from dotenv import load_dotenv # Para cargar variables de entorno
            from google import genai # Cliente de Google Generative AI

            load_dotenv() # Cargar variables de entorno desde .env

            if os.getenv("GEMINI_API_KEY") is None:
                print("La variable de entorno GEMINI_API_KEY no está configurada.")
                usar_ia = False

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Inicializar el cliente de Google Generative AI
        except ImportError:
            print("Instala el archivo requirements.txt para usar IA.")
            usar_ia = False
        except ValueError as ve:
            print(ve)
            usar_ia = False
    
    # Configuración de Rutas y Fecha (Ahora dentro de main)
    summary_dir = BASE_DIR / "summary"
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    timestamp_dir = summary_dir / timestamp
    output_file = timestamp_dir / f"musica_metadatos_{timestamp}.json"
    summary_file = timestamp_dir / f"musica_metadatos_resumen_{timestamp}.json"
    analisis_ia = timestamp_dir / f"musica_metadatos_resumen_ia_{timestamp}.txt"
    
    audio_extensions = (".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg")  # Extensiones de audio soportadas
    
    print(f"🎵 Buscando archivos de audio en {music_dir}...")
    files = []
    for root, _, filenames in os.walk(music_dir):
        for f in filenames:
            if f.lower().endswith(audio_extensions):
                files.append(os.path.join(root, f))
    total_files = len(files)
    print(f"🎵 Archivos encontrados: {total_files}")

    start_time = time.time()

    # Procesar con multiprocessing y tqdm para barra de progreso
    with Pool(processes=cpu_count()) as pool: results = list(tqdm(pool.imap(get_audio_metadata, files), total=total_files, unit="archivo"))

    # Filtrar None (archivos no procesados)
    results = [r for r in results if r is not None]

    elapsed_time = time.time() - start_time

    # Asegurarse de que el directorio de resumen exista
    summary_dir.mkdir(parents=True, exist_ok=True)

    # Asegurarse de que el directorio con timestamp exista
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    # Generar resumen y guardar aparte
    summary = analyze_library(results, elapsed_time)

    if usar_ia:
        # Avisar que se esperará respuesta de IA por posible demora
        print("🤖 Usando IA para análisis adicional, esto puede tardar unos momentos...")
        # Usar barra de progreso infinita mientras se espera la respuesta de IA
        tqdm_bar = tqdm(total=1, desc="Esperando respuesta de IA", bar_format="{desc} {bar} | {elapsed}")

        try:
            
            prompt = f"""
            Eres un experto crítico musical y analista de datos.
            Analiza el siguiente resumen estadístico de una biblioteca musical personal:
            
            {json.dumps(summary)}
            
            Por favor dime:
            1. ¿Qué dice el bitrate promedio sobre la calidad de audio que prefiere el usuario?
            2. Basado en la duración promedio y el género, ¿es coherente? (Ej: canciones de punk suelen ser cortas, prog largas).
            3. Calcula mentalmente la variedad: ¿Hay muchos artistas para la cantidad de canciones o escucha siempre a los mismos?
            4. Dame una conclusión breve sobre el perfil de este oyente.
            """

            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt) if client is not None else "Sin respuesta IA debido a un error."
        except Exception as e:
            print(f"Error al usar IA: {e}")
            response = "Sin respuesta IA debido a un error."
        
        # Agregar análisis de IA al resumen JSON como dato crudo.
        if response and not isinstance(response, str) and hasattr(response, 'text') and response.text is not None:
            # Terminar la barra de progreso
            tqdm_bar.update(1)
            texto_ia = response.text if not isinstance(response, str) else response
            summary["analisis_ia"] = texto_ia

            #guardar análisis de IA en archivo de texto
            with open(analisis_ia, "w", encoding="utf-8") as f:
                tqdm_bar.close()
                f.write("Análisis de IA:\n\n")
                f.write(texto_ia)
        elif response and isinstance(response, str):
            tqdm_bar.update(1)
            tqdm_bar.close()
            texto_ia = response
            summary["analisis_ia"] = texto_ia
            # no guardamos archivo de IA si es solo un mensaje de error
        else:
            tqdm_bar.update(1)
            tqdm_bar.close()
            texto_ia = "Sin respuesta IA."
            summary["analisis_ia"] = texto_ia
    
    # Guardar resumen en JSON
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Guardar metadatos en JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Proceso completado: {output_file} generado con {len(results)} archivos.") # Indicar archivo generado
    print(f"✅ Resumen de metadatos guardado en: {summary_file}") # Indicar archivo de resumen generado
    print(f"⏱️ Tiempo total de análisis: {round(elapsed_time, 2)} segundos.") # Indicar tiempo total
    if usar_ia:
        print(f"🤖 Análisis de IA guardado en: {analisis_ia}")

def main():
    parser = argparse.ArgumentParser(description="Generar resumen de metadatos de archivos de audio en un directorio.")
    parser.add_argument("--music_dir", type=str, help="Directorio donde buscar archivos de audio.")
    parser.add_argument("--usar_ia", action="store_true", help="Usar IA para análisis adicional.")
    args = parser.parse_args()

    if not args.music_dir:
        print("Por favor, especifica el directorio de música usando --music_dir")
        return

    main_script(args.music_dir, usar_ia=True) if args.usar_ia else main_script(args.music_dir) # Ejecutar función principal con IA si se especifica de lo contrario sin IA.

if __name__ == "__main__":
    main()
