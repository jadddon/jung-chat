"use client";

import Link from "next/link";

export default function ProcessPage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[var(--bg-primary)]/90 backdrop-blur-md">
        <div className="max-w-2xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link href="/" className="text-lg font-medium tracking-tight text-[var(--text-primary)] hover:text-[var(--text-secondary)] transition-colors">
            JungRAG
          </Link>
          <span className="text-sm text-[var(--text-tertiary)]">Technical Process</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-12">
        {/* Title */}
        <div className="mb-16">
          <h1 className="text-3xl font-normal tracking-tight mb-4">
            Building a RAG System for Jung&apos;s Works
          </h1>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            A technical overview of how this retrieval-augmented generation system was built,
            from raw PDF extraction to semantic search and LLM integration.
          </p>
        </div>

        {/* Table of Contents */}
        <nav className="mb-16 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)]">
          <h2 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-4">Contents</h2>
          <ol className="space-y-2 text-[14px]">
            <li><a href="#overview" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">1. System Overview</a></li>
            <li><a href="#extraction" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">2. Text Extraction</a></li>
            <li><a href="#cleaning" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">3. Text Cleaning</a></li>
            <li><a href="#chunking" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">4. Semantic Chunking</a></li>
            <li><a href="#embeddings" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">5. Vector Embeddings</a></li>
            <li><a href="#retrieval" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">6. Semantic Retrieval</a></li>
            <li><a href="#generation" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">7. LLM Integration</a></li>
            <li><a href="#frontend" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">8. Frontend Architecture</a></li>
          </ol>
        </nav>

        {/* Content */}
        <article className="space-y-16">

          {/* Section 1: Overview */}
          <section id="overview">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">1. System Overview</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                Retrieval-Augmented Generation (RAG) combines the knowledge retrieval capabilities of search systems
                with the natural language generation of large language models. Instead of relying solely on an LLM&apos;s
                training data, RAG retrieves relevant context from a curated knowledge base at query time.
              </p>
              <p>
                This system indexes 34 volumes of Jung&apos;s writings—approximately 47,000 text chunks totaling
                millions of words—into a vector database. When a user asks a question, the system:
              </p>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                <li>Converts the query into a vector embedding</li>
                <li>Finds the most semantically similar text chunks</li>
                <li>Passes those chunks as context to Claude</li>
                <li>Returns a grounded response with citations</li>
              </ol>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px]">
                <div className="text-[var(--text-tertiary)] mb-2">// Pipeline overview</div>
                <div className="text-[var(--text-secondary)]">
                  PDF/EPUB → Extract → Clean → Chunk → Embed → Index → Query → Retrieve → Generate
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Extraction */}
          <section id="extraction">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">2. Text Extraction</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                The source material was collected from{" "}
                <a href="https://en.wikipedia.org/wiki/Anna%27s_Archive" target="_blank" rel="noopener noreferrer" className="text-[var(--text-primary)] hover:underline">
                  Anna&apos;s Archive
                </a>
                . The corpus consists of PDFs and EPUBs of varying quality—some are clean digital
                publications, others are OCR scans from the 1950s with significant artifacts.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">PDF extraction</strong> uses PyMuPDF (fitz) to extract text
                while preserving reading order. For scanned documents, the extracted text often contains OCR errors
                like &quot;j u n g&quot; instead of &quot;Jung&quot; or broken hyphenation across page boundaries.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">EPUB extraction</strong> parses the XML/HTML structure
                to extract text content while stripping formatting tags, preserving semantic structure like chapters
                and sections where possible.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># PDF extraction with PyMuPDF</div>
                <pre className="text-[var(--text-secondary)]">{`import fitz  # PyMuPDF

def extract_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text`}</pre>
              </div>
            </div>
          </section>

          {/* Section 3: Cleaning */}
          <section id="cleaning">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">3. Text Cleaning</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                Raw extracted text requires extensive cleaning before it&apos;s suitable for semantic search.
                The cleaning pipeline handles several categories of issues:
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">OCR artifact correction:</strong> Fixes character spacing
                errors (&quot;j u n g&quot; → &quot;Jung&quot;), corrects common OCR misreadings, and removes scanning artifacts
                like &quot;Copyrighted Material&quot; watermarks that appear throughout some volumes.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Structural cleaning:</strong> Removes front matter (title pages,
                copyright notices, tables of contents) and back matter (indices, bibliographies) that would add noise
                to semantic search without adding value.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Normalization:</strong> Standardizes unicode characters,
                fixes broken hyphenation across line/page breaks, normalizes whitespace, and ensures consistent
                paragraph boundaries.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># OCR artifact correction</div>
                <pre className="text-[var(--text-secondary)]">{`def clean_ocr_artifacts(text):
    # Fix spaced-out names
    text = re.sub(r"j\\s+u\\s+n\\s+g", "Jung", text, flags=re.I)
    text = re.sub(r"f\\s+r\\s+e\\s+u\\s+d", "Freud", text, flags=re.I)

    # Remove watermarks
    text = re.sub(r"Copyrighted Material\\s*", "", text, flags=re.I)

    # Fix broken hyphenation
    text = re.sub(r"(\\w+)-\\n(\\w+)", r"\\1\\2", text)

    return text`}</pre>
              </div>
            </div>
          </section>

          {/* Section 4: Chunking */}
          <section id="chunking">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">4. Semantic Chunking</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                Chunking is perhaps the most critical step in RAG pipeline design. The goal is to split text into
                segments that are small enough to be relevant (a full book chapter would dilute the signal) but
                large enough to preserve context (a single sentence loses meaning).
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Target size:</strong> Chunks target 400 tokens with a
                maximum of 600 tokens. This balances retrieval precision with context preservation—small enough
                that retrieved chunks are topically focused, large enough that they contain complete thoughts.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Boundary detection:</strong> The chunker respects semantic
                boundaries. It never splits mid-sentence—chunks end at sentence boundaries (periods, question marks).
                Where possible, it also preserves paragraph structure, preferring to break at paragraph boundaries
                over mid-paragraph.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Chapter detection:</strong> Each chunk is tagged with its
                source chapter, detected through regex patterns matching headers like &quot;CHAPTER VII&quot;,
                &quot;Part Two&quot;, or &quot;Lecture 3&quot;. This metadata enables citation.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Concept tagging:</strong> Chunks are automatically tagged
                with Jungian concepts they contain (shadow, anima, individuation, etc.) using keyword detection.
                This enriches the metadata for potential filtered searches.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># Chunking parameters</div>
                <pre className="text-[var(--text-secondary)]">{`TARGET_TOKENS = 400
MAX_TOKENS = 600
MIN_TOKENS = 80

# Result: 47,576 chunks from 34 volumes
# Average chunk: ~350 tokens
# Chunk metadata: work_title, chapter, concepts[],
#                 prev_chunk_id, next_chunk_id`}</pre>
              </div>
            </div>
          </section>

          {/* Section 5: Embeddings */}
          <section id="embeddings">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">5. Vector Embeddings</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                Vector embeddings are the mathematical foundation of semantic search. An embedding model converts
                text into a high-dimensional vector (a list of numbers) that captures semantic meaning—texts with
                similar meanings have vectors that are close together in this space.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">The model:</strong> This system uses Pinecone&apos;s
                multilingual-e5-large model, which produces 1024-dimensional embeddings. The &quot;e5&quot; architecture
                is trained contrastively on text pairs, learning to place semantically similar texts nearby in
                vector space.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">The linear algebra:</strong> Each text chunk becomes a
                point in 1024-dimensional space. To find relevant chunks for a query, we compute the cosine
                similarity between the query vector and all chunk vectors:
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)]">
                <div className="text-center text-[var(--text-secondary)] font-mono text-[14px] mb-4">
                  cos(θ) = (A · B) / (||A|| × ||B||)
                </div>
                <p className="text-[13px] text-[var(--text-tertiary)]">
                  Where A · B is the dot product and ||A|| is the magnitude. Cosine similarity ranges from -1
                  (opposite) to 1 (identical), with higher scores indicating greater semantic similarity.
                </p>
              </div>
              <p>
                <strong className="text-[var(--text-primary)]">Query prefixing:</strong> The e5 model uses instruction
                prefixes—passages are prefixed with &quot;passage: &quot; during indexing, and queries are prefixed with
                &quot;query: &quot; during search. This asymmetric approach improves retrieval quality.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># Embedding generation</div>
                <pre className="text-[var(--text-secondary)]">{`# During indexing (each chunk)
text = "passage: " + chunk.text
embedding = model.encode(text)  # → [0.023, -0.041, ..., 0.018]  (1024 dims)

# During query
query = "query: What is the shadow?"
query_embedding = model.encode(query)

# Similarity search returns top-k nearest neighbors`}</pre>
              </div>
            </div>
          </section>

          {/* Section 6: Retrieval */}
          <section id="retrieval">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">6. Semantic Retrieval</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                <strong className="text-[var(--text-primary)]">Vector database:</strong> The 47,576 chunk embeddings are
                stored in Pinecone, a managed vector database optimized for similarity search. Pinecone uses
                approximate nearest neighbor (ANN) algorithms to search billions of vectors in milliseconds.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">ANN indexing:</strong> Exact nearest neighbor search
                requires comparing the query against every vector—O(n) complexity. Pinecone uses hierarchical
                navigable small world (HNSW) graphs to achieve approximate results in O(log n) time, trading
                a small amount of recall for massive speed gains.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Retrieval strategy:</strong> For each query, the system
                retrieves the top 6 chunks by cosine similarity, then filters to only those with similarity
                scores above 0.7 (70% match), keeping at most 3. This ensures only highly relevant context
                reaches the LLM.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># Retrieval with filtering</div>
                <pre className="text-[var(--text-secondary)]">{`async function queryPinecone(query: string) {
  const embedding = await generateQueryEmbedding(query);

  const results = await index.query({
    vector: embedding,
    topK: 6,
    includeMetadata: true,
  });

  // Filter to high-relevance only
  return results.matches
    .filter(m => m.score > 0.7)
    .slice(0, 3);
}`}</pre>
              </div>
            </div>
          </section>

          {/* Section 7: Generation */}
          <section id="generation">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">7. LLM Integration</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                <strong className="text-[var(--text-primary)]">Context injection:</strong> Retrieved chunks are formatted
                and injected into Claude&apos;s system prompt. Each chunk is numbered [1], [2], etc., with its source
                (work title and chapter) clearly marked. This gives Claude both the content and the citation
                information needed for grounded responses.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Prompt engineering:</strong> The system prompt instructs
                Claude to be conversational rather than academic, to keep responses concise (2-4 sentences for
                simple questions), and to only cite sources when directly quoting. This creates a more natural
                interaction pattern.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Grounding:</strong> Because Claude receives the actual
                source text, it can accurately represent Jung&apos;s ideas rather than relying on its training data
                (which may contain inaccuracies or lack depth). The citations provide verifiability.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># System prompt structure</div>
                <pre className="text-[var(--text-secondary)]">{`const systemPrompt = \`
You're a knowledgeable guide to Jung's psychology.
Be concise and conversational.

Rules:
- Keep responses to 2-4 sentences max
- Only cite [1], [2] when directly quoting
- Sound like a knowledgeable friend, not a textbook

Sources:
[1] Memories, Dreams, Reflections, Ch. 6
"The shadow is a moral problem that challenges..."

[2] Archetypes of the Collective Unconscious
"The shadow personifies everything that the subject..."
\`;`}</pre>
              </div>
            </div>
          </section>

          {/* Section 8: Frontend */}
          <section id="frontend">
            <h2 className="text-xl font-medium mb-6 pb-2 border-b border-[var(--border)]">8. Frontend Architecture</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                <strong className="text-[var(--text-primary)]">Stack:</strong> The frontend is built with Next.js 14
                using the App Router, deployed on Vercel. The API route handles the RAG pipeline—embedding the
                query, searching Pinecone, calling Claude, and returning the response with sources.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Serverless architecture:</strong> The entire backend runs
                as a serverless function. Each request spins up an isolated instance, calls the external APIs
                (Pinecone for retrieval, Anthropic for generation), and returns. No persistent server to maintain.
              </p>
              <p>
                <strong className="text-[var(--text-primary)]">Exploration UX:</strong> The interface is designed for
                exploration rather than linear chat. Each query creates an expandable card showing the response
                and sources. Related concepts are extracted from responses and offered as follow-up queries,
                encouraging users to explore connections between Jung&apos;s ideas.
              </p>
              <div className="my-8 p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] font-mono text-[13px] overflow-x-auto">
                <div className="text-[var(--text-tertiary)] mb-2"># API route flow</div>
                <pre className="text-[var(--text-secondary)]">{`export async function POST(request: NextRequest) {
  const { query } = await request.json();

  // 1. Retrieve relevant chunks
  const sources = await queryPinecone(query);

  // 2. Build context for Claude
  const context = formatSourcesForPrompt(sources);

  // 3. Generate response
  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 550,
    system: buildSystemPrompt(context),
    messages: [{ role: "user", content: query }],
  });

  // 4. Return with sources for citation
  return NextResponse.json({
    message: response.content[0].text,
    sources: sources,
  });
}`}</pre>
              </div>
            </div>
          </section>

          {/* Summary */}
          <section className="pt-8 border-t border-[var(--border)]">
            <h2 className="text-xl font-medium mb-6">Summary</h2>
            <div className="space-y-4 text-[15px] text-[var(--text-secondary)] leading-[1.8]">
              <p>
                This RAG system demonstrates how to make a large corpus of specialized text accessible through
                natural language queries. The key technical decisions—chunk size, embedding model, retrieval
                filtering, prompt design—all compound to determine the quality of the final output.
              </p>
              <p>
                The result is a system that can answer questions about Jungian psychology with responses
                grounded in primary sources, complete with citations that allow users to explore further
                in the original texts.
              </p>
            </div>
          </section>

        </article>

        {/* Back link */}
        <div className="mt-16 pt-8 border-t border-[var(--border)]">
          <Link
            href="/"
            className="text-[14px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
          >
            ← Back to JungRAG
          </Link>
        </div>
      </main>
    </div>
  );
}
