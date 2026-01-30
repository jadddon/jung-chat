"""
EPUB Text Extraction Script
Extracts and orders text content from EPUB files with improved quality.
"""

import re
import sys
from pathlib import Path
from typing import List, Optional

# pip install ebooklib beautifulsoup4
from ebooklib import epub, ITEM_DOCUMENT, ITEM_NAVIGATION
from bs4 import BeautifulSoup, NavigableString


def should_skip_item(item, soup: BeautifulSoup) -> bool:
    """Determine if an EPUB item should be skipped (navigation, TOC, etc.)"""
    # Skip navigation items
    if item.get_type() == ITEM_NAVIGATION:
        return True

    # Check filename for navigation indicators
    name = item.get_name().lower()
    skip_names = ['nav', 'toc', 'contents', 'cover', 'title', 'copyright', 'ncx']
    if any(skip in name for skip in skip_names):
        return True

    # Check for nav elements in HTML
    if soup.find('nav'):
        nav_content = soup.find('nav').get_text(strip=True)
        other_content = soup.get_text(strip=True).replace(nav_content, '')
        # If most content is in nav, skip
        if len(other_content) < 100:
            return True

    # Check for landmark/TOC structures
    if soup.find(attrs={'epub:type': 'toc'}) or soup.find(attrs={'epub:type': 'landmarks'}):
        return True

    return False


def extract_text_from_html(html_content: bytes) -> str:
    """Extract clean text from HTML content, preserving paragraph structure."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()

    # Remove elements with navigation roles
    for element in soup.find_all(attrs={'role': 'navigation'}):
        element.decompose()
    for element in soup.find_all(attrs={'epub:type': ['toc', 'landmarks', 'pagebreak']}):
        element.decompose()

    # Extract text with paragraph preservation
    paragraphs = []

    # Process block-level elements
    block_tags = ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'blockquote', 'li', 'td', 'th', 'article', 'section']

    for tag in soup.find_all(block_tags):
        text = tag.get_text(separator=' ', strip=True)
        if text:
            # Clean up whitespace within the text
            text = re.sub(r'\s+', ' ', text)
            paragraphs.append(text)

    # If no block elements found, fall back to body text
    if not paragraphs:
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    return '\n\n'.join(paragraphs)


def get_spine_order(book: epub.EpubBook) -> List[str]:
    """Get the reading order from the spine."""
    spine_ids = [item[0] for item in book.spine]
    id_to_href = {}

    for item in book.get_items():
        if hasattr(item, 'id') and hasattr(item, 'file_name'):
            id_to_href[item.id] = item.file_name

    return [id_to_href.get(sid, sid) for sid in spine_ids]


def extract_epub(epub_path: str) -> str:
    """Extract text from EPUB file with proper ordering and cleaning."""
    book = epub.read_epub(epub_path, options={'ignore_ncx': True})

    # Get spine order for proper chapter sequencing
    spine_order = get_spine_order(book)

    # Build mapping of href to items
    href_to_item = {}
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            href_to_item[item.file_name] = item

    chapters = []
    processed_hrefs = set()

    # Process items in spine order first
    for href in spine_order:
        if href in href_to_item and href not in processed_hrefs:
            item = href_to_item[href]
            processed_hrefs.add(href)

            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # Skip navigation/TOC items
            if should_skip_item(item, soup):
                continue

            text = extract_text_from_html(item.get_content())

            # Skip very short content (likely cover pages, etc.)
            if len(text.strip()) > 100:
                chapters.append(text)

    # Process any remaining items not in spine
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT and item.file_name not in processed_hrefs:
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            if should_skip_item(item, soup):
                continue

            text = extract_text_from_html(item.get_content())

            if len(text.strip()) > 100:
                chapters.append(text)

    # Join chapters with clear separation
    return '\n\n'.join(chapters)


def extract_metadata(epub_path: str) -> dict:
    """Extract metadata from EPUB for context."""
    book = epub.read_epub(epub_path, options={'ignore_ncx': True})

    metadata = {
        'title': '',
        'creator': '',
        'language': '',
        'publisher': '',
        'date': '',
    }

    try:
        title = book.get_metadata('DC', 'title')
        if title:
            metadata['title'] = title[0][0]

        creator = book.get_metadata('DC', 'creator')
        if creator:
            metadata['creator'] = creator[0][0]

        language = book.get_metadata('DC', 'language')
        if language:
            metadata['language'] = language[0][0]

        publisher = book.get_metadata('DC', 'publisher')
        if publisher:
            metadata['publisher'] = publisher[0][0]

        date = book.get_metadata('DC', 'date')
        if date:
            metadata['date'] = date[0][0]
    except Exception:
        pass

    return metadata


def process_all_epubs(input_dir: str, output_dir: str):
    """Process all EPUBs in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    epub_files = list(input_path.glob("*.epub"))
    if not epub_files:
        print(f"No EPUB files found in {input_dir}")
        return

    for epub_file in epub_files:
        print(f"Processing: {epub_file.name}")

        try:
            text = extract_epub(str(epub_file))
            metadata = extract_metadata(str(epub_file))

            output_file = output_path / f"{epub_file.stem}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            char_count = len(text)
            para_count = text.count('\n\n') + 1
            print(f"  Saved: {char_count:,} chars, ~{para_count} paragraphs")
            if metadata.get('title'):
                print(f"  Title: {metadata['title'][:60]}")

        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "raw/epubs"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted"
    process_all_epubs(input_dir, output_dir)
