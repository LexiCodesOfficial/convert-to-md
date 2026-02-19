"""Excel (.xlsx / .xls) → Markdown converter using openpyxl."""

from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading, table

logger = get_logger(__name__)


class XlsxConverter:
    """Convert an Excel workbook to Markdown.

    Each worksheet becomes its own ``## Sheet: <name>`` section with the
    sheet data rendered as a Markdown table.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        input_path: str | os.PathLike,
        output_path: str | os.PathLike,
        images_dir: str | os.PathLike | None = None,  # unused, kept for API symmetry
    ) -> None:
        """Convert *input_path* (.xlsx) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source Excel file.
            output_path: Destination ``.md`` file path.
            images_dir: Unused — present for API consistency.
        """
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "openpyxl is required for Excel conversion. "
                "Install it with: pip install openpyxl"
            ) from exc

        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting XLSX: %s → %s", input_path, output_path)

        wb = openpyxl.load_workbook(str(input_path), data_only=True)
        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sections.append(heading(f"Sheet: {sheet_name}", level=2))
            sections.append("")

            rows: list[list[str]] = []
            for row in ws.iter_rows(values_only=True):
                # Skip entirely empty rows.
                str_cells = [str(c) if c is not None else "" for c in row]
                if any(str_cells):
                    rows.append(str_cells)

            if not rows:
                sections.append("*Empty sheet.*")
                sections.append("")
                continue

            # Use the first non-empty row as headers.
            headers = rows[0]
            data_rows = rows[1:]
            sections.append(table(headers, data_rows))
            sections.append("")

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("XLSX conversion complete: %s", output_path)
