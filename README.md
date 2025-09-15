# NowPlayingExporterPy

![NowPlayingExporterPy (1)](https://github.com/user-attachments/assets/162df03c-33f2-4275-89f1-eebd064d7c77)

Exporta el historial de **Now Playing / Está sonando** (Android System Intelligence, ASI) de dispositivos Google Pixel a **CSV**, e incorpora una función para **descargar las canciones** listadas en ese historial (vía `yt-dlp`) al almacenamiento de la app. Pensada y construida como proyecto de **Aprendizaje Basado en Proyectos (PBL)**.&#x20;

> **⚠️ Requiere root.** La base de datos de ASI es privada del sistema. Concede permisos de superusuario (Magisk / KernelSU / aPatch) antes de usarla. Para explorar los ficheros resultantes puede hacer falta un gestor con root.

---

## Características

* ✅ Exportación a **CSV** del historial “Está Sonando”.
* ✅ **Deduplicación** inteligente (ventanas de tiempo) para limpiar duplicados y “falsos repetidos”.
* ✅ **Descarga de canciones** desde el CSV con `yt-dlp` al directorio privado de la app (no necesita permisos de almacenamiento).
* ✅ UI minimalista con feedback de progreso en tiempo real.&#x20;

---

## Rutas y formatos

* **DB de ASI** (ejemplos habituales):

  ```
  /data/data/com.google.android.as/databases/history_db
  /data/user_de/0/com.google.android.as/databases/history_db
  /data/data/com.google.android.as.oss/databases/history_db
  ```
* **Salida CSV**: en `Descargas` (MediaStore) con nombre `now_playing_export_YYYYMMDD_HHMMSS[_dedup].csv`.
* **Descargas de audio** (con `yt-dlp`):

  ```
  /Android/data/com.d4vram.nowplayingexporterpy/files/Music/NPEpy_download_songs/
  ```

  Formato típico: `.webm` (sin post-procesado FFmpeg). Para escucharlas en tu reproductor, **mueve/copialas** a `/sdcard/Music/`.&#x20;

---

## Cómo funciona (resumen técnico)

1. **Root (libsu)** copia `history_db` de ASI a la sandbox de la app.
2. **Chaquopy (Python)** ejecuta `np_export.py` para leer SQLite y generar el **CSV** temporal.
3. (Opcional) `np_dedupe.py` aplica **deduplicación** por ventana temporal.
4. La app guarda el CSV final en **Descargas** y ofrece **compartir** por intent estándar.
5. Con el CSV listo, **`yt-dlp`** busca y descarga los audios a la carpeta privada de la app.&#x20;

---

## Requisitos

* **Root** (Magisk / KernelSU Next / aPatch).
* **ASI** instalado (Android System Intelligence).
* Probado en **Android 16** (Pixel con KernelSU Next). Se espera compatibilidad Android **12–15** en Pixel (no garantizada).&#x20;

---

## Lecciones aprendidas (problemas → soluciones)

1. **FFmpeg & `yt-dlp`**: Chaquopy no aporta FFmpeg vía pip. `yt-dlp` puede bajar audio nativo (`.webm`) **sin FFmpeg**, así que se eliminó la falsa dependencia y se configuró “best audio”.
2. **Progreso en tiempo real**: se añadió una interfaz `PythonCallback` desde Kotlin para recibir logs/estado del script Python y mostrarlos en la UI.
3. **DNS / red intermitente**: además de declarar `android.permission.INTERNET`, se implementaron **reintentos** con pausas y “pausa larga” tras N descargas.
4. **Scoped Storage (API 29+)**: escribir en `Music` público da `Operation not permitted`. Solución: **usar almacenamiento privado de la app** en `/Android/data/.../files/` (no requiere permisos en Android 10+).&#x20;

---

## Uso

1. **Instala** el APK.
2. **Concede root** cuando te lo pida.
3. Pulsa **Exportar** para generar el CSV del historial.
4. (Opcional, recomendado) Activa **Deduplicar**.
5. Pulsa **Descargar canciones** para poblar `NPEpy_download_songs/`.&#x20;

> **Tip importante para buena legibilidad**: abrir el CSV en hojas de cálculo sin romper columnas


    >   Para que no te “trocee” los títulos por espacios, toca exactamente esto:
    
    En Opciones de separador

    ✅ Coma

    ⛔ Espacio → DESMARCA
    
    ⛔ Punto y coma → DESMARCA

    ⛔ Tabulador → DESMARCA (déjalo solo si tu archivo lleva tabs)

    En Delimitador de cadena → elige " (comillas dobles).

    Conjunto de caracteres → Unicode (UTF-8) (como ya tienes).

    (Recomendado) En la vista previa, haz clic en el encabezado de la columna timestamp_iso (y cualquier otra de tiempo) y en Tipo de columna pon Texto para que no te lo reinterprete como fecha rara.

    Luego pulsa Aceptar.
    Con eso la vista previa debe pasar de palabras sueltas en mil columnas a columnas limpias: artist | title | timestamp_iso | ...

    👉 Si aun así ves todo roto, abre el archivo en un editor y mira el separador real:

    Si ves ; entre campos, importa marcando Punto y coma (y desmarcando lo demás).

    Si ves ,, usa Coma como arriba.

---

## Arquitectura y tecnologías

* **Kotlin (Android)**: UI + lógica principal.
* **Chaquopy (Python)**: ejecución de scripts (`np_export.py`, `np_dedupe.py`, `np_download.py`).
* **`yt-dlp`**: búsqueda/descarga de audio.
* **`libsu`**: operaciones root.
* **SQLite**: base de datos de ASI.
* **Scoped Storage**: políticas de acceso en Android 10+.&#x20;

---

## Compilación

### Android Studio

* Abre el proyecto y **Sync**.
* **Build > Make Project** o **Run**.

### CLI

```bash
git clone <URL_DEL_REPOSITORIO>
cd NowPlayingExporterPy
./gradlew :app:assembleDebug
# APK en: app/build/outputs/apk/debug/app-debug.apk
```



---

## Contribuciones

¡Bienvenidas! Abre un *issue* o un *pull request* con tu propuesta.&#x20;

## Licencia

**GPL-3.0**. Consulta el archivo `LICENSE` para más detalles.&#x20;

---
