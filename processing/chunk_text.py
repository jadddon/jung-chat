"""Text Chunking - Splits cleaned text into semantic chunks for vector DB."""

import re
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Set
import tiktoken

# Chunk configuration
TARGET_TOKENS = 400
MAX_TOKENS = 600
MIN_TOKENS = 80

# Jungian concepts for tagging
JUNGIAN_CONCEPTS = {
    "anima": r"\banima\b",
    "animus": r"\banimus\b",
    "shadow": r"\bshadow\b",
    "self": r"\bSelf\b",  # Capital S for Jungian Self
    "ego": r"\bego\b",
    "individuation": r"\bindividuation\b",
    "archetype": r"\barchetype",
    "collective_unconscious": r"collective unconscious",
    "personal_unconscious": r"personal unconscious",
    "complex": r"\bcomplex(es)?\b",
    "persona": r"\bpersona\b",
    "synchronicity": r"\bsynchronicity\b",
    "mandala": r"\bmandala",
    "quaternity": r"\bquaternity\b",
    "coniunctio": r"\bconiunctio\b",
    "projection": r"\bprojection\b",
    "transference": r"\btransference\b",
    "libido": r"\blibido\b",
    "introversion": r"\bintroversion\b",
    "extraversion": r"\bextraversion\b",
    "feeling": r"\bfeeling\s+(function|type)",
    "thinking": r"\bthinking\s+(function|type)",
    "sensation": r"\bsensation\s+(function|type)",
    "intuition": r"\bintuition\s+(function|type)",
    "alchemy": r"\balchem",
    "dream": r"\bdream(s|ing)?\b",
    "symbol": r"\bsymbol",
    "myth": r"\bmyth",
    "religion": r"\breligion|\breligious\b",
    "god_image": r"\bgod[- ]image|imago dei\b",
    "transformation": r"\btransformation\b",
    "rebirth": r"\brebirth\b",
    "mother": r"\b(mother|maternal)\s*(archetype|complex|image)?",
    "father": r"\b(father|paternal)\s*(archetype|complex|image)?",
    "child": r"\bchild\s*(archetype)?|puer|divine child",
    "wise_old_man": r"wise old man|senex",
    "trickster": r"\btrickster\b",
    "hero": r"\bhero\s*(archetype|myth|journey)?",
}


@dataclass
class Chunk:
    id: str
    text: str
    source_file: str
    work_title: str
    chapter: Optional[str]
    chunk_index: int
    total_chunks: int
    token_count: int
    char_count: int
    start_char: int
    end_char: int
    # New fields for optimizations
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    concepts: List[str] = field(default_factory=list)


def get_tokenizer():
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, tokenizer) -> int:
    return len(tokenizer.encode(text))


def extract_work_metadata(filename: str) -> Dict:
    """Extract metadata from filename (title, year, CW volume)."""
    name = Path(filename).stem

    year_matches = re.findall(r"\((\d{4})\)", name)
    year = year_matches[-1] if year_matches else None

    cw_match = re.search(r"Volume\s*(\d+)", name, re.IGNORECASE)
    cw_volume = cw_match.group(1) if cw_match else None

    title_map = {
        "Letters of C. G. Jung Vol 1": "Letters of C. G. Jung, Vol. 1 (1906-1950)",
        "Letters of C. G. Jung Vol 2": "Letters of C. G. Jung, Vol. 2 (1951-1961)",
        "The Collected Works of Jung I-XX": "The Collected Works of C. G. Jung",
        "Collected-Works-Volume-9i": "Archetypes of the Collective Unconscious (CW 9i)",
        "Freud_Jung letters": "The Freud/Jung Letters",
        "History of Modern History": "History of Modern Psychology (ETH Lectures Vol. 1)",
        "Jung Contra Freud": "Jung Contra Freud",
        "practice of psychotherapy": "The Practice of Psychotherapy (CW 16)",
        "Active Imagination": "Jung on Active Imagination",
        "Analytical Psychology in Exile": "Analytical Psychology in Exile: Jung-Neumann Correspondence",
        "Question of Psychological Types": "The Question of Psychological Types: Jung-Schmid Correspondence",
        "Atom and Archetype": "Atom and Archetype: The Pauli/Jung Letters",
        "On Theology and Psychology": "On Theology and Psychology: Jung-Keller Correspondence",
        "Psychology of Kundalini": "The Psychology of Kundalini Yoga (1932 Seminar)",
        "Psychology of Yoga and Meditation": "Psychology of Yoga and Meditation (ETH Lectures Vol. 6)",
        "Ignatius of Loyola": "Jung on Ignatius of Loyola (ETH Lectures Vol. 7)",
        "Dream Symbols of the Individuation": "Dream Symbols of the Individuation Process",
        "Children's Dreams": "Children's Dreams (1936-1940 Seminar)",
        "Dream Interpretation Ancient": "Dream Interpretation Ancient and Modern (1936-1941 Seminar)",
        "Seminar on Dream Analysis": "Seminar on Dream Analysis (1928-1930)",
        "Analytical Psychology_ Notes of the Seminar": "Analytical Psychology (1925 Seminar)",
        "Introduction to Jungian psychology": "Introduction to Jungian Psychology (1925 Seminar)",
        "Visions _ Notes": "Visions Seminar (1930-1934)",
        "Zarathustra": "Nietzsche's Zarathustra (1934-1939 Seminar)",
        "On Psychological and Visionary Art": "On Psychological and Visionary Art: Nerval's Aurélia",
        "Red Book": "The Red Book: A Reader's Edition",
        "Man and His Symbols": "Man and His Symbols",
        "Memories, Dreams, Reflections": "Memories, Dreams, Reflections",
        "Modern Man in Search": "Modern Man in Search of a Soul",
        "Psychology of the Unconscious": "Psychology of the Unconscious",
        "Selected Letters": "Selected Letters of C. G. Jung",
        "C. G. Jung Speaking": "C. G. Jung Speaking: Interviews and Encounters",
    }

    title = None
    for key, mapped in title_map.items():
        if key.lower() in name.lower():
            title = mapped
            break

    if not title:
        title = name
        title = re.sub(r"^\([^)]+\)\s*", "", title)
        if " - " in title:
            parts = title.split(" - ")
            title = parts[1] if len(parts) >= 2 else title
        title = title.replace("_", " ")
        title = re.sub(r"\s*-\s*(Princeton|Routledge|Norton|Vintage).*$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*\(\d{4}\)\s*$", "", title)
        title = re.sub(r"\s+", " ", title).strip()

    if year and not re.search(r"\(\d{4}", title):
        title = f"{title} ({year})"

    return {"title": title.strip(), "year": year, "cw_volume": cw_volume}


def find_chapter_markers(text: str, source_file: str) -> List[Dict]:
    """Find chapter/section boundaries in text with source-aware patterns."""
    markers = []

    # Standard patterns for seminars, CW, etc.
    standard_patterns = [
        (r"^(CHAPTER|Chapter)\s+([IVXLCDM\d]+)[\s:.]*(.*)$", "Chapter"),
        (r"^(PART|Part)\s+([IVXLCDM\d]+)[\s:.]*(.*)$", "Part"),
        (r"^(SECTION|Section)\s+([IVXLCDM\d]+)[\s:.]*(.*)$", "Section"),
        (r"^(LECTURE|Lecture)\s+([IVXLCDM\d]+)[\s:.]*(.*)$", "Lecture"),
        (r"^(Seminar)\s+(\d+)[\s:.]*(.*)$", "Seminar"),
    ]

    # Date patterns for letters/correspondence
    date_patterns = [
        (r"^(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})$", "Letter"),
        (r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})$", "Letter"),
        (r"^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$", "Letter"),  # "To Sigmund Freud"
    ]

    # MDR chapter patterns
    mdr_patterns = [
        (r"^(Prologue|First Years|School Years|Student Years|Psychiatric Activities|Sigmund Freud|Confrontation with the Unconscious|The Work|The Tower|Travels|Visions|On Life after Death|Late Thoughts|Retrospect)$", "Chapter"),
    ]

    # CW essay title patterns (ALL CAPS titles)
    cw_patterns = [
        (r"^([A-Z][A-Z\s]{10,60})$", "Essay"),  # All caps title
    ]

    is_letters = "letters" in source_file.lower() or "correspondence" in source_file.lower()
    is_mdr = "memories" in source_file.lower() and "dreams" in source_file.lower()
    is_cw = "collected works" in source_file.lower() or "C.G.Jung -" in source_file

    char_pos = 0
    for line in text.split("\n"):
        stripped = line.strip()

        # Try standard patterns
        for pattern, marker_type in standard_patterns:
            match = re.match(pattern, stripped)
            if match:
                markers.append({
                    "char_index": char_pos,
                    "type": marker_type,
                    "number": match.group(2) if len(match.groups()) >= 2 else "",
                    "title": match.group(3).strip() if len(match.groups()) >= 3 else "",
                })
                break

        # Try date patterns for letters
        if is_letters and not markers or (markers and markers[-1]["char_index"] != char_pos):
            for pattern, marker_type in date_patterns:
                match = re.match(pattern, stripped)
                if match:
                    markers.append({
                        "char_index": char_pos,
                        "type": marker_type,
                        "number": "",
                        "title": stripped,
                    })
                    break

        # Try MDR patterns
        if is_mdr and not markers or (markers and markers[-1]["char_index"] != char_pos):
            for pattern, marker_type in mdr_patterns:
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    markers.append({
                        "char_index": char_pos,
                        "type": marker_type,
                        "number": "",
                        "title": match.group(1),
                    })
                    break

        # Try CW essay patterns
        if is_cw and len(stripped) > 10 and not markers or (markers and markers[-1]["char_index"] != char_pos):
            for pattern, marker_type in cw_patterns:
                match = re.match(pattern, stripped)
                if match and not any(skip in stripped for skip in ["CHAPTER", "PART", "SECTION", "LECTURE"]):
                    markers.append({
                        "char_index": char_pos,
                        "type": marker_type,
                        "number": "",
                        "title": stripped.title(),
                    })
                    break

        char_pos += len(line) + 1

    return markers


def is_index_content(text: str) -> bool:
    """Check if text looks like index content."""
    page_refs = len(re.findall(r",\s*\d{1,4}(?:\s*-\s*\d{1,4})?", text))
    words = len(text.split())
    if words < 10:
        return False
    return page_refs > words * 0.15


def detect_concepts(text: str) -> List[str]:
    """Detect Jungian concepts in text."""
    concepts = []
    text_lower = text.lower()
    for concept, pattern in JUNGIAN_CONCEPTS.items():
        if re.search(pattern, text, re.IGNORECASE):
            concepts.append(concept)
    return concepts


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving sentence integrity."""
    text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Jr|Sr|vs|etc|i\.e|e\.g|vol|Vol|par|pars|cf|Cf)\.\s+', r'\1<ABBR> ', text)
    text = re.sub(r'\b([A-Z])\.\s+([A-Z])\.\s+', r'\1<ABBR> \2<ABBR> ', text)
    text = re.sub(r'\b(CW|cw)\s+(\d)', r'\1<ABBR>\2', text)

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', text)
    sentences = [s.replace('<ABBR>', '.') for s in sentences]
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def create_chunks(text: str, source_file: str) -> List[Chunk]:
    """Create semantic chunks - preserving paragraph structure, no overlap."""
    tokenizer = get_tokenizer()
    metadata = extract_work_metadata(source_file)
    chapter_markers = find_chapter_markers(text, source_file)

    def get_chapter_at(pos: int) -> Optional[str]:
        for marker in reversed(chapter_markers):
            if marker["char_index"] <= pos:
                title_part = f": {marker['title']}" if marker['title'] else ""
                number_part = f" {marker['number']}" if marker['number'] else ""
                return f"{marker['type']}{number_part}{title_part}"
        return None

    chunks = []
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    current_paragraphs = []  # List of (paragraph_text, sentences) tuples
    current_tokens = 0
    current_chapter = None
    chunk_start_char = 0
    char_position = 0

    def save_chunk(para_list: List[tuple], start: int, end: int):
        if not para_list:
            return

        # Join paragraphs with \n\n, sentences within paragraphs with space
        content_parts = []
        for para_text, sentences in para_list:
            content_parts.append(" ".join(sentences))
        content = "\n\n".join(content_parts)

        tokens = count_tokens(content, tokenizer)
        if tokens < MIN_TOKENS and chunks:
            return

        chunk_id = hashlib.md5(f"{source_file}:{start}:{end}:{len(chunks)}".encode()).hexdigest()[:16]

        # Detect concepts in this chunk
        concepts = detect_concepts(content)

        chunks.append(Chunk(
            id=chunk_id,
            text=content,
            source_file=source_file,
            work_title=metadata["title"],
            chapter=current_chapter,
            chunk_index=len(chunks),
            total_chunks=0,
            token_count=tokens,
            char_count=len(content),
            start_char=start,
            end_char=end,
            concepts=concepts,
        ))

    for para in paragraphs:
        para_start = text.find(para, char_position)
        if para_start == -1:
            para_start = char_position
        para_end = para_start + len(para)

        # Skip index-like content
        if is_index_content(para):
            char_position = para_end
            continue

        # Check for chapter change
        new_chapter = get_chapter_at(para_start)
        if new_chapter != current_chapter:
            if current_paragraphs:
                save_chunk(current_paragraphs, chunk_start_char, char_position)
                current_paragraphs = []
                current_tokens = 0
            current_chapter = new_chapter
            chunk_start_char = para_start

        # Split paragraph into sentences
        sentences = split_into_sentences(para)
        para_tokens = count_tokens(para, tokenizer)

        # If adding this paragraph exceeds target, save current chunk first
        if current_tokens + para_tokens > TARGET_TOKENS and current_paragraphs:
            save_chunk(current_paragraphs, chunk_start_char, para_start)
            current_paragraphs = []
            current_tokens = 0
            chunk_start_char = para_start

        # Handle very large paragraphs by splitting at sentence boundaries
        if para_tokens > MAX_TOKENS:
            # Save any current content first
            if current_paragraphs:
                save_chunk(current_paragraphs, chunk_start_char, para_start)
                current_paragraphs = []
                current_tokens = 0
                chunk_start_char = para_start

            # Split this paragraph into smaller chunks
            current_sents = []
            current_sent_tokens = 0
            for sent in sentences:
                sent_tokens = count_tokens(sent, tokenizer)
                if current_sent_tokens + sent_tokens > TARGET_TOKENS and current_sents:
                    # Save current sentences as a chunk
                    save_chunk([(para, current_sents)], chunk_start_char, para_end)
                    current_sents = []
                    current_sent_tokens = 0
                    chunk_start_char = para_start

                current_sents.append(sent)
                current_sent_tokens += sent_tokens

            # Add remaining sentences to current paragraphs
            if current_sents:
                current_paragraphs.append((para, current_sents))
                current_tokens = current_sent_tokens
        else:
            # Add paragraph to current chunk
            current_paragraphs.append((para, sentences))
            current_tokens += para_tokens

        char_position = para_end

    # Save final chunk
    if current_paragraphs:
        save_chunk(current_paragraphs, chunk_start_char, len(text))

    # Update total_chunks and add prev/next IDs
    for i, chunk in enumerate(chunks):
        chunk.total_chunks = len(chunks)
        if i > 0:
            chunk.prev_chunk_id = chunks[i - 1].id
        if i < len(chunks) - 1:
            chunk.next_chunk_id = chunks[i + 1].id

    return chunks


def add_embedding_prefix(chunks: List[Dict]) -> List[Dict]:
    """Add E5 embedding prefix to chunk text for better retrieval."""
    for chunk in chunks:
        # E5 models use "passage: " prefix for documents
        chunk["text_for_embedding"] = f"passage: {chunk['text']}"
    return chunks


def process_all(input_dir: str, output_dir: str):
    """Process all cleaned texts into chunks."""
    input_path, output_path = Path(input_dir), Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    for txt_file in sorted(input_path.glob("*.txt")):
        print(f"Chunking: {txt_file.name}")
        try:
            text = txt_file.read_text(encoding='utf-8')
            chunks = create_chunks(text, txt_file.name)

            print(f"  Created {len(chunks)} chunks")
            if chunks:
                avg = sum(c.token_count for c in chunks) / len(chunks)
                with_concepts = sum(1 for c in chunks if c.concepts)
                with_chapter = sum(1 for c in chunks if c.chapter)
                print(f"  Avg tokens: {avg:.0f}, with concepts: {with_concepts}, with chapter: {with_chapter}")

            output_file = output_path / f"{txt_file.stem}_chunks.json"
            chunk_dicts = [asdict(c) for c in chunks]
            output_file.write_text(json.dumps(chunk_dicts, indent=2))
            all_chunks.extend(chunks)

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Convert to dicts and add embedding prefix
    all_chunk_dicts = [asdict(c) for c in all_chunks]
    all_chunk_dicts = add_embedding_prefix(all_chunk_dicts)

    # Save combined file
    combined = output_path / "_all_chunks.json"
    combined.write_text(json.dumps(all_chunk_dicts, indent=2))
    print(f"\nTotal: {len(all_chunks)} chunks -> {combined}")

    # Print concept summary
    concept_counts = {}
    for chunk in all_chunks:
        for concept in chunk.concepts:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
    print("\nTop concepts detected:")
    for concept, count in sorted(concept_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {concept}: {count}")


if __name__ == "__main__":
    process_all(
        sys.argv[1] if len(sys.argv) > 1 else "cleaned",
        sys.argv[2] if len(sys.argv) > 2 else "chunks"
    )
