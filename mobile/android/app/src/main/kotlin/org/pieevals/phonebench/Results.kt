package org.pieevals.phonebench

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

object Results {
    fun file(context: Context): File = context.filesDir.resolve("records.jsonl")

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
}
