#include <jni.h>
#include <android/log.h>
#include <time.h>
#include <unistd.h>

#include <algorithm>
#include <cmath>
#include <deque>
#include <string>
#include <vector>

#include "llama.h"
#include "ggml-backend.h"

#define TAG "benchllama"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

static int64_t now_ns() {
    timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t) ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

struct Handle {
    llama_model * model = nullptr;
    llama_context * ctx = nullptr;
    const llama_vocab * vocab = nullptr;
    int n_seq = 1;
    int n_batch = 512;
    std::vector<llama_token> eog;
};

static void throw_java(JNIEnv * env, const std::string & msg) {
    jclass cls = env->FindClass("java/lang/RuntimeException");
    env->ThrowNew(cls, msg.c_str());
}

static std::string jstr(JNIEnv * env, jstring s) {
    const char * c = env->GetStringUTFChars(s, nullptr);
    std::string out(c);
    env->ReleaseStringUTFChars(s, c);
    return out;
}

static void log_cb(ggml_log_level level, const char * text, void *) {
    if (level >= GGML_LOG_LEVEL_WARN) __android_log_print(ANDROID_LOG_WARN, TAG, "%s", text);
    else if (level == GGML_LOG_LEVEL_INFO) __android_log_print(ANDROID_LOG_INFO, TAG, "%s", text);
}

extern "C" JNIEXPORT void JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_init(JNIEnv * env, jclass, jstring libDir) {
    llama_log_set(log_cb, nullptr);
    ggml_backend_load_all_from_path(jstr(env, libDir).c_str());
    llama_backend_init();
}

extern "C" JNIEXPORT jstring JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_systemInfo(JNIEnv * env, jclass) {
    std::string s = llama_print_system_info();
    s += " | devices:";
    for (size_t i = 0; i < ggml_backend_dev_count(); i++) {
        ggml_backend_dev_t d = ggml_backend_dev_get(i);
        s += " ";
        s += ggml_backend_dev_name(d);
        s += "(";
        s += ggml_backend_dev_description(d);
        s += ")";
    }
    return env->NewStringUTF(s.c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_gpuDevices(JNIEnv * env, jclass) {
    std::string s;
    for (size_t i = 0; i < ggml_backend_dev_count(); i++) {
        ggml_backend_dev_t d = ggml_backend_dev_get(i);
        auto t = ggml_backend_dev_type(d);
        if (t == GGML_BACKEND_DEVICE_TYPE_GPU || t == GGML_BACKEND_DEVICE_TYPE_IGPU) {
            if (!s.empty()) s += "; ";
            s += ggml_backend_dev_name(d);
            s += ": ";
            s += ggml_backend_dev_description(d);
        }
    }
    return env->NewStringUTF(s.c_str());
}

extern "C" JNIEXPORT jlong JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_load(JNIEnv * env, jclass, jstring path, jint n_ctx,
                                                     jint n_batch, jint n_ubatch, jint n_threads,
                                                     jint n_seq, jint n_gpu_layers, jboolean flash_attn) {
    auto * h = new Handle();
    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = n_gpu_layers;
    static ggml_backend_dev_t no_gpu[1] = {nullptr};
    if (n_gpu_layers == 0) mp.devices = no_gpu;
    h->model = llama_model_load_from_file(jstr(env, path).c_str(), mp);
    if (!h->model) {
        delete h;
        throw_java(env, "llama_model_load_from_file failed");
        return 0;
    }
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = n_ctx;
    cp.n_batch = n_batch;
    cp.n_ubatch = n_ubatch;
    cp.n_seq_max = n_seq;
    cp.n_threads = n_threads;
    cp.n_threads_batch = n_threads;
    cp.kv_unified = false;
    cp.flash_attn_type = flash_attn ? LLAMA_FLASH_ATTN_TYPE_ENABLED : LLAMA_FLASH_ATTN_TYPE_DISABLED;
    cp.no_perf = true;
    cp.op_offload = n_gpu_layers > 0;
    h->ctx = llama_init_from_model(h->model, cp);
    if (!h->ctx) {
        llama_model_free(h->model);
        delete h;
        throw_java(env, "llama_init_from_model failed");
        return 0;
    }
    h->vocab = llama_model_get_vocab(h->model);
    h->n_seq = n_seq;
    h->n_batch = n_batch;
    const int nv = llama_vocab_n_tokens(h->vocab);
    for (int t = 0; t < nv; t++) if (llama_vocab_is_eog(h->vocab, t)) h->eog.push_back(t);
    LOGI("loaded: n_ctx=%u n_seq=%d eog=%zu", llama_n_ctx(h->ctx), n_seq, h->eog.size());
    return (jlong) h;
}

extern "C" JNIEXPORT jstring JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_modelDesc(JNIEnv * env, jclass, jlong hp) {
    auto * h = (Handle *) hp;
    char buf[256];
    llama_model_desc(h->model, buf, sizeof buf);
    return env->NewStringUTF(buf);
}

extern "C" JNIEXPORT jint JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_countTokens(JNIEnv * env, jclass, jlong hp, jstring text) {
    auto * h = (Handle *) hp;
    std::string s = jstr(env, text);
    int n = -llama_tokenize(h->vocab, s.c_str(), (int) s.size(), nullptr, 0, false, true);
    return n;
}

static std::vector<llama_token> tokenize(Handle * h, const std::string & s) {
    int n = -llama_tokenize(h->vocab, s.c_str(), (int) s.size(), nullptr, 0, false, true);
    std::vector<llama_token> out(std::max(n, 0));
    if (n > 0) llama_tokenize(h->vocab, s.c_str(), (int) s.size(), out.data(), n, false, true);
    return out;
}

struct Slot {
    int req = -1;
    std::vector<llama_token> prompt;
    size_t fed = 0;
    llama_pos pos = 0;
    llama_token next = -1;
    int produced = 0;
    int logit_idx = -1;
};

extern "C" JNIEXPORT jlongArray JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_run(JNIEnv * env, jclass, jlong hp, jobjectArray jprompts,
                                                    jint max_new, jint slots, jboolean ignore_eos) {
    auto * h = (Handle *) hp;
    const int n = env->GetArrayLength(jprompts);
    std::vector<std::string> prompts(n);
    for (int i = 0; i < n; i++) {
        auto js = (jstring) env->GetObjectArrayElement(jprompts, i);
        prompts[i] = jstr(env, js);
        env->DeleteLocalRef(js);
    }
    const int ns = std::max(1, std::min((int) slots, h->n_seq));
    std::vector<int64_t> out((size_t) n * 5, 0);
    std::vector<Slot> sl(ns);
    std::deque<int> queue;
    for (int i = 0; i < n; i++) queue.push_back(i);
    llama_memory_t mem = llama_get_memory(h->ctx);
    const int nv = llama_vocab_n_tokens(h->vocab);
    llama_batch batch = llama_batch_init(h->n_batch, 0, 1);
    int done = 0;
    std::string err;

    while (done < n) {
        for (int s = 0; s < ns; s++) {
            if (sl[s].req >= 0 || queue.empty()) continue;
            int r = queue.front();
            queue.pop_front();
            llama_memory_seq_rm(mem, s, -1, -1);
            Slot & x = sl[s];
            x = Slot();
            x.req = r;
            out[r * 5 + 2] = now_ns();
            x.prompt = tokenize(h, prompts[r]);
            out[r * 5 + 0] = (int64_t) x.prompt.size();
            if (x.prompt.empty()) { err = "empty prompt"; break; }
        }
        if (!err.empty()) break;
        batch.n_tokens = 0;
        auto add = [&](llama_token t, llama_pos p, int s, bool logits) {
            int i = batch.n_tokens++;
            batch.token[i] = t;
            batch.pos[i] = p;
            batch.n_seq_id[i] = 1;
            batch.seq_id[i][0] = s;
            batch.logits[i] = logits;
            return i;
        };
        for (int s = 0; s < ns; s++) {
            Slot & x = sl[s];
            x.logit_idx = -1;
            if (x.req >= 0 && x.next >= 0) {
                x.logit_idx = add(x.next, x.pos, s, true);
                x.pos++;
                x.next = -1;
            }
        }
        for (int s = 0; s < ns; s++) {
            Slot & x = sl[s];
            if (x.req < 0 || x.fed >= x.prompt.size()) continue;
            while (x.fed < x.prompt.size() && batch.n_tokens < h->n_batch) {
                bool last = x.fed + 1 == x.prompt.size();
                int i = add(x.prompt[x.fed], x.pos, s, last);
                if (last) x.logit_idx = i;
                x.fed++;
                x.pos++;
            }
        }
        if (batch.n_tokens == 0) { err = "scheduler stalled"; break; }
        int rc = llama_decode(h->ctx, batch);
        if (rc != 0) { err = "llama_decode returned " + std::to_string(rc); break; }
        const int64_t t = now_ns();
        for (int s = 0; s < ns; s++) {
            Slot & x = sl[s];
            if (x.req < 0 || x.logit_idx < 0) continue;
            float * lg = llama_get_logits_ith(h->ctx, x.logit_idx);
            if (ignore_eos) for (llama_token e : h->eog) lg[e] = -INFINITY;
            llama_token best = 0;
            float bv = lg[0];
            for (int v = 1; v < nv; v++) if (lg[v] > bv) { bv = lg[v]; best = v; }
            x.produced++;
            const int r = x.req;
            if (x.produced == 1) out[r * 5 + 3] = t;
            out[r * 5 + 4] = t;
            out[r * 5 + 1] = x.produced;
            bool stop = x.produced >= max_new || (!ignore_eos && llama_vocab_is_eog(h->vocab, best));
            if (stop) {
                llama_memory_seq_rm(mem, s, -1, -1);
                x.req = -1;
                done++;
            } else {
                x.next = best;
            }
        }
    }
    llama_batch_free(batch);
    for (int s = 0; s < ns; s++) llama_memory_seq_rm(mem, s, -1, -1);
    if (!err.empty()) {
        throw_java(env, err);
        return nullptr;
    }
    jlongArray arr = env->NewLongArray((jsize) out.size());
    env->SetLongArrayRegion(arr, 0, (jsize) out.size(), (const jlong *) out.data());
    return arr;
}

extern "C" JNIEXPORT void JNICALL
Java_org_pieevals_phonebench_engines_LlamaNative_free(JNIEnv *, jclass, jlong hp) {
    auto * h = (Handle *) hp;
    if (!h) return;
    if (h->ctx) llama_free(h->ctx);
    if (h->model) llama_model_free(h->model);
    delete h;
}
