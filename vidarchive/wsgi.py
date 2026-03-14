"""WSGI entrypoint for production deployment (gunicorn)."""

import os

from vidarchive.web import create_app

app = create_app(
    output_dir=os.environ.get("VIDARCHIVE_OUTPUT_DIR", "/downloads"),
    cookies_file=os.environ.get("VIDARCHIVE_COOKIES_FILE"),
)
