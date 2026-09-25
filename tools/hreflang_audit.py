#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools/seo_check.py"), *sys.argv[1:]]))
