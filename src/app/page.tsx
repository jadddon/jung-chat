"use client";

import { useState, useRef } from "react";
import Link from "next/link";

interface Source {
  work_title: string;
  chapter: string | null;
  text: string;
  score: number;
}

interface Exploration {
  id: string;
  query: string;
  response: string;
  sources: Source[];
  relatedConcepts: string[];
}

// Complete library of sources
const LIBRARY = [
  {
    category: "Major Works",
    works: [
      { title: "Psychology of the Unconscious", year: "1912", wiki: "https://en.wikipedia.org/wiki/Psychology_of_the_Unconscious" },
      { title: "Modern Man in Search of a Soul", year: "1933", wiki: "https://en.wikipedia.org/wiki/Modern_Man_in_Search_of_a_Soul" },
      { title: "Memories, Dreams, Reflections", year: "1961", wiki: "https://en.wikipedia.org/wiki/Memories,_Dreams,_Reflections" },
      { title: "Man and His Symbols", year: "1961", wiki: "https://en.wikipedia.org/wiki/Man_and_His_Symbols" },
      { title: "The Red Book: Liber Novus", year: "1914–30", wiki: "https://en.wikipedia.org/wiki/The_Red_Book_(Jung)" },
      { title: "C. G. Jung Speaking: Interviews", year: "1912–61", wiki: "https://press.princeton.edu/books/paperback/9780691018713/cg-jung-speaking" },
    ]
  },
  {
    category: "Collected Works",
    works: [
      { title: "Archetypes and the Collective Unconscious", year: "1934–55", wiki: "https://press.princeton.edu/books/hardcover/9780691097619/the-collected-works-of-c-g-jung-volume-9-part-1" },
      { title: "The Practice of Psychotherapy", year: "1935–58", wiki: "https://press.princeton.edu/books/paperback/9780691018706/collected-works-of-c-g-jung-volume-16" },
      { title: "Complete Collected Works (Vols. I–XX)", year: "1902–61", wiki: "https://en.wikipedia.org/wiki/Collected_Works_of_C._G._Jung" },
    ]
  },
  {
    category: "Seminars",
    works: [
      { title: "Analytical Psychology", year: "1925", wiki: "https://press.princeton.edu/books/paperback/9780691152059/introduction-to-jungian-psychology" },
      { title: "Dream Analysis", year: "1928–30", wiki: "https://press.princeton.edu/books/hardcover/9780691098968/dream-analysis-volume-i" },
      { title: "Visions", year: "1930–34", wiki: "https://press.princeton.edu/books/hardcover/9780691099712/visions" },
      { title: "Kundalini Yoga", year: "1932", wiki: "https://press.princeton.edu/books/paperback/9780691006765/the-psychology-of-kundalini-yoga" },
      { title: "Nietzsche's Zarathustra", year: "1934–39", wiki: "https://press.princeton.edu/books/paperback/9780691017389/jungs-seminar-on-nietzsches-zarathustra" },
      { title: "Children's Dreams", year: "1936–40", wiki: "https://press.princeton.edu/books/paperback/9780691148076/childrens-dreams" },
      { title: "Dream Interpretation Ancient & Modern", year: "1936–41", wiki: "https://press.princeton.edu/books/paperback/9780691173405/dream-interpretation-ancient-and-modern" },
    ]
  },
  {
    category: "ETH Lectures",
    works: [
      { title: "History of Modern Psychology", year: "1933–34", wiki: "https://press.princeton.edu/books/paperback/9780691210698/history-of-modern-psychology" },
      { title: "Psychology of Yoga and Meditation", year: "1938–40", wiki: "https://press.princeton.edu/books/hardcover/9780691206585/psychology-of-yoga-and-meditation" },
      { title: "Spiritual Exercises of Ignatius Loyola", year: "1939–40", wiki: "https://press.princeton.edu/books/hardcover/9780691244167/jung-on-ignatius-of-loyolas-spiritual-exercises" },
    ]
  },
  {
    category: "Letters",
    works: [
      { title: "Letters Vol. 1", year: "1906–50", wiki: "https://press.princeton.edu/books/hardcover/9780691098951/cg-jung-letters-volume-1" },
      { title: "Letters Vol. 2", year: "1951–61", wiki: "https://press.princeton.edu/books/hardcover/9780691097244/cg-jung-letters-volume-2" },
      { title: "The Freud/Jung Letters", year: "1906–14", wiki: "https://en.wikipedia.org/wiki/The_Freud/Jung_Letters" },
      { title: "Atom and Archetype: Pauli Letters", year: "1932–58", wiki: "https://press.princeton.edu/books/paperback/9780691161471/atom-and-archetype" },
      { title: "Jung–Neumann Correspondence", year: "1934–59", wiki: "https://press.princeton.edu/books/hardcover/9780691166179/analytical-psychology-in-exile" },
      { title: "Jung–White Correspondence", year: "1945–60", wiki: "https://philemonfoundation.org/works/white-letters/" },
    ]
  },
];

const SEED_CONCEPTS = [
  { name: "The Shadow", query: "What is the shadow in Jungian psychology?" },
  { name: "Anima & Animus", query: "Explain the anima and animus archetypes" },
  { name: "Individuation", query: "What is the process of individuation?" },
  { name: "The Self", query: "What does Jung mean by the Self?" },
  { name: "Archetypes", query: "What are archetypes according to Jung?" },
  { name: "Dreams", query: "How did Jung interpret dreams?" },
  { name: "Collective Unconscious", query: "What is the collective unconscious?" },
  { name: "Active Imagination", query: "What is active imagination?" },
];

function formatChapter(chapter: string | null): string | null {
  if (!chapter) return null;

  // Clean up whitespace
  let formatted = chapter.trim().replace(/\s+/g, ' ');

  // Remove common prefixes
  formatted = formatted
    .replace(/^(Chapter|CHAPTER|Ch\.?|Section|SECTION)\s*/i, 'Ch. ')
    .replace(/^(Part|PART)\s*/i, 'Part ');

  // If it's just a number, prefix with "Ch."
  if (/^\d+$/.test(formatted)) {
    formatted = `Ch. ${formatted}`;
  }

  // Truncate if too long
  if (formatted.length > 60) {
    formatted = formatted.substring(0, 57) + '...';
  }

  return formatted;
}

function extractRelatedConcepts(text: string): string[] {
  const concepts = [
    "shadow", "anima", "animus", "self", "ego", "persona", "archetype",
    "unconscious", "collective unconscious", "individuation", "dream",
    "symbol", "mandala", "projection", "complex", "libido", "psyche",
    "introversion", "extraversion", "synchronicity", "alchemy", "transformation"
  ];

  const found = concepts.filter(c =>
    text.toLowerCase().includes(c) && c.length > 4
  );

  return [...new Set(found)]
    .sort(() => Math.random() - 0.5)
    .slice(0, 4)
    .map(c => c.charAt(0).toUpperCase() + c.slice(1));
}

export default function Home() {
  const [explorations, setExplorations] = useState<Exploration[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleExplore = async (query: string) => {
    if (!query.trim() || isLoading) return;

    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [], query }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();
      const newExploration: Exploration = {
        id: Date.now().toString(),
        query,
        response: data.message,
        sources: data.rawSources || [],
        relatedConcepts: extractRelatedConcepts(data.message),
      };

      setExplorations(prev => [newExploration, ...prev]);
      setExpandedId(newExploration.id);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grain">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[var(--bg-primary)]/90 backdrop-blur-md">
        <div className="max-w-2xl mx-auto px-6 py-5 flex items-center justify-between">
          <h1 className="text-lg font-medium tracking-tight text-[var(--text-primary)]">JungRAG</h1>
          {explorations.length > 0 && (
            <button
              onClick={() => {
                setExplorations([]);
                setExpandedId(null);
              }}
              className="text-sm text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        {/* Hero - only show when empty */}
        {explorations.length === 0 && !isLoading && (
          <div className="text-center py-20 animate-fade-in">
            <h2 className="text-3xl md:text-4xl font-normal tracking-tight mb-3 text-[var(--text-primary)]">
              Explore Jung&apos;s ideas
            </h2>
            <p className="text-base text-[var(--text-tertiary)] max-w-sm mx-auto">
              34 volumes of writings, seminars, and letters
            </p>
          </div>
        )}

        {/* Search */}
        <div className="mb-10">
          <form onSubmit={(e) => { e.preventDefault(); handleExplore(input); }}>
            <div className="input-wrapper px-4 py-3">
              <div className="flex items-center gap-3">
                <svg className="w-4 h-4 text-[var(--text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question..."
                  className="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none text-base"
                  disabled={isLoading}
                />
                {(input.trim() || isLoading) && (
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:text-[var(--text-tertiary)] transition-colors"
                  >
                    {isLoading ? (
                      <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin inline-block" />
                    ) : (
                      "Go"
                    )}
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>

        {/* Concept pills - only show when empty */}
        {explorations.length === 0 && !isLoading && (
          <div className="flex flex-wrap justify-center gap-2 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            {SEED_CONCEPTS.map((concept, i) => (
              <button
                key={i}
                onClick={() => handleExplore(concept.query)}
                className="pill"
              >
                {concept.name}
              </button>
            ))}
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && (
          <div className="py-8">
            <div className="space-y-3 animate-pulse-soft">
              <div className="h-3 bg-[var(--bg-tertiary)] rounded w-3/4" />
              <div className="h-3 bg-[var(--bg-tertiary)] rounded w-full" />
              <div className="h-3 bg-[var(--bg-tertiary)] rounded w-5/6" />
            </div>
          </div>
        )}

        {/* Explorations */}
        <div className="space-y-4">
          {explorations.map((exploration, index) => {
            const isExpanded = expandedId === exploration.id;

            return (
              <div
                key={exploration.id}
                className="card overflow-hidden animate-fade-in"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {/* Header */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : exploration.id)}
                  className="w-full px-5 py-4 flex items-start justify-between gap-4 text-left"
                >
                  <h3 className="font-normal text-[var(--text-primary)] text-[15px]">
                    {exploration.query}
                  </h3>
                  <svg
                    className={`w-4 h-4 text-[var(--text-tertiary)] flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Content */}
                <div className={`px-5 pb-5 ${!isExpanded ? 'hidden' : ''}`}>
                  {/* Response */}
                  <div className="text-[var(--text-secondary)] leading-[1.7] whitespace-pre-wrap mb-6 text-[15px]">
                    {exploration.response}
                  </div>

                  {/* Sources */}
                  {exploration.sources.length > 0 && (
                    <div className="mb-6 pt-4 border-t border-[var(--border)]">
                      <div className="space-y-1">
                        {exploration.sources.map((source, si) => {
                          const chapter = formatChapter(source.chapter);
                          return (
                            <div key={si} className="text-[13px] text-[var(--text-tertiary)]">
                              <span className="opacity-50">[{si + 1}]</span>{" "}
                              {source.work_title}{chapter && ` — ${chapter}`}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                </div>

                {/* Preview when collapsed */}
                {!isExpanded && (
                  <div className="px-5 pb-4 -mt-1">
                    <p className="text-[14px] text-[var(--text-tertiary)] line-clamp-2 leading-relaxed">
                      {exploration.response}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>

      {/* Library */}
      <section className="max-w-3xl mx-auto px-6 py-20 border-t border-[var(--border)]">
        <h3 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-widest mb-12 text-center">
          Source Library
        </h3>
        <div className="grid gap-x-12 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
          {LIBRARY.map((section, i) => (
            <div key={i}>
              <h4 className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-4 pb-2 border-b border-[var(--border)]">
                {section.category}
              </h4>
              <ul className="space-y-2.5">
                {section.works.map((work, j) => (
                  <li key={j} className="flex justify-between items-baseline gap-3 group">
                    <span className="text-[13px] text-[var(--text-secondary)] flex items-center gap-1.5">
                      {work.title}
                      <a
                        href={work.wiki}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <svg className="w-3 h-3 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </span>
                    <span className="text-[11px] text-[var(--text-tertiary)] tabular-nums shrink-0">{work.year}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Process link */}
        <div className="mt-12 pt-8 border-t border-[var(--border)] text-center">
          <Link
            href="/process"
            className="text-[13px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
          >
            How this was built →
          </Link>
        </div>
      </section>

    </div>
  );
}
