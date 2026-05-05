import { useState } from "react";

export default function SearchBar({ onSearch, initialValue = "", autoFocus = false, large = false }) {
  const [value, setValue] = useState(initialValue);

  function handleSubmit(e) {
    e.preventDefault();
    onSearch(value);
  }

  return (
    <form onSubmit={handleSubmit} role="search" style={{ width: "100%" }}>
      <div className={`search-pill ${large ? "lg" : ""}`}>
        <span className="search-icon">
          <svg width={large ? 20 : 16} height={large ? 20 : 16} fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </span>
        <input
          type="search"
          aria-label="Search notes"
          autoFocus={autoFocus}
          placeholder="Search by meaning…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        {value && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setValue("")}
            className="btn-icon"
            style={{ marginRight: 4 }}
          >
            ✕
          </button>
        )}
        <button type="submit" className="btn-accent">
          Search
        </button>
      </div>
    </form>
  );
}
