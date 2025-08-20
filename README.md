# NowPlayingExporterPy

![NowPlayingExporterPy (1)](https://github.com/user-attachments/assets/162df03c-33f2-4275-89f1-eebd064d7c77)


Exporta el historial de **Now Playing / Está sonando** (Android System Intelligence) a **CSV** directamente desde Android.  
Incluye **deduplicación opcional** (por intervalos de tiempo) para eliminar líneas repetidas en y **compartir** el CSV generado.

> **Requiere root.** La base de datos de ASI es privada del sistema y no es accesible sin privilegios elevados (root).

---

## Características
- ✅ Exportación a **CSV** en `Descargas` (vía MediaStore).
- ✅ **Deduplicación** por ventanas de tiempo (p. ej., 10 min).
- ✅ **Compartir** el CSV desde la app.
- ✅ UI Material minimalista, modo oscuro.
- ✅ Reutiliza scripts Python (Chaquopy) para la lógica de export/dedupe.

---

## Cómo funciona (resumen técnico)
1. **Root** (libsu) copia la base de datos privada de ASI (`history_db`) a la sandbox de la app.
   - Rutas candidatas (ejemplos):  
     ```
     /data/data/com.google.android.as/databases/history_db
     /data/user_de/0/com.google.android.as/databases/history_db
     /data/data/com.google.android.as.oss/databases/history_db
     ...
     ```
2. **Chaquopy** ejecuta `np_export.py` para leer SQLite y generar el **CSV** temporal.
3. (Opcional) `np_dedupe.py` aplica **deduplicación** por tiempo.
4. La app mueve el CSV final a **Descargas** con nombre `now_playing_export_YYYYMMDD_HHMMSS[_dedup].csv`.
5. Botón/acción para **compartir** el CSV (intent estándar).

---

## Requisitos
- Probado en Andorid 16 en Pixel usando KernelSU Next con ASI → ✅ funciona.
- Esperado (no verificado): Android 12–15 en Pixel con ASI debería funcionar (las rutas de la DB suelen ser alguna de estas, previamente mencionadas en el punto 1:

    /data/data/com.google.android.as/databases/history_db,
    /data/user_de/0/com.google.android.as/databases/history_db,
    /data/data/com.google.android.as.oss/databases/history_db),

   pero no garantizado. 

- **Root** (Magisk, KernelSU/KSU Next, aPatch).
- Android System Intelligence (o equivalente) instalado.
- Android Studio (Arctic Fox+), JDK 17+.

---

## Compilación
### Opción Android Studio
- Abrir el proyecto.
- **Build > Make Project** o **Run**.

### Opción CLI
```bash
./gradlew :app:assembleDebug
# o
./gradlew :app:assembleRelease

