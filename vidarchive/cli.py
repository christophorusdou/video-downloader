"""CLI entry point for vidarchive."""

import click

from .downloader import Downloader


@click.group()
def main():
    """vidarchive - Personal YouTube video archiver."""


@main.command()
@click.argument("url")
@click.option(
    "-o",
    "--output-dir",
    default="./downloads",
    type=click.Path(),
    help="Output directory for downloaded videos.",
)
def video(url, output_dir):
    """Download a single YouTube video."""
    dl = Downloader(output_dir)
    click.echo(f"Downloading video: {url}")
    result = dl.download_video(url)

    if result.success:
        click.echo(f"Saved: {result.video_path}")
        if result.metadata_path:
            click.echo(f"Metadata: {result.metadata_path}")
        if result.thumbnail_path:
            click.echo(f"Thumbnail: {result.thumbnail_path}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("url")
@click.option(
    "-o",
    "--output-dir",
    default="./downloads",
    type=click.Path(),
    help="Output directory for downloaded videos.",
)
def playlist(url, output_dir):
    """Download all videos in a YouTube playlist."""
    dl = Downloader(output_dir)
    click.echo(f"Downloading playlist: {url}")
    results = dl.download_playlist(url)

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    click.echo(f"\nDone: {succeeded} downloaded, {failed} failed")

    for r in results:
        if r.success:
            click.echo(f"  OK: {r.title}")
        else:
            click.echo(f"  FAIL: {r.error}", err=True)


@main.command()
@click.option(
    "-p", "--port", default=5000, type=int, help="Port to run the web UI on."
)
@click.option(
    "-o",
    "--output-dir",
    default="./downloads",
    type=click.Path(),
    help="Output directory for downloaded videos.",
)
def serve(port, output_dir):
    """Start the web UI."""
    from .web import create_app

    app = create_app(output_dir)
    click.echo(f"Starting web UI on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
