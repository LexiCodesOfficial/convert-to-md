"""Image (.png / .jpg / .jpeg) → Markdown converter using pytesseract OCR."""

from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading

logger = get_logger(__name__)


class ImageConverter:
    """Convert an image file to Markdown by running OCR.

    Args:
        run_ocr: Whether to run pytesseract OCR (defaults to ``True``).
        tesseract_cmd: Optional path to the ``tesseract`` binary.
    """

    def __init__(
        self,
        run_ocr: bool = True,
        tesseract_cmd: str | None = None,
    ) -> None:
        self.run_ocr = run_ocr
        self.tesseract_cmd = tesseract_cmd

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        input_path: str | os.PathLike,
        output_path: str | os.PathLike,
        images_dir: str | os.PathLike | None = None,
    ) -> None:
        """Convert *input_path* (image) to a Markdown file at *output_path*.

        The image itself is always copied/referenced in the output.  When
        *run_ocr* is ``True`` the extracted text is appended below the image.

        Args:
            input_path: Path to the source image.
            output_path: Destination ``.md`` file path.
            images_dir: Directory where the image reference will point.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting image: %s → %s", input_path, output_path)

        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]

        # Build image reference path.
        if images_dir:
            images_dir = Path(images_dir)
            images_dir.mkdir(parents=True, exist_ok=True)
            dest = images_dir / input_path.name
            import shutil
            shutil.copy2(str(input_path), str(dest))
            ref_path = images_dir.name + "/" + input_path.name
        else:
            ref_path = input_path.name

        sections.append(f"![{input_path.stem}]({ref_path})")
        sections.append("")

        if self.run_ocr:
            ocr_text = self._run_ocr(input_path)
            if ocr_text:
                sections.append(heading("Extracted Text", level=2))
                sections.append("")
                sections.append(ocr_text)

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("Image conversion complete: %s", output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_ocr(self, image_path: Path) -> str:
        """Return OCR text extracted from *image_path*, or empty string on error."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ImportError(
                "pytesseract and Pillow are required for OCR. "
                "Install them with: pip install pytesseract Pillow"
            ) from exc

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return clean_text(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OCR failed for %s: %s", image_path, exc)
            return ""
