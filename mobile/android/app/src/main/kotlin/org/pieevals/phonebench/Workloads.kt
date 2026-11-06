package org.pieevals.phonebench

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class Round(val warmup: List<String>, val measured: List<String>)

data class Workload(
    val id: String,
    val concurrency: Int,
    val prefill: Int,
    val decode: Int,
    val requests: Int,
    val warmup: Int,
    val coldCache: Boolean,
    val rounds: List<Round>,
)

data class Template(val prefix: String, val suffix: String, val promptTokens: JSONObject) {
    fun render(user: String) = prefix + user + suffix
    /** Harness tokenizer count for measured request i of round r. */
    fun expected(workload: String, round: Int, i: Int): Int =
        promptTokens.optJSONArray(workload)?.optJSONArray(round)?.optInt(i, -1) ?: -1
}

/** mobile/shared/workloads.json, made by the harness (mobile/tools/gen_workloads.py), bundled as an asset. */
class Workloads(val harnessCommit: String, val system: String, val rounds: Int, val workloads: List<Workload>, val templates: Map<String, Template>) {
    companion object {
        fun load(context: Context): Workloads {
            val j = JSONObject(context.assets.open("workloads.json").bufferedReader().use { it.readText() })
            fun strs(a: JSONArray) = (0 until a.length()).map { a.getString(it) }
            val wls = j.getJSONArray("workloads").let { arr ->
                (0 until arr.length()).map { k ->
                    val w = arr.getJSONObject(k)
                    val rs = w.getJSONArray("rounds")
                    Workload(
                        w.getString("id"), w.getInt("concurrency"), w.getInt("prefill"), w.getInt("decode"),
                        w.getInt("requests"), w.getInt("warmup"), w.optBoolean("cold_cache"),
                        (0 until rs.length()).map { r -> rs.getJSONObject(r).let { Round(strs(it.getJSONArray("warmup")), strs(it.getJSONArray("measured"))) } },
                    )
                }
            }
            val t = j.getJSONObject("templates")
            val tm = t.keys().asSequence().associateWith { m ->
                t.getJSONObject(m).let { Template(it.getString("prefix"), it.getString("suffix"), it.getJSONObject("prompt_tokens")) }
            }
            return Workloads(j.getString("harness_commit"), j.getString("system"), j.getInt("rounds"), wls, tm)
        }
    }
}
