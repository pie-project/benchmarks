from __future__ import annotations

import re

from pie_bench.schema import ErrorClass

_ERROR_PATTERNS: list[tuple[ErrorClass, re.Pattern[str]]] = [
    (ErrorClass.OOM, re.compile(r"out of memory|CUDA_ERROR_OUT_OF_MEMORY|OutOfMemoryError|cudaErrorMemoryAllocation|kIOGPUCommandBufferCallbackErrorOutOfMemory|MTLResourceOptions.*failed|insufficient memory", re.I)),
    (ErrorClass.DOESNT_FIT, re.compile(r"does not fit|refus\w+ .*fit|exceeds .*working set|recommendedMaxWorkingSetSize|host fit check", re.I)),
    (ErrorClass.LOAD_FAIL, re.compile(r"failed to load|load plan|missing quant metadata|unknown variant|No such file|safetensors|model import|failed to import|not found in cache|resolve_local_model|matches no SKU|no SKU this build|missing .*\.wasm|in /root/\.pie/models|not in HF cache|pull model manifest|model .* not found", re.I)),
    (ErrorClass.CRASH, re.compile(r"Traceback|panicked at|Segmentation fault|SIGSEGV|SIGABRT|invalid resource handle|invalid argument|NCCL error|cudaGraphInstantiate", re.I)),
]


def classify_failure(returncode: int, stderr: str, stdout: str, timed_out: bool) -> tuple[ErrorClass, str]:
    if timed_out:
        return ErrorClass.HANG, "timed out (hang is only ever observed via timeout)"
    text = stderr + "\n" + stdout
    if "Traceback (most recent call last)" in text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        at = next((i for i in reversed(range(len(lines))) if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*(Error|Exception|Exit|Interrupt)\b", lines[i])), len(lines) - 1)
        exc = " | ".join(lines[at:]) or "Traceback"
        told = exc if len(exc) <= 1000 else lines[at][:300] + " | ... " + exc[-690:]
        for cls, pat in _ERROR_PATTERNS[:3]:
            if pat.search(exc):
                return cls, told
        return ErrorClass.CRASH, told
    for cls, pat in _ERROR_PATTERNS:
        m = pat.search(text)
        if m:
            line = next((ln for ln in text.splitlines() if m.group(0) in ln), m.group(0))
            return cls, line.strip()[:400]
    if returncode < 0:
        return ErrorClass.CRASH, f"killed by signal {-returncode}"
    return ErrorClass.CRASH, f"exit {returncode}: " + (stderr.strip().splitlines() or ["(no stderr)"])[-1][:400]
