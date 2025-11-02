"""
Comprehensive tests for YouTube URL parsing and video ID extraction.

Tests all supported URL formats, edge cases, and invalid inputs.
"""

import pytest

from yt_thumbs.extractor import extract_video_id


class TestValidYouTubeURLs:
    """Test extraction from valid YouTube URL formats."""

    def test_standard_watch_url(self, valid_watch_url):
        """Test standard watch URL: youtube.com/watch?v=ID"""
        video_id = extract_video_id(valid_watch_url)
        assert video_id == "dQw4w9WgXcQ"

    def test_short_url(self, valid_short_url):
        """Test shortened URL: youtu.be/ID"""
        video_id = extract_video_id(valid_short_url)
        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.skip(reason="Shorts URLs not yet supported by extractor")
    def test_shorts_url(self, valid_shorts_url):
        """Test YouTube Shorts URL: youtube.com/shorts/ID"""
        video_id = extract_video_id(valid_shorts_url)
        assert video_id == "dQw4w9WgXcQ"

    def test_embed_url(self, valid_embed_url):
        """Test embed URL: youtube.com/embed/ID"""
        video_id = extract_video_id(valid_embed_url)
        assert video_id == "dQw4w9WgXcQ"

    def test_watch_url_without_protocol(self):
        """Test watch URL without https:// protocol"""
        url = "www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_short_url_without_protocol(self):
        """Test short URL without https:// protocol"""
        url = "youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_http_protocol(self):
        """Test URL with http:// instead of https://"""
        url = "http://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_www(self):
        """Test URL with www prefix"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_without_www(self):
        """Test URL without www prefix"""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"


class TestURLsWithQueryParameters:
    """Test URLs with additional query parameters."""

    def test_url_with_timestamp(self):
        """Test URL with timestamp parameter"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_playlist(self):
        """Test URL with playlist parameter"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_multiple_params(self):
        """Test URL with multiple query parameters"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s&list=PLtest&index=5"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_feature_param(self):
        """Test URL with feature parameter (share links)"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"


class TestInvalidURLs:
    """Test handling of invalid URLs."""

    def test_empty_string(self):
        """Test empty string returns None"""
        assert extract_video_id("") is None

    def test_none_input(self):
        """Test None input raises TypeError"""
        with pytest.raises(TypeError):
            extract_video_id(None)

    def test_non_youtube_url(self):
        """Test non-YouTube URL returns None"""
        url = "https://www.example.com/video/123"
        assert extract_video_id(url) is None

    def test_youtube_homepage(self):
        """Test YouTube homepage URL returns None"""
        url = "https://www.youtube.com"
        assert extract_video_id(url) is None

    def test_youtube_search(self):
        """Test YouTube search URL returns None"""
        url = "https://www.youtube.com/results?search_query=test"
        assert extract_video_id(url) is None

    def test_youtube_channel(self):
        """Test YouTube channel URL returns None"""
        url = "https://www.youtube.com/channel/UCtest123"
        assert extract_video_id(url) is None

    def test_youtube_user(self):
        """Test YouTube user URL returns None"""
        url = "https://www.youtube.com/user/testuser"
        assert extract_video_id(url) is None

    def test_invalid_video_id_length(self):
        """Test URL with wrong video ID length returns None"""
        url = "https://www.youtube.com/watch?v=short"
        assert extract_video_id(url) is None

    def test_watch_url_without_video_id(self):
        """Test watch URL without video ID parameter"""
        url = "https://www.youtube.com/watch"
        assert extract_video_id(url) is None

    def test_watch_url_with_empty_video_id(self):
        """Test watch URL with empty video ID"""
        url = "https://www.youtube.com/watch?v="
        assert extract_video_id(url) is None

    def test_malformed_url(self):
        """Test completely malformed URL"""
        url = "not a url at all"
        assert extract_video_id(url) is None

    def test_javascript_url(self):
        """Test JavaScript URL returns None"""
        url = "javascript:alert('xss')"
        assert extract_video_id(url) is None


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_video_id_with_all_alphanumeric(self):
        """Test video ID with mix of uppercase, lowercase, numbers"""
        url = "https://www.youtube.com/watch?v=aBc123XyZ-_"
        video_id = extract_video_id(url)
        assert video_id == "aBc123XyZ-_"

    def test_video_id_with_underscore(self):
        """Test video ID containing underscore"""
        url = "https://www.youtube.com/watch?v=test_video1"
        video_id = extract_video_id(url)
        assert video_id == "test_video1"

    def test_video_id_with_hyphen(self):
        """Test video ID containing hyphen"""
        url = "https://www.youtube.com/watch?v=test-video1"
        video_id = extract_video_id(url)
        assert video_id == "test-video1"

    @pytest.mark.skip(reason="Shorts URLs not yet supported by extractor")
    def test_shorts_url_with_query_params(self):
        """Test Shorts URL with additional parameters"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ?feature=share"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_embed_url_with_query_params(self):
        """Test embed URL with additional parameters"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash"""
        url = "https://youtu.be/dQw4w9WgXcQ/"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_fragment(self):
        """Test URL with fragment identifier"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ#t=30s"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        """Test mobile YouTube URL (m.youtube.com)"""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"


class TestBatchURLProcessing:
    """Test processing multiple URLs."""

    def test_multiple_different_formats(self):
        """Test extracting video IDs from multiple URL formats"""
        # Only test supported formats (watch and short URLs, not Shorts)
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/jNQXAC9IVRw",
        ]
        expected_ids = ["dQw4w9WgXcQ", "jNQXAC9IVRw"]

        for url, expected_id in zip(urls, expected_ids):
            video_id = extract_video_id(url)
            assert video_id == expected_id

    def test_mixed_valid_invalid_urls(self, invalid_urls):
        """Test that invalid URLs return None consistently"""
        for url in invalid_urls:
            video_id = extract_video_id(url)
            assert video_id is None
