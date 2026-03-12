"""Tests for the core downloader module."""

import tempfile
from pathlib import Path

from vidarchive.downloader import DownloadResult, Downloader


class TestDownloadResult:
    def test_success_result(self):
        result = DownloadResult(
            title="Test Video",
            video_path=Path("/tmp/test.mkv"),
            metadata_path=Path("/tmp/test.info.json"),
            thumbnail_path=Path("/tmp/test.jpg"),
            url="https://youtube.com/watch?v=test",
            success=True,
            duration=120,
        )
        assert result.success is True
        assert result.title == "Test Video"
        assert result.error is None
        assert result.duration == 120

    def test_error_result(self):
        result = DownloadResult(
            title="Unknown",
            video_path=None,
            metadata_path=None,
            thumbnail_path=None,
            url="https://youtube.com/watch?v=bad",
            success=False,
            error="Video not found",
        )
        assert result.success is False
        assert result.error == "Video not found"
        assert result.video_path is None


class TestDownloader:
    def test_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "new_subdir" / "downloads"
            dl = Downloader(str(output))
            assert output.exists()
            assert output.is_dir()

    def test_default_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            assert dl.output_dir == Path(tmpdir)

    def test_ydl_opts_single_video(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts(is_playlist=False)

            assert opts["format"] == "bestvideo+bestaudio/best"
            assert opts["merge_output_format"] == "mkv"
            assert opts["writethumbnail"] is True
            assert opts["writeinfojson"] is True
            assert opts["noplaylist"] is True

    def test_ydl_opts_playlist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts(is_playlist=True)

            assert opts["noplaylist"] is False

    def test_ydl_opts_output_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts()

            assert "%(uploader)s" in opts["outtmpl"]
            assert "%(title)s" in opts["outtmpl"]
            assert "%(id)s" in opts["outtmpl"]
            assert "%(ext)s" in opts["outtmpl"]

    def test_ydl_opts_has_thumbnail_converter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts()

            pp_keys = [pp["key"] for pp in opts["postprocessors"]]
            assert "FFmpegThumbnailsConvertor" in pp_keys
