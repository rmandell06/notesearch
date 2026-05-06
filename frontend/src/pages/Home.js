import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";
import UploadArea from "../components/UploadArea";
import StatsPanel from "../components/StatsPanel";
import { getRecentNotes, getConnections } from "../api";

const EMPTY_GRAPH = { nodes: [], links: [] };

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);
  const [notes, setNotes] = useState([]);
  const [graph, setGraph] = useState(EMPTY_GRAPH);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      getRecentNotes()
        .then((data) => {
          const list = data.notes ?? data;
          if (Array.isArray(list)) setNotes(list);
        })
        .catch(() => {}),
      getConnections()
        .then((data) => {
          if (data && Array.isArray(data.nodes)) setGraph(data);
        })
        .catch(() => {}),
    ]).finally(() => setLoading(false));
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
          <p className="subtle" style={{ fontSize: 12 }}>
            {notes.length} {notes.length === 1 ? "note" : "notes"}
          </p>
        </div>

        {!loading && notes.length === 0 ? (
          <div
            className="glass r-xl text-center"
            style={{ padding: "56px 24px" }}
          >
            <p className="serif italic" style={{ fontSize: 22, color: "var(--ink)", margin: 0 }}>
              Your library is empty.
            </p>
            <p className="muted" style={{ marginTop: 8, fontSize: 13 }}>
              Upload a note to get started — it'll appear here once indexed.
            </p>
            <button
              onClick={() => setShowUpload(true)}
              className="btn-accent mt-4"
              style={{ marginTop: 20 }}
            >
              + Upload your first note
            </button>
          </div>
        ) : (
          <div className="grid-2 gap-3">
            {notes.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
