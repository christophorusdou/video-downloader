"""Core download logic wrapping yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yt_dlp


@dataclass
class DownloadResult:
    """Result of a single video download."""

    title: str
    video_path: Path | None
    metadata_path: Path | None
    thumbnail_path: Path | None
    url: str
    success: bool
    error: str | None = None
    duration: int | None = None


class Downloader:
    """Downloads YouTube videos and playlists using yt-dlp."""

    def __init__(self, output_dir: str = "./downloads", cookies_from_browser: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_from_browser = cookies_from_browser

    def _get_ydl_opts(self, *, is_playlist: bool = False) -> dict:
        """Build yt-dlp options dict."""
        outtmpl = str(
            self.output_dir / "%(uploader)s" / "%(title)s [%(id)s].%(ext)s"
        )
        opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mkv",
            "outtmpl": outtmpl,
            "writethumbnail": True,
            "writeinfojson": True,
            "postprocessors": [
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
            ],
            "noplaylist": not is_playlist,
            "quiet": False,
            "no_warnings": False,
        }
        if self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return opts

    def download_video(self, url: str) -> DownloadResult:
        """Download a single video at best quality with metadata."""
        opts = self._get_ydl_opts(is_playlist=False)
        return self._do_download(url, opts)

    def download_channel(self, url: str) -> list[DownloadResult]:
        """Download all videos from a channel."""
        return self.download_playlist(url)

    def download_playlist(self, url: str) -> list[DownloadResult]:
        """Download all videos in a playlist or channel."""
        opts = self._get_ydl_opts(is_playlist=True)
        results: list[DownloadResult] = []

        # First extract playlist info to get entries
        try:
            with yt_dlp.YoutubeDL({**opts, "extract_flat": True}) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            return [
                DownloadResult(
                    title="Playlist",
                    video_path=None,
                    metadata_path=None,
                    thumbnail_path=None,
                    url=url,
                    success=False,
                    error=str(e),
                )
            ]

        if info is None:
            return [
                DownloadResult(
                    title="Playlist",
                    video_path=None,
                    metadata_path=None,
                    thumbnail_path=None,
                    url=url,
                    success=False,
                    error="Could not extract playlist info",
                )
            ]

        entries = info.get("entries", [])
        if not entries:
            return [
                DownloadResult(
                    title=info.get("title", "Playlist"),
                    video_path=None,
                    metadata_path=None,
                    thumbnail_path=None,
                    url=url,
                    success=False,
                    error="Playlist is empty",
                )
            ]

        # Download each entry
        for entry in entries:
            entry_url = entry.get("url") or entry.get("webpage_url", "")
            if not entry_url:
                continue
            result = self._do_download(entry_url, opts)
            results.append(result)

        return results

    def _do_download(self, url: str, opts: dict) -> DownloadResult:
        """Execute a single download and return a DownloadResult."""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

            if info is None:
                return DownloadResult(
                    title="Unknown",
                    video_path=None,
                    metadata_path=None,
                    thumbnail_path=None,
                    url=url,
                    success=False,
                    error="Could not extract video info",
                )

            title = info.get("title", "Unknown")
            video_id = info.get("id", "unknown")
            uploader = info.get("uploader", "Unknown")
            duration = info.get("duration")

            base_dir = self.output_dir / uploader
            base_name = f"{title} [{video_id}]"

            # Find the actual video file (yt-dlp may use sanitized names)
            video_path = None
            for ext in ("mkv", "mp4", "webm"):
                candidate = base_dir / f"{base_name}.{ext}"
                if candidate.exists():
                    video_path = candidate
                    break

            metadata_path = base_dir / f"{base_name}.info.json"
            thumbnail_path = base_dir / f"{base_name}.jpg"

            return DownloadResult(
                title=title,
                video_path=video_path,
                metadata_path=metadata_path if metadata_path.exists() else None,
                thumbnail_path=thumbnail_path if thumbnail_path.exists() else None,
                url=url,
                success=True,
                duration=duration,
            )

        except yt_dlp.utils.DownloadError as e:
            return DownloadResult(
                title="Unknown",
                video_path=None,
                metadata_path=None,
                thumbnail_path=None,
                url=url,
                success=False,
                error=str(e),
            )
        except Exception as e:
            return DownloadResult(
                title="Unknown",
                video_path=None,
                metadata_path=None,
                thumbnail_path=None,
                url=url,
                success=False,
                error=f"Unexpected error: {e}",
            )
