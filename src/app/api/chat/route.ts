import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { Pinecone } from "@pinecone-database/pinecone";

// Types
interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Source {
  work_title: string;
  chapter: string | null;
  text: string;
  score: number;
}

// Initialize clients
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
});

const pinecone = new Pinecone({
  apiKey: process.env.PINECONE_API_KEY!,
});

// Generate embedding using Pinecone's inference API
async function generateQueryEmbedding(query: string): Promise<number[]> {
  const response = await fetch("https://api.pinecone.io/embed", {
    method: "POST",
    headers: {
      "Api-Key": process.env.PINECONE_API_KEY!,
      "Content-Type": "application/json",
      "X-Pinecone-API-Version": "2024-10",
    },
    body: JSON.stringify({
      model: "multilingual-e5-large",
      inputs: [{ text: `query: ${query}` }],
      parameters: { input_type: "query", truncate: "END" },
    }),
  });

  if (!response.ok) {
    throw new Error(`Embedding API error: ${response.status}`);
  }

  const data = await response.json();
  return data.data[0].values;
}

// Query Pinecone for relevant chunks
async function queryPinecone(query: string, topK: number = 5): Promise<Source[]> {
  const embedding = await generateQueryEmbedding(query);
  const index = pinecone.index(process.env.PINECONE_INDEX || "jung-works");

  const results = await index.query({
    vector: embedding,
    topK,
    includeMetadata: true,
  });

  return results.matches?.map((match) => ({
    work_title: (match.metadata?.work_title as string) || "Unknown",
    chapter: (match.metadata?.chapter as string) || null,
    text: (match.metadata?.text as string) || "",
    score: match.score || 0,
  })) || [];
}

// Format sources for the prompt
function formatSourcesForPrompt(sources: Source[]): string {
  return sources
    .map((source, i) => {
      const citation = source.chapter
        ? `[${i + 1}] ${source.work_title}, ${source.chapter}`
        : `[${i + 1}] ${source.work_title}`;
      return `${citation}\n${source.text}`;
    })
    .join("\n\n---\n\n");
}

// Format sources for response
function formatSourcesForResponse(sources: Source[]): string {
  return sources
    .map((source, i) => {
      const chapter = source.chapter ? `, ${source.chapter}` : "";
      return `[${i + 1}] ${source.work_title}${chapter}`;
    })
    .join("\n");
}

export async function POST(request: NextRequest) {
  try {
    const { messages, query } = await request.json();

    // Get relevant sources from Pinecone
    const allSources = await queryPinecone(query, 6);

    // Filter to only highly relevant sources (score > 0.7)
    const sources = allSources.filter(s => s.score > 0.7).slice(0, 3);

    // Format context from sources
    const context = formatSourcesForPrompt(sources);

    // System prompt for Claude
    const systemPrompt = `You're a knowledgeable guide to Jung's psychology. Be concise and conversational.

Rules:
- Keep responses to 2-4 sentences max
- Be direct, not academic
- Only cite [1], [2] etc. when directly quoting Jung's words
- Don't cite for general concepts - only for specific quotes
- If asked to elaborate, you can go deeper

${sources.length > 0 ? `Sources:\n${context}` : 'No highly relevant sources found - answer from general knowledge of Jung.'}`;

    // Build conversation history for Claude
    const claudeMessages: Anthropic.MessageParam[] = messages.map((msg: Message) => ({
      role: msg.role,
      content: msg.content,
    }));

    // Add the current query
    claudeMessages.push({
      role: "user",
      content: query,
    });

    // Call Claude
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 550,
      system: systemPrompt,
      messages: claudeMessages,
    });

    // Extract response text
    const assistantMessage =
      response.content[0].type === "text" ? response.content[0].text : "";

    // Format sources for display
    const sourcesText = formatSourcesForResponse(sources);

    return NextResponse.json({
      message: assistantMessage,
      sources: sourcesText,
      rawSources: sources,
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}
