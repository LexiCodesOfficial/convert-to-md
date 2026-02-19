# convert-to-md

A modular, production-ready CLI tool that converts common study-related file
types into clean, structured Markdown (`.md`) documents.

## Supported Input Formats

| Extension | Type | Notes |
|---|---|---|
| `.pdf` | PDF | Tables + text extraction; optional image extraction |
| `.docx` / `.doc` | Word | Headings, lists, tables, inline images |
| `.pptx` / `.ppt` | PowerPoint | One section per slide; tables & images |
| `.txt` | Plain text | Heading/list heuristics applied |
| `.png` / `.jpg` / `.jpeg` | Image | Embedded reference + optional OCR |
| `.mp4` | Video | Audio extraction → Whisper transcription |
| `.xlsx` / `.xls` | Excel | Each worksheet → Markdown table |

## Project Structure

```
convert-to-md/
├── main.py                  # CLI entry point
├── requirements.txt
├── converters/
│   ├── __init__.py
│   ├── pdf_converter.py
│   ├── word_converter.py
│   ├── pptx_converter.py
│   ├── text_converter.py
│   ├── image_converter.py
│   ├── video_converter.py
│   └── xlsx_converter.py
└── utils/
    ├── __init__.py
    ├── logger.py
    ├── file_utils.py
    └── markdown_utils.py
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/LexiCodesOfficial/convert-to-md.git
cd convert-to-md
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install system dependencies

#### Tesseract (for OCR on images)

| OS | Command |
|---|---|
| Ubuntu/Debian | `sudo apt-get install tesseract-ocr` |
| macOS | `brew install tesseract` |
| Windows | Download the [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) |

#### FFmpeg (for video audio extraction)

| OS | Command |
|---|---|
| Ubuntu/Debian | `sudo apt-get install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) |

## Usage

```
python main.py INPUT OUTPUT [OPTIONS]
```

### Arguments

| Argument | Description |
|---|---|
| `INPUT` | Source file **or** directory |
| `OUTPUT` | Destination directory for `.md` files |

### Options

| Flag | Description |
|---|---|
| `--ocr` | Run OCR on image files (requires Tesseract) |
| `--transcribe` | Transcribe audio from video files (requires FFmpeg + Whisper) |
| `--images` | Extract and save embedded images from documents |
| `--clean` | Remove the output directory before converting |
| `--verbose` / `-v` | Enable DEBUG logging |

### Examples

```bash
# Convert a single PDF
python main.py report.pdf output/

# Convert an entire folder
python main.py input_folder/ output_folder/

# PowerPoint with image extraction
python main.py lecture.pptx notes/ --images

# Image with OCR
python main.py diagram.png notes/ --ocr

# Video with transcription
python main.py lecture.mp4 notes/ --transcribe

# Full batch with all features, clean output first
python main.py study_materials/ markdown_notes/ --images --ocr --transcribe --clean
```

## Markdown Output Conventions

* Document title → `# Title`
* PDF pages → `## Page N`
* PPTX slides → `## Slide N: Slide Title`
* Excel sheets → `## Sheet: Sheet Name`
* ALL-CAPS lines in `.txt` files → `## Heading`
* Tables → GitHub-flavoured Markdown table syntax
* Extracted images → `![alt](images/filename.ext)` references

## License

MIT