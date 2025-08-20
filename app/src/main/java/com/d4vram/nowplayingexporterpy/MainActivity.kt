package com.d4vram.np.exporter

import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var tvStatus: TextView
    private lateinit var tvLog: TextView
    private lateinit var btnExport: Button
    private lateinit var btnShare: Button
    private lateinit var cbDedupe: CheckBox

    private var lastCsvUri: Uri? = null
    private var lastCsvName: String? = null

    private val candidates = listOf(
        "/data/data/com.google.android.as/databases/history_db",
        "/data/user_de/0/com.google.android.as/databases/history_db",
        "/data/data/com.google.android.as.oss/databases/history_db",
        "/data/user_de/0/com.google.android.as.oss/databases/history_db",
        "/data/data/com.google.intelligence.sense/databases/history_db"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvStatus = findViewById(R.id.tvStatus)
        tvLog = findViewById(R.id.tvLog)
        btnExport = findViewById(R.id.btnExport)
        btnShare = findViewById(R.id.btnShare)
        cbDedupe = findViewById(R.id.cbDedupe)

        RootHelper.init()

        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        if (!RootHelper.isRootAvailable()) {
            tvStatus.text = "Root NO disponible. Esta app requiere root para leer la DB privada de Android System Intelligence."
            btnExport.isEnabled = false
            Toast.makeText(this, "Root no detectado", Toast.LENGTH_LONG).show()
            return
        }

        tvStatus.text = "Root OK. Pulsa Exportar para generar el CSV en Descargas."

        btnExport.setOnClickListener { doExport() }
        btnShare.setOnClickListener { shareCsv() }
    }

    private fun doExport() {
        runCatching {
            log("Buscando DB de Now Playing…")
            val src = RootHelper.findFirstExistingPath(candidates)
                ?: error("No se encontró la DB en rutas conocidas.")

            // Copiar a caché legible por la app
            val localDb = File(cacheDir, "np_history.db").absolutePath
            if (!RootHelper.copyFileAsRoot(src, localDb)) error("Falló la copia con root.")
            log("DB copiada a sandbox.")

            // Salida temporal en caché (luego movemos a Descargas)
            val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
            val tmpCsv = File(cacheDir, "now_playing_export_${stamp}.csv").absolutePath

            // Llamar a Python: exportar
            val py = Python.getInstance()
            val mod = py.getModule("np_export")
            val rows = mod.callAttr("export_csv", localDb, tmpCsv).toInt()
            log("Exportadas $rows filas a temporal.")

            var finalCsvPath = tmpCsv

            if (cbDedupe.isChecked) {
                val dedupPath = File(cacheDir, "now_playing_export_${stamp}_dedup_10min.csv").absolutePath
                py.getModule("np_dedupe")
                    .callAttr("dedupe_csv", tmpCsv, dedupPath, 10, false)
                log("Deduplicación 10 min aplicada.")
                finalCsvPath = dedupPath
            }

            // Mover a Descargas (MediaStore)
            val nameOnly = File(finalCsvPath).name
            val uri = insertIntoDownloads(nameOnly, "text/csv")
            contentResolver.openOutputStream(uri)!!.use { out ->
                File(finalCsvPath).inputStream().use { it.copyTo(out) }
            }
            lastCsvUri = uri
            lastCsvName = nameOnly

            tvStatus.text = "Exportación completada: $nameOnly (Descargas)"
            Toast.makeText(this, "Listo: $nameOnly", Toast.LENGTH_LONG).show()
            log("Guardado en Descargas como $nameOnly")

        }.onFailure { e ->
            val msg = "Error: ${e.message}"
            tvStatus.text = msg
            log(msg)
        }
    }

    private fun insertIntoDownloads(name: String, mime: String): Uri {
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, name)
            put(MediaStore.Downloads.MIME_TYPE, mime)
            put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
        }
        return contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            ?: error("No se pudo crear el archivo en Descargas")
    }

    private fun shareCsv() {
        val uri = lastCsvUri ?: run {
            Toast.makeText(this, "Primero exporta un CSV.", Toast.LENGTH_SHORT).show()
            return
        }
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/csv"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, "Compartir CSV"))
    }

    private fun log(msg: String) { tvLog.append(msg + "\n") }
}
