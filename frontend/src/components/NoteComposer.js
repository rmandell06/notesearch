import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createNote } from "../api";
import MathText from "./MathText";

/**
 * Inline note editor. Two-pane: textarea on the left, live KaTeX preview
 * on the right (collapses to single-pane on narrow screens).
 *
 * The user types LaTeX inline ($…$, $$…$$, \begin{align}…), sees it render
 * in real time, and clicks Create — which POSTs to /notes/ and navigates
 * to the new note's viewer page.
 */
export default function NoteComposer({ onClose }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const note = await createNote(title.trim(), content);
      navigate(`/note/${note.id}`);
    } catch (err) {
      setError(err.message || "Failed to create note");
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="glass r-xl"
      style={{ padding: 20 }}
    >
      <input
        type="text"
        placeholder="Note title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        autoFocus
        required
        className="input-glass"
        style={{ marginBottom: 12, fontSize: 17, fontWeight: 500 }}
      />

      <div className="grid-2 gap-4">
        {/* Editor */}
        <div className="col gap-2">
          <p className="eyebrow">Editor</p>
          <textarea
            placeholder={`Start writing…\n\nLaTeX is supported:  $\\sigma^2 = \\frac{1}{n}\\sum (x_i - \\mu)^2$`}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="input-glass"
            rows={14}
            style={{
              resize: "vertical",
              fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
              fontSize: 13,
              lineHeight: 1.6,
              minHeight: 280,
            }}
          />
        </div>

        {/* Preview */}
        <div className="col gap-2">
          <p className="eyebrow">Preview</p>
          <div
            className="glass r-md"
            style={{
              padding: "14px 16px",
              minHeight: 280,
              fontFamily: "var(--font-display)",
              fontSize: 15,
              lineHeight: 1.7,
              color: "var(--ink-soft)",
              fontVariationSettings: '"opsz" 14',
              overflow: "auto",
            }}
          >
            {content.trim() ? (
              <MathText text={content} />
            ) : (
              <p className="serif italic subtle" style={{ margin: 0 }}>
                Live preview appears here as you type.
              </p>
            )}
          </div>
        </div>
      </div>

      {error && (
        <p
          role="alert"
          style={{
            color: "var(--error)",
            fontSize: 12,
            marginTop: 12,
            padding: "8px 12px",
            borderRadius: 6,
            background: "var(--error-soft, rgba(194,65,12,0.08))",
            border: "1px solid rgba(194,65,12,0.25)",
          }}
        >
          {error}
        </p>
      )}

      <div className="row end gap-3" style={{ marginTop: 16 }}>
        <button
          type="button"
          onClick={onClose}
          className="btn-ghost"
          disabled={saving}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving || !title.trim()}
          className="btn-primary"
        >
          {saving ? "Saving…" : "Create note"}
        </button>
      </div>
    </form>
  );
}
