"""
Pytest fixtures for YT_Thumbs tests
"""

from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

import pytest


@pytest.fixture
def valid_watch_url():
    """Sample YouTube watch URL"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def valid_short_url():
    """Sample YouTube short URL (youtu.be)"""
    return "https://youtu.be/dQw4w9WgXcQ"


@pytest.fixture
def valid_shorts_url():
    """Sample YouTube Shorts URL"""
    return "https://www.youtube.com/shorts/dQw4w9WgXcQ"


@pytest.fixture
def valid_embed_url():
    """Sample YouTube embed URL"""
    return "https://www.youtube.com/embed/dQw4w9WgXcQ"


@pytest.fixture
def video_id():
    """Sample video ID"""
    return "dQw4w9WgXcQ"


@pytest.fixture
def invalid_urls():
    """Collection of invalid URLs"""
    return [
        "",
        "not a url",
        "https://example.com",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?v=",
        "https://www.youtube.com/watch?v=short",
        "https://youtu.be/",
    ]


@pytest.fixture
def mock_successful_response():
    """Mock a successful HTTP response"""
    mock_response = MagicMock()
    mock_response.read.return_value = b"fake image data"
    mock_response.status = 200
    mock_response.getcode.return_value = 200
    return mock_response


@pytest.fixture
def mock_404_response():
    """Mock a 404 HTTP error"""
    return HTTPError(url="https://example.com", code=404, msg="Not Found", hdrs={}, fp=None)


@pytest.fixture
def mock_network_error():
    """Mock a network error"""
    return URLError("Network unreachable")


@pytest.fixture
def mock_video_html():
    """Mock HTML content from a YouTube video page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Rick Astley - Never Gonna Give You Up">
        <meta property="og:description" content="The official video for Rick Astley's Never Gonna Give You Up">
        <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
    </head>
    <body>
    </body>
    </html>
    """


@pytest.fixture
def mock_video_html_no_title():
    """Mock HTML content missing title"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:description" content="Some description">
        <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
    </head>
    <body>
    </body>
    </html>
    """


@pytest.fixture
def mock_video_html_no_description():
    """Mock HTML content missing description"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Test Video">
        <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
    </head>
    <body>
    </body>
    </html>
    """


@pytest.fixture
def sample_batch_urls():
    """Sample batch of YouTube URLs"""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/jNQXAC9IVRw",
        "https://www.youtube.com/shorts/abc123defgh",
    ]


@pytest.fixture
def sample_batch_file_content():
    """Content for a batch file with multiple URLs"""
    return """https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/jNQXAC9IVRw
https://www.youtube.com/embed/abc123defgh
"""


@pytest.fixture
def expected_markdown_table_header():
    """Expected markdown table header"""
    return "| Thumbnail URL | Title | Description |\n|---|---|---|"


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file operations"""
    return tmp_path


@pytest.fixture
def batch_file(tmp_path, sample_batch_file_content):
    """Create a temporary batch file with URLs"""
    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(sample_batch_file_content)
    return batch_file


@pytest.fixture
def empty_batch_file(tmp_path):
    """Create an empty batch file"""
    batch_file = tmp_path / "empty.txt"
    batch_file.write_text("")
    return batch_file


@pytest.fixture
def batch_file_with_invalid_urls(tmp_path):
    """Create a batch file with some invalid URLs"""
    content = """https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://example.com
not a url
https://youtu.be/jNQXAC9IVRw
"""
    batch_file = tmp_path / "mixed.txt"
    batch_file.write_text(content)
    return batch_file
