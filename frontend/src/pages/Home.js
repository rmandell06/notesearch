import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";
import UploadArea from "../components/UploadArea";
import StatsPanel from "../components/StatsPanel";
import { getRecentNotes, getConnections } from "../api";

const FALLBACK_NOTES = [
  { id: "1", title: "Q2 planning", preview: "Roadmap priorities, search UX, onboarding, embedding pipeline.", date: "Mar 30", source: "text" },
  { id: "2", title: "Vector embeddings", preview: "Cosine similarity vs dot product, sentence transformers, BM25.", date: "Mar 27", source: "text" },
  { id: "3", title: "Thinking, Fast and Slow", preview: "System 1 vs 2, anchoring, availability heuristic, loss aversion.", date: "Mar 22", source: "upload" },
  { id: "4", title: "Information retrieval", preview: "TF-IDF, BM25, dense retrieval, ColBERT.", date: "Mar 18", source: "text" },
];
const FALLBACK_GRAPH = {
  nodes: FALLBACK_NOTES.map((n) => ({ id: n.id, title: n.title })),
  links: [
    { source: "2", target: "4", value: 0.88 },
    { source: "1", target: "2", value: 0.61 },
    { source: "1", target: "4", value: 0.55 },
    { source: "3", target: "1", value: 0.38 },
  ],
};

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);
  const [notes, setNotes] = useState(FALLBACK_NOTES);
  const [graph, setGraph] = useState(FALLBACK_GRAPH);
  const navigate = useNavigate();

  useEffect(() => {
    getRecentNotes()
      .then((data) => {
        const list = data.notes ?? data;
        if (Array.isArray(list) && list.length > 0) setNotes(list);
      })
      .catch(() => {});
    getConnections()
      .then((data) => {
        if (data && Array.isArray(data.nodes) && data.nodes.length > 0) setGraph(data);
      })
      .catch(() => {});
  }, []);

  function handleSearch(q) {
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <AppShell>
      {/* HERO — centered, single column */}
      <section className="text-center mb-12">
        <p className="eyebrow rise mb-4">Semantic note search</p>
        <h1 className="display rise delay-1" style={{
          fontSize: "clamp(56px, 9vw, 104px)",
          marginBottom: 16,
        }}>
          Search by{" "}
          <span className="serif italic" style={{ color: "var(--accent)", fontWeight: 500 }}>
            meaning.
          </span>
        </h1>
        <p className="muted rise delay-2" style={{
          fontSize: 16, maxWidth: 540, margin: "0 auto 32px",
        }}>
          A custom transformer encoder, trained on entailment pairs, returns notes that share intent — not just words.
        </p>
        <div className="rise delay-3" style={{ maxWidth: 640, margin: "0 auto" }}>
          <SearchBar onSearch={handleSearch} large />
        </div>
        <div className="rise delay-4 row center mt-4 gap-3">
          <button
            onClick={() => setShowUpload((v) => !v)}
            className={showUpload ? "btn-ghost" : "btn-primary"}
          >
            {showUpload ? "Close uploader" : "+ Upload note"}
          </button>
          <button onClick={() => navigate("/connections")} className="btn-ghost">
            View graph →
          </button>
        </div>
      </section>

      {showUpload && (
        <section className="mb-12 rise">
          <UploadArea />
        </section>
      )}

      {/* STATS DASHBOARD */}
      <section className="mb-14">
        <StatsPanel notes={notes} graph={graph} />
      </section>

      {/* LIBRARY — centered grid */}
      <section className="fade delay-5">
        <div className="row between mb-6" style={{ alignItems: "baseline" }}>
          <h2 className="display" style={{ fontSize: 32, margin: 0 }}>
            Your library
          </h2>
          <p className="subtle" style={{ fontSize: 12 }}>{notes.length} notes</p>
        </div>

        <div className="grid-2 gap-3">
          {notes.map((note) => (
            <NoteCard key={note.id} note={note} />
          ))}
        </div>
      </section>
    </AppShell>
  );
}
