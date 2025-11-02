"""
Comprehensive tests for thumbnail extraction and download functionality.

Tests thumbnail URL generation, downloading with quality fallback, and metadata extraction.
"""

from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from yt_thumbs.extractor import download_thumbnail, get_thumbnail_url, get_video_metadata


class TestGetThumbnailUrl:
    """Test thumbnail URL generation."""

    def test_basic_video_id(self, video_id):
        """Test thumbnail URL generation with standard video ID"""
        url = get_thumbnail_url(video_id)
        assert url == f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    def test_url_format(self, video_id):
        """Test that URL follows correct format"""
        url = get_thumbnail_url(video_id)
        assert url.startswith("https://img.youtube.com/vi/")
        assert url.endswith("/maxresdefault.jpg")
        assert video_id in url

    def test_different_video_ids(self):
        """Test URL generation with multiple video IDs"""
        video_ids = ["dQw4w9WgXcQ", "jNQXAC9IVRw", "abc123XyZ-_"]
        for vid_id in video_ids:
            url = get_thumbnail_url(vid_id)
            assert vid_id in url
            assert url == f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"

    def test_video_id_with_special_chars(self):
        """Test URL generation with video ID containing special characters"""
        video_id = "test-video_1"
        url = get_thumbnail_url(video_id)
        assert url == "https://img.youtube.com/vi/test-video_1/maxresdefault.jpg"


class TestDownloadThumbnail:
    """Test thumbnail downloading with quality fallback."""

    @patch("urllib.request.urlopen")
    def test_successful_download_maxres(self, mock_urlopen, video_id, temp_dir):
        """Test successful download of maxresdefault quality"""
        output_path = temp_dir / "thumbnail.jpg"

        # Mock successful response with valid content length
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.headers.get.return_value = "5000"  # >1000 bytes
        mock_response.read.return_value = b"fake image data"
        mock_urlopen.return_value = mock_response

        result = download_thumbnail(video_id, str(output_path))

        assert result is True
        assert output_path.exists()
        assert output_path.read_bytes() == b"fake image data"

    @patch("urllib.request.urlopen")
    def test_fallback_to_hqdefault(self, mock_urlopen, video_id, temp_dir):
        """Test fallback to hqdefault when maxres fails"""
        output_path = temp_dir / "thumbnail.jpg"

        # First call (maxres) raises 404
        # Second call (hqdefault) succeeds
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b"hq image data"

        def side_effect(url):
            if "maxresdefault" in url:
                raise HTTPError(url, 404, "Not Found", {}, None)
            return mock_response

        mock_urlopen.side_effect = side_effect

        result = download_thumbnail(video_id, str(output_path))

        assert result is True
        assert output_path.exists()
        assert output_path.read_bytes() == b"hq image data"

    @patch("urllib.request.urlopen")
    def test_fallback_on_small_content_length(self, mock_urlopen, video_id, temp_dir):
        """Test fallback when maxres returns small content (thumbnail not available)"""
        output_path = temp_dir / "thumbnail.jpg"

        # First call returns small content length (placeholder image)
        mock_maxres = MagicMock()
        mock_maxres.__enter__.return_value = mock_maxres
        mock_maxres.headers.get.return_value = "500"  # <1000 bytes, placeholder

        # Second call (hqdefault) succeeds
        mock_hq = MagicMock()
        mock_hq.__enter__.return_value = mock_hq
        mock_hq.read.return_value = b"hq image data"

        mock_urlopen.side_effect = [mock_maxres, mock_hq]

        result = download_thumbnail(video_id, str(output_path))

        assert result is True
        assert output_path.exists()

    @patch("urllib.request.urlopen")
    def test_both_qualities_fail_404(self, mock_urlopen, video_id, temp_dir):
        """Test complete failure when both qualities return 404"""
        output_path = temp_dir / "thumbnail.jpg"

        # Both calls raise 404
        mock_urlopen.side_effect = HTTPError("", 404, "Not Found", {}, None)

        result = download_thumbnail(video_id, str(output_path))

        assert result is False
        assert not output_path.exists()

    @patch("urllib.request.urlopen")
    def test_network_error(self, mock_urlopen, video_id, temp_dir):
        """Test handling of network errors"""
        output_path = temp_dir / "thumbnail.jpg"

        # Network error on all attempts
        mock_urlopen.side_effect = URLError("Network unreachable")

        result = download_thumbnail(video_id, str(output_path))

        assert result is False
        assert not output_path.exists()

    @patch("urllib.request.urlopen")
    def test_file_write_error(self, mock_urlopen, video_id):
        """Test handling of file write errors"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.headers.get.return_value = "5000"
        mock_response.read.return_value = b"fake image data"
        mock_urlopen.return_value = mock_response

        # Invalid path that will cause OSError
        invalid_path = "/invalid/path/that/does/not/exist/thumbnail.jpg"

        # The current implementation doesn't catch OSError on file write
        # It only catches on the fallback hqdefault download
        # So we expect this to raise an exception
        with pytest.raises((OSError, FileNotFoundError, PermissionError)):
            download_thumbnail(video_id, invalid_path)

    @patch("urllib.request.urlopen")
    def test_creates_parent_directory(self, mock_urlopen, video_id, temp_dir):
        """Test that parent directories are NOT created (documents current behavior)"""
        # Note: The current implementation doesn't create parent dirs
        # This test documents the current behavior
        output_path = temp_dir / "subdir" / "thumbnail.jpg"

        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.headers.get.return_value = "5000"
        mock_response.read.return_value = b"fake image data"
        mock_urlopen.return_value = mock_response

        # Parent directory doesn't exist, so this will raise FileNotFoundError
        with pytest.raises((OSError, FileNotFoundError)):
            download_thumbnail(video_id, str(output_path))

    @patch("urllib.request.urlopen")
    def test_urlopen_called_with_correct_urls(self, mock_urlopen, video_id, temp_dir):
        """Test that urlopen is called with correct thumbnail URLs"""
        output_path = temp_dir / "thumbnail.jpg"

        # Both calls fail to test that both URLs are tried
        mock_urlopen.side_effect = HTTPError("", 404, "Not Found", {}, None)

        download_thumbnail(video_id, str(output_path))

        # Verify both maxresdefault and hqdefault URLs were attempted
        calls = mock_urlopen.call_args_list
        assert len(calls) == 2
        assert "maxresdefault" in str(calls[0])
        assert "hqdefault" in str(calls[1])


class TestGetVideoMetadata:
    """Test video metadata extraction."""

    @patch("urllib.request.urlopen")
    def test_successful_metadata_extraction(self, mock_urlopen, video_id, mock_video_html):
        """Test successful extraction of title, description, and thumbnail"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = mock_video_html.encode("utf-8")
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == "Rick Astley - Never Gonna Give You Up"
        assert (
            metadata["description"]
            == "The official video for Rick Astley's Never Gonna Give You Up"
        )
        assert (
            metadata["thumbnail_url"] == f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        )

    @patch("urllib.request.urlopen")
    def test_missing_title(self, mock_urlopen, video_id, mock_video_html_no_title):
        """Test metadata extraction when title is missing"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = mock_video_html_no_title.encode("utf-8")
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == "Some description"
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_missing_description(self, mock_urlopen, video_id, mock_video_html_no_description):
        """Test metadata extraction when description is missing"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = mock_video_html_no_description.encode("utf-8")
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == "Test Video"
        assert metadata["description"] == ""
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_network_error_returns_empty_metadata(self, mock_urlopen, video_id):
        """Test that network errors return empty metadata gracefully"""
        mock_urlopen.side_effect = URLError("Network unreachable")

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert (
            metadata["thumbnail_url"] == f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        )

    @patch("urllib.request.urlopen")
    def test_http_error_returns_empty_metadata(self, mock_urlopen, video_id):
        """Test that HTTP errors return empty metadata gracefully"""
        mock_urlopen.side_effect = HTTPError("", 404, "Not Found", {}, None)

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_malformed_html(self, mock_urlopen, video_id):
        """Test handling of malformed HTML without meta tags"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b"<html><body>No meta tags here</body></html>"
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_empty_html_response(self, mock_urlopen, video_id):
        """Test handling of empty HTML response"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b""
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen, video_id):
        """Test handling of timeout errors"""
        mock_urlopen.side_effect = OSError("Timeout")

        metadata = get_video_metadata(video_id)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert "thumbnail_url" in metadata

    @patch("urllib.request.urlopen")
    def test_urlopen_called_with_correct_url(self, mock_urlopen, video_id):
        """Test that urlopen is called with correct YouTube video URL"""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b"<html></html>"
        mock_urlopen.return_value = mock_response

        get_video_metadata(video_id)

        expected_url = f"https://www.youtube.com/watch?v={video_id}"
        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args
        assert call_args[0][0] == expected_url
        assert call_args[1]["timeout"] == 10

    @patch("urllib.request.urlopen")
    def test_special_characters_in_metadata(self, mock_urlopen, video_id):
        """Test handling of special characters in title and description"""
        html_with_special_chars = """
        <html>
        <head>
            <meta property="og:title" content="Test & Video | Special 'Chars' \"Quotes\"">
            <meta property="og:description" content="Description with <tags> & symbols">
        </head>
        </html>
        """
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = html_with_special_chars.encode("utf-8")
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        # The regex captures content until the first unescaped quote
        # So "Test & Video | Special 'Chars' " is expected (truncated at \")
        assert "Test & Video | Special 'Chars' " in metadata["title"]
        # Description captures until closing quote properly
        assert "Description with <tags> & symbols" in metadata["description"]

    @patch("urllib.request.urlopen")
    def test_unicode_in_metadata(self, mock_urlopen, video_id):
        """Test handling of Unicode characters in metadata"""
        html_with_unicode = """
        <html>
        <head>
            <meta property="og:title" content="日本語 Title 中文 العربية">
            <meta property="og:description" content="Emoji test 🎵 🎬 🎮">
        </head>
        </html>
        """
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = html_with_unicode.encode("utf-8")
        mock_urlopen.return_value = mock_response

        metadata = get_video_metadata(video_id)

        assert "日本語" in metadata["title"]
        assert "🎵" in metadata["description"]
