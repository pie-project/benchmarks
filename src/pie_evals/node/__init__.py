"""Node side: everything that runs on the machine under test. Takes a JobSpec,
writes records. Knows nothing about GitHub, RunPod, or queues."""

import os

# huggingface_hub reads these at import: its 10 s metadata/read timeouts failed whole shards on slow pod links (5090, A100 x2, nightly 36295521260)
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
