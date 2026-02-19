#!/usr/bin/env python3
"""convert-to-md: Convert study-related files to Markdown.

Usage examples::

    # Convert a single file:
    python main.py report.pdf output/

    # Batch-convert a folder:
    python main.py input_folder/ output_folder/

    # With optional flags:
    python main.py slides.pptx out/ --images --ocr --transcribe

    # Clean output directory before converting:
    python main.py notes/ md_notes/ --clean
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from utils.file_utils import collect_files, detect_file_type, ensure_dir, get_output_path
from utils.logger import get_logger

logger = get_logger("convert-to-md")

# ---------------------------------------------------------------------------
# Converter registry
# ---------------------------------------------------------------------------

def _build_registry(
    extract_images: bool,
    run_ocr: bool,
    transcribe: bool,
) -> dict:
    """Lazily build a mapping from type-id → converter instance.

    All converters are imported here so that missing optional dependencies
    produce a clear error only when that specific converter is actually used.
    """
    from converters.pdf_converter import PdfConverter
    from converters.word_converter import WordConverter
    from converters.pptx_converter import PptxConverter
    from converters.text_converter import TextConverter
    from converters.image_converter import ImageConverter
    from converters.video_converter import VideoConverter
    from converters.xlsx_converter import XlsxConverter

    return {
        "pdf": PdfConverter(extract_images=extract_images),
        "word": WordConverter(extract_images=extract_images),
        "pptx": PptxConverter(extract_images=extract_images),
        "text": TextConverter(),
        "image": ImageConverter(run_ocr=run_ocr),
        "video": VideoConverter(transcribe=transcribe),
        "xlsx": XlsxConverter(),
    }


# ---------------------------------------------------------------------------
# Core conversion logic
# ---------------------------------------------------------------------------

def convert_file(
    input_path: Path,
    output_dir: Path,
    registry: dict,
    images_dir: Path | None,
    input_root: Path | None = None,
) -> bool:
    """Convert a single *input_path* and write output into *output_dir*.

    Args:
        input_path: Source file to convert.
        output_dir: Destination directory for the ``.md`` file.
        registry: Mapping of type-id → converter instance.
        images_dir: Where to save extracted images/assets (may be ``None``).
        input_root: Root directory of the input tree.  When provided the
            relative sub-path is preserved inside *output_dir*.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    file_type = detect_file_type(input_path)
    if file_type is None:
        logger.warning("Skipping unsupported file: %s", input_path)
        return False

    converter = registry.get(file_type)
    if converter is None:
        logger.warning("No converter registered for type '%s': %s", file_type, input_path)
        return False

    output_path = get_output_path(input_path, output_dir, input_root)

    try:
        converter.convert(
            input_path=input_path,
            output_path=output_path,
            images_dir=images_dir,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to convert %s: %s", input_path, exc)
        return False


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------

def _progress_bar(current: int, total: int, width: int = 40) -> str:
    """Return a simple ASCII progress bar string."""
    filled = int(width * current / total) if total else width
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="convert-to-md",
        description="Convert study-related files to clean Markdown documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        metavar="INPUT",
        help="Source file or directory to convert.",
    )
    parser.add_argument(
        "output",
        metavar="OUTPUT",
        help="Destination directory for Markdown output.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Run OCR on image files (requires pytesseract + Tesseract).",
    )
    parser.add_argument(
        "--transcribe",
        action="store_true",
        default=False,
        help="Transcribe audio from video files (requires moviepy + openai-whisper).",
    )
    parser.add_argument(
        "--images",
        action="store_true",
        default=False,
        help="Extract and save embedded images from documents.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Remove the output directory before converting.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG) logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (``0`` = success, ``1`` = partial failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Adjust log level.
    if args.verbose:
        logging.getLogger("convert-to-md").setLevel(logging.DEBUG)
        logging.getLogger("converters").setLevel(logging.DEBUG)

    input_path = Path(args.input)
    output_dir = Path(args.output)

    # Validate input.
    if not input_path.exists():
        logger.error("Input path does not exist: %s", input_path)
        return 1

    # Optionally clean output directory.
    if args.clean and output_dir.exists():
        logger.info("Cleaning output directory: %s", output_dir)
        shutil.rmtree(output_dir)

    ensure_dir(output_dir)

    # Set up images sub-directory when requested.
    images_dir: Path | None = None
    if args.images or args.ocr:
        images_dir = output_dir / "images"
        ensure_dir(images_dir)

    # Collect files to convert.
    files = collect_files(input_path)
    if not files:
        logger.error("No supported files found at: %s", input_path)
        return 1

    # When the input is a directory preserve its subdirectory structure in
    # the output so that files with the same name in different subdirectories
    # do not overwrite each other.
    input_root = input_path if input_path.is_dir() else None

    total = len(files)
    logger.info("Found %d file(s) to convert.", total)

    # Build converter registry.
    registry = _build_registry(
        extract_images=args.images,
        run_ocr=args.ocr,
        transcribe=args.transcribe,
    )

    # Convert each file.
    success_count = 0
    for idx, file_path in enumerate(files, start=1):
        print(_progress_bar(idx - 1, total), end="\r", flush=True)
        ok = convert_file(file_path, output_dir, registry, images_dir, input_root)
        if ok:
            success_count += 1

    # Final progress update.
    print(_progress_bar(total, total))

    logger.info(
        "Conversion finished: %d/%d succeeded.", success_count, total
    )

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
