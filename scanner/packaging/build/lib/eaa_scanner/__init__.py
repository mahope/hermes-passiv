"""eaa-scanner — universal EAA/WCAG compliance scanner.

Pure stdlib. Scan a URL or an HTML file, get a scored report.
"""

from .core import scan_html, scan_url, contrast_ratio  # noqa: F401

__version__ = "1.2.0"
