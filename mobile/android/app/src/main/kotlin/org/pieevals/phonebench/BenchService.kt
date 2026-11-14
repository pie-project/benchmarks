package org.pieevals.phonebench

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.ServiceCompat

/** Runs a benchmark in a foreground service with a wake lock so an hour-long run is not killed. */
class BenchService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val cfg = pending ?: run { stopSelf(); return START_NOT_STICKY }
        pending = null
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(NotificationChannel("bench", "Benchmark", NotificationManager.IMPORTANCE_LOW))
        val n = Notification.Builder(this, "bench").setContentTitle("pie-evals phone benchmark").setContentText("running")
            .setSmallIcon(android.R.drawable.ic_menu_compass).setOngoing(true).build()
        ServiceCompat.startForeground(this, 1, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        val wl = (getSystemService(Context.POWER_SERVICE) as PowerManager).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "pieevals:bench")
        wl.acquire(6 * 60 * 60 * 1000L)
        BenchState.running.value = true
        BenchState.cancel = false
        Thread({
            try {
                BenchRunner(applicationContext, cfg).run()
                if (cfg.send && cfg.url.isNotBlank()) {
                    BenchState.say("sending to ${cfg.url}/v1/results")
                    val reply = runCatching { Results.send(applicationContext, cfg.url, cfg.token) }.getOrElse { "send failed: $it" }
                    BenchState.lastReply.value = reply
                    BenchState.say("server: $reply")
                }
            } catch (t: Throwable) {
                BenchState.say("run crashed: $t")
            } finally {
                BenchState.running.value = false
                BenchState.progress.value = ""
                if (wl.isHeld) wl.release()
                ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }, "bench").start()
        return START_NOT_STICKY
    }

    companion object {
        @Volatile private var pending: RunConfig? = null

        fun start(context: Context, cfg: RunConfig): Boolean {
            if (BenchState.running.value) return false
            pending = cfg
            context.startForegroundService(Intent(context, BenchService::class.java))
            return true
        }
    }
}
