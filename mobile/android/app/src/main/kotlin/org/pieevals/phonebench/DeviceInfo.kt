package org.pieevals.phonebench

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.GLES20
import android.os.BatteryManager
import android.os.Build
import android.os.PowerManager
import org.json.JSONObject
import java.io.File

object DeviceInfo {
    private var gpuName: String? = null
    private var gpuQueried = false

    fun thermal(context: Context): String {
        val pm = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        return when (pm.currentThermalStatus) {
            PowerManager.THERMAL_STATUS_NONE -> "NONE"
            PowerManager.THERMAL_STATUS_LIGHT -> "LIGHT"
            PowerManager.THERMAL_STATUS_MODERATE -> "MODERATE"
            PowerManager.THERMAL_STATUS_SEVERE -> "SEVERE"
            PowerManager.THERMAL_STATUS_CRITICAL -> "CRITICAL"
            PowerManager.THERMAL_STATUS_EMERGENCY -> "EMERGENCY"
            PowerManager.THERMAL_STATUS_SHUTDOWN -> "SHUTDOWN"
            else -> "UNKNOWN"
        }
    }

    fun battery(context: Context): Pair<Int, Boolean> {
        val i = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = i?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = i?.getIntExtra(BatteryManager.EXTRA_SCALE, 100) ?: 100
        val status = i?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
        return Pair(if (level >= 0 && scale > 0) level * 100 / scale else -1, charging)
    }

    fun totalRamBytes(context: Context): Long {
        val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        return ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }.totalMem
    }

    fun isEmulator(): Boolean =
        Build.FINGERPRINT.contains("generic") || Build.FINGERPRINT.contains("emulator") ||
            Build.HARDWARE.contains("ranchu") || Build.HARDWARE.contains("goldfish") ||
            Build.PRODUCT.contains("sdk") || Build.MODEL.contains("Emulator") || Build.MODEL.contains("Android SDK")

    /** GL_RENDERER from a throwaway offscreen EGL context (cheap, once). */
    @Synchronized
    fun gpu(): String? {
        if (gpuQueried) return gpuName
        gpuQueried = true
        gpuName = runCatching {
            val dpy = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
            val v = IntArray(2)
            EGL14.eglInitialize(dpy, v, 0, v, 1)
            val attrs = intArrayOf(EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT, EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT, EGL14.EGL_NONE)
            val cfgs = arrayOfNulls<EGLConfig>(1)
            val n = IntArray(1)
            EGL14.eglChooseConfig(dpy, attrs, 0, cfgs, 0, 1, n, 0)
            val ctx = EGL14.eglCreateContext(dpy, cfgs[0], EGL14.EGL_NO_CONTEXT, intArrayOf(EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE), 0)
            val surf = EGL14.eglCreatePbufferSurface(dpy, cfgs[0], intArrayOf(EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE), 0)
            EGL14.eglMakeCurrent(dpy, surf, surf, ctx)
            val r = GLES20.glGetString(GLES20.GL_RENDERER)
            EGL14.eglMakeCurrent(dpy, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT)
            EGL14.eglDestroySurface(dpy, surf)
            EGL14.eglDestroyContext(dpy, ctx)
            EGL14.eglTerminate(dpy)
            r
        }.getOrNull()
        return gpuName
    }

    /** Cores whose max frequency is within 70% of the fastest (the performance cluster(s)). */
    fun defaultThreads(): Int {
        val cores = Runtime.getRuntime().availableProcessors()
        val freqs = (0 until cores).mapNotNull { File("/sys/devices/system/cpu/cpu$it/cpufreq/cpuinfo_max_freq").takeIf { f -> f.canRead() }?.readText()?.trim()?.toLongOrNull() }
        if (freqs.size != cores || freqs.isEmpty()) return minOf(4, cores).coerceAtLeast(1)
        val top = freqs.max()
        return freqs.count { it >= top * 0.7 }.coerceIn(2, 8).coerceAtMost(cores)
    }

    fun json(context: Context, thermalStart: String, thermalEnd: String): JSONObject {
        val (pct, charging) = battery(context)
        return JSONObject()
            .put("os", "android")
            .put("os_version", "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
            .put("manufacturer", Build.MANUFACTURER)
            .put("model", Build.MODEL)
            .put("device", Build.DEVICE)
            .put("soc", if (Build.VERSION.SDK_INT >= 31) Build.SOC_MODEL else JSONObject.NULL)
            .put("soc_vendor", if (Build.VERSION.SDK_INT >= 31) Build.SOC_MANUFACTURER else JSONObject.NULL)
            .put("gpu", gpu() ?: JSONObject.NULL)
            .put("ram_gib", totalRamBytes(context) / GIB)
            .put("cpu_cores", Runtime.getRuntime().availableProcessors())
            .put("abi", Build.SUPPORTED_ABIS.firstOrNull() ?: "arm64-v8a")
            .put("emulator", isEmulator())
            .put("thermal_start", thermalStart)
            .put("thermal_end", thermalEnd)
            .put("battery_pct", pct)
            .put("charging", charging)
    }

    fun summary(context: Context): String {
        val (pct, charging) = battery(context)
        return buildString {
            append("${Build.MANUFACTURER} ${Build.MODEL} (${Build.DEVICE})\n")
            append("Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
            if (Build.VERSION.SDK_INT >= 31) append(" · SoC ${Build.SOC_MANUFACTURER} ${Build.SOC_MODEL}")
            append("\nGPU ${gpu() ?: "?"} · RAM %.1f GiB · %d cores · %s".format(totalRamBytes(context) / GIB, Runtime.getRuntime().availableProcessors(), Build.SUPPORTED_ABIS.firstOrNull()))
            append("\nthermal ${thermal(context)} · battery $pct%${if (charging) " charging" else ""}${if (isEmulator()) " · EMULATOR" else ""}")
        }
    }

    const val GIB = 1024.0 * 1024.0 * 1024.0
}

object Mem {
    private fun statusKb(key: String): Long? = runCatching {
        File("/proc/self/status").readLines().firstOrNull { it.startsWith("$key:") }?.split(Regex("\\s+"))?.get(1)?.toLong()
    }.getOrNull()

    fun rssGib(): Double = (statusKb("VmRSS") ?: 0L) * 1024.0 / DeviceInfo.GIB
    fun hwmGib(): Double = (statusKb("VmHWM") ?: 0L) * 1024.0 / DeviceInfo.GIB

    /** Reset VmHWM to the current RSS (Linux clear_refs "5"); false if the kernel/SELinux refuses. */
    fun resetPeak(): Boolean = runCatching {
        File("/proc/self/clear_refs").writeText("5")
        true
    }.getOrDefault(false)
}
