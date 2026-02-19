"""Markdown formatting helpers for convert-to-md."""

import re


def clean_text(text: str) -> str:
    """Normalise whitespace and strip leading/trailing blank lines.

    Args:
        text: Raw text to clean.

    Returns:
        Cleaned text with normalised line endings.
    """
    # Collapse multiple blank lines into a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def heading(text: str, level: int = 1) -> str:
    """Return a Markdown heading.

    Args:
        text: Heading text.
        level: Heading level 1–6 (defaults to ``1``).

    Returns:
        Markdown heading string.
    """
    level = max(1, min(6, level))
    return f"{'#' * level} {text.strip()}"


def bullet_list(items: list[str], indent: int = 0) -> str:
    """Return a Markdown bullet list.

    Args:
        items: List of item strings.
        indent: Number of spaces to indent each bullet (defaults to ``0``).

    Returns:
        Multi-line Markdown bullet list.
    """
    prefix = " " * indent + "- "
    return "\n".join(f"{prefix}{item.strip()}" for item in items if item.strip())


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Return a GitHub-flavoured Markdown table.

    Args:
        headers: Column header strings.
        rows: List of rows; each row is a list of cell strings.

    Returns:
        Markdown table string, or an empty string when *headers* is empty.
    """
    if not headers:
        return ""

    def _escape(cell: str) -> str:
        return str(cell).replace("|", "\\|").replace("\n", " ").strip()

    header_row = "| " + " | ".join(_escape(h) for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(_escape(c) for c in row) + " |" for row in rows
    ]

    return "\n".join([header_row, separator] + data_rows)
