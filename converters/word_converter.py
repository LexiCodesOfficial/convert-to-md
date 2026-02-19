"""Word (.docx / .doc) → Markdown converter using python-docx."""

from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading, table

logger = get_logger(__name__)

# Word paragraph style name prefixes that map to heading levels.
_HEADING_STYLE_MAP: dict[str, int] = {
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "Heading 4": 4,
    "Heading 5": 5,
    "Heading 6": 6,
}


class WordConverter:
    """Convert a Word document (.docx) to Markdown.

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
        """Convert *input_path* (.docx) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source Word document.
            output_path: Destination ``.md`` file path.
            images_dir: Directory to save extracted images (optional).
        """
        try:
            from docx import Document
            from docx.oxml.ns import qn
        except ImportError as exc:
            raise ImportError(
                "python-docx is required for Word conversion. "
                "Install it with: pip install python-docx"
            ) from exc

        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting Word: %s → %s", input_path, output_path)

        doc = Document(str(input_path))
        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]

        img_counter = 0

        for block in self._iter_block_items(doc):
            block_type = type(block).__name__

            if block_type == "Paragraph":
                md_line = self._paragraph_to_md(block)
                if md_line:
                    sections.append(md_line)

                # Extract inline images.
                if self.extract_images and images_dir:
                    for img_md, img_counter in self._extract_paragraph_images(
                        block, images_dir, img_counter
                    ):
                        sections.append(img_md)

            elif block_type == "Table":
                md_table = self._table_to_md(block)
                if md_table:
                    sections.append("")
                    sections.append(md_table)
                    sections.append("")

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("Word conversion complete: %s", output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_block_items(doc):
        """Yield paragraphs and tables in document order."""
        from docx.oxml.ns import qn

        body = doc.element.body
        for child in body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "p":
                from docx.text.paragraph import Paragraph

                yield Paragraph(child, doc)
            elif tag == "tbl":
                from docx.table import Table

                yield Table(child, doc)

    @staticmethod
    def _paragraph_to_md(para) -> str:
        """Convert a single paragraph to a Markdown line."""
        style_name: str = para.style.name if para.style else ""
        text: str = para.text.strip()

        if not text:
            return ""

        # Headings.
        for style_prefix, level in _HEADING_STYLE_MAP.items():
            if style_name.startswith(style_prefix):
                return heading(text, level=level)

        # List items.
        if style_name.startswith("List Bullet"):
            return f"- {text}"
        if style_name.startswith("List Number"):
            return f"1. {text}"

        return text

    @staticmethod
    def _table_to_md(tbl) -> str:
        """Convert a python-docx Table to a Markdown table."""
        rows = [[cell.text.strip() for cell in row.cells] for row in tbl.rows]
        if not rows:
            return ""
        headers = rows[0]
        data_rows = rows[1:]
        return table(headers, data_rows)

    @staticmethod
    def _extract_paragraph_images(para, images_dir, img_counter: int):
        """Yield (markdown_img_string, new_counter) for each inline image."""
        from docx.oxml.ns import qn

        images_dir = Path(images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)

        for run in para.runs:
            for elem in run._element:
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag != "drawing":
                    continue
                # Walk the drawing tree to find blipFill.
                for blip in elem.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
                    r_embed = blip.get(
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                    )
                    if r_embed is None:
                        continue
                    try:
                        img_part = para.part.related_parts[r_embed]
                        img_counter += 1
                        ext = img_part.content_type.split("/")[-1].replace("jpeg", "jpg")
                        filename = f"image_{img_counter}.{ext}"
                        img_path = images_dir / filename
                        img_path.write_bytes(img_part.blob)
                        rel_path = images_dir.name + "/" + filename
                        yield f"![Image {img_counter}]({rel_path})", img_counter
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Could not extract Word image: %s", exc)
