#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

from check_live_sitemaps import main

ROOT = Path(__file__).resolve().parent.parent
build = subprocess.run([sys.executable, str(ROOT / "build_sites.py")])
if build.returncode:
    raise SystemExit(build.returncode)
raise SystemExit(main(sys.argv[1:]))
