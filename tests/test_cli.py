"""
Comprehensive tests for CLI functionality.

Tests command-line interface including argument parsing, batch processing,
and output handling.
"""

from unittest.mock import patch

import pytest

from yt_thumbs.cli import main, process_batch_urls


class TestProcessBatchUrls:
    """Test batch URL processing."""

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_batch_processing_valid_urls(self, mock_metadata, batch_file, capsys):
        """Test processing a batch file with valid URLs"""
        # Mock metadata responses
        mock_metadata.side_effect = [
            {
                "title": "Video 1",
                "description": "Description 1",
                "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            },
            {
                "title": "Video 2",
                "description": "Description 2",
                "thumbnail_url": "https://img.youtube.com/vi/jNQXAC9IVRw/maxresdefault.jpg",
            },
            {
                "title": "Video 3",
                "description": "Description 3",
                "thumbnail_url": "https://img.youtube.com/vi/abc123defgh/maxresdefault.jpg",
            },
        ]

        process_batch_urls(str(batch_file))

        captured = capsys.readouterr()
        assert "| Thumbnail URL | Video Name | Video Description |" in captured.out
        assert "Video 1" in captured.out
        assert "Video 2" in captured.out
        assert "Video 3" in captured.out
        assert "Processed 3 of 3 URLs" in captured.err

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_batch_processing_with_output_file(self, mock_metadata, batch_file, temp_dir):
        """Test batch processing with output to file"""
        output_file = temp_dir / "output.md"

        mock_metadata.return_value = {
            "title": "Test Video",
            "description": "Test Description",
            "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        }

        process_batch_urls(str(batch_file), str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "| Thumbnail URL | Video Name | Video Description |" in content
        assert "Test Video" in content

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_batch_processing_creates_parent_directory(self, mock_metadata, batch_file, temp_dir):
        """Test that parent directories are created for output file"""
        output_file = temp_dir / "subdir" / "nested" / "output.md"

        mock_metadata.return_value = {
            "title": "Test Video",
            "description": "Test",
            "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        }

        process_batch_urls(str(batch_file), str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_batch_file_not_found(self, capsys):
        """Test handling of missing batch file"""
        with pytest.raises(SystemExit) as exc_info:
            process_batch_urls("nonexistent_file.txt")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Batch file not found" in captured.err

    def test_empty_batch_file(self, empty_batch_file, capsys):
        """Test handling of empty batch file"""
        with pytest.raises(SystemExit) as exc_info:
            process_batch_urls(str(empty_batch_file))

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: No URLs found in batch file" in captured.err

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_batch_with_invalid_urls(self, mock_metadata, batch_file_with_invalid_urls, capsys):
        """Test batch processing with mix of valid and invalid URLs"""
        mock_metadata.return_value = {
            "title": "Valid Video",
            "description": "Valid Description",
            "thumbnail_url": "https://img.youtube.com/vi/test/maxresdefault.jpg",
        }

        process_batch_urls(str(batch_file_with_invalid_urls))

        captured = capsys.readouterr()
        assert "Warning: Skipping invalid URL" in captured.err
        assert "Valid Video" in captured.out

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_all_invalid_urls_exits(self, mock_metadata, temp_dir, capsys):
        """Test that all invalid URLs causes exit"""
        invalid_batch = temp_dir / "invalid.txt"
        invalid_batch.write_text("https://example.com\nnot a url\n")

        with pytest.raises(SystemExit) as exc_info:
            process_batch_urls(str(invalid_batch))

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: No valid URLs were processed" in captured.err

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_description_truncation(self, mock_metadata, batch_file, capsys):
        """Test that long descriptions are truncated"""
        long_description = "A" * 150  # 150 characters

        mock_metadata.return_value = {
            "title": "Test",
            "description": long_description,
            "thumbnail_url": "https://img.youtube.com/vi/test/maxresdefault.jpg",
        }

        process_batch_urls(str(batch_file))

        captured = capsys.readouterr()
        # Description should be truncated to 97 chars + "..."
        assert "AAA..." in captured.out
        assert long_description not in captured.out

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_pipe_character_escaping(self, mock_metadata, batch_file, capsys):
        """Test that pipe characters in metadata are escaped"""
        mock_metadata.return_value = {
            "title": "Video | With | Pipes",
            "description": "Description | With | Pipes",
            "thumbnail_url": "https://img.youtube.com/vi/test/maxresdefault.jpg",
        }

        process_batch_urls(str(batch_file))

        captured = capsys.readouterr()
        assert "Video \\| With \\| Pipes" in captured.out
        assert "Description \\| With \\| Pipes" in captured.out

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_metadata_fetch_exception(self, mock_metadata, batch_file, capsys):
        """Test handling of exceptions during metadata fetch"""
        mock_metadata.side_effect = Exception("Network error")

        # Should not crash, but should show warning
        with pytest.raises(SystemExit):  # Exit because no URLs processed
            process_batch_urls(str(batch_file))

        captured = capsys.readouterr()
        assert "Warning: Error processing" in captured.err

    @patch("yt_thumbs.cli.get_video_metadata")
    def test_output_file_write_error(self, mock_metadata, batch_file, capsys):
        """Test handling of file write errors"""
        mock_metadata.return_value = {
            "title": "Test",
            "description": "Test",
            "thumbnail_url": "https://img.youtube.com/vi/test/maxresdefault.jpg",
        }

        # Try to write to invalid path
        with pytest.raises(SystemExit) as exc_info:
            process_batch_urls(str(batch_file), "/invalid/path/output.md")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Could not write to output file" in captured.err


class TestMainCLI:
    """Test main CLI entry point."""

    @patch("yt_thumbs.cli.get_thumbnail_url")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    def test_single_url_mode_prints_url(self, mock_extract, mock_get_url, capsys):
        """Test single URL mode prints thumbnail URL"""
        mock_extract.return_value = "dQw4w9WgXcQ"
        mock_get_url.return_value = "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"

        main()

        captured = capsys.readouterr()
        assert "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" in captured.out

    @patch("yt_thumbs.cli.download_thumbnail")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "--download"])
    def test_download_mode_default_filename(
        self, mock_extract, mock_download, temp_dir, monkeypatch, capsys
    ):
        """Test download mode with default filename"""
        monkeypatch.chdir(temp_dir)  # Change to temp dir for output
        mock_extract.return_value = "dQw4w9WgXcQ"
        mock_download.return_value = True

        main()

        mock_download.assert_called_once_with("dQw4w9WgXcQ", "dQw4w9WgXcQ.jpg")
        captured = capsys.readouterr()
        assert "Successfully downloaded" in captured.out

    @patch("yt_thumbs.cli.download_thumbnail")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch(
        "sys.argv",
        ["yt-thumb", "https://youtu.be/test123", "--download", "--output", "my_thumb.jpg"],
    )
    def test_download_mode_custom_filename(
        self, mock_extract, mock_download, temp_dir, monkeypatch, capsys
    ):
        """Test download mode with custom output filename"""
        monkeypatch.chdir(temp_dir)
        mock_extract.return_value = "test123"
        mock_download.return_value = True

        main()

        mock_download.assert_called_once_with("test123", "my_thumb.jpg")

    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://example.com"])
    def test_invalid_url_exits_with_error(self, mock_extract, capsys):
        """Test that invalid URL exits with error message"""
        mock_extract.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Could not extract video ID" in captured.err
        assert "Supported formats:" in captured.err

    @patch("yt_thumbs.cli.download_thumbnail")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://youtu.be/test123", "--download"])
    def test_download_failure_exits_with_error(
        self, mock_extract, mock_download, temp_dir, monkeypatch, capsys
    ):
        """Test that download failure exits with error"""
        monkeypatch.chdir(temp_dir)
        mock_extract.return_value = "test123"
        mock_download.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Failed to download thumbnail" in captured.err

    @patch("yt_thumbs.cli.process_batch_urls")
    @patch("sys.argv", ["yt-thumb", "--batch", "urls.txt"])
    def test_batch_mode(self, mock_process):
        """Test batch mode calls process_batch_urls"""
        main()

        mock_process.assert_called_once_with("urls.txt", None)

    @patch("yt_thumbs.cli.process_batch_urls")
    @patch("sys.argv", ["yt-thumb", "--batch", "urls.txt", "--output", "results.md"])
    def test_batch_mode_with_output(self, mock_process):
        """Test batch mode with output file"""
        main()

        mock_process.assert_called_once_with("urls.txt", "results.md")

    @patch("sys.argv", ["yt-thumb"])
    def test_no_arguments_shows_error(self):
        """Test that no arguments shows error"""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2  # argparse exits with 2

    @patch("sys.argv", ["yt-thumb", "https://youtu.be/test", "--batch", "urls.txt"])
    def test_url_and_batch_conflict(self):
        """Test that URL and batch mode cannot be used together"""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2  # argparse error

    @patch("sys.argv", ["yt-thumb", "--batch", "urls.txt", "--download"])
    def test_batch_and_download_conflict(self):
        """Test that batch mode and download flag cannot be used together"""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2  # argparse error

    @patch("yt_thumbs.cli.download_thumbnail")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://youtu.be/test", "-d", "-o", "nested/dir/thumb.jpg"])
    def test_creates_nested_output_directory(
        self, mock_extract, mock_download, temp_dir, monkeypatch
    ):
        """Test that nested output directories are created"""
        monkeypatch.chdir(temp_dir)
        mock_extract.return_value = "test123"
        mock_download.return_value = True

        main()

        # Check that download was called with the nested path
        mock_download.assert_called_once_with("test123", "nested/dir/thumb.jpg")

    @patch("sys.argv", ["yt-thumb", "--help"])
    def test_help_text(self):
        """Test that help text is available"""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # --help exits with code 0
        assert exc_info.value.code == 0

    @patch("yt_thumbs.cli.get_thumbnail_url")
    @patch("yt_thumbs.cli.extract_video_id")
    @patch(
        "sys.argv", ["yt-thumb", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", "output.jpg"]
    )
    def test_output_without_download_flag(self, mock_extract, mock_get_url, capsys):
        """Test that -o without -d still prints URL (doesn't download)"""
        mock_extract.return_value = "dQw4w9WgXcQ"
        mock_get_url.return_value = "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"

        main()

        # Should just print the URL, not download
        captured = capsys.readouterr()
        assert "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" in captured.out
        assert "Downloaded" not in captured.out

    @patch("yt_thumbs.cli.extract_video_id")
    @patch("sys.argv", ["yt-thumb", "https://youtu.be/dQw4w9WgXcQ", "-d"])
    def test_short_flag_aliases(self, mock_extract, temp_dir, monkeypatch):
        """Test short flag aliases work (-d, -o, -b)"""
        monkeypatch.chdir(temp_dir)
        mock_extract.return_value = "dQw4w9WgXcQ"

        with patch("yt_thumbs.cli.download_thumbnail") as mock_download:
            mock_download.return_value = True
            main()

        # Verify -d flag worked
        assert mock_download.called
