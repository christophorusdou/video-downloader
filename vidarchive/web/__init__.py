import os

from flask import Flask


def create_app(output_dir="./downloads", cookies_from_browser=None, cookies_file=None):
    app = Flask(__name__)
    app.config["OUTPUT_DIR"] = output_dir
    app.config["COOKIES_FROM_BROWSER"] = cookies_from_browser
    app.config["COOKIES_FILE"] = cookies_file
    app.secret_key = os.environ.get("SECRET_KEY", "vidarchive-dev-only")

    from .routes import bp

    app.register_blueprint(bp)
    return app
