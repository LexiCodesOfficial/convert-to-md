"""Video (.mp4) → Markdown converter: audio extraction + transcription."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from utils.logger import get_logger
from utils.markdown_utils import clean_text, heading

logger = get_logger(__name__)


class VideoConverter:
    """Convert a video file to Markdown by transcribing its audio.

    The pipeline is:

    1. Extract the audio track with **moviepy** (writes a temporary WAV file).
    2. Transcribe the audio with **openai-whisper** (``whisper`` package).
    3. Write a Markdown document containing the transcript.

    Args:
        transcribe: Whether to run audio transcription (defaults to ``True``).
        whisper_model: Whisper model size to load (defaults to ``"base"``).
    """

    def __init__(
        self,
        transcribe: bool = True,
        whisper_model: str = "base",
    ) -> None:
        self.transcribe = transcribe
        self.whisper_model = whisper_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        input_path: str | os.PathLike,
        output_path: str | os.PathLike,
        images_dir: str | os.PathLike | None = None,  # unused, kept for API symmetry
    ) -> None:
        """Convert *input_path* (video) to a Markdown file at *output_path*.

        Args:
            input_path: Path to the source video file.
            output_path: Destination ``.md`` file path.
            images_dir: Unused — present for API consistency.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info("Converting video: %s → %s", input_path, output_path)

        sections: list[str] = [heading(input_path.stem.replace("_", " ").title()), ""]
        sections.append(f"**Source:** `{input_path.name}`\n")

        if self.transcribe:
            transcript = self._transcribe(input_path)
            if transcript:
                sections.append(heading("Transcript", level=2))
                sections.append("")
                sections.append(transcript)
            else:
                sections.append("*No transcript could be extracted.*")
        else:
            sections.append("*Transcription disabled.*")

        markdown = clean_text("\n".join(sections))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("Video conversion complete: %s", output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _transcribe(self, video_path: Path) -> str:
        """Extract audio from *video_path* and return its transcript."""
        # Lazy imports — these are optional heavy dependencies.
        try:
            from moviepy.editor import VideoFileClip
        except ImportError as exc:
            raise ImportError(
                "moviepy is required for video conversion. "
                "Install it with: pip install moviepy"
            ) from exc

        try:
            import whisper
        except ImportError as exc:
            raise ImportError(
                "openai-whisper is required for transcription. "
                "Install it with: pip install openai-whisper"
            ) from exc

        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "audio.wav"

            logger.info("Extracting audio from %s …", video_path.name)
            try:
                clip = VideoFileClip(str(video_path))
                if clip.audio is None:
                    logger.warning("No audio track found in %s", video_path)
                    return ""
                clip.audio.write_audiofile(str(audio_path), logger=None)
                clip.close()
            except Exception as exc:  # noqa: BLE001
                logger.error("Audio extraction failed: %s", exc)
                return ""

            logger.info("Transcribing audio with Whisper (%s) …", self.whisper_model)
            try:
                model = whisper.load_model(self.whisper_model)
                result = model.transcribe(str(audio_path))
                return clean_text(result.get("text", ""))
            except Exception as exc:  # noqa: BLE001
                logger.error("Transcription failed: %s", exc)
                return ""
