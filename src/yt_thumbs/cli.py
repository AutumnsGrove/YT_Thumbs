"""Command-line interface for YouTube thumbnail extractor."""

import argparse
import sys
from pathlib import Path

from .extractor import (
    download_thumbnail,
    extract_video_id,
    get_thumbnail_url,
    get_video_metadata,
)


def process_batch_urls(batch_file: str, output_file: str = None) -> None:
    """Process multiple URLs from a file and output as markdown table.

    Args:
        batch_file: Path to file containing URLs (one per line)
        output_file: Optional path to write output (defaults to stdout)
    """
    # Read URLs from file
    try:
        with open(batch_file) as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Batch file not found: {batch_file}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Could not read batch file: {e}", file=sys.stderr)
        sys.exit(1)

    if not urls:
        print(f"Error: No URLs found in batch file: {batch_file}", file=sys.stderr)
        sys.exit(1)

    # Prepare markdown table
    table_lines = []
    table_lines.append("| Thumbnail URL | Video Name | Video Description |")
    table_lines.append("|---------------|------------|-------------------|")

    # Process each URL
    processed_count = 0
    for url in urls:
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            print(f"Warning: Skipping invalid URL: {url}", file=sys.stderr)
            continue

        # Get metadata
        try:
            metadata = get_video_metadata(video_id)
            thumbnail_url = metadata.get("thumbnail_url", "")
            title = metadata.get("title", "").replace("|", "\\|")  # Escape pipes
            description = metadata.get("description", "").replace("|", "\\|")  # Escape pipes

            # Truncate description if too long (optional, for readability)
            if len(description) > 100:
                description = description[:97] + "..."

            table_lines.append(f"| {thumbnail_url} | {title} | {description} |")
            processed_count += 1
            print(f"Processed: {title}", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Error processing {url}: {e}", file=sys.stderr)
            continue

    if processed_count == 0:
        print("Error: No valid URLs were processed", file=sys.stderr)
        sys.exit(1)

    # Output results
    output_text = "\n".join(table_lines)

    if output_file:
        try:
            # Create parent directory if needed
            output_path = Path(output_file)
            if output_path.parent != Path("."):
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                f.write(output_text)
                f.write("\n")  # Add final newline

            print(
                f"\nSuccessfully wrote markdown table to: {output_file}",
                file=sys.stderr,
            )
            print(f"Processed {processed_count} of {len(urls)} URLs", file=sys.stderr)
        except OSError as e:
            print(f"Error: Could not write to output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_text)
        print(f"\nProcessed {processed_count} of {len(urls)} URLs", file=sys.stderr)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Extract and download YouTube video thumbnails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single URL mode:
    %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ
    %(prog)s https://youtu.be/dQw4w9WgXcQ --download
    %(prog)s https://youtu.be/dQw4w9WgXcQ --download --output my_thumb.jpg

  Batch mode:
    %(prog)s --batch urls.txt
    %(prog)s --batch urls.txt --output results.md
        """,
    )

    parser.add_argument(
        "url",
        nargs="?",  # Make optional
        help="YouTube video URL",
    )

    parser.add_argument(
        "--batch",
        "-b",
        metavar="FILE",
        help="Batch mode: process URLs from file (one per line) and output markdown table",
    )

    parser.add_argument(
        "--download",
        "-d",
        action="store_true",
        help="Download the thumbnail instead of printing the URL (single URL mode only)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output filename (default: {video_id}.jpg in download mode, or stdout in batch mode)",
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.batch and args.url:
        parser.error("Cannot use both URL argument and --batch flag. Choose one mode.")

    if not args.batch and not args.url:
        parser.error("Either provide a URL or use --batch flag with a file")

    if args.batch and args.download:
        parser.error("--download flag is not supported in batch mode")

    # Batch mode
    if args.batch:
        process_batch_urls(args.batch, args.output)
        return

    # Extract video ID from URL
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {args.url}", file=sys.stderr)
        print("Supported formats:", file=sys.stderr)
        print("  - https://www.youtube.com/watch?v=VIDEO_ID", file=sys.stderr)
        print("  - https://youtu.be/VIDEO_ID", file=sys.stderr)
        print("  - https://www.youtube.com/embed/VIDEO_ID", file=sys.stderr)
        sys.exit(1)

    # Get thumbnail URL
    thumbnail_url = get_thumbnail_url(video_id)

    # If download flag is not set, just print the URL
    if not args.download:
        print(thumbnail_url)
        return

    # Download mode
    output_path = args.output if args.output else f"{video_id}.jpg"

    # Create parent directory if it doesn't exist
    output_file = Path(output_path)
    if output_file.parent != Path("."):
        output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading thumbnail for video ID: {video_id}")
    print(f"Saving to: {output_path}")

    success = download_thumbnail(video_id, output_path)

    if success:
        print(f"Successfully downloaded thumbnail to {output_path}")
    else:
        print(
            f"Error: Failed to download thumbnail for video ID: {video_id}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
