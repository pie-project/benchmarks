import os
import signal
import subprocess
import sys
import threading


def main() -> int:
    child = subprocess.Popen(sys.argv[1:], start_new_session=True)

    def stop(*_):
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(child.pid)], capture_output=True, check=False
            )
            return
        for sig, wait in ((signal.SIGTERM, 20), (signal.SIGKILL, 5)):
            try:
                os.killpg(child.pid, sig)
            except ProcessLookupError:
                return
            except PermissionError:
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
