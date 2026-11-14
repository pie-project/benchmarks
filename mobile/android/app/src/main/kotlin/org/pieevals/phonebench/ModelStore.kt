package org.pieevals.phonebench

import android.content.Context
import android.net.Uri
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.io.RandomAccessFile
import java.net.HttpURLConnection
import java.net.URL

/** A model on disk: `path` is the file (GGUF, .litertlm, .zt) or the directory (MLC weights). */
data class LocalModel(val path: File, val repo: String, val file: String?, val revision: String?, val bytes: Long)

/**
 * Models live in <app files>/models/<artifact-id>/ (adb: push to /data/local/tmp, then run-as cp), with
 * meta.json {repo, file, revision, bytes}. Downloads come from Hugging Face with resume; the
 * revision is the X-Repo-Commit header of the resolve response.
 */
class ModelStore(private val context: Context) {
    /** Downloads go to internal storage (adb: `run-as org.pieevals.phonebench cp /data/local/tmp/... files/models/<id>/`). */
    val root: File = context.filesDir.resolve("models").apply { mkdirs() }
    /** Also searched: the app's external files dir. */
    private val external: File? = context.getExternalFilesDir(null)?.resolve("models")

    fun dir(a: Artifact) = root.resolve(a.id)

    fun local(a: Artifact, litertCpu: Boolean = false): LocalModel? =
        localIn(root.resolve(a.id), a, litertCpu) ?: external?.let { localIn(it.resolve(a.id), a, litertCpu) }

    fun fileFor(a: Artifact, litertCpu: Boolean): String? = if (a.engine == "litert" && litertCpu && a.cpuFile != null) a.cpuFile else a.file

    private fun localIn(d: File, a: Artifact, litertCpu: Boolean): LocalModel? {
        val meta = d.resolve("meta.json").takeIf { it.exists() }?.let { runCatching { JSONObject(it.readText()) }.getOrNull() }
        val file = fileFor(a, litertCpu)
        if (file != null) {
            val f = d.resolve(file)
            if (!f.isFile || f.length() == 0L) return null
            val m = meta?.optJSONObject(file)
            return LocalModel(f, m?.optString("repo") ?: a.repo, file, m?.optString("revision")?.ifEmpty { null }, f.length())
        }
        // whole-repo artifact: complete when meta.json lists it as done
        if (meta?.optBoolean("complete") != true) return null
        val path = meta.optString("path").takeIf { it.isNotEmpty() }?.let { d.resolve(it) } ?: d
        return LocalModel(path, meta.optString("repo", a.repo), null, meta.optString("revision").ifEmpty { null }, meta.optLong("bytes"))
    }

    private fun writeMeta(a: Artifact, update: (JSONObject) -> Unit) {
        val f = dir(a).resolve("meta.json")
        val j = f.takeIf { it.exists() }?.let { runCatching { JSONObject(it.readText()) }.getOrNull() } ?: JSONObject()
        update(j)
        f.writeText(j.toString(1))
    }

    /** Size of the file(s) from the HF API (null if offline). */
    fun remoteSize(a: Artifact, litertCpu: Boolean = false): Long? = runCatching {
        val sib = siblings(a.repo)
        val file = fileFor(a, litertCpu)
        if (file != null) sib.firstOrNull { it.first == file }?.second else sib.sumOf { it.second }
    }.getOrNull()

    private fun siblings(repo: String): List<Pair<String, Long>> {
        val c = URL("https://huggingface.co/api/models/$repo?blobs=true").openConnection() as HttpURLConnection
        c.connectTimeout = 15000
        c.readTimeout = 30000
        val j = JSONObject(c.inputStream.bufferedReader().use { it.readText() })
        val s = j.getJSONArray("siblings")
        return (0 until s.length()).map { s.getJSONObject(it).let { o -> o.getString("rfilename") to o.optLong("size") } }
    }

    fun download(a: Artifact, litertCpu: Boolean, progress: (String, Long, Long) -> Unit, cancelled: () -> Boolean): LocalModel {
        if (!Catalog.downloadable(a)) throw IOException("${a.id}: pie artifacts are not hosted; adb push ${a.file} or pick it with File")
        val d = dir(a).apply { mkdirs() }
        val file = fileFor(a, litertCpu)
        if (file != null) {
            val (bytes, rev) = fetch(a.repo, file, d.resolve(file), progress, cancelled)
            writeMeta(a) { it.put(file, JSONObject().put("repo", a.repo).put("file", file).put("revision", rev ?: JSONObject.NULL).put("bytes", bytes)) }
            return local(a, litertCpu)!!
        }
        val files = siblings(a.repo).filter { !it.first.startsWith(".") && it.first != "README.md" }
        var rev: String? = null
        var total = 0L
        for ((name, _) in files) {
            val (b, r) = fetch(a.repo, name, d.resolve(name), progress, cancelled)
            total += b
            rev = rev ?: r
        }
        writeMeta(a) { it.put("complete", true).put("repo", a.repo).put("revision", rev ?: JSONObject.NULL).put("bytes", total) }
        return local(a, litertCpu)!!
    }

    /** One file with HTTP Range resume; redirects followed by hand so the first X-Repo-Commit is kept. */
    private fun fetch(repo: String, name: String, dest: File, progress: (String, Long, Long) -> Unit, cancelled: () -> Boolean): Pair<Long, String?> {
        dest.parentFile?.mkdirs()
        val part = File(dest.path + ".part")
        val revFile = File(dest.path + ".rev")
        if (dest.exists() && dest.length() > 0) return dest.length() to revFile.takeIf { it.exists() }?.readText()
        var url = URL("https://huggingface.co/$repo/resolve/main/$name")
        var rev: String? = null
        var hops = 0
        while (true) {
            val have = if (part.exists()) part.length() else 0L
            val c = url.openConnection() as HttpURLConnection
            c.instanceFollowRedirects = false
            c.connectTimeout = 20000
            c.readTimeout = 60000
            if (have > 0) c.setRequestProperty("Range", "bytes=$have-")
            val code = c.responseCode
            c.getHeaderField("X-Repo-Commit")?.let { if (rev == null) rev = it }
            if (code in 300..399) {
                url = URL(url, c.getHeaderField("Location"))
                c.disconnect()
                if (++hops > 10) throw IOException("too many redirects")
                continue
            }
            if (code == 416 && have > 0) { // already complete
                c.disconnect()
                break
            }
            if (code != 200 && code != 206) throw IOException("HTTP $code for $repo/$name")
            val append = code == 206
            val total = (c.getHeaderField("Content-Range")?.substringAfter('/')?.toLongOrNull()) ?: (c.contentLengthLong.takeIf { it > 0 }?.plus(if (append) have else 0))
            RandomAccessFile(part, "rw").use { raf ->
                if (!append) raf.setLength(0)
                raf.seek(raf.length())
                var done = raf.length()
                val buf = ByteArray(1 shl 20)
                var lastReport = 0L
                c.inputStream.use { ins ->
                    while (true) {
                        if (cancelled()) throw IOException("download cancelled")
                        val n = ins.read(buf)
                        if (n < 0) break
                        raf.write(buf, 0, n)
                        done += n
                        if (done - lastReport > (8 shl 20)) { progress(name, done, total ?: -1); lastReport = done }
                    }
                }
                progress(name, done, total ?: done)
            }
            c.disconnect()
            break
        }
        if (!part.renameTo(dest)) throw IOException("rename failed for $dest")
        rev?.let { revFile.writeText(it) }
        return dest.length() to rev
    }

    /** Copy a user-picked local file in as this artifact's model (revision unknown). */
    fun importFile(a: Artifact, uri: Uri, litertCpu: Boolean, progress: (String, Long, Long) -> Unit): LocalModel {
        val file = fileFor(a, litertCpu) ?: throw IOException("${a.id} is a directory artifact; push the directory with adb instead")
        val d = dir(a).apply { mkdirs() }
        val dest = d.resolve(file)
        val tmp = File(dest.path + ".part")
        context.contentResolver.openInputStream(uri)!!.use { ins ->
            tmp.outputStream().use { out ->
                val buf = ByteArray(1 shl 20)
                var done = 0L
                while (true) {
                    val n = ins.read(buf)
                    if (n < 0) break
                    out.write(buf, 0, n)
                    done += n
                    if (done % (64 shl 20) < buf.size) progress(file, done, -1)
                }
            }
        }
        tmp.renameTo(dest)
        writeMeta(a) { it.put(file, JSONObject().put("repo", a.repo).put("file", file).put("revision", "local-file").put("bytes", dest.length())) }
        return local(a, litertCpu)!!
    }
}
