package org.pieevals.phonebench

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val scripted = BuildConfig.DEBUG && intent?.hasExtra("engines") == true
        if (!scripted && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        handleDebugIntent(intent)
        setContent { MaterialTheme(colorScheme = darkColorScheme()) { Surface(Modifier.fillMaxSize()) { Screen() } } }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleDebugIntent(intent)
    }

    /**
     * Debug-only scripted run, no UI clicks:
     * am start -n org.pieevals.phonebench/.MainActivity --es engines llamacpp --es models qwen3.5-0.8b-llamacpp
     *   --es workloads raw-512-256 --es tag test-phone-e2e --ez send true --es url http://127.0.0.1:8787 --es token T
     * models: site model ids or artifact ids, comma separated.
     */
    private fun handleDebugIntent(i: Intent?) {
        if (!BuildConfig.DEBUG || i == null || !i.hasExtra("engines")) return
        val engines = i.getStringExtra("engines")!!.split(",").map { it.trim() }.filter { it.isNotEmpty() }
        val models = (i.getStringExtra("models") ?: "").split(",").map { it.trim() }.filter { it.isNotEmpty() }
            .map { Catalog.byId(it)?.model ?: it }.distinct()
        val workloads = (i.getStringExtra("workloads") ?: "raw-512-256,c4,pf4-512").split(",").map { it.trim() }
        val p = prefs(this)
        val cfg = RunConfig(
            engines = engines, models = models, workloads = workloads,
            tag = i.getStringExtra("tag") ?: p.getString("tag", null),
            litertGpu = i.getStringExtra("litert_backend")?.let { it != "cpu" } ?: p.getBoolean("litert_gpu", true),
            llamaGpu = i.getStringExtra("llama_backend")?.let { it != "cpu" } ?: p.getBoolean("llama_gpu", false),
            threads = i.getIntExtra("threads", p.getString("threads", "0")!!.toIntOrNull() ?: 0),
            download = i.getBooleanExtra("download", true),
            send = i.getBooleanExtra("send", false),
            url = i.getStringExtra("url") ?: p.getString("url", DEFAULT_URL)!!,
            token = i.getStringExtra("token") ?: p.getString("token", "")!!,
        )
        BenchState.say("debug intent: $cfg".replace(cfg.token.ifEmpty { "\u0000" }, "***"))
        BenchService.start(this, cfg)
    }

    companion object {
        const val DEFAULT_URL = "http://100.85.194.44:8787"
        fun prefs(c: Context) = c.getSharedPreferences("bench", Context.MODE_PRIVATE)
    }
}

@Composable
private fun Screen() {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val act = ctx as ComponentActivity
    val p = remember { MainActivity.prefs(ctx) }
    val scope = rememberCoroutineScope()
    val store = remember { ModelStore(ctx) }
    val running by BenchState.running.collectAsState()
    val log by BenchState.log.collectAsState()
    val progress by BenchState.progress.collectAsState()
    val results by BenchState.results.collectAsState()
    val reply by BenchState.lastReply.collectAsState()
    var device by remember { mutableStateOf("") }
    val engines = remember { mutableStateListOf(*(p.getString("engines", "llamacpp,litert,mlc,pie")!!.split(",").filter { it.isNotEmpty() }.toTypedArray())) }
    val models = remember { mutableStateListOf(*(p.getString("models", "qwen3.5-0.8b")!!.split(",").filter { it.isNotEmpty() }.toTypedArray())) }
    val wls = remember { mutableStateListOf(*(p.getString("workloads", "raw-512-256,c4,pf4-512")!!.split(",").filter { it.isNotEmpty() }.toTypedArray())) }
    var url by remember { mutableStateOf(p.getString("url", MainActivity.DEFAULT_URL)!!) }
    var token by remember { mutableStateOf(p.getString("token", "")!!) }
    var tag by remember { mutableStateOf(p.getString("tag", "")!!) }
    var threads by remember { mutableStateOf(p.getString("threads", "0")!!) }
    var litertGpu by remember { mutableStateOf(p.getBoolean("litert_gpu", true)) }
    var llamaGpu by remember { mutableStateOf(p.getBoolean("llama_gpu", false)) }
    var status by remember { mutableStateOf("") }
    var sizes by remember { mutableStateOf(mapOf<String, Long>()) }
    var importFor by remember { mutableStateOf<Artifact?>(null) }
    var refresh by remember { mutableStateOf(0) }

    LaunchedEffect(Unit) { device = withContext(Dispatchers.IO) { DeviceInfo.summary(ctx) } }
    LaunchedEffect(running) {
        if (running) act.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        else act.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        refresh++
    }
    fun save() {
        p.edit().putString("engines", engines.joinToString(",")).putString("models", models.joinToString(","))
            .putString("workloads", wls.joinToString(",")).putString("url", url).putString("token", token)
            .putString("tag", tag).putString("threads", threads).putBoolean("litert_gpu", litertGpu).putBoolean("llama_gpu", llamaGpu).apply()
    }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        val a = importFor ?: return@rememberLauncherForActivityResult
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch(Dispatchers.IO) {
            runCatching { store.importFile(a, uri, !litertGpu) { f, d, _ -> BenchState.progress.value = "import $f %.0f MiB".format(d / 1048576.0) } }
                .onSuccess { BenchState.say("${a.id}: imported ${it.path}") }.onFailure { BenchState.say("${a.id}: import failed: $it") }
            BenchState.progress.value = ""
            refresh++
        }
    }

    LazyColumn(Modifier.fillMaxSize().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        item { Text("pie-evals phone · ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.titleLarge) }
        item { Text(device, fontSize = 12.sp) }
        item { Section("Engines") }
        item {
            Column {
                Catalog.engines.forEach { e ->
                    val note = when (e) {
                        "llamacpp" -> "llama.cpp ${BuildConfig.LLAMA_CPP_TAG} (CPU${if (BuildConfig.LLAMA_GPU == "none") "" else " or " + BuildConfig.LLAMA_GPU})"
                        "litert" -> "LiteRT-LM ${org.pieevals.phonebench.engines.LiteRtEngine.LITERTLM_VERSION}"
                        "mlc" -> if (BuildConfig.HAS_MLC) "MLC LLM (OpenCL)" else "MLC LLM (not in this build)"
                        else -> if (BuildConfig.HAS_PIE) "pie (Vulkan)" else "pie (not in this build)"
                    }
                    Check(note, e in engines) { if (it) engines.add(e) else engines.remove(e); save() }
                }
            }
        }
        item { Section("Models") }
        item { Column { Catalog.models.forEach { m -> Check(m, m in models) { if (it) models.add(m) else models.remove(m); save() } } } }
        item { Section("Workloads") }
        item {
            Row { listOf("raw-512-256", "c4", "pf4-512").forEach { w -> Check(w, w in wls) { if (it) wls.add(w) else wls.remove(w); save() } } }
        }
        item { Section("Model files") }
        val arts = Catalog.artifacts.filter { it.engine in engines && it.model in models }
        items(arts, key = { it.id + refresh }) { a ->
            val local = store.local(a, a.engine == "litert" && !litertGpu)
            val sz = sizes[a.id] ?: a.approxBytes
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(a.id, fontSize = 13.sp)
                    Text("${a.format} · ~%.2f GB · %s".format(sz / 1e9, if (local != null) "on device" else "not downloaded"), fontSize = 11.sp)
                }
                if (local == null && a.engine in listOf("llamacpp", "litert", "pie")) {
                    OutlinedButton(enabled = !running, onClick = { importFor = a; picker.launch(arrayOf("*/*")) }) { Text("File", fontSize = 11.sp) }
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedButton(onClick = {
                    scope.launch(Dispatchers.IO) {
                        sizes = arts.associate { a -> a.id to (store.remoteSize(a, a.engine == "litert" && !litertGpu) ?: a.approxBytes) }
                    }
                }) { Text("Check sizes") }
                OutlinedButton(enabled = !running, onClick = {
                    scope.launch(Dispatchers.IO) {
                        for (a in arts) {
                            if (a.engine in listOf("mlc", "pie") && !(if (a.engine == "mlc") BuildConfig.HAS_MLC else BuildConfig.HAS_PIE)) continue
                            if (store.local(a, a.engine == "litert" && !litertGpu) != null) continue
                            BenchState.say("${a.id}: downloading")
                            runCatching { store.download(a, a.engine == "litert" && !litertGpu, { f, d, t -> BenchState.progress.value = "download $f %.0f / %.0f MiB".format(d / 1048576.0, t / 1048576.0) }, { BenchState.cancel }) }
                                .onSuccess { BenchState.say("${a.id}: downloaded (${it.bytes} bytes, rev ${it.revision})") }
                                .onFailure { BenchState.say("${a.id}: download failed: ${it.message}") }
                            refresh++
                        }
                        BenchState.progress.value = ""
                    }
                }) { Text("Download selected") }
            }
        }
        item { Section("Settings") }
        item { OutlinedTextField(url, { url = it; save() }, label = { Text("Ingest URL") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
        item { OutlinedTextField(token, { token = it; save() }, label = { Text("Token") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
        item { OutlinedTextField(tag, { tag = it; save() }, label = { Text("Tag (empty = server default)") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(threads, { threads = it; save() }, label = { Text("CPU threads (0 = auto ${DeviceInfo.defaultThreads()})") }, singleLine = true, modifier = Modifier.weight(1f))
                Spacer(Modifier.width(8.dp))
                Check("LiteRT GPU", litertGpu) { litertGpu = it; save(); refresh++ }
                if (BuildConfig.LLAMA_GPU != "none") Check("llama.cpp ${BuildConfig.LLAMA_GPU}", llamaGpu) { llamaGpu = it; save() }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Button(enabled = !running && engines.isNotEmpty() && models.isNotEmpty() && wls.isNotEmpty(), onClick = {
                    save()
                    BenchService.start(ctx, RunConfig(engines.toList(), models.toList(), wls.toList(), tag.ifBlank { null }, litertGpu, llamaGpu, threads.toIntOrNull() ?: 0))
                }) { Text("Run") }
                OutlinedButton(enabled = running, onClick = { BenchState.cancel = true; BenchState.say("cancel requested") }) { Text("Stop") }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedButton(enabled = !running, onClick = {
                    status = "sending…"
                    scope.launch(Dispatchers.IO) {
                        val r = runCatching { Results.send(ctx, url, token) }.getOrElse { "send failed: $it" }
                        BenchState.lastReply.value = r
                        status = ""
                    }
                }) { Text("Send") }
                OutlinedButton(onClick = { runCatching { Results.share(ctx) }.onFailure { status = "share failed: $it" } }) { Text("Share records.jsonl") }
                OutlinedButton(onClick = { status = "copied ${Results.copyForWorkflow(ctx)} chars (gzip+base64)" }) { Text("Copy for workflow") }
            }
        }
        if (status.isNotEmpty()) item { Text(status, fontSize = 12.sp) }
        if (reply.isNotEmpty()) item { Text("Server: $reply", fontSize = 12.sp, fontFamily = FontFamily.Monospace) }
        if (progress.isNotEmpty()) item { Text(progress, fontSize = 12.sp, color = MaterialTheme.colorScheme.primary) }
        item { Section("Results (local, display only)") }
        item { Text("engine  artifact  workload  status  decode tok/s  prefill tok/s  TTFT s  peak GiB", fontSize = 11.sp, fontFamily = FontFamily.Monospace) }
        items(results) { r ->
            Text(
                "%s  %s  %s  %s  %s  %s  %s  %s%s".format(r.engine, r.artifact, r.workload, r.status,
                    r.decodeTokS?.let { "%.1f".format(it) } ?: "-", r.prefillTokS?.let { "%.1f".format(it) } ?: "-",
                    r.ttftS?.let { "%.3f".format(it) } ?: "-", r.peakGib?.let { "%.2f".format(it) } ?: "-",
                    r.error?.let { "  ($it)" } ?: ""),
                fontSize = 11.sp, fontFamily = FontFamily.Monospace,
            )
        }
        item { Section("Log") }
        items(log.reversed().take(200)) { Text(it, fontSize = 10.sp, fontFamily = FontFamily.Monospace) }
        item { Spacer(Modifier.height(40.dp)) }
    }
}

@Composable
private fun Section(t: String) {
    Column { Spacer(Modifier.height(6.dp)); HorizontalDivider(); Text(t, style = MaterialTheme.typography.titleMedium) }
}

@Composable
private fun Check(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Checkbox(checked, onChange)
        Text(label, fontSize = 13.sp)
    }
}
