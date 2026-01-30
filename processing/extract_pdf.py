"""
PDF Text Extraction Script
Handles OCR'd and native PDFs with improved text quality.
"""

import re
import sys
from pathlib import Path

# pip install pymupdf
import fitz


def clean_extracted_text(text: str) -> str:
    """Clean up common PDF extraction artifacts."""
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

    # Normalize quotes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r"[''']", "'", text)

    # Normalize dashes
    text = re.sub(r'—|–', '-', text)

    # Remove form feed and other control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    # Normalize whitespace within lines (but preserve newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Clean up lines that are just whitespace
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)

    return text


def is_header_footer(line: str, page_num: int, total_pages: int) -> bool:
    """Check if a line is likely a header or footer."""
    stripped = line.strip()

    # Empty or very short lines
    if len(stripped) < 3:
        return True

    # Just a page number
    if re.match(r'^\d{1,4}$', stripped):
        return True

    # Page number with dashes
    if re.match(r'^[-—]\s*\d+\s*[-—]$', stripped):
        return True

    # Common header patterns
    header_patterns = [
        r'^C\.?\s*G\.?\s*JUNG$',
        r'^CARL\s+(GUSTAV\s+)?JUNG$',
        r'^THE\s+COLLECTED\s+WORKS',
        r'^VOLUME\s+[IVXLCDM\d]+$',
        r'^BOLLINGEN\s+SERIES',
    ]
    if any(re.match(p, stripped, re.IGNORECASE) for p in header_patterns):
        return True

    return False


def merge_paragraphs(lines: list) -> str:
    """Merge lines into paragraphs based on content analysis."""
    if not lines:
        return ""

    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line might indicate paragraph break
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            continue

        # Check if this line starts a new paragraph
        starts_new = False

        # Starts with capital letter after period suggests new paragraph
        if current_para:
            prev_text = ' '.join(current_para)
            if prev_text.rstrip().endswith(('.', '!', '?', ':', '"')):
                if stripped[0].isupper():
                    starts_new = True

        # Indentation or special markers
        if line.startswith('   ') or line.startswith('\t'):
            starts_new = True

        # Chapter/section headers
        if re.match(r'^(CHAPTER|PART|SECTION|LECTURE)\s+[IVXLCDM\d]+', stripped, re.IGNORECASE):
            starts_new = True

        if starts_new and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = []

        current_para.append(stripped)

    # Don't forget the last paragraph
    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def extract_pdf_pymupdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF with improved quality."""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    all_lines = []

    for page_num, page in enumerate(doc):
        # Extract text blocks (preserves reading order better)
        blocks = page.get_text("blocks")

        page_lines = []
        for block in blocks:
            if block[6] == 0:  # Text block (not image)
                text = block[4]
                lines = text.split('\n')

                for line in lines:
                    # Filter out headers/footers
                    if not is_header_footer(line, page_num, total_pages):
                        page_lines.append(line)

        all_lines.extend(page_lines)

        # Add a marker between pages to help with paragraph detection
        all_lines.append('')

    doc.close()

    # Clean the extracted text
    raw_text = '\n'.join(all_lines)
    text = clean_extracted_text(raw_text)

    # Merge into proper paragraphs
    lines = text.split('\n')
    text = merge_paragraphs(lines)

    # Final cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


def process_all_pdfs(input_dir: str, output_dir: str):
    """Process all PDFs in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")

        try:
            text = extract_pdf_pymupdf(str(pdf_file))

            # Save extracted text
            output_file = output_path / f"{pdf_file.stem}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            char_count = len(text)
            para_count = text.count('\n\n') + 1
            print(f"  Saved: {char_count:,} chars, ~{para_count} paragraphs")

        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "raw/pdfs"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted"
    process_all_pdfs(input_dir, output_dir)
