import { useState, useRef } from "react";

export default function UploadArea() {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRef = useRef(null);

  function handleFiles(incoming) {
    const list = Array.from(incoming);
    setFiles((prev) => [...prev, ...list]);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleChange(e) {
    handleFiles(e.target.files);
    e.target.value = "";
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div>
      <div
        role="region"
        aria-label="File upload area"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="px-6 py-10 text-center cursor-pointer rounded-xl transition-all"
        style={
          dragging
            ? {
                background: "rgba(0,229,255,0.04)",
                border: "2px dashed #00e5ff",
                boxShadow: "0 0 24px rgba(0,229,255,0.12), inset 0 0 24px rgba(0,229,255,0.03)",
              }
            : {
                background: "#0e0e1c",
                border: "2px dashed #1e1e32",
              }
        }
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleChange}
          className="hidden"
          data-testid="file-input"
        />
        <div className="flex flex-col items-center gap-2 pointer-events-none">
          <svg
            width="28" height="28" fill="none" strokeWidth="1.5" viewBox="0 0 24 24"
            stroke={dragging ? "#00e5ff" : "#252540"}
            style={dragging ? { filter: "drop-shadow(0 0 6px rgba(0,229,255,0.6))" } : {}}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0-3.5 3.5M12 4l3.5 3.5" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
          </svg>
          <p className="text-sm" style={{ color: "#3a3a5a" }}>
            drop files here or{" "}
            <span
              className="mono text-xs"
              style={{ color: "#00e5ff", textShadow: "0 0 8px rgba(0,229,255,0.4)" }}
            >
              browse
            </span>
          </p>
          <p className="mono text-xs" style={{ color: "#252540", letterSpacing: "0.08em" }}>
            .txt / .md / .pdf
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5" aria-label="Uploaded files">
          {files.map((file, i) => (
            <li
              key={i}
              className="flex items-center justify-between px-3 py-2 rounded-lg text-sm"
              style={{ background: "#0e0e1c", border: "1.5px solid #1a1a2e" }}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="mono text-xs" style={{ color: "#252540" }}>→</span>
                <span
                  className="truncate mono text-xs"
                  style={{ color: "#8888aa" }}
                  data-testid="file-name"
                >
                  {file.name}
                </span>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                className="ml-3 shrink-0 mono text-xs transition-colors"
                style={{ color: "#252540" }}
                onMouseEnter={(e) => (e.target.style.color = "#ff2d55")}
                onMouseLeave={(e) => (e.target.style.color = "#252540")}
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
