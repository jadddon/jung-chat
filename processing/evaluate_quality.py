"""Quick quality evaluation for cleaned text files."""

import re
import sys
from pathlib import Path


def evaluate_file(filepath: Path) -> dict:
    """Evaluate a single file's quality."""
    text = filepath.read_text(encoding='utf-8')

    if not text.strip():
        return {
            'name': filepath.name[:60],
            'chars': 0,
            'lines': 0,
            'paragraphs': 0,
            'avg_para_len': 0,
            'issues': ['EMPTY FILE'],
            'score': 0
        }

    lines = text.split('\n')
    paragraphs = [p for p in text.split('\n\n') if p.strip()]

    issues = []
    score = 100

    # Check for single-line file (all content on one line)
    non_empty_lines = [l for l in lines if l.strip()]
    if len(non_empty_lines) == 1 and len(text) > 1000:
        issues.append('SINGLE LINE (no paragraphs)')
        score -= 50

    # Check paragraph structure
    if paragraphs:
        avg_para = sum(len(p) for p in paragraphs) / len(paragraphs)
        if avg_para > 5000:
            issues.append(f'Paragraphs too long (avg {avg_para:.0f} chars)')
            score -= 20
        elif avg_para < 50:
            issues.append(f'Paragraphs too short (avg {avg_para:.0f} chars)')
            score -= 10
    else:
        avg_para = 0
        issues.append('No paragraphs detected')
        score -= 30

    # Check for TOC remnants
    toc_patterns = [
        r'^\s*[IVXLCDM]+\.\s*\d+\s*$',  # Roman numeral + page number
        r'^\s*Chapter\s+\d+\s*\.+\s*\d+\s*$',  # Chapter...page
    ]
    toc_lines = sum(1 for line in lines if any(re.match(p, line, re.I) for p in toc_patterns))
    if toc_lines > 5:
        issues.append(f'TOC remnants ({toc_lines} lines)')
        score -= 10

    # Check for excessive page numbers
    page_num_lines = sum(1 for line in lines if re.match(r'^\s*\d{1,4}\s*$', line.strip()))
    if page_num_lines > 20:
        issues.append(f'Page numbers ({page_num_lines})')
        score -= 5

    # Check for front matter remnants
    front_patterns = ['copyright', 'isbn', 'all rights reserved', 'library of congress']
    front_found = [p for p in front_patterns if p in text.lower()[:2000]]
    if front_found:
        issues.append(f'Front matter remnants')
        score -= 5

    # Check prose quality (% of lines that look like sentences)
    prose_lines = sum(1 for l in non_empty_lines if len(l) > 60 and re.search(r'[.!?]', l))
    prose_ratio = prose_lines / len(non_empty_lines) if non_empty_lines else 0
    if prose_ratio < 0.3:
        issues.append(f'Low prose ratio ({prose_ratio:.0%})')
        score -= 15

    score = max(0, score)

    return {
        'name': filepath.name[:60],
        'chars': len(text),
        'lines': len(non_empty_lines),
        'paragraphs': len(paragraphs),
        'avg_para_len': int(avg_para),
        'issues': issues,
        'score': score
    }


def main(directory: str = "cleaned"):
    path = Path(directory)
    files = sorted(path.glob("*.txt"))

    if not files:
        print(f"No files found in {directory}")
        return

    results = []
    for f in files:
        result = evaluate_file(f)
        results.append(result)

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    # Print results
    print(f"\n{'File':<62} {'Chars':>10} {'Lines':>7} {'Paras':>6} {'Score':>6}")
    print("=" * 95)

    for r in results:
        name = r['name'][:60] + '..' if len(r['name']) > 60 else r['name']
        issues_str = ', '.join(r['issues']) if r['issues'] else 'OK'
        print(f"{name:<62} {r['chars']:>10,} {r['lines']:>7,} {r['paragraphs']:>6,} {r['score']:>6}")
        if r['issues']:
            print(f"    Issues: {issues_str}")

    # Summary
    good = sum(1 for r in results if r['score'] >= 70)
    avg_score = sum(r['score'] for r in results) / len(results)
    total_chars = sum(r['chars'] for r in results)

    print("=" * 95)
    print(f"Total: {len(results)} files, {total_chars:,} chars, {good} good (>=70), avg score: {avg_score:.1f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cleaned")
