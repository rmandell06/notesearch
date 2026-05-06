import { useState, useRef } from "react";
import { uploadFile } from "../api";

export default function UploadArea({ onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRef = useRef(null);
  const uidRef = useRef(0);

  function nextId() { uidRef.current += 1; return uidRef.current; }

  function addFiles(incoming) {
    const entries = Array.from(incoming).map((file) => ({
      id: nextId(), file, status: "uploading", error: null,
    }));
    setFiles((prev) => [...prev, ...entries]);
    entries.forEach(({ id, file }) => runUpload(id, file));
  }
  function runUpload(id, file) {
    uploadFile(file)
      .then((result) => {
        setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status: "done" } : f)));
        onUploaded?.(result);
      })
      .catch((err) =>
        setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status: "error", error: err.message } : f)))
      );
  }
  function handleDrop(e) { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }
  function handleChange(e) { addFiles(e.target.files); e.target.value = ""; }
  function removeFile(id) { setFiles((prev) => prev.filter((f) => f.id !== id)); }

  const statusColor = {
    uploading: "var(--ink-muted)",
    done: "var(--accent-deep)",
    error: "var(--error)",
  };

  return (
    <div>
      <div
        role="region"
        aria-label="File upload area"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="glass r-xl text-center"
        style={{
          padding: "48px 24px",
          cursor: "pointer",
          borderStyle: "dashed",
          borderColor: dragging ? "var(--accent)" : "var(--hairline-2)",
          borderWidth: 1.5,
          background: dragging ? "var(--accent-soft)" : "var(--glass)",
          transition: "all 200ms ease",
        }}
      >
        <input ref={inputRef} type="file" multiple onChange={handleChange} style={{ display: "none" }} data-testid="file-input" />
        <svg width="32" height="32" fill="none" strokeWidth="1.5" viewBox="0 0 24 24"
             stroke={dragging ? "var(--accent)" : "var(--ink-muted)"}
             style={{ marginBottom: 12 }}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0-3.5 3.5M12 4l3.5 3.5" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
        <p className="serif" style={{ fontSize: 18, fontWeight: 600, color: "var(--ink)", margin: 0 }}>
          Drop a file{" "}
          <span className="serif italic" style={{ color: "var(--accent)", fontWeight: 400 }}>or browse</span>
        </p>
        <p className="subtle" style={{ marginTop: 6, fontSize: 12 }}>.txt · .md · .pdf</p>
      </div>

      {files.length > 0 && (
        <ul style={{ marginTop: 12, padding: 0, listStyle: "none" }} aria-label="Uploaded files">
          {files.map(({ id, file, status, error }, i) => (
            <li
              key={id}
              className="glass r-md row between"
              style={{ padding: "10px 16px", marginBottom: 6, fontSize: 13 }}
            >
              <div className="row gap-3 flex-1" style={{ minWidth: 0 }}>
                <span className="clamp-1" style={{ color: "var(--ink)" }} data-testid="file-name">{file.name}</span>
                <span className="shrink-0" style={{ color: statusColor[status], fontSize: 11 }} data-testid={`file-status-${i}`}>
                  {status === "error" ? error : status === "done" ? "✓ done" : "uploading…"}
                </span>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(id); }}
                className="btn-icon"
                style={{ marginLeft: 12 }}
                aria-label={`Remove ${file.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
