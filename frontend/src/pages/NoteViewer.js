import { useParams, useNavigate } from "react-router-dom";

const NOTES = {
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

export default function NoteViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const note = NOTES[id];

  if (!note) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Note not found.</p>
          <button onClick={() => navigate(-1)} className="text-sm text-blue-500 hover:underline">
            Go back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="px-6 py-4 border-b border-gray-100 flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-400 hover:text-gray-700 flex items-center gap-1"
        >
          ← Back
        </button>
        <a href="/" className="text-lg font-semibold tracking-tight text-gray-900">NoteSearch</a>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-10 pb-20">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">{note.title}</h1>
          <div className="flex items-center gap-3 text-sm text-gray-400">
            <span>{note.date}</span>
            <span>·</span>
            <div className="flex gap-2">
              {note.tags.map((tag) => (
                <span
                  key={tag}
                  className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-gray-100 pt-6">
          <pre className="whitespace-pre-wrap font-sans text-gray-700 text-sm leading-relaxed">
            {note.body}
          </pre>
        </div>
      </main>
    </div>
  );
}
