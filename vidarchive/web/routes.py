"""Flask route handlers for the web UI."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ..downloader import Downloader

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Show the download form."""
    return render_template("index.html")


@bp.route("/download", methods=["POST"])
def download():
    """Accept a URL and download the video/playlist."""
    url = request.form.get("url", "").strip()
    mode = request.form.get("mode", "video")

    if not url:
        flash("Please enter a URL.")
        return redirect(url_for("main.index"))

    dl = Downloader(
        current_app.config["OUTPUT_DIR"],
        cookies_from_browser=current_app.config.get("COOKIES_FROM_BROWSER"),
    )

    if mode == "playlist":
        results = dl.download_playlist(url)
    elif mode == "channel":
        results = dl.download_channel(url)
    else:
        results = [dl.download_video(url)]

    return render_template("status.html", results=results)
