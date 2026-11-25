// Metal's own GPU times of every command buffer a process commits, with no kernel tracing.
//
// Preloaded into the job's processes (DYLD_INSERT_LIBRARIES) with PIE_BENCH_METAL_CB_DIR set, it wraps the Metal
// device's command buffer classes' -commit once the process creates its device. While <dir>/recording exists, each
// committed buffer gets a completed handler that appends its GPUStartTime and GPUEndTime, in Unix ns, to <dir>/<pid>.txt.
// Outside that window -commit costs one atomic load more.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <objc/runtime.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static atomic_int on, dirty;
static atomic_llong offset_ns;  // Unix ns minus host-time ns, taken as the gate opens
static char dir[900];
static FILE *out;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static void flush(void) {
    pthread_mutex_lock(&lock);
    if (out) fflush(out);
    pthread_mutex_unlock(&lock);
}

static void record(CFTimeInterval start, CFTimeInterval end) {
    if (start <= 0 || end < start) return;  // a buffer that errored or never ran
    long long off = atomic_load(&offset_ns);
    pthread_mutex_lock(&lock);
    if (!out) {
        char path[1024];
        snprintf(path, sizeof path, "%s/%d.txt", dir, getpid());
        out = fopen(path, "a");
    }
    if (out) fprintf(out, "%lld %lld\n", (long long)(start * 1e9) + off, (long long)(end * 1e9) + off);
    pthread_mutex_unlock(&lock);
    atomic_store(&dirty, 1);
}

static void *watch(void *arg) {
    char gate[1024];
    struct stat st;
    snprintf(gate, sizeof gate, "%s/recording", dir);
    for (;;) {
        int open = stat(gate, &st) == 0;
        if (open && !atomic_load(&on)) {
            atomic_store(&offset_ns, (long long)clock_gettime_nsec_np(CLOCK_REALTIME) - (long long)clock_gettime_nsec_np(CLOCK_UPTIME_RAW));
            atomic_store(&on, 1);
        } else if (!open && atomic_load(&on)) {
            atomic_store(&on, 0);
        }
        if (atomic_exchange(&dirty, 0)) flush();
        usleep(10000);
    }
    return NULL;
}

static void forked(void) { atomic_store(&on, 0); out = NULL; }  // a forked child records nothing (no watcher in it)

static NSMutableSet *wrapped;

static void wrap(Class cls) {
    Method m = class_getInstanceMethod(cls, @selector(commit));
    NSValue *key = [NSValue valueWithPointer:m];
    if (!m || [wrapped containsObject:key]) return;
    [wrapped addObject:key];
    IMP orig = method_getImplementation(m);
    IMP mine = imp_implementationWithBlock(^(id cb) {
        if (atomic_load(&on))
            [cb addCompletedHandler:^(id<MTLCommandBuffer> done) { record(done.GPUStartTime, done.GPUEndTime); }];
        ((void (*)(id, SEL))orig)(cb, @selector(commit));
    });
    method_setImplementation(m, mine);
}

static void arm(id<MTLDevice> device) {
    static dispatch_once_t once;
    if (!device || !dir[0]) return;
    dispatch_once(&once, ^{
        @autoreleasepool {
            wrapped = [NSMutableSet new];
            id<MTLCommandQueue> q = [device newCommandQueue];
            wrap(object_getClass([q commandBuffer]));
            wrap(object_getClass([q commandBufferWithUnretainedReferences]));
            MTLCommandBufferDescriptor *d = [MTLCommandBufferDescriptor new];
            wrap(object_getClass([q commandBufferWithDescriptor:d]));
            [d release];
            [q release];
        }
        pthread_atfork(NULL, NULL, forked);
        pthread_t t;
        pthread_create(&t, NULL, watch, NULL);
        pthread_detach(t);
    });
}

static id<MTLDevice> pie_create_device(void) {
    id<MTLDevice> d = MTLCreateSystemDefaultDevice();
    arm(d);
    return d;
}

static NSArray<id<MTLDevice>> *pie_copy_devices(void) {
    NSArray<id<MTLDevice>> *all = MTLCopyAllDevices();
    if (all.count) arm(all[0]);
    return all;
}

__attribute__((used)) static const struct { const void *replacement, *replacee; } interposers[] __attribute__((section("__DATA,__interpose"))) = {
    {(const void *)pie_create_device, (const void *)MTLCreateSystemDefaultDevice},
    {(const void *)pie_copy_devices, (const void *)MTLCopyAllDevices},
};

__attribute__((constructor)) static void init(void) {
    const char *d = getenv("PIE_BENCH_METAL_CB_DIR");
    if (d && strlen(d) < sizeof dir) strcpy(dir, d);
}
