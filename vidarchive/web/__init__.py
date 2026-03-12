from flask import Flask


def create_app(output_dir="./downloads"):
    app = Flask(__name__)
    app.config["OUTPUT_DIR"] = output_dir
    app.secret_key = "vidarchive-local"

    from .routes import bp

    app.register_blueprint(bp)
    return app
