package org.pieevals.phonebench

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.util.Base64
import androidx.core.content.FileProvider
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.GZIPOutputStream

object Results {
    fun file(context: Context): File = context.filesDir.resolve("records.jsonl")

    /** POST records.jsonl to <url>/v1/results; returns "HTTP <code>: <body>". */
    fun send(context: Context, baseUrl: String, token: String): String {
        val f = file(context)
        if (!f.exists() || f.length() == 0L) return "no records.jsonl yet"
        val c = URL(baseUrl.trimEnd('/') + "/v1/results").openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.doOutput = true
        c.connectTimeout = 15000
        c.readTimeout = 60000
        c.setRequestProperty("Content-Type", "application/x-ndjson")
        if (token.isNotBlank()) c.setRequestProperty("Authorization", "Bearer ${token.trim()}")
        c.outputStream.use { it.write(f.readBytes()) }
        val code = c.responseCode
        val body = (if (code < 400) c.inputStream else c.errorStream)?.bufferedReader()?.use { it.readText() } ?: ""
        c.disconnect()
        return "HTTP $code: $body"
    }

    fun share(context: Context) {
        val f = file(context)
        val uri = FileProvider.getUriForFile(context, context.packageName + ".files", f)
        val send = Intent(Intent.ACTION_SEND).apply {
            type = "application/x-ndjson"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, "pie-evals phone records.jsonl")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(send, "Share records.jsonl").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    /** gzip + base64 of records.jsonl on the clipboard (to paste into a workflow input). */
    fun copyForWorkflow(context: Context): Int {
        val bytes = file(context).takeIf { it.exists() }?.readBytes() ?: ByteArray(0)
        val bo = ByteArrayOutputStream()
        GZIPOutputStream(bo).use { it.write(bytes) }
        val b64 = Base64.encodeToString(bo.toByteArray(), Base64.NO_WRAP)
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("records.jsonl.gz.b64", b64))
        return b64.length
    }
}
