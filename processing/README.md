# Data Processing Pipeline

Python scripts for processing Jung's collected works into vector embeddings.

## Pipeline Overview

```
Raw PDFs/EPUBs
      ↓
[1] extract_pdf.py / extract_epub.py
      ↓
Extracted text (per volume)
      ↓
[2] clean_text.py
      ↓
Cleaned text (OCR artifacts removed)
      ↓
[3] chunk_text.py
      ↓
Semantic chunks (~400 tokens each)
      ↓
[4] upload_to_pinecone.py
      ↓
Indexed vectors in Pinecone
```

## Scripts

### `extract_pdf.py`
Extracts text from PDF files using PyMuPDF. Handles both digital PDFs and OCR-scanned documents.

### `extract_epub.py`
Parses EPUB files and extracts text content while preserving chapter structure.

### `clean_text.py`
Cleans extracted text:
- Fixes OCR spacing errors ("j u n g" → "Jung")
- Removes watermarks and artifacts
- Fixes broken hyphenation across pages
- Normalizes whitespace and unicode

### `chunk_text.py`
Splits cleaned text into semantic chunks:
- Target: 400 tokens, max: 600 tokens
- Respects sentence and paragraph boundaries
- Detects and tags chapter metadata
- Tags Jungian concepts for filtering

### `upload_to_pinecone.py`
Generates embeddings and uploads to Pinecone:
- Uses multilingual-e5-large model (1024 dims)
- Batches uploads for efficiency
- Stores metadata: work_title, chapter, text

### `evaluate_quality.py`
Quality checks for the processed data.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in this directory:

```
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=jung-works
```

## Usage

Run scripts in order:

```bash
python extract_pdf.py --input ./raw --output ./extracted
python clean_text.py --input ./extracted --output ./cleaned
python chunk_text.py --input ./cleaned --output ./chunks
python upload_to_pinecone.py --input ./chunks
```

## Output

- **47,576 chunks** from 34 volumes
- **~350 tokens** average chunk size
- **1024-dimensional** vectors
