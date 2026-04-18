import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getNote } from "../api";

const MOCK_NOTES = {
  "1": {
    title: "Meeting notes — Q2 planning",
    date: "Mar 30, 2026",
    tags: ["meetings", "planning"],
    body: `We kicked off the Q2 planning session with a review of Q1 outcomes. Overall velocity was good, though the search indexing pipeline ran behind due to infra delays.

Key priorities for Q2:
- Improve search UX: result ranking transparency, snippet highlighting
- Onboarding flow for new users uploading their first notes
- Performance benchmarks for the embedding pipeline (target: <200ms p95)
- Begin work on the connections graph view

Action items:
- [ ] Draft UX mockups for snippet highlighting (Aashna)
- [ ] Profile embedding latency on the staging cluster (Bobby)
- [ ] Write onboarding copy and wireframes (design team)

Next sync: April 10th.`,
  },
  "2": {
    title: "Research: vector embeddings",
    date: "Mar 27, 2026",
    tags: ["research", "ml", "search"],
    body: `Spent time comparing retrieval strategies for semantic search.

**Cosine similarity vs dot product**
Both work for unit-normalized vectors. Cosine is more robust when vectors aren't normalized. Dot product is faster at scale.

**Sentence Transformers**
all-MiniLM-L6-v2 is a solid baseline: fast, small (~80MB), good quality on general text. For longer documents, chunking at ~256 tokens with 32-token overlap gives better recall.

**BM25 vs dense retrieval**
BM25 handles keyword-heavy queries well and has no inference cost. Dense models win on paraphrase, synonym matching, and cross-lingual tasks. Hybrid approaches (combine both scores) tend to outperform either alone.

**Next steps:** Test a hybrid retrieval pipeline. Evaluate recall@10 on a held-out note set.`,
  },
  "3": {
    title: "Book notes — Thinking Fast and Slow",
    date: "Mar 22, 2026",
    tags: ["books", "psychology"],
    body: `Daniel Kahneman's framework of System 1 (fast, intuitive) vs System 2 (slow, deliberate) thinking.

**Key concepts:**

Anchoring bias — estimates are heavily influenced by an initial number, even when people know it's arbitrary. Experiment: spin a wheel landing on 10 or 65, then ask what % of African countries are in the UN. The wheel number shifts answers significantly.

Availability heuristic — we judge probability by how easily examples come to mind. Plane crashes feel more likely than car crashes because they get more media coverage.

WYSIATI (What You See Is All There Is) — our minds construct coherent narratives from available information without flagging what's missing.

Loss aversion — losses hurt roughly twice as much as equivalent gains feel good. This explains why people hold losing stocks too long.`,
  },
  "4": {
    title: "Notes on information retrieval",
    date: "Mar 18, 2026",
    tags: ["research", "ir"],
    body: `Classic IR vs modern neural approaches.

TF-IDF weights terms by frequency in a document relative to frequency across the corpus. Rare terms in a document get high weight. Simple and interpretable.

BM25 improves on TF-IDF with document length normalization and a saturation function for term frequency. Still a competitive baseline for keyword search.

Dense retrieval encodes queries and documents into a shared embedding space. Models like DPR (Dense Passage Retrieval) are trained end-to-end on question-answer pairs. Much better at handling natural language variation.

ColBERT (Contextualized Late Interaction) keeps token-level representations and scores with MaxSim — better quality than single-vector dense, faster than cross-encoder reranking.`,
  },
};

const TAG_PALETTE = [
  { color: "#00e5ff", shadow: "rgba(0,229,255,0.35)" },
  { color: "#bf5af2", shadow: "rgba(191,90,242,0.35)" },
  { color: "#32d74b", shadow: "rgba(50,215,75,0.35)" },
  { color: "#ff9f0a", shadow: "rgba(255,159,10,0.35)" },
  { color: "#ff375f", shadow: "rgba(255,55,95,0.35)" },
];

export default function NoteViewer() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    getNote(id)
      .then((data) => setNote(data))
      .catch(() => {
        const fallback = MOCK_NOTES[id];
        if (fallback) {
          setNote(fallback);
        } else {
          setError("Note not found");
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="min-h-screen">
      <header
        className="px-6 py-4 flex items-center gap-4"
        style={{ borderBottom: "1px solid #1a1a2e" }}
      >
        <button
          onClick={() => navigate(-1)}
          className="mono text-xs transition-colors flex items-center gap-1"
          style={{ color: "#3a3a5a" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#00e5ff")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#3a3a5a")}
        >
          ← back
        </button>
        <a href="/" className="mono text-base font-bold tracking-tight neon-cyan" style={{ textDecoration: "none" }}>
          note<span style={{ color: "#bf5af2", textShadow: "0 0 8px rgba(191,90,242,0.55)" }}>search</span>
          <span style={{ color: "#3a3a5a" }}>.app</span>
        </a>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-10 pb-20">
        {loading && (
          <p className="mono text-xs text-center py-10" style={{ color: "#3a3a5a" }} role="status">
            loading...
          </p>
        )}

        {error && !loading && (
          <div className="text-center py-10">
            <p className="mono text-xs mb-4" style={{ color: "#3a3a5a" }}>// {error}</p>
            <button
              onClick={() => navigate(-1)}
              className="mono text-xs transition-colors"
              style={{ color: "#00e5ff", textShadow: "0 0 8px rgba(0,229,255,0.4)" }}
            >
              ← go back
            </button>
          </div>
        )}

        {note && !loading && (
          <>
            <div className="mb-8">
              <h1 className="text-xl font-semibold mb-3" style={{ color: "#e2e2f0" }}>
                {note.title}
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="mono text-xs" style={{ color: "#252540" }}>{note.date}</span>
                {note.tags?.length > 0 && (
                  <>
                    <span style={{ color: "#1e1e32" }}>·</span>
                    <div className="flex gap-2 flex-wrap">
                      {note.tags.map((tag, i) => {
                        const p = TAG_PALETTE[i % TAG_PALETTE.length];
                        return (
                          <span
                            key={tag}
                            className="mono text-xs px-2 py-0.5 rounded"
                            style={{
                              color: p.color,
                              background: `${p.color}12`,
                              border: `1px solid ${p.color}30`,
                              textShadow: `0 0 8px ${p.shadow}`,
                            }}
                          >
                            #{tag}
                          </span>
                        );
                      })}
                    </div>
                  </>
                )}
              </div>
            </div>

            <div
              className="rounded-xl p-6"
              style={{ background: "#0e0e1c", border: "1.5px solid #1a1a2e" }}
            >
              <pre
                className="whitespace-pre-wrap text-sm leading-relaxed"
                style={{ fontFamily: "'Space Mono', monospace", color: "#8888aa" }}
              >
                {note.body ?? note.raw_content ?? note.processed_content}
              </pre>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
