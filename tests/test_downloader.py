"""Tests for the core downloader module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

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

    def test_ydl_opts_no_cookies_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts()

            assert "cookiesfrombrowser" not in opts

    def test_ydl_opts_with_cookies_from_browser(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir, cookies_from_browser="chrome")
            opts = dl._get_ydl_opts()

            assert opts["cookiesfrombrowser"] == ("chrome",)

    def test_ydl_opts_with_cookies_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cookies_path = Path(tmpdir) / "cookies.txt"
            cookies_path.write_text("# Netscape HTTP Cookie File\n")

            dl = Downloader(tmpdir, cookies_file=str(cookies_path))
            opts = dl._get_ydl_opts()

            assert opts["cookiefile"] == str(cookies_path)
            assert "cookiesfrombrowser" not in opts

    def test_ydl_opts_cookies_file_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cookies_path = Path(tmpdir) / "cookies.txt"
            cookies_path.write_text("# Netscape HTTP Cookie File\n")

            dl = Downloader(
                tmpdir,
                cookies_from_browser="chrome",
                cookies_file=str(cookies_path),
            )
            opts = dl._get_ydl_opts()

            assert opts["cookiefile"] == str(cookies_path)
            assert "cookiesfrombrowser" not in opts

    def test_ydl_opts_cookies_file_missing_falls_back(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(
                tmpdir,
                cookies_from_browser="chrome",
                cookies_file="/nonexistent/cookies.txt",
            )
            opts = dl._get_ydl_opts()

            assert "cookiefile" not in opts
            assert opts["cookiesfrombrowser"] == ("chrome",)

    def test_ydl_opts_no_cookies_file_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            opts = dl._get_ydl_opts()

            assert "cookiefile" not in opts

    def test_disk_space_check_passes_normally(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            assert dl._check_disk_space() is None

    def test_disk_space_check_fails_when_low(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            # Mock disk_usage to return very low free space (1 GB)
            mock_usage = type("Usage", (), {"free": 1 * (1024**3)})()
            with patch("vidarchive.downloader.shutil.disk_usage", return_value=mock_usage):
                error = dl._check_disk_space()
                assert error is not None
                assert "Low disk space" in error

    def test_download_video_refuses_on_low_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            mock_usage = type("Usage", (), {"free": 1 * (1024**3)})()
            with patch("vidarchive.downloader.shutil.disk_usage", return_value=mock_usage):
                result = dl.download_video("https://youtube.com/watch?v=test")
                assert result.success is False
                assert "Low disk space" in result.error

    def test_download_playlist_refuses_on_low_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = Downloader(tmpdir)
            mock_usage = type("Usage", (), {"free": 1 * (1024**3)})()
            with patch("vidarchive.downloader.shutil.disk_usage", return_value=mock_usage):
                results = dl.download_playlist("https://youtube.com/playlist?list=test")
                assert len(results) == 1
                assert results[0].success is False
                assert "Low disk space" in results[0].error
