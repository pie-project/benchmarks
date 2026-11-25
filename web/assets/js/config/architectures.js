window.Pie = window.Pie || {};

Pie.architectures = {
  "gemma-4-e2b": { total: 4.647, emb: 0.403, tied: true, ple: 2.349, routed: 0, k: 1, full: 7, sliding: 28, window: 512, kvLayer: 1024, kvFull: 2048, linear: 0, state: 0, layers: 35, shared: 20, hidden: 1536 },
  "gemma-4-e4b": { total: 7.518, emb: 0.671, tied: true, ple: 2.819, routed: 0, k: 1, full: 7, sliding: 35, window: 512, kvLayer: 2048, kvFull: 4096, linear: 0, state: 0, layers: 42, shared: 18, hidden: 2560 },
  "gemma-4-12b": { total: 11.908, emb: 1.007, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 40, window: 1024, kvLayer: 8192, kvFull: 2048, linear: 0, state: 0, layers: 48, shared: 0, hidden: 3840 },
  "gemma-4-26b-a4b": { total: 25.233, emb: 0.738, tied: true, ple: 0, routed: 22.838, k: 0.0625, full: 5, sliding: 25, window: 1024, kvLayer: 8192, kvFull: 4096, linear: 0, state: 0, layers: 30, shared: 0, hidden: 2816 },
  "gemma-4-31b": { total: 30.697, emb: 1.409, tied: true, ple: 0, routed: 0, k: 1, full: 10, sliding: 50, window: 1024, kvLayer: 16384, kvFull: 8192, linear: 0, state: 0, layers: 60, shared: 0, hidden: 5376 },
  "qwen3.5-4b": { total: 4.205, emb: 0.636, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 1048576, layers: 32, shared: 0, hidden: 2560 },
  "qwen3.5-9b": { total: 8.954, emb: 1.017, tied: false, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 1048576, layers: 32, shared: 0, hidden: 4096 },
  "qwen3.6-35b-a3b": { total: 34.661, emb: 0.509, tied: false, ple: 0, routed: 32.212, k: 0.03125, full: 10, sliding: 0, window: 0, kvLayer: 2048, linear: 30, state: 1048576, layers: 40, shared: 0, hidden: 2048,
    routes: [[1, 0.0313], [2, 0.0541], [4, 0.0987], [8, 0.1615], [16, 0.2485], [32, 0.3482], [64, 0.4436], [128, 0.5391], [256, 0.6282], [512, 0.7009], [1024, 0.757]] },
  "qwen3.8-27b": { total: 26.895, emb: 1.271, tied: false, ple: 0, routed: 0, k: 1, full: 16, sliding: 0, window: 0, kvLayer: 4096, linear: 48, state: 1572864, layers: 64, shared: 0, hidden: 5120 },
  "qwen3.8-flash-next": { total: 176.944, emb: 0.636, tied: false, ple: 51.2, routed: 120.796, k: 0.01953, full: 12, sliding: 0, window: 0, kvLayer: 2048, linear: 36, state: 1572864, layers: 48, shared: 0, hidden: 2560 },
  "gpt-oss-20b": { total: 20.915, emb: 0.579, tied: false, ple: 0, routed: 19.11, k: 0.125, full: 12, sliding: 12, window: 128, kvLayer: 2048, linear: 0, state: 0, layers: 24, shared: 0, hidden: 2880 },
  "muse-glimmer-30b": { total: 27.855, emb: 1.345, tied: false, ple: 0, routed: 0, k: 1, full: 13, sliding: 39, window: 2048, kvLayer: 1024, linear: 0, state: 0, layers: 52, shared: 0, hidden: 6656 },
  "qwen3.5-0.8b": { total: 0.752, emb: 0.254, tied: true, ple: 0, routed: 0, k: 1, full: 6, sliding: 0, window: 0, kvLayer: 2048, linear: 18, state: 524288, layers: 24, shared: 0, hidden: 1024 },
  "qwen3.6-27b": { total: 26.895, emb: 1.271, tied: false, ple: 0, routed: 0, k: 1, full: 16, sliding: 0, window: 0, kvLayer: 4096, linear: 48, state: 1572864, layers: 64, shared: 0, hidden: 5120 },
  "gpt-oss-120b": { total: 116.829, emb: 0.579, tied: false, ple: 0, routed: 114.662, k: 0.03125, full: 18, sliding: 18, window: 128, kvLayer: 2048, linear: 0, state: 0, layers: 36, shared: 0, hidden: 2880 },
  "qwen3-0.6b": { total: 0.596, emb: 0.156, tied: true, ple: 0, routed: 0, k: 1, full: 28, sliding: 0, window: 0, kvLayer: 4096, linear: 0, state: 0, layers: 28, shared: 0, hidden: 1024 },
};
