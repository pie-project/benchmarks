// CUDA injection (CUDA_INJECTION64_PATH) that records only the device's kernel, copy and memset intervals through
// CUPTI's activity API: no API tracing, nothing enabled until the profiler asks. A thread polls
// $PIE_CUPTI_DIR/on: while it exists (it holds the round's number N) the activities are on; when it goes, they are
// flushed and the process writes <pid>-<N>.bin (start, end pairs of uint64 CUPTI ns), <pid>-<N>.clock (a CUPTI
// timestamp and the CLOCK_REALTIME ns taken together) and <pid>-<N>.done.
#include <cupti.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define BUF_BYTES (8u << 20)

static const char *dir;
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static FILE *out;
static long round_no = -1;

static void CUPTIAPI request(uint8_t **buffer, size_t *size, size_t *max_records) {
    *buffer = aligned_alloc(8, BUF_BYTES);
    *size = *buffer ? BUF_BYTES : 0;
    *max_records = 0;
}

static void CUPTIAPI complete(CUcontext ctx, uint32_t stream, uint8_t *buffer, size_t size, size_t valid) {
    (void)ctx, (void)stream, (void)size;
    CUpti_Activity *rec = NULL;
    pthread_mutex_lock(&mu);
    while (cuptiActivityGetNextRecord(buffer, valid, &rec) == CUPTI_SUCCESS) {
        uint64_t se[2];
        switch (rec->kind) {
        case CUPTI_ACTIVITY_KIND_KERNEL:
        case CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL:
            se[0] = ((CUpti_ActivityKernel10 *)rec)->start, se[1] = ((CUpti_ActivityKernel10 *)rec)->end;
            break;
        case CUPTI_ACTIVITY_KIND_MEMCPY:
            se[0] = ((CUpti_ActivityMemcpy6 *)rec)->start, se[1] = ((CUpti_ActivityMemcpy6 *)rec)->end;
            break;
        case CUPTI_ACTIVITY_KIND_MEMSET:
            se[0] = ((CUpti_ActivityMemset4 *)rec)->start, se[1] = ((CUpti_ActivityMemset4 *)rec)->end;
            break;
        default:
            continue;
        }
        if (out)
            fwrite(se, sizeof se[0], 2, out);
    }
    pthread_mutex_unlock(&mu);
    free(buffer);
}

static void path(char *p, size_t n, const char *ext) { snprintf(p, n, "%s/%d-%ld.%s", dir, (int)getpid(), round_no, ext); }

static void *control(void *arg) {
    (void)arg;
    char on[4096], p[4096];
    snprintf(on, sizeof on, "%s/on", dir);
    int active = 0;
    for (;;) {
        FILE *f = fopen(on, "r");
        if (f && !active) {
            long n = -1;
            if (fscanf(f, "%ld", &n) != 1)
                n = 0;
            pthread_mutex_lock(&mu);
            round_no = n;
            path(p, sizeof p, "bin");
            out = fopen(p, "wb");
            pthread_mutex_unlock(&mu);
            uint64_t ts = 0;
            struct timespec rt;
            cuptiGetTimestamp(&ts);
            clock_gettime(CLOCK_REALTIME, &rt);
            path(p, sizeof p, "clock");
            FILE *c = fopen(p, "w");
            if (c)
                fprintf(c, "%llu %lld\n", (unsigned long long)ts, (long long)rt.tv_sec * 1000000000LL + rt.tv_nsec), fclose(c);
            cuptiActivityEnable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL);
            cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMCPY);
            cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMSET);
            active = 1;
        } else if (!f && active) {
            cuptiActivityDisable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL);
            cuptiActivityDisable(CUPTI_ACTIVITY_KIND_MEMCPY);
            cuptiActivityDisable(CUPTI_ACTIVITY_KIND_MEMSET);
            cuptiActivityFlushAll(CUPTI_ACTIVITY_FLAG_FLUSH_FORCED);
            pthread_mutex_lock(&mu);
            if (out)
                fclose(out), out = NULL;
            pthread_mutex_unlock(&mu);
            path(p, sizeof p, "done");
            FILE *d = fopen(p, "w");
            if (d)
                fclose(d);
            active = 0;
        }
        if (f)
            fclose(f);
        usleep(2000);
    }
    return NULL;
}

int InitializeInjection(void) {
    dir = getenv("PIE_CUPTI_DIR");
    if (!dir || cuptiActivityRegisterCallbacks(request, complete) != CUPTI_SUCCESS)
        return 1;
    pthread_t t;
    pthread_attr_t a;
    pthread_attr_init(&a);
    pthread_attr_setdetachstate(&a, PTHREAD_CREATE_DETACHED);
    pthread_create(&t, &a, control, NULL);
    return 1;
}
