# NowPlayingExporterPy

![NowPlayingExporterPy (1)](https://github.com/user-attachments/assets/162df03c-33f2-4275-89f1-eebd064d7c77)

Exports the **Now Playing** history (Android System Intelligence, ASI) from Google Pixel devices to **CSV**, and adds a function to **download the songs** listed in that history (via `yt-dlp`) to the app's storage. Designed and built as a **Project-Based Learning (PBL)** project.

> **⚠️ Requires root.** The ASI database is private to the system. Grant superuser permissions (Magisk / KernelSU / aPatch) before using it. To browse the resulting files, a root manager may be required.

---

## Features

* ✅ CSV export of "Now Playing" history.
* ✅ Smart deduplication (time windows) to clean up duplicates and "false repeats."
* ✅ Download songs from CSV with `yt-dlp` to the app's private directory (no storage permissions required).
* ✅ Minimalist UI with real-time progress feedback.

---

## 📁 Paths and Formats

* **ASI DB** (common examples):

```
/data/data/com.google.android.as/databases/history_db
/data/user_de/0/com.google.android.as/databases/history_db
/data/data/com.google.android.as.oss/databases/history_db
```
* **CSV Output**: in `Downloads` (MediaStore) with the name `now_playing_export_YYYYMMDD_HHMMSS[_dedup].csv`.
* **Audio Downloads** (with `yt-dlp`):

```
/Android/data/com.d4vram.nowplayingexporterpy/files/Music/NPEpy_download_songs/
```

Typical format: `.webm` (no FFmpeg post-processing). To listen to them on your player, **move/copy** them to `/sdcard/Music/`.&#x20;

---

## 🚀🔍 How it works (technical summary)

1. **Root (libsu)** copies `history_db` from ASI to the app sandbox.
2. **Chaquopy (Python)** runs `np_export.py` to read SQLite and generate the temporary **CSV**.
3. (Optional) `np_dedupe.py` applies **deduplication** per time window.
4. The app saves the final CSV in **Downloads** and offers **sharing** via standard intent.
5. With the CSV ready, **yt-dlp** searches for and downloads the audio files to the app's private folder.

---

## 📋 Requirements

* **Root** (Magisk / KernelSU Next / aPatch).
* **ASI** installed (Android System Intelligence).
* Tested on **Android 16** (Pixel with KernelSU Next). Android **12–15** compatibility expected on Pixel (not guaranteed).

---

## Lessons learned ✍️ (issues → solutions)

1. **FFmpeg & `yt-dlp`**: Chaquopy does not provide FFmpeg via pip. `yt-dlp` can download native audio (`.webm`) **without FFmpeg**, so the false dependency was removed and “best audio” was configured.
2. **Real-time progress**: Added a `PythonCallback` interface from Kotlin to receive logs/status from the Python script and display them in the UI.
3. **DNS/intermittent network**: In addition to declaring `android.permission.INTERNET`, **retries** with pauses and a “long pause” after N downloads were implemented.
4. **Scoped Storage (API 29+)**: Writing to public `Music` results in `Operation not permitted`. Workaround: **Use private app storage** in `/Android/data/.../files/` (no permissions required on Android 10+).

---

## 🚀 Usage

1. **Install** the APK.
2. **Grant root** when prompted.
3. Click **Export** to generate the CSV of the history.
4. (Optional, recommended) Enable **Deduplication**.
5. Click **Download songs** to populate `NPEpy_download_songs/`.

> **Important tip for good readability**: Open the CSV in a spreadsheet without breaking columns

> To prevent your titles from being "chopped up" by spaces, click exactly this:

In Separator Options

✅ Comma

⛔ Space → UNCHECK

⛔ Semicolon → UNCHECK

⛔ Tab → UNCHECK (leave it alone if your file has tabs)

In String Delimiter → choose " (double quotes).

Character Set → Unicode (UTF-8) (as you already have).

(Recommended) In the preview, click on the header of the timestamp_iso column (and any other time column) and set the Column Type to Text so it doesn't reinterpret it as a strange date.

Then click OK.
With that, the preview should go from single words in a thousand columns to clean columns: artist | title | timestamp_iso | ...

👉 If everything still looks broken, open the file in an editor and look at the actual separator:

If you see ; between fields, import by selecting a semicolon (and unselecting the rest).

If you see ,, use a comma as above.

---

## ⚙️ Architecture and Technologies

* **Kotlin (Android)**: UI + main logic.
* **Chaquopy (Python)**: script execution (`np_export.py`, `np_dedupe.py`, `np_download.py`).
* **`yt-dlp`**: audio search/download.
* **`libsu`**: root operations.
* **SQLite**: ASI database.
* **Scoped Storage**: access policies on Android 10+.

---

## 🛠️ Build

### Android Studio

* Open the project and **Sync**.
* **Build > Make Project** or **Run**.

### ⌨️ CLI

```bash
git clone <URL_REPO>
cd NowPlayingExporterPy
./gradlew :app:assembleDebug
# APK in: app/build/outputs/apk/debug/app-debug.apk
