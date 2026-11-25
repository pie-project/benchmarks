#define _GNU_SOURCE
#include <dlfcn.h>
#include <link.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

typedef struct Ext { size_t struct_size; int type; struct Ext *next; } Ext;
typedef struct { size_t struct_size; Ext *extension_start; } Api;
typedef struct Err Err;
typedef struct Prof Prof;
typedef struct { size_t struct_size; void *priv; Err *error; } ErrDestroy;
typedef struct { size_t struct_size; void *priv; const Err *error; const char *message; size_t message_size; } ErrMessage;
typedef struct { size_t struct_size; const char *options; size_t options_size; Prof *profiler; } Create;
typedef struct { size_t struct_size; Prof *profiler; } Args;
typedef struct { size_t struct_size; Prof *profiler; uint8_t *buffer; size_t buffer_size_in_bytes; } Collect;
typedef struct {
  size_t struct_size;
  void *priv;
  void (*error_destroy)(ErrDestroy *);
  void (*error_message)(ErrMessage *);
  void *error_get_code;
  Err *(*create)(Create *);
  Err *(*destroy)(Args *);
  Err *(*start)(Args *);
  Err *(*stop)(Args *);
  Err *(*collect_data)(Collect *);
} ProfApi;
typedef struct { Ext base; const ProfApi *api; } ProfExt;
enum { PROFILER_EXTENSION = 1 };

static char dir[4096];
static int pipe_fd[2];
static const ProfApi *table;
static Prof *live;

static long long now_ns(void) {
  struct timespec t;
  clock_gettime(CLOCK_REALTIME, &t);
  return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}

static void mark(const char *kind, const char *text) {
  char path[4200], tmp[4210];
  snprintf(path, sizeof path, "%s/pie-%d.%s", dir, (int)getpid(), kind);
  snprintf(tmp, sizeof tmp, "%s.tmp", path);
  FILE *f = fopen(tmp, "w");
  if (!f) return;
  fputs(text, f);
  fclose(f);
  rename(tmp, path);
}

static int failed(Err *e, char *out, size_t n) {
  if (!e) return 0;
  ErrMessage m = {sizeof m, NULL, e, NULL, 0};
  table->error_message(&m);
  snprintf(out, n, "error %.*s", (int)m.message_size, m.message ? m.message : "");
  ErrDestroy d = {sizeof d, NULL, e};
  table->error_destroy(&d);
  return 1;
}

static int find_libtpu(struct dl_phdr_info *info, size_t size, void *data) {
  (void)size;
  if (info->dlpi_name && strstr(info->dlpi_name, "libtpu")) {
    snprintf((char *)data, 4096, "%s", info->dlpi_name);
    return 1;
  }
  return 0;
}

static const ProfApi *profiler_api(char *why, size_t n) {
  char name[4096] = "";
  dl_iterate_phdr(find_libtpu, name);
  void *lib = name[0] ? dlopen(name, RTLD_LAZY | RTLD_NOLOAD) : NULL;
  const Api *(*get)(void) = lib ? (const Api *(*)(void))dlsym(lib, "GetPjrtApi") : NULL;
  if (!get) {
    snprintf(why, n, "error libtpu is not loaded in this process");
    return NULL;
  }
  for (Ext *e = get()->extension_start; e; e = e->next)
    if (e->type == PROFILER_EXTENSION && ((ProfExt *)e)->api) return ((ProfExt *)e)->api;
  snprintf(why, n, "error the plugin has no profiler extension");
  return NULL;
}

static void start(void) {
  char text[1200];
  if (live) { mark("started", "error already tracing"); return; }
  if (!table && !(table = profiler_api(text, sizeof text))) { mark("started", text); return; }
  static const char options[] = {0x10, 0x02, 0x18, 0x01, 0x28, 0x01, 0x38, 0x01};
  Create c = {sizeof c, options, sizeof options, NULL};
  long long t0 = now_ns();
  if (failed(table->create(&c), text, sizeof text)) { mark("started", text); return; }
  Args a = {sizeof a, c.profiler};
  if (failed(table->start(&a), text, sizeof text)) {
    table->destroy(&a);
    mark("started", text);
    return;
  }
  live = c.profiler;
  snprintf(text, sizeof text, "ok %lld %lld", t0, now_ns());
  mark("started", text);
}

static void stop(void) {
  char text[1200], path[4200];
  if (!live) { mark("done", "error not tracing"); return; }
  Args a = {sizeof a, live};
  live = NULL;
  long long t0 = now_ns();
  Collect c = {sizeof c, a.profiler, NULL, 0};
  if (failed(table->stop(&a), text, sizeof text) || failed(table->collect_data(&c), text, sizeof text)) {
    table->destroy(&a);
    mark("done", text);
    return;
  }
  uint8_t *bytes = c.buffer, *own = NULL;
  if (!bytes) {
    bytes = own = malloc(c.buffer_size_in_bytes ? c.buffer_size_in_bytes : 1);
    c.buffer = own;
    if (failed(table->collect_data(&c), text, sizeof text)) {
      free(own);
      table->destroy(&a);
      mark("done", text);
      return;
    }
  }
  size_t n = c.buffer_size_in_bytes;
  if (n && bytes[n - 1] == 0) n--;
  snprintf(path, sizeof path, "%s/pie-%d", dir, (int)getpid());
  mkdir(path, 0755);
  snprintf(path, sizeof path, "%s/pie-%d/trace.xplane.pb", dir, (int)getpid());
  FILE *f = fopen(path, "wb");
  size_t wrote = f ? fwrite(bytes, 1, n, f) : 0;
  if (f) fclose(f);
  free(own);
  table->destroy(&a);
  if (wrote != n) snprintf(text, sizeof text, "error wrote %zu of %zu bytes to %s", wrote, n, path);
  else snprintf(text, sizeof text, "ok %zu bytes in %.1f s", n, (now_ns() - t0) / 1e9);
  mark("done", text);
}

static void *loop(void *arg) {
  (void)arg;
  unsigned char s;
  while (read(pipe_fd[0], &s, 1) == 1) s == SIGUSR1 ? start() : stop();
  return NULL;
}

static void on_signal(int s) {
  unsigned char b = (unsigned char)s;
  ssize_t r = write(pipe_fd[1], &b, 1);
  (void)r;
}

__attribute__((constructor)) static void arm(void) {
  const char *d = getenv("PIE_BENCH_JAX_TRACE_DIR");
  char exe[4096];
  ssize_t n = readlink("/proc/self/exe", exe, sizeof exe - 1);
  if (!d || n <= 0) return;
  exe[n] = 0;
  const char *base = strrchr(exe, '/');
  if (strcmp(base ? base + 1 : exe, "pie") != 0) return;
  snprintf(dir, sizeof dir, "%s", d);
  mkdir(dir, 0755);
  if (pipe(pipe_fd) != 0) return;
  pthread_t t;
  sigset_t all, old;
  sigfillset(&all);
  pthread_sigmask(SIG_BLOCK, &all, &old);
  int ok = pthread_create(&t, NULL, loop, NULL) == 0;
  pthread_sigmask(SIG_SETMASK, &old, NULL);
  if (!ok) return;
  pthread_detach(t);
  struct sigaction sa;
  memset(&sa, 0, sizeof sa);
  sa.sa_handler = on_signal;
  sa.sa_flags = SA_RESTART;
  sigaction(SIGUSR1, &sa, NULL);
  sigaction(SIGUSR2, &sa, NULL);
  mark("pid", "");
}
