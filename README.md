# Now Playing Exporter (Python inside APK)

App Android que **integra tu script de exportación en Python** para extraer el historial de *Now Playing* (Android System Intelligence) y guardarlo como **CSV** en `Descargas`. Dedupe opcional.

- Lógica Python basada en tu [`nowplaying_export.py`] y [`dedupe_nowplaying.py`]. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}
- La copia desde `/data/data/...` se hace con **root** (libsu) y la APK **no requiere Termux**.

## Requisitos

- Android 9+ (minSdk 28).
- Dispositivo **rooteado** (Magisk, KernelSU, KSU Next o aPatch).
- *Now Playing* activo (`com.google.android.as` o `.as.oss`).

> **Sin root no es posible**: la DB está en `/data/data/...`. Shizuku sin root no da acceso a esa ruta.

## Cómo compilar

1. Clona el repo y ábrelo en Android Studio (AGP 8.5, Kotlin 1.9).
2. Sincroniza Gradle. No hay dependencias pip.
3. Conecta el Pixel rooteado y pulsa *Run*.

## Uso

1. Abre **Now Playing Exporter**.
2. Verás *Root OK*. Pulsa **Exportar**.
3. Opcional: marca **Deduplicar (10 min)** para eliminar repeticiones cercanas.
4. El archivo se guarda en **Descargas** como `now_playing_export_YYYYMMDD_HHMMSS.csv` (o `_dedup_10min.csv`).
5. Usa **Compartir** para enviarlo.

## ¿Qué hace internamente?

1. **RootHelper** copia la DB `history_db` desde rutas conocidas a `cacheDir/np_history.db`.
2. Kotlin llama al módulo Python `np_export.export_csv(db, tmpCsv)` que:
    - Detecta tablas/columnas y extrae `artist`, `title`, `timestamp` (convierte a ISO UTC).
    - Usa `display` como *fallback* si faltan artista/título.
3. Si está activado, llama a `np_dedupe.dedupe_csv(tmpCsv, dedupCsv, 10)`.
4. Mueve el CSV a **Descargas** usando **MediaStore**.
5. La app nunca sube datos: todo es **local**.

## Rutas de DB buscadas

- `/data/data/com.google.android.as/databases/history_db`
- `/data/user_de/0/com.google.android.as/databases/history_db`
- `/data/data/com.google.android.as.oss/databases/history_db`
- `/data/user_de/0/com.google.android.as.oss/databases/history_db`
- `/data/data/com.google.intelligence.sense/databases/history_db`

## Licencia
MIT
