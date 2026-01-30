# JungRAG

A retrieval-augmented generation (RAG) system for exploring Carl Jung's collected works. Ask questions about Jungian psychology and receive answers grounded in primary sources with citations.

**Live demo:** [jung-chat.vercel.app](https://jung-chat.vercel.app)

## Overview

This project indexes 34 volumes of Jung's writings (~47,000 text chunks) into a vector database, enabling semantic search over millions of words. When you ask a question:

1. Your query is converted to a vector embedding
2. The most semantically similar text chunks are retrieved from Pinecone
3. Retrieved context is passed to Claude for grounded response generation
4. You receive an answer with citations to the source texts

## Tech Stack

**Frontend & API**
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS
- Deployed on Vercel

**AI & Search**
- Claude (Anthropic) for response generation
- Pinecone for vector storage and semantic search
- multilingual-e5-large embeddings (1024 dimensions)

**Data Processing**
- Python scripts for PDF/EPUB extraction
- Custom text cleaning for OCR artifacts
- Semantic chunking with chapter detection

## Project Structure

```
jung-chat/
├── src/
│   └── app/
│       ├── api/chat/       # RAG API endpoint
│       │   └── route.ts    # Query → Retrieve → Generate
│       ├── page.tsx        # Main exploration interface
│       ├── process/        # Technical documentation page
│       └── globals.css     # Styling
├── processing/             # Data pipeline (Python)
│   ├── extract_pdf.py      # PDF text extraction
│   ├── extract_epub.py     # EPUB text extraction
│   ├── clean_text.py       # OCR artifact correction
│   ├── chunk_text.py       # Semantic chunking
│   ├── upload_to_pinecone.py  # Vector indexing
│   └── requirements.txt
├── public/                 # Static assets
└── package.json
```

## Setup

### Prerequisites

- Node.js 18+
- Python 3.9+ (for data processing)
- Pinecone account
- Anthropic API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/jadddon/jung-chat.git
cd jung-chat
```

2. Install dependencies
```bash
npm install
```

3. Set up environment variables
```bash
cp .env.example .env.local
```

Edit `.env.local` with your API keys:
```
ANTHROPIC_API_KEY=your_anthropic_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=jung-works
```

4. Run the development server
```bash
npm run dev
```

### Data Processing Pipeline

To process source texts and populate the vector database:

```bash
cd processing
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run pipeline steps
python extract_pdf.py      # Extract text from PDFs
python extract_epub.py     # Extract text from EPUBs
python clean_text.py       # Clean OCR artifacts
python chunk_text.py       # Create semantic chunks
python upload_to_pinecone.py  # Index vectors
```

## Architecture

### RAG Pipeline

```
User Query
    ↓
Generate Query Embedding (multilingual-e5-large)
    ↓
Semantic Search (Pinecone, top-k=6)
    ↓
Filter by Relevance (score > 0.7, max 3)
    ↓
Build Context with Citations
    ↓
Generate Response (Claude)
    ↓
Return Answer + Sources
```

### Key Design Decisions

- **Chunk size**: 400 tokens target, 600 max. Balances retrieval precision with context preservation.
- **Similarity threshold**: 0.7 minimum. Ensures only highly relevant context reaches the LLM.
- **Embedding model**: multilingual-e5-large for strong semantic understanding of philosophical text.
- **Citation style**: Numbered references [1], [2] linking to work title and chapter.

## License

MIT
