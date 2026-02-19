"""File-system utilities for convert-to-md."""

import os
from pathlib import Path

# Mapping from lowercase extension to a short type identifier.
_EXT_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".ppt": "pptx",
    ".pptx": "pptx",
    ".txt": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".mp4": "video",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
}


def detect_file_type(path: str | os.PathLike) -> str | None:
    """Return the type identifier for *path*, or ``None`` if unsupported.

    Args:
        path: Path to the file.

    Returns:
        A string such as ``"pdf"``, ``"word"``, ``"image"``, etc., or
        ``None`` when the extension is not recognised.
    """
    ext = Path(path).suffix.lower()
    return _EXT_MAP.get(ext)


def get_output_path(
    input_path: str | os.PathLike,
    output_dir: str | os.PathLike,
    input_root: str | os.PathLike | None = None,
) -> Path:
    """Compute the output ``.md`` path for *input_path* inside *output_dir*.

    When *input_root* is provided the relative sub-path from *input_root* to
    *input_path* is preserved inside *output_dir*, so files in subdirectories
    are placed in matching subdirectories of the output and name collisions
    across different subdirectories are avoided.

    Args:
        input_path: Original source file.
        output_dir: Destination directory for Markdown output.
        input_root: Root directory used when collecting files recursively.
            If given, the output mirrors the directory structure relative to
            this root.

    Returns:
        :class:`~pathlib.Path` for the output ``.md`` file.
    """
    p = Path(input_path)
    if input_root is not None:
        try:
            rel = p.relative_to(input_root)
            return Path(output_dir) / rel.with_suffix(".md")
        except ValueError:
            pass
    stem = p.stem
    return Path(output_dir) / f"{stem}.md"


def ensure_dir(path: str | os.PathLike) -> Path:
    """Create *path* (and parents) if it does not exist.

    Args:
        path: Directory path to create.

    Returns:
        The resolved :class:`~pathlib.Path`.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def collect_files(source: str | os.PathLike) -> list[Path]:
    """Collect all supported files from a file or directory.

    If *source* is a file it is returned as a single-element list.
    If *source* is a directory, all supported files within it (including
    subdirectories, recursively) are returned.

    Args:
        source: A file or directory path.

    Returns:
        List of :class:`~pathlib.Path` objects for supported input files.
    """
    source = Path(source)
    if source.is_file():
        return [source] if detect_file_type(source) else []
    if source.is_dir():
        return sorted(
            f
            for f in source.rglob("*")
            if f.is_file() and detect_file_type(f) is not None
        )
    return []
