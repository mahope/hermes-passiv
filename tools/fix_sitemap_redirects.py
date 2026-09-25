#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
build = subprocess.run([sys.executable, str(ROOT / "build_sites.py"), *sys.argv[1:]])
if build.returncode:
    raise SystemExit(build.returncode)
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools/check_sitemaps.py"), *sys.argv[1:]]))
