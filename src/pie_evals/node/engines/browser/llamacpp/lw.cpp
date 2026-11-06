// llama.cpp in a browser tab: the library built for wasm with its WebGPU backend (ggml-webgpu), driven the way
// llama-server drives it. Each request is a slot (a sequence of its own); every step decodes one token for each
// slot that is generating and fills the rest of the n_batch budget with prompt tokens of the slots still reading
// theirs, so prompts and decodes share a batch as they do in llama-server. JavaScript (page/engines/llamacpp-worker.mjs)
// submits requests and calls lw_step until every slot is done.
#include <cstdint>
#include <cstdio>
#include <vector>

#include <emscripten/emscripten.h>

#include "llama.h"

namespace {

struct Slot {
    bool active = false;
    std::vector<llama_token> prompt;
    size_t fed = 0;            // prompt tokens already in the KV
    int max_tokens = 0;
    int produced = 0;
    llama_pos pos = 0;
    llama_token last = 0;
    llama_sampler * smpl = nullptr;
    int logits_at = -1;        // the batch row whose logits this slot samples this step
};

llama_model * g_model = nullptr;
llama_context * g_ctx = nullptr;
const llama_vocab * g_vocab = nullptr;
std::vector<Slot> g_slots;
int g_n_batch = 2048;
llama_batch g_batch;

void log_cb(ggml_log_level level, const char * text, void *) {
    if (level >= GGML_LOG_LEVEL_WARN || level == GGML_LOG_LEVEL_INFO) fputs(text, stderr);
}

}  // namespace

extern "C" {

// load a GGUF from the virtual file system (the worker mounts the fetched file there); every layer on the GPU
EMSCRIPTEN_KEEPALIVE int lw_load(const char * path, int n_ctx, int n_slots, int n_batch, int n_ubatch, int flash_attn) {
    llama_log_set(log_cb, nullptr);
    llama_backend_init();
    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = 9999;
    mp.load_mode = LLAMA_LOAD_MODE_NONE;  // read, not mmap: the file is a Blob in the worker
    mp.lazy_mode = LLAMA_LAZY_MODE_OFF;   // lazy rows need mmap (Gemma-4's per-layer embeddings): read every tensor up front
    g_model = llama_model_load_from_file(path, mp);
    if (!g_model) return -1;
    g_vocab = llama_model_get_vocab(g_model);
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = n_ctx;
    cp.n_seq_max = n_slots;
    cp.n_batch = n_batch;
    cp.n_ubatch = n_ubatch;
    cp.n_threads = 1;
    cp.n_threads_batch = 1;
    cp.no_perf = true;
    cp.kv_unified = false;  // llama-server with --parallel N (as the native rows run it): a KV of its own per slot
    cp.flash_attn_type = flash_attn > 0 ? LLAMA_FLASH_ATTN_TYPE_ENABLED : (flash_attn == 0 ? LLAMA_FLASH_ATTN_TYPE_DISABLED : LLAMA_FLASH_ATTN_TYPE_AUTO);
    g_ctx = llama_init_from_model(g_model, cp);
    if (!g_ctx) return -2;
    g_n_batch = n_batch;
    g_slots.assign(n_slots, Slot{});
    g_batch = llama_batch_init(n_batch, 0, 1);
    return 0;
}

EMSCRIPTEN_KEEPALIVE int lw_n_slots() { return (int) g_slots.size(); }

// a request in slot `slot`: its prompt token ids, its output budget and its sampling
EMSCRIPTEN_KEEPALIVE int lw_submit(int slot, const int32_t * ids, int n, int max_tokens, float temperature, float top_p, uint32_t seed) {
    if (slot < 0 || slot >= (int) g_slots.size() || g_slots[slot].active || n <= 0) return -1;
    Slot & s = g_slots[slot];
    llama_memory_seq_rm(llama_get_memory(g_ctx), slot, -1, -1);
    s.prompt.assign(ids, ids + n);
    s.fed = 0;
    s.max_tokens = max_tokens;
    s.produced = 0;
    s.pos = 0;
    if (s.smpl) llama_sampler_free(s.smpl);
    s.smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
    if (temperature <= 0.0f) {
        llama_sampler_chain_add(s.smpl, llama_sampler_init_greedy());
    } else {
        llama_sampler_chain_add(s.smpl, llama_sampler_init_top_p(top_p, 1));
        llama_sampler_chain_add(s.smpl, llama_sampler_init_temp(temperature));
        llama_sampler_chain_add(s.smpl, llama_sampler_init_dist(seed));
    }
    s.active = true;
    return 0;
}

// one decode: returns how many (slot, token) pairs it wrote to out (2 ints each), or a negative llama_decode error.
// A slot is done (and free again) once it has written max_tokens tokens; the end-of-generation token does not stop
// it (the bench pins every request's length, as llama-server's ignore_eos does).
EMSCRIPTEN_KEEPALIVE int lw_step(int32_t * out, int cap) {
    llama_batch & b = g_batch;
    b.n_tokens = 0;
    auto add = [&](llama_token t, llama_pos p, int seq, bool logits) {
        b.token[b.n_tokens] = t;
        b.pos[b.n_tokens] = p;
        b.n_seq_id[b.n_tokens] = 1;
        b.seq_id[b.n_tokens][0] = seq;
        b.logits[b.n_tokens] = logits;
        return b.n_tokens++;
    };
    // the generating slots first, one token each
    for (int i = 0; i < (int) g_slots.size(); i++) {
        Slot & s = g_slots[i];
        s.logits_at = -1;
        if (s.active && s.fed == s.prompt.size() && s.produced > 0 && b.n_tokens < g_n_batch) {
            s.logits_at = add(s.last, s.pos++, i, true);
        }
    }
    // then prompt chunks in slot order, while the batch has room
    for (int i = 0; i < (int) g_slots.size() && b.n_tokens < g_n_batch; i++) {
        Slot & s = g_slots[i];
        if (!s.active || s.fed >= s.prompt.size()) continue;
        while (s.fed < s.prompt.size() && b.n_tokens < g_n_batch) {
            bool last = s.fed + 1 == s.prompt.size();
            int at = add(s.prompt[s.fed++], s.pos++, i, last);
            if (last) s.logits_at = at;
        }
    }
    if (b.n_tokens == 0) return 0;
    int rc = llama_decode(g_ctx, b);
    if (rc != 0) return -100 - rc;
    int n = 0;
    for (int i = 0; i < (int) g_slots.size(); i++) {
        Slot & s = g_slots[i];
        if (s.logits_at < 0) continue;
        llama_token t = llama_sampler_sample(s.smpl, g_ctx, s.logits_at);
        s.last = t;
        s.produced++;
        if (n < cap) {
            out[2 * n] = i;
            out[2 * n + 1] = t;
            n++;
        }
        if (s.produced >= s.max_tokens) s.active = false;
    }
    return n;
}

EMSCRIPTEN_KEEPALIVE int lw_active() {
    int n = 0;
    for (auto & s : g_slots) n += s.active;
    return n;
}

}  // extern "C"
