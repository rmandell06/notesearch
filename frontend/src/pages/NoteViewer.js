import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { getNote, getConnections } from "../api";
import { gradientClass } from "../lib/colors";
import { safeBody } from "../lib/text";

const MOCK_NOTES = {
  "1": {
    id: "1", title: "Q2 planning", date: "Mar 30, 2026", source: "text",
    body: `We kicked off the Q2 planning session with a review of Q1 outcomes. Velocity was good, though the search indexing pipeline ran behind due to infra delays.

Key priorities for Q2:
- Improve search UX: result ranking transparency, snippet highlighting
- Onboarding flow for new users uploading their first notes
- Performance benchmarks for the embedding pipeline (target: <200ms p95)
- Begin work on the connections graph view`,
  },
};

export default function NoteViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true); setError(null);
    getNote(id)
      .then((data) => setNote(data))
      .catch(() => {
        const fallback = MOCK_NOTES[id];
        if (fallback) setNote(fallback); else setError("Note not found");
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    getConnections()
      .then((graph) => {
        const links = (graph.links ?? []).filter((l) => l.source === id || l.target === id);
        const otherIds = links
          .map((l) => ({ id: l.source === id ? l.target : l.source, value: l.value }))
          .sort((a, b) => b.value - a.value).slice(0, 5);
        const nodeById = new Map((graph.nodes ?? []).map((n) => [n.id, n]));
        setRelated(otherIds.map(({ id: oid, value }) => {
          const n = nodeById.get(oid);
          return n ? { ...n, similarity: value } : null;
        }).filter(Boolean));
      })
      .catch(() => setRelated([]));
  }, [id]);

  return (
    <AppShell>
      <button onClick={() => navigate(-1)} className="btn-ghost mb-8" style={{ marginLeft: -12 }}>
        ← Back
      </button>

      {loading && (
        <p className="serif italic text-center" style={{
          fontSize: 24, color: "var(--ink-muted)", padding: "60px 0",
        }}>loading…</p>
      )}

      {error && !loading && (
        <div className="text-center" style={{ padding: "80px 0" }}>
          <p className="serif italic" style={{ fontSize: 28 }}>{error}</p>
        </div>
      )}

      {note && !loading && (
        <article className="rise">
          <header className="row gap-6 mb-10" style={{ alignItems: "flex-end" }}>
            <div
              className={gradientClass(note.id ?? note.title)}
              style={{ width: 132, height: 132, borderRadius: 18, flexShrink: 0 }}
              aria-hidden="true"
            />
            <div className="flex-1">
              <p className="eyebrow mb-3">Note</p>
              <h1 className="display" style={{
                fontSize: "clamp(36px, 5vw, 60px)", lineHeight: 1.05, margin: 0, marginBottom: 12,
              }}>
                {note.title}
              </h1>
              <div className="row gap-3 muted" style={{ fontSize: 12 }}>
                <span>{note.date}</span>
                {note.source && (<>
                  <span className="subtle">·</span>
                  <span style={{ textTransform: "capitalize" }}>{note.source}</span>
                </>)}
              </div>
            </div>
          </header>

          <div className="glass-2 r-xl mb-10" style={{ padding: 36 }}>
            <pre className="serif" style={{
              whiteSpace: "pre-wrap", lineHeight: 1.7,
              fontVariationSettings: '"opsz" 14',
              fontSize: 16, color: "var(--ink-soft)", margin: 0,
            }}>
              {safeBody(note.body ?? note.content ?? note.raw_content ?? "")}
            </pre>
          </div>

          {related.length > 0 && (
            <section className="fade delay-2">
              <p className="eyebrow mb-4">Related notes</p>
              <div className="col gap-2">
                {related.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => navigate(`/note/${r.id}`)}
                    className="glass r-md row gap-3"
                    style={{
                      padding: 12, textAlign: "left", width: "100%",
                      transition: "background 200ms",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--glass-2)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "var(--glass)")}
                  >
                    <div
                      className={gradientClass(r.id ?? r.title)}
                      style={{ width: 36, height: 36, borderRadius: 8, flexShrink: 0 }}
                    />
                    <div className="flex-1">
                      <p className="serif clamp-1" style={{
                        fontSize: 15, fontWeight: 600, margin: 0, color: "var(--ink)",
                      }}>{r.title}</p>
                      <div className="row gap-2 mt-1">
                        <div style={{
                          flex: 1, height: 3, background: "var(--hairline-2)",
                          borderRadius: 999, overflow: "hidden",
                        }}>
                          <div style={{
                            width: `${Math.round(r.similarity * 100)}%`,
                            height: "100%", background: "var(--accent)",
                          }} />
                        </div>
                        <span className="muted tabular" style={{ fontSize: 11 }}>
                          {Math.round(r.similarity * 100)}%
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}
        </article>
      )}
    </AppShell>
  );
}
