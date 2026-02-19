"""Plain text (.txt) → Markdown converter."""

from __future__ import annotations

import os
import re
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading

logger = get_logger(__name__)


class TextConverter:
    """Convert a plain-text file to Markdown.

    The converter applies simple heuristics to detect structure:

    * Lines in ALL CAPS (≥ 4 chars) become ``##`` headings.
    * Blank-line–separated paragraphs are preserved.
    * Leading ``*``, ``-``, or digit+dot markers become Markdown list items.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        input_path: str | os.PathLike,
        output_path: str | os.PathLike,
        images_dir: str | os.PathLike | None = None,  # unused but kept for API symmetry
    ) -> None:
        """Convert *input_path* (.txt) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source text file.
            output_path: Destination ``.md`` file path.
            images_dir: Unused — present for API consistency.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting text: %s → %s", input_path, output_path)

        raw = input_path.read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines()

        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                sections.append("")
                continue

            # Detect ALL-CAPS headings.
            if stripped.isupper() and len(stripped) >= 4:
                sections.append(heading(stripped.title(), level=2))
                continue

            # Preserve existing list markers.
            if stripped.startswith(("- ", "* ", "• ")):
                sections.append(f"- {stripped[2:].strip()}")
                continue

            # Numbered list: "1. item" or "1) item".
            if re.match(r"^\d+[.)]\s", stripped):
                sections.append(stripped)
                continue

            sections.append(stripped)

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("Text conversion complete: %s", output_path)
