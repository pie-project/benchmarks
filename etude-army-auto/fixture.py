import os
import subprocess
import sys

name, root = sys.argv[1], sys.argv[2]
os.makedirs(root, exist_ok=True)


def write(path, text):
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full) or root, exist_ok=True)
    with open(full, "w") as handle:
        handle.write(text)


def package(pkg, modules, functions, tested):
    write(f"{pkg}/__init__.py", "")
    for m in range(modules):
        body = "".join(
            f"\n\ndef op{m}_{f}(x):\n    \"\"\"Return x * {m + 2} + {f}.\"\"\"\n    raise NotImplementedError\n"
            for f in range(functions)
        )
        write(f"{pkg}/m{m}.py", body.lstrip())
        if m < tested:
            cases = "".join(
                f"\n    def test_op{m}_{f}(self):\n        self.assertEqual(m{m}.op{m}_{f}(3), {3 * (m + 2) + f})\n"
                for f in range(functions)
            )
            write(f"test_m{m}.py", f"import unittest\n\nfrom {pkg} import m{m}\n\n\nclass TestM{m}(unittest.TestCase):{cases}")


if name in ("median", "best"):
    write("stats.py", "def mean(values):\n    return sum(values) / len(values)\n\n\ndef median(values):\n    ordered = sorted(values)\n    return ordered[len(ordered) // 2 - 1]\n")
    write("test_stats.py", "import unittest\n\nfrom stats import mean, median\n\n\nclass TestStats(unittest.TestCase):\n    def test_mean(self):\n        self.assertEqual(mean([1, 2, 3]), 2)\n\n    def test_median_odd(self):\n        self.assertEqual(median([3, 1, 2]), 2)\n")
elif name.startswith("library"):
    package("geometry", 16, 4, 16)
elif name == "escalate":
    package("units", 6, 1, 2)
else:
    sys.exit(f"unknown fixture {name}")


def git(*args):
    subprocess.run(["git", *args], cwd=root, check=True)


git("init", "-q")
git("config", "user.name", "etude army")
git("config", "user.email", "army@example.invalid")
git("add", "-A")
git("commit", "-qm", "fixture")
