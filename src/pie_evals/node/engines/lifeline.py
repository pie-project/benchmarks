import os
import signal
import subprocess
import sys
import threading


def main() -> int:
    # its own process group: a server that starts helpers (Splash, Ollama) is stopped whole
    child = subprocess.Popen(sys.argv[1:], start_new_session=True)

    def stop(*_):
        for sig, wait in ((signal.SIGTERM, 20), (signal.SIGKILL, 5)):
            try:
                os.killpg(child.pid, sig)
            except ProcessLookupError:
                return
            except PermissionError:
                # macOS refuses the group when one member is already gone; the child itself can still be told
                child.send_signal(sig)
            try:
                child.wait(timeout=wait)
            except subprocess.TimeoutExpired:
                continue

    signal.signal(signal.SIGTERM, lambda *a: (stop(), sys.exit(0)))
    signal.signal(signal.SIGINT, lambda *a: (stop(), sys.exit(0)))
    threading.Thread(target=lambda: (sys.stdin.read(), stop()), daemon=True).start()
    return child.wait()


if __name__ == "__main__":
    sys.exit(main())
