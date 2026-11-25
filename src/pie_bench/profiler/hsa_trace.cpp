// hsa_trace: an engine process's kernel intervals, from the GPU's own dispatch timestamps, recorded only while the
// profiler's marker file ($PIE_BENCH_HSA_TRACE_DIR/recording) exists. ROCr loads it into every process that starts
// HSA (HSA_TOOLS_LIB). Queues are made as the engine asks; outside a recording the tool only checks one flag on each
// signal store. While recording, a store to a queue's doorbell first gives each kernel packet it publishes (written,
// not yet seen by the GPU) a completion signal from the queue's pool, the queue writes start and end timestamps into
// it, and a thread of the tool's own writes them as Unix ns to kernels-<pid>-<n>.csv, then kernels-<pid>-<n>.done
// once the round's dispatches have all completed (or 5 s after the round, counting the ones that had not in
// kernels-<pid>-<n>.unfinished). A kernel that carries a completion signal of its own is left as it is and counted in
// kernels-<pid>-<n>.skipped.
#include <hsa.h>
#include <hsa_api_trace.h>
#include <hsa_ext_amd.h>

#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <mutex>
#include <string>
#include <sys/stat.h>
#include <thread>
#include <vector>

namespace
{
decltype(hsa_queue_create)*                       queue_create;
decltype(hsa_signal_load_relaxed)*                signal_load;
decltype(hsa_signal_store_relaxed)*               store_relaxed;
decltype(hsa_signal_store_screlease)*             store_screlease;
decltype(hsa_queue_load_write_index_relaxed)*     write_index;
decltype(hsa_system_get_info)*                    system_info;
decltype(hsa_amd_profiling_set_profiler_enabled)* set_profiling;
decltype(hsa_amd_profiling_get_dispatch_time)*    dispatch_time;
decltype(hsa_amd_signal_create)*                  signal_create;
#if HSA_AMD_EXT_API_TABLE_STEP_VERSION >= 0x10
decltype(hsa_amd_queue_create)* amd_queue_create;
#endif

constexpr size_t POOL = 4096;  // signals per queue, made when a round starts
constexpr size_t SLOTS = 1024;  // doorbell table

struct Queue
{
    hsa_agent_t               agent{};
    hsa_queue_t*              queue = nullptr;
    std::mutex                mu;
    uint64_t                  next = 0;  // the first packet not yet looked at in this round
    bool                      armed = false;
    std::vector<hsa_signal_t> pending;  // a long kernel does not hold back the ones done after it
    std::vector<hsa_signal_t> pool;
    uint64_t                  skipped = 0;
};

std::atomic<uint64_t> keys[SLOTS];  // doorbell signal handle -> queue, open addressing, entries only added
Queue*                values[SLOTS];
std::mutex            mu;  // the queue list
std::vector<Queue*>   queues;
std::atomic<bool>     recording{false};
std::atomic<bool>     quit{false};
std::atomic<bool>     stopped{false};
std::string           dir;

Queue*
find(uint64_t handle)
{
    for(size_t i = (handle >> 6) % SLOTS, n = 0; n < SLOTS; i = (i + 1) % SLOTS, ++n)
    {
        const auto k = keys[i].load(std::memory_order_acquire);
        if(k == handle) return values[i];
        if(k == 0) return nullptr;
    }
    return nullptr;
}

void
add(hsa_agent_t agent, hsa_queue_t* queue)
{
    auto* q  = new Queue{};
    q->agent = agent;
    q->queue = queue;
    std::lock_guard<std::mutex> lock(mu);
    const uint64_t h = queue->doorbell_signal.handle;
    for(size_t i = (h >> 6) % SLOTS, n = 0; n < SLOTS; i = (i + 1) % SLOTS, ++n)
    {
        const auto k = keys[i].load(std::memory_order_relaxed);
        if(k == 0 || k == h)
        {
            values[i] = q;
            keys[i].store(h, std::memory_order_release);
            break;
        }
    }
    queues.push_back(q);
}

hsa_signal_t
make_signal()
{
    // polled by the tool's thread only: no interrupt on completion
    hsa_signal_t s{};
    signal_create(1, 0, nullptr, HSA_AMD_SIGNAL_AMD_GPU_ONLY, &s);
    return s;
}

// before the GPU hears of them: give the kernels the doorbell publishes a pooled completion signal
void
mark(Queue* q, hsa_signal_value_t last)
{
    std::lock_guard<std::mutex> lock(q->mu);
    if(!q->armed) return;
    auto* ring = static_cast<hsa_kernel_dispatch_packet_t*>(q->queue->base_address);
    for(uint64_t i = q->next; i <= uint64_t(last); ++i)
    {
        auto&      p    = ring[i % q->queue->size];
        const auto type = (__atomic_load_n(&p.header, __ATOMIC_ACQUIRE) >> HSA_PACKET_HEADER_TYPE) & ((1 << HSA_PACKET_HEADER_WIDTH_TYPE) - 1);
        if(type == HSA_PACKET_TYPE_INVALID)
        {
            q->next = i;  // not written yet: looked at with a later doorbell
            return;
        }
        if(type == HSA_PACKET_TYPE_KERNEL_DISPATCH)
        {
            if(p.completion_signal.handle != 0)
                ++q->skipped;
            else
            {
                if(q->pool.empty()) q->pool.push_back(make_signal());
                p.completion_signal = q->pool.back();
                q->pool.pop_back();
                q->pending.push_back(p.completion_signal);
            }
        }
    }
    q->next = uint64_t(last) + 1;
}

void
my_store_relaxed(hsa_signal_t s, hsa_signal_value_t v)
{
    if(recording.load(std::memory_order_relaxed))
        if(auto* q = find(s.handle)) mark(q, v);
    store_relaxed(s, v);
}

void
my_store_screlease(hsa_signal_t s, hsa_signal_value_t v)
{
    if(recording.load(std::memory_order_relaxed))
        if(auto* q = find(s.handle)) mark(q, v);
    store_screlease(s, v);
}

hsa_status_t
my_queue_create(hsa_agent_t agent, uint32_t size, hsa_queue_type32_t type, void (*cb)(hsa_status_t, hsa_queue_t*, void*),
                void* data, uint32_t priv, uint32_t group, hsa_queue_t** queue)
{
    auto s = queue_create(agent, size, type, cb, data, priv, group, queue);
    if(s == HSA_STATUS_SUCCESS) add(agent, *queue);
    return s;
}

#if HSA_AMD_EXT_API_TABLE_STEP_VERSION >= 0x10
// HIP on ROCm 10 makes its queues with hsa_amd_queue_create
hsa_status_t
my_amd_queue_create(hsa_agent_t agent, hsa_amd_queue_create_desc_t* descs, uint32_t n)
{
    auto s = amd_queue_create(agent, descs, n);
    for(uint32_t i = 0; i < n; ++i)
        if(descs[i].queue && descs[i].engine_type == HSA_AMD_QUEUE_ENGINE_COMPUTE) add(agent, descs[i].queue);
    return s;
}
#endif

void
arm(Queue* q)
{
    size_t want = 0;
    {
        std::lock_guard<std::mutex> lock(q->mu);
        if(q->pool.size() < POOL) want = POOL - q->pool.size();
    }
    std::vector<hsa_signal_t> made;
    while(made.size() < want) made.push_back(make_signal());
    set_profiling(q->queue, 1);
    std::lock_guard<std::mutex> lock(q->mu);
    q->pool.insert(q->pool.end(), made.begin(), made.end());
    q->pending.clear();  // ones left unfinished by an earlier round
    q->next    = write_index(q->queue);
    q->skipped = 0;
    q->armed   = true;
}

void
read_loop()
{
    const std::string marker = dir + "/recording";
    FILE*             out    = nullptr;
    std::string       name;
    int               round = 0;
    int64_t           shift = 0;
    double            scale = 1;
    std::vector<hsa_signal_t> done, keep;
    uint64_t          last_skipped = 0;
    auto              ended = std::chrono::steady_clock::now();
    while(!quit)
    {
        struct stat st{};
        const bool  want = stat(marker.c_str(), &st) == 0;
        std::vector<Queue*> qs;
        {
            std::lock_guard<std::mutex> lock(mu);
            qs = queues;
        }
        if(want && !recording && !out)
        {
            uint64_t freq = 1, ts = 0;
            timespec t{};
            system_info(HSA_SYSTEM_INFO_TIMESTAMP_FREQUENCY, &freq);
            scale = 1e9 / double(freq);
            system_info(HSA_SYSTEM_INFO_TIMESTAMP, &ts);
            clock_gettime(CLOCK_REALTIME, &t);
            shift = int64_t(t.tv_sec) * 1000000000 + t.tv_nsec - int64_t(double(ts) * scale);
            name  = dir + "/kernels-" + std::to_string(getpid()) + "-" + std::to_string(round++);
            out   = std::fopen((name + ".csv").c_str(), "w");
            last_skipped = 0;
            for(auto* q : qs) arm(q);
            recording.store(true, std::memory_order_release);
        }
        else if(!want && recording)
        {
            recording.store(false, std::memory_order_release);
            ended = std::chrono::steady_clock::now();
            for(auto* q : qs)
            {
                std::lock_guard<std::mutex> lock(q->mu);
                q->armed = false;
            }
        }
        bool     drained    = true;
        uint64_t skipped    = 0;
        uint64_t unfinished = 0;
        for(auto* q : qs)
        {
            bool fresh;
            {
                std::lock_guard<std::mutex> lock(q->mu);
                fresh = recording && !q->armed;
            }
            if(fresh) arm(q);  // a queue made during the round
            done.clear();
            keep.clear();
            {
                std::lock_guard<std::mutex> lock(q->mu);  // the launch thread waits only for the swap
                keep.swap(q->pending);
                skipped += q->skipped;
            }
            for(size_t i = 0; i < keep.size();)
                if(signal_load(keep[i]) == 0)
                {
                    done.push_back(keep[i]);
                    keep[i] = keep.back();
                    keep.pop_back();
                }
                else
                    ++i;
            {
                std::lock_guard<std::mutex> lock(q->mu);
                q->pending.insert(q->pending.end(), keep.begin(), keep.end());
                drained = drained && q->pending.empty();
                unfinished += q->pending.size();
            }
            for(auto s : done)
            {
                hsa_amd_profiling_dispatch_time_t t{};
                if(out && dispatch_time(q->agent, s, &t) == HSA_STATUS_SUCCESS)
                    std::fprintf(out, "%lld,%lld\n", (long long) (int64_t(double(t.start) * scale) + shift),
                                 (long long) (int64_t(double(t.end) * scale) + shift));
                store_relaxed(s, 1);
            }
            if(!done.empty())
            {
                std::lock_guard<std::mutex> lock(q->mu);
                q->pool.insert(q->pool.end(), done.begin(), done.end());
            }
        }
        if(out)
        {
            // an engine that stops inside the round (an offline engine in its bench client) leaves its file complete
            // to the last millisecond, with its skipped count
            std::fflush(out);
            if(skipped != last_skipped)
                if(FILE* f = std::fopen((name + ".skipped").c_str(), "w"))
                {
                    std::fprintf(f, "%llu\n", (unsigned long long) skipped);
                    std::fclose(f);
                    last_skipped = skipped;
                }
        }
        if(out && !recording && (drained || std::chrono::steady_clock::now() - ended > std::chrono::seconds(5)))
        {
            std::fclose(out);
            out = nullptr;
            if(unfinished)
                if(FILE* f = std::fopen((name + ".unfinished").c_str(), "w"))
                {
                    std::fprintf(f, "%llu\n", (unsigned long long) unfinished);
                    std::fclose(f);
                }
            std::fclose(std::fopen((name + ".done").c_str(), "w"));
        }
        // once a millisecond: the pools hold several milliseconds of a queue's kernels
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    if(out) std::fclose(out);
    stopped = true;
}
}  // namespace

extern "C" bool
OnLoad(HsaApiTable* table, uint64_t, uint64_t, const char* const*)
{
    const char* d = std::getenv("PIE_BENCH_HSA_TRACE_DIR");
    if(!d) return true;
    dir             = d;
    auto* core      = table->core_;
    auto* ext       = table->amd_ext_;
    queue_create    = core->hsa_queue_create_fn;
    signal_load     = core->hsa_signal_load_relaxed_fn;
    store_relaxed   = core->hsa_signal_store_relaxed_fn;
    store_screlease = core->hsa_signal_store_screlease_fn;
    write_index     = core->hsa_queue_load_write_index_relaxed_fn;
    system_info     = core->hsa_system_get_info_fn;
    set_profiling   = ext->hsa_amd_profiling_set_profiler_enabled_fn;
    dispatch_time   = ext->hsa_amd_profiling_get_dispatch_time_fn;
    signal_create   = ext->hsa_amd_signal_create_fn;
#if HSA_AMD_EXT_API_TABLE_STEP_VERSION >= 0x10
    amd_queue_create             = ext->hsa_amd_queue_create_fn;
    ext->hsa_amd_queue_create_fn = my_amd_queue_create;
#endif
    core->hsa_queue_create_fn          = my_queue_create;
    core->hsa_signal_store_relaxed_fn   = my_store_relaxed;
    core->hsa_signal_store_screlease_fn = my_store_screlease;
    std::thread(read_loop).detach();  // a joinable thread left at exit would abort the engine
    return true;
}

extern "C" void
OnUnload()
{
    quit = true;
    for(int i = 0; i < 100 && !stopped; ++i) std::this_thread::sleep_for(std::chrono::milliseconds(1));
}
