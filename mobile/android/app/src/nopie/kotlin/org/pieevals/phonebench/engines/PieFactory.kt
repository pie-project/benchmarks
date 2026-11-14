package org.pieevals.phonebench.engines

import android.content.Context

/** Built without app/libs/pie: pie rows are declared_unsupported with this reason. */
object PieFactory {
    const val PIE_COMMIT = "a6547509432d48c76e258bfefbb85bd58984f8e4"
    const val REASON = "pie Android engine not built into this APK (no pie AAR in app/libs/pie at build time)"
    fun create(context: Context): BenchEngine = UnavailableEngine("pie", REASON, "vulkan", version = PIE_COMMIT)
}
