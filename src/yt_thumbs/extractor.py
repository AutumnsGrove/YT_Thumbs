"""YouTube thumbnail extractor utilities.

This module provides functions to extract video IDs from YouTube URLs,
generate thumbnail URLs, and download thumbnails.
"""

import re
import urllib.error
import urllib.request


def extract_video_id(url: str) -> str | None:
    """Extract video ID from a YouTube URL.

    Supports the following URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID

    Args:
        url: The YouTube URL to parse

    Returns:
        The video ID if found, None otherwise
    """
    # Pattern for youtube.com/watch?v=VIDEO_ID
    watch_pattern = r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})"

    # Pattern for youtu.be/VIDEO_ID
    short_pattern = r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})"

    # Pattern for youtube.com/embed/VIDEO_ID
    embed_pattern = r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})"

    # Try each pattern
    for pattern in [watch_pattern, short_pattern, embed_pattern]:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_thumbnail_url(video_id: str) -> str:
    """Get the maxresdefault thumbnail URL for a video ID.

    Args:
        video_id: The YouTube video ID

    Returns:
        The maxresdefault thumbnail URL
    """
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


def download_thumbnail(video_id: str, output_path: str) -> bool:
    """Download a YouTube thumbnail to a file.

    Attempts to download the maxresdefault quality thumbnail first.
    If that returns a 404, falls back to hqdefault quality.

    Args:
        video_id: The YouTube video ID
        output_path: Path where the thumbnail should be saved

    Returns:
        True if download succeeded, False otherwise
    """
    # Try maxresdefault first
    max_res_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    try:
        with urllib.request.urlopen(max_res_url) as response:
            # Check if we got actual image data (maxresdefault exists)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > 1000:  # Valid image
                with open(output_path, "wb") as f:
                    f.write(response.read())
                return True
    except (urllib.error.HTTPError, urllib.error.URLError):
        pass

    # Fallback to hqdefault
    hq_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    try:
        with urllib.request.urlopen(hq_url) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return False


def get_video_metadata(video_id: str) -> dict[str, str]:
    """Fetch video metadata from YouTube.

    Extracts the title and description from a YouTube video page by parsing
    the HTML meta tags. Makes a single HTTP request to the video page.

    Args:
        video_id: The YouTube video ID

    Returns:
        A dictionary containing:
        - 'title': The video title (empty string if not found)
        - 'description': The video description (empty string if not found)
        - 'thumbnail_url': The maxresdefault thumbnail URL

    Example:
        >>> metadata = get_video_metadata('dQw4w9WgXcQ')
        >>> print(metadata['title'])
        'Rick Astley - Never Gonna Give You Up (Official Video)'
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    metadata = {
        "title": "",
        "description": "",
        "thumbnail_url": get_thumbnail_url(video_id),
    }

    try:
        # Fetch the video page HTML
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode("utf-8")

        # Extract title from <meta property="og:title" content="...">
        title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
        if title_match:
            metadata["title"] = title_match.group(1)

        # Extract description from <meta property="og:description" content="...">
        desc_match = re.search(r'<meta\s+property="og:description"\s+content="([^"]*)"', html)
        if desc_match:
            metadata["description"] = desc_match.group(1)

    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        # Return empty strings for title and description on error
        pass

    return metadata
