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
    return render_template(
        "index.html",
        has_cookies_file=bool(current_app.config.get("COOKIES_FILE")),
    )


@bp.route("/download", methods=["POST"])
def download():
    """Accept a URL and download the video/playlist."""
    url = request.form.get("url", "").strip()
    mode = request.form.get("mode", "video")
    browser = request.form.get("browser", "").strip() or None

    if not url:
        flash("Please enter a URL.")
        return redirect(url_for("main.index"))

    cookies_file = current_app.config.get("COOKIES_FILE")
    dl = Downloader(
        current_app.config["OUTPUT_DIR"],
        cookies_from_browser=browser if not cookies_file else None,
        cookies_file=cookies_file,
    )

    if mode == "playlist":
        results = dl.download_playlist(url)
    elif mode == "channel":
        results = dl.download_channel(url)
    else:
        results = [dl.download_video(url)]

    return render_template("status.html", results=results)
