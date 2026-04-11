import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";
import UploadArea from "../components/UploadArea";

const RECENT_NOTES = [
  {
    id: "1",
    title: "Meeting notes — Q2 planning",
    preview: "Discussed roadmap priorities for Q2. Key themes: search UX, onboarding flow, and performance benchmarks...",
    date: "Mar 30, 2026",
  },
  {
    id: "2",
    title: "Research: vector embeddings",
    preview: "Explored cosine similarity vs dot product for nearest-neighbor search. Sentence transformers outperform...",
    date: "Mar 27, 2026",
  },
  {
    id: "3",
    title: "Book notes — Thinking Fast and Slow",
    preview: "System 1 vs System 2 thinking. Anchoring bias affects estimates even when people know the anchor is random...",
    date: "Mar 22, 2026",
  },
];

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);
  const navigate = useNavigate();

  function handleSearch(query) {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <div className="min-h-screen">
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid #1a1a2e" }}
      >
        <span className="mono text-base font-bold tracking-tight neon-cyan">
          note<span style={{ color: "#bf5af2", textShadow: "0 0 8px rgba(191,90,242,0.55)" }}>search</span>
          <span style={{ color: "#3a3a5a" }}>.app</span>
        </span>
        <nav className="flex gap-6 text-sm" style={{ color: "#4a4a6a" }}>
          <a href="/" style={{ color: "#4a4a6a" }} className="hover:text-white transition-colors">home</a>
          <button
            onClick={() => setShowUpload((v) => !v)}
            className="hover:text-white transition-colors cursor-pointer mono text-xs"
            style={{ color: showUpload ? "#00e5ff" : "#4a4a6a" }}
          >
            {showUpload ? "[ close ]" : "[ upload ]"}
          </button>
        </nav>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-20 pb-16">
        <div className="text-center mb-12">
          <p className="mono text-xs mb-3" style={{ color: "#3a3a5a", letterSpacing: "0.15em" }}>
            semantic note search
          </p>
          <h1 className="mono text-4xl font-bold mb-4 gradient-text" style={{ lineHeight: 1.15 }}>
            find what you<br />actually meant
          </h1>
          <p className="text-sm" style={{ color: "#4a4a6a" }}>
            search by meaning, not just keywords — your notes, semantically indexed
          </p>
        </div>

        <SearchBar onSearch={handleSearch} />

        {showUpload && (
          <div className="mt-8">
            <UploadArea />
          </div>
        )}

        <section className="mt-16">
          <h2
            className="mono text-xs mb-5"
            style={{ color: "#3a3a5a", letterSpacing: "0.18em" }}
          >
            // recent notes
          </h2>
          <div className="flex flex-col gap-3">
            {RECENT_NOTES.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
