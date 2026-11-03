"""Run one analysis script with extra environment variables and, optionally, in its own working sub-directory (kernel jobs that
must not share outputs, e.g. the same job on two devices). Arguments are passed through unchanged (the kernel runner has already
resolved DUMP / DIR: tokens to absolute paths).
Usage: envrun.py [VAR=VALUE ...] [@subdir] <script.py> [args...]"""
import sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]; env = dict(os.environ); cwd = None
while a and ("=" in a[0] and not a[0].endswith(".py") or a[0].startswith("@")):
    if a[0].startswith("@"): cwd = os.path.abspath(a[0][1:]); os.makedirs(cwd, exist_ok=True)
    else: k, v = a[0].split("=", 1); env[k] = v
    a = a[1:]
if cwd:                                   # relative inputs (e.g. Oxford's "results") stay relative to the caller's directory
    a = [os.path.abspath(x) if (os.path.exists(x) and not x.endswith(".py")) else x for x in a]
sys.exit(subprocess.run([sys.executable, os.path.join(HERE, a[0])] + a[1:], env=env, cwd=cwd).returncode)
