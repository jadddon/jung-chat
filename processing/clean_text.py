"""
Text Cleaning Script for Carl Jung Works

This script removes:
- Table of contents
- Indexes and indices
- Forewords (unless by Jung himself)
- Commentaries and editorial notes
- Translator's notes
- Publisher information
- Page headers/footers
- Footnote markers (preserving footnote content where it's Jung's)

Preserves:
- All text written by Jung
- Jung's own footnotes
- Chapter titles and structure
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# Patterns to identify sections to REMOVE
REMOVE_PATTERNS = [
    # Table of contents variations
    r"(?i)^\s*table\s+of\s+contents?\s*$",
    r"(?i)^\s*contents?\s*$",
    r"(?i)^\s*INHALT\s*$",  # German
    # Index sections
    r"(?i)^\s*index\s*$",
    r"(?i)^\s*subject\s+index\s*$",
    r"(?i)^\s*name\s+index\s*$",
    r"(?i)^\s*general\s+index\s*$",
    # Forewords and introductions (not by Jung)
    r"(?i)^\s*foreword\s*$",
    r"(?i)^\s*editor\'?s?\s+(note|preface|introduction|foreword)\s*$",
    r"(?i)^\s*translator\'?s?\s+(note|preface|introduction|foreword)\s*$",
    r"(?i)^\s*publisher\'?s?\s+note\s*$",
    r"(?i)^\s*editorial\s+note\s*$",
    r"(?i)^\s*introduction\s+by\s+(?!c\.?g\.?\s*jung|carl\s+(gustav\s+)?jung)",
    r"(?i)^\s*preface\s+by\s+(?!c\.?g\.?\s*jung|carl\s+(gustav\s+)?jung)",
    # Bibliography and references (editorial)
    r"(?i)^\s*bibliography\s*$",
    r"(?i)^\s*references\s*$",
    r"(?i)^\s*works\s+cited\s*$",
    r"(?i)^\s*suggested\s+reading\s*$",
    r"(?i)^\s*further\s+reading\s*$",
    # Appendices (often editorial)
    r"(?i)^\s*appendix\s*:\s*chronolog",
    r"(?i)^\s*appendix\s*:\s*bibliograph",
    # Copyright and publication info
    r"(?i)^\s*copyright\s*©?\s*\d{4}",
    r"(?i)^\s*all\s+rights\s+reserved",
    r"(?i)^\s*isbn[\s:-]*[\d-]+",
    r"(?i)^\s*library\s+of\s+congress",
    r"(?i)^\s*printed\s+in\s+(the\s+)?(united\s+states|usa|u\.s\.a\.|great\s+britain|uk)",
    r"(?i)^\s*published\s+by\s+",
    r"(?i)^\s*first\s+(published|edition|printing)",
]

# Patterns for headers/footers to remove (usually page numbers, running headers)
HEADER_FOOTER_PATTERNS = [
    r"^\s*\d+\s*$",  # Just page numbers
    r"^\s*[-—]\s*\d+\s*[-—]\s*$",  # Page numbers with dashes
    r"^\s*(chapter|part)\s+[IVXLCDM\d]+\s*$",  # Chapter/part headers alone
    r"^\s*C\.?\s*G\.?\s*JUNG\s*$",  # Author name as header
    r"^\s*CARL\s+JUNG\s*$",
    r"^\s*THE\s+COLLECTED\s+WORKS\s*$",
]

# Patterns indicating Jung's own content (KEEP these)
JUNG_CONTENT_PATTERNS = [
    r"(?i)^\s*(preface|foreword|introduction)\s+by\s+(c\.?g\.?\s*jung|carl\s+(gustav\s+)?jung)",
    r"(?i)^\s*author\'?s?\s+(preface|foreword|note|introduction)",
    r"(?i)^\s*jung\'?s?\s+(preface|foreword|note)",
]


def is_section_to_remove(line: str) -> bool:
    """Check if line indicates start of a section to remove"""
    for pattern in REMOVE_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def is_jung_content(line: str) -> bool:
    """Check if line indicates Jung's own content"""
    for pattern in JUNG_CONTENT_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def is_header_footer(line: str) -> bool:
    """Check if line is likely a header/footer"""
    for pattern in HEADER_FOOTER_PATTERNS:
        if re.match(pattern, line.strip()):
            return True
    return False


def clean_page_markers(text: str) -> str:
    """Remove [PAGE X] markers but preserve structure"""
    text = re.sub(r"\[PAGE\s+\d+\]", "", text)
    return text


def is_toc_line(line: str) -> bool:
    """Check if a line looks like a TOC entry"""
    stripped = line.strip()
    if not stripped:
        return False

    toc_patterns = [
        # Roman numeral entries (I., II., III., etc.)
        r"^\s*[IVXLCDM]+\.?\s*$",
        # Roman numeral with date (seminar listings)
        r"^\s*[IVXLCDM]+\.?\s+\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)",
        # Chapter/Part listings
        r"(?i)^\s*(chapter|part|section|lecture|seminar)\s+\d+",
        # Page number references (roman or arabic)
        r"^\s*[ivxlcdm]+\s*$",
        r"^\s*[IVXLCDM]+\s*$",
        r"^\s*\d{1,4}\s*$",
        # Section titles with page numbers
        r"(?i)^\s*(introduction|preface|foreword|acknowledgments?|bibliography|index|contents)\s*[ivxlcdm]*\s*$",
        # Lines that are just titles (all caps, short)
        r"^[A-Z][A-Z\s]{2,30}$",
        # Date-only lines
        r"^\s*\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\s*$",
    ]
    return any(re.match(p, stripped, re.IGNORECASE) for p in toc_patterns)


def is_prose_paragraph(line: str) -> bool:
    """Check if a line looks like actual prose content"""
    stripped = line.strip()
    if len(stripped) < 80:  # Too short to be a real paragraph
        return False

    # Must start with a capital letter or quote
    if not re.match(r'^[A-Z"\']', stripped):
        return False

    # Must contain multiple words with lowercase letters
    words = stripped.split()
    if len(words) < 10:
        return False

    # Check for sentence-like structure (has periods, commas)
    if not re.search(r'[,.]', stripped):
        return False

    # Should have a mix of upper and lower case (not all caps)
    if stripped.isupper():
        return False

    return True


def remove_front_matter(text: str, verbose: bool = False) -> str:
    """
    Remove front matter (copyright, publisher info, TOC) from the beginning.
    Uses a more sophisticated approach to find actual prose content.
    """
    lines = text.split('\n')

    # Patterns indicating we're definitely still in front matter
    front_matter_patterns = [
        r"(?i)copyright",
        r"(?i)all\s+rights\s+reserved",
        r"(?i)isbn",
        r"(?i)library\s+of\s+congress",
        r"(?i)printed\s+in\s+(the\s+)?(united|usa|u\.s)",
        r"(?i)published\s+by",
        r"(?i)bollingen\s+series",
        r"(?i)princeton\s+university\s+press",
        r"(?i)routledge",
        r"(?i)first\s+(edition|printing|published)",
        r"(?i)^\s*table\s+of\s+contents\s*$",
        r"(?i)^\s*contents\s*$",
        r"(?i)^\s*acknowledgments?\s*$",
        r"(?i)^\s*members\s+of\s+the\s+seminar\s*$",
        r"(?i)^\s*list\s+of\s+(abbreviations|illustrations)\s*$",
        r"(?i)^\s*bibliographical\s+note\s*$",
        r"(?i)^\s*chronolog(y|ical)\s*",
    ]

    # Track state
    content_start_idx = 0
    consecutive_prose = 0
    last_front_matter_idx = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this is clearly front matter
        is_front_matter = any(re.search(p, stripped) for p in front_matter_patterns)
        if is_front_matter:
            last_front_matter_idx = i
            consecutive_prose = 0
            continue

        # Check if this looks like a TOC line
        if is_toc_line(stripped):
            consecutive_prose = 0
            continue

        # Check if this looks like prose
        if is_prose_paragraph(stripped):
            consecutive_prose += 1
            # If we see 2+ consecutive prose paragraphs, we've found content
            if consecutive_prose >= 2:
                # Start from the first prose paragraph
                content_start_idx = max(last_front_matter_idx + 1, i - consecutive_prose + 1)
                break
        else:
            # Reset if we see non-prose after prose (might still be in mixed section)
            if consecutive_prose == 1:
                consecutive_prose = 0

        # Safety limit
        if i > 1000:
            break

    if content_start_idx > 0 and verbose:
        print(f"  Removing {content_start_idx} lines of front matter")

    return '\n'.join(lines[content_start_idx:])


def remove_back_matter(text: str, verbose: bool = False) -> str:
    """Remove back matter (index, bibliography) from the end.

    Only removes back matter if:
    1. The pattern is found in the last 15% of the document
    2. The remaining content after removal is at least 85% of original
    """
    lines = text.split('\n')
    total_lines = len(lines)

    if total_lines < 100:
        return text  # Too short to have meaningful back matter

    # Patterns indicating back matter start (must be standalone section headers)
    back_matter_patterns = [
        r"(?i)^\s*index\s*$",
        r"(?i)^\s*subject\s+index\s*$",
        r"(?i)^\s*name\s+index\s*$",
        r"(?i)^\s*general\s+index\s*$",
        r"(?i)^\s*bibliography\s*$",
        r"(?i)^\s*works\s+cited\s*$",
    ]

    # Only search in the last 15% of the document
    search_start = int(total_lines * 0.85)

    back_matter_start = total_lines
    for i in range(total_lines - 1, search_start, -1):
        stripped = lines[i].strip()
        if any(re.match(p, stripped) for p in back_matter_patterns):
            # Verify this looks like a real section header (followed by content)
            # Check that there's substantial content after this point
            remaining_content = '\n'.join(lines[i:])
            if len(remaining_content) > 500:  # Must have some content to be real back matter
                back_matter_start = i
                break

    # Safety check: don't remove more than 15% of the document
    if back_matter_start < int(total_lines * 0.85):
        return text  # Would remove too much, skip

    if back_matter_start < total_lines and verbose:
        print(f"  Removing {total_lines - back_matter_start} lines of back matter")

    return '\n'.join(lines[:back_matter_start])


def identify_section_boundaries(text: str) -> List[Tuple[int, int, str]]:
    """
    Find sections that should be removed.
    Returns list of (start_line, end_line, section_type) tuples.
    """
    lines = text.split("\n")
    sections_to_remove = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this line starts a section to remove
        if is_section_to_remove(line) and not is_jung_content(line):
            section_start = i
            section_type = line

            # Find where this section ends
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()

                # Section ends at next major heading or Jung content
                if is_jung_content(next_line):
                    break
                if re.match(r"(?i)^\s*(chapter|part)\s+[IVXLCDM\d]+", next_line):
                    break
                if re.match(r"(?i)^\s*\d+\.\s+[A-Z]", next_line):  # Numbered chapter
                    break

                j += 1

            sections_to_remove.append((section_start, j, section_type))
            i = j
        else:
            i += 1

    return sections_to_remove


def remove_footnote_markers(text: str) -> str:
    """
    Remove footnote reference numbers but preserve the footnote content.
    Handles various footnote styles: superscript, bracketed, etc.
    """
    # Remove superscript numbers (common in academic texts)
    text = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", text)

    # Remove bracketed numbers like [1], [2], etc. (but keep if followed by actual text)
    # This preserves footnote content while removing inline references
    text = re.sub(r"\[\d+\](?!\s*[A-Z])", "", text)

    return text


def clean_ocr_artifacts(text: str) -> str:
    """Clean common OCR errors and artifacts while preserving paragraph structure"""
    # First, normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove "Copyrighted Material" watermarks
    text = re.sub(r"Copyrighted Material\s*", "", text, flags=re.IGNORECASE)

    # Fix OCR spacing in names (j u n g -> jung, C . G . -> C.G.)
    text = re.sub(r"\bj\s+u\s+n\s+g\b", "Jung", text, flags=re.IGNORECASE)
    text = re.sub(r"\bC\s*\.\s*G\s*\.", "C.G.", text)
    text = re.sub(r"\bM\s*\.\s*D\s*\.", "M.D.", text)
    text = re.sub(r"\bP\s*h\s*\.\s*D\s*\.", "Ph.D.", text)
    # Fix spaced-out words (common OCR issue): "w o r d" -> "word"
    text = re.sub(r"\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\b", r"\1\2\3\4\5", text)
    text = re.sub(r"\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\b", r"\1\2\3\4", text)

    # Normalize quotes and punctuation (safe, doesn't affect structure)
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r"[''']", "'", text)
    text = re.sub(r"…", "...", text)
    text = re.sub(r"—|–", "-", text)

    # Fix hyphenation at line breaks (word-\nword -> wordword)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Normalize multiple spaces (but NOT newlines) to single space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove [PAGE X] markers
    text = re.sub(r"\[PAGE\s+\d+\]", "\n", text)

    # Remove ---CHAPTER BREAK--- markers but preserve the break
    text = re.sub(r"---CHAPTER BREAK---", "\n\n", text)

    # Normalize multiple newlines to max 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean up lines that are just whitespace
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)

    # Remove duplicate blank lines again after stripping
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def clean_text(text: str, verbose: bool = False) -> str:
    """
    Main cleaning function.
    Removes non-Jung content while preserving his writings.
    """
    original_length = len(text)

    # Step 1: Clean OCR artifacts and normalize structure
    text = clean_ocr_artifacts(text)

    # Step 2: Remove front matter (copyright, TOC, etc.)
    text = remove_front_matter(text, verbose=verbose)

    # Step 3: Remove back matter (index, bibliography)
    text = remove_back_matter(text, verbose=verbose)

    # Step 4: Remove header/footer lines (standalone page numbers, etc.)
    lines = text.split("\n")
    lines = [line for line in lines if not is_header_footer(line)]
    text = "\n".join(lines)

    # Step 5: Clean up footnote markers (but keep footnote content)
    text = remove_footnote_markers(text)

    # Step 6: Final cleanup - normalize whitespace while preserving paragraphs
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 newlines (paragraph break)
    text = re.sub(r"[ \t]+", " ", text)  # Single spaces within lines

    # Clean up leading/trailing whitespace on each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)

    # Remove any remaining excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if verbose:
        reduction = 100 * len(text) / original_length if original_length else 0
        print(f"  Reduced from {original_length:,} to {len(text):,} chars ({reduction:.1f}%)")

    return text


def process_directory(input_dir: str, output_dir: str, verbose: bool = True):
    """Process all text files in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_files = list(input_path.glob("*.txt"))
    if not txt_files:
        print(f"No text files found in {input_dir}")
        return

    for txt_file in txt_files:
        print(f"Cleaning: {txt_file.name}")

        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()

            cleaned = clean_text(text, verbose=verbose)

            output_file = output_path / txt_file.name
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned)

            print(f"  Saved to: {output_file}")

        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "extracted"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "cleaned"
    process_directory(input_dir, output_dir)
