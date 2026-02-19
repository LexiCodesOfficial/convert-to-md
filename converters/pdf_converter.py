"""PDF → Markdown converter using pdfplumber."""

from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading, table

logger = get_logger(__name__)


class PdfConverter:
    """Convert a PDF file to a Markdown document.

    Extracted images (if any) are saved to *images_dir* and referenced in
    the output Markdown.

    Args:
        extract_images: Whether to extract embedded images.
    """

    def __init__(self, extract_images: bool = False) -> None:
        self.extract_images = extract_images

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        input_path: str | os.PathLike,
        output_path: str | os.PathLike,
        images_dir: str | os.PathLike | None = None,
    ) -> None:
        """Convert *input_path* (PDF) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source PDF file.
            output_path: Destination ``.md`` file path.
            images_dir: Directory to save extracted images (optional).
        """
        try:
            import pdfplumber
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is required for PDF conversion. "
                "Install it with: pip install pdfplumber"
            ) from exc

        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting PDF: %s → %s", input_path, output_path)

        sections: list[str] = [heading(input_path.stem.replace("_", " ").title())]

        with pdfplumber.open(input_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                sections.append(f"\n{heading(f'Page {page_num}', level=2)}\n")

                # Extract tables before text so we don't duplicate content.
                page_tables = page.extract_tables()
                table_bboxes: list = []

                for tbl in page_tables:
                    if not tbl:
                        continue
                    headers = [str(c or "") for c in tbl[0]]
                    rows = [[str(c or "") for c in row] for row in tbl[1:]]
                    sections.append(table(headers, rows))
                    sections.append("")
                    # Remember bounding box to exclude from plain text.
                    table_bboxes.extend(page.find_tables())

                # Extract plain text (crop out table areas).
                cropped = page
                for tbl_obj in page.find_tables():
                    try:
                        cropped = cropped.outside_bbox(tbl_obj.bbox)
                    except Exception:  # noqa: BLE001
                        pass

                text = cropped.extract_text() or ""
                if text.strip():
                    sections.append(clean_text(text))
                    sections.append("")

                # Extract images (if requested).
                if self.extract_images and images_dir:
                    self._extract_images(page, page_num, images_dir, sections)

        markdown = "\n".join(sections)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("PDF conversion complete: %s", output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_images(
        self,
        page,
        page_num: int,
        images_dir: str | os.PathLike,
        sections: list[str],
    ) -> None:
        """Extract images from *page* and append Markdown references to *sections*."""
        images_dir = Path(images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)

        for img_index, img in enumerate(page.images, start=1):
            try:
                # pdfplumber exposes raw image bytes via the page's PDF object.
                img_bytes = img.get("stream", None)
                if img_bytes is None:
                    continue
                data = img_bytes.get_data()
                ext = "png"
                filename = f"page{page_num}_img{img_index}.{ext}"
                img_path = images_dir / filename
                img_path.write_bytes(data)
                rel_path = images_dir.name + "/" + filename
                sections.append(f"![Image {img_index} on page {page_num}]({rel_path})\n")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not extract image on page %d: %s", page_num, exc)
