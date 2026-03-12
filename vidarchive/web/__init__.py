from flask import Flask


def create_app(output_dir="./downloads", cookies_from_browser=None):
    app = Flask(__name__)
    app.config["OUTPUT_DIR"] = output_dir
    app.config["COOKIES_FROM_BROWSER"] = cookies_from_browser
    app.secret_key = "vidarchive-local"

    from .routes import bp

    app.register_blueprint(bp)
    return app
