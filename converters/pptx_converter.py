"""PowerPoint (.pptx / .ppt) → Markdown converter using python-pptx."""

from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading, bullet_list, table

logger = get_logger(__name__)


class PptxConverter:
    """Convert a PowerPoint presentation to Markdown.

    Each slide becomes its own ``## Slide N: Title`` section.

    Args:
        extract_images: Whether to extract embedded slide images.
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
        """Convert *input_path* (.pptx) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source presentation.
            output_path: Destination ``.md`` file path.
            images_dir: Directory to save extracted images (optional).
        """
        try:
            from pptx import Presentation
            from pptx.util import Pt
            from pptx.enum.text import PP_ALIGN
        except ImportError as exc:
            raise ImportError(
                "python-pptx is required for PowerPoint conversion. "
                "Install it with: pip install python-pptx"
            ) from exc

        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting PPTX: %s → %s", input_path, output_path)

        prs = Presentation(str(input_path))
        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]

        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_title = self._get_slide_title(slide)
            sections.append(heading(f"Slide {slide_num}: {slide_title}", level=2))
            sections.append("")

            for shape in slide.shapes:
                # Tables.
                if shape.has_table:
                    md_table = self._shape_table_to_md(shape.table)
                    if md_table:
                        sections.append(md_table)
                        sections.append("")
                    continue

                # Text frames.
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if not text:
                            continue
                        level = para.level  # indentation level (0 = top)
                        if level == 0 and shape.shape_type == 13:
                            # Placeholder title — already captured above.
                            continue
                        if level > 0:
                            indent = (level - 1) * 2
                            sections.append(" " * indent + f"- {text}")
                        else:
                            sections.append(f"- {text}")

                # Images.
                if self.extract_images and images_dir:
                    img_lines = self._extract_shape_image(
                        shape, slide_num, images_dir
                    )
                    sections.extend(img_lines)

            sections.append("")

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("PPTX conversion complete: %s", output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_slide_title(slide) -> str:
        """Return the title text of *slide*, or ``'Untitled'``."""
        try:
            return slide.shapes.title.text.strip() or "Untitled"
        except AttributeError:
            return "Untitled"

    @staticmethod
    def _shape_table_to_md(tbl) -> str:
        """Convert a pptx Table object to a Markdown table."""
        rows = [
            [cell.text.strip() for cell in row.cells] for row in tbl.rows
        ]
        if not rows:
            return ""
        return table(rows[0], rows[1:])

    @staticmethod
    def _extract_shape_image(shape, slide_num: int, images_dir) -> list[str]:
        """Extract an image from *shape* and return Markdown lines."""
        from pptx.enum.shapes import MSO_SHAPE_TYPE

        images_dir = Path(images_dir)
        lines: list[str] = []

        if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
            return lines

        try:
            images_dir.mkdir(parents=True, exist_ok=True)
            img = shape.image
            ext = img.ext
            # Use a unique name based on slide number and shape id.
            filename = f"slide{slide_num}_shape{shape.shape_id}.{ext}"
            img_path = images_dir / filename
            img_path.write_bytes(img.blob)
            rel_path = images_dir.name + "/" + filename
            lines.append(f"![Slide {slide_num} image]({rel_path})")
            lines.append("")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not extract PPTX image on slide %d: %s", slide_num, exc)

        return lines
