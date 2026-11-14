package org.pieevals.phonebench.engines

import android.content.Context

/** Built without app/libs/mlc: mlc rows are declared_unsupported with this reason. */
object MlcFactory {
    const val REASON = "MLC LLM not built into this APK (no mlc4j + compiled model libraries in app/libs/mlc at build time)"
    fun create(context: Context): BenchEngine = UnavailableEngine("mlc", REASON, "opencl")
}
